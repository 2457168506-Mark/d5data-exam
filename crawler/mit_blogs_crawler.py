# -*- coding: utf-8 -*-
"""
MIT 招生博客爬虫（https://mitadmissions.org/blogs/）。

分工：
  * Playwright   -- 渲染列表页，遍历分页，拿到标题/作者/详情链接和
                    Disqus identifier，并等组件注入评论数作为兜底；
  * DrissionPage -- 用 requests 会话抓详情页，提取时间/正文/正文图片。

评论数首选向 Disqus 的 count-data.js 批量查询（一次可查多篇），
查询失败时回落到列表页组件注入的数字，仍为空则记 0。

输出 CSV（utf-8-sig），表头：Title | Author | Comment Count | Time |
Article Content | Images In Article（图片为绝对地址的 JSON 数组字符串）。

用法：python mit_blogs_crawler.py --pages 3 --out output/mit_blogs.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

BASE_URL = "https://mitadmissions.org/blogs/"
# Disqus 计数接口：?1=<identifier>&1=<identifier>... 返回 DISQUSWIDGETS.displayCount({...})
COUNT_API = "https://mitadmissions.disqus.com/count-data.js"

# 礼貌爬取：详情页间隔 1.5~3.5s，翻页间隔 2~4s
DETAIL_DELAY = (1.5, 3.5)
PAGE_DELAY = (2.0, 4.0)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

# 列表页提取：标题、详情链接、作者、评论数文本、Disqus identifier。
# 注意：页面上的 emoji 会被 WordPress 替换成 <img alt="emoji">，取文本时要用 alt 还原。
LIST_EXTRACT_JS = r"""
() => {
  const text = el => {
    if (!el) return '';
    const c = el.cloneNode(true);
    c.querySelectorAll('img[alt]').forEach(i => i.replaceWith(i.alt));
    return c.textContent.replace(/\s+/g, ' ').trim();
  };
  return Array.from(document.querySelectorAll('main article')).map(art => {
    const h2 = art.querySelector('h2');
    const cc = art.querySelector('a[data-disqus-identifier]');
    return {
      title: text(h2),
      url: h2?.querySelector('a[href*="/blogs/entry/"]')?.href || '',
      author: text(art.querySelector('a[href*="/blogs/author/"]')),
      comments: (cc?.textContent || '').trim(),
      identifier: cc?.getAttribute('data-disqus-identifier') || '',
    };
  });
}
"""

# Disqus 是否已把评论数注入所有文章（每篇的链接文本都非空）
DISQUS_READY_JS = r"""
() => Array.from(document.querySelectorAll('main article a[data-disqus-identifier]'))
    .every(a => (a.textContent || '').trim() !== '')
"""

# 正文 HTML 转纯文本时，在这些块级标签前插入换行以保留段落
BLOCK_TAGS = ("address article aside blockquote br details div figure figcaption "
              "footer form h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre "
              "section table tr td th ul").split()


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def normalize_url(url: str) -> str:
    """URL 规范化（去重用）：host 小写、去掉 query/fragment 和结尾斜杠。"""
    p = urlsplit(url.strip())
    path = p.path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, "", ""))


def html_to_text(html: str) -> str:
    """正文 HTML 转纯文本：块级标签前换行，空白折叠，段落间单换行。"""
    from lxml import html as lxml_html

    root = lxml_html.fromstring(f"<div>{html}</div>")
    for el in list(root.iter("script", "style", "noscript")):
        el.drop_tree()
    for br in root.iter("br"):
        br.tail = "\n" + (br.tail or "")
    for el in root.iter():
        if el.tag in BLOCK_TAGS:
            el.text = "\n" + (el.text or "")
    text = re.sub(r"[ \t\r\f\v]+", " ", root.text_content().replace("\xa0", " "))
    return "\n".join(ln.strip() for ln in text.split("\n") if ln.strip())


def fetch_comment_counts(posts: list[dict]) -> None:
    """批量查 Disqus 评论数；失败时保留列表页注入的文本值（空则 0）。"""
    ids = [p["identifier"] for p in posts if p["identifier"]]
    counts = {}
    for i in range(0, len(ids), 20):  # 一批 20 篇，避免 URL 过长
        query = urllib.parse.urlencode([("1", v) for v in ids[i:i + 20]])
        try:
            req = urllib.request.Request(f"{COUNT_API}?{query}", headers=HEADERS)
            body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
            data = json.loads(re.search(r"displayCount\((.*)\);", body, re.S).group(1))
            counts.update({c["id"]: int(c["comments"]) for c in data["counts"]})
        except Exception as exc:
            log(f"  Disqus 计数接口不可用（{exc}），改用页面注入值")
    for p in posts:
        if p["identifier"] in counts:
            p["comment_count"] = counts[p["identifier"]]
    log(f"  评论数查询成功 {len(counts)}/{len(posts)} 篇")


# --------------------------------------------------------------------------- #
# 第一步：Playwright 扫描列表页（含分页）
# --------------------------------------------------------------------------- #
def scan_list_pages(num_pages: int, start_page: int = 1) -> list[dict]:
    from playwright.sync_api import sync_playwright

    posts, seen = [], set()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(user_agent=HEADERS["User-Agent"]).new_page()
        # 列表页只需 HTML 和 Disqus 组件，拦截图片/字体/媒体加速
        page.route("**/*", lambda route: route.abort()
                   if route.request.resource_type in ("image", "font", "media")
                   else route.continue_())

        for i in range(start_page, start_page + num_pages):
            # 第 1 页是 /blogs/，其余是 /blogs/page/N/
            url = BASE_URL if i == 1 else urljoin(BASE_URL, f"page/{i}/")
            log(f"[Playwright] 列表页 {i}: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_selector("main article", timeout=30_000)
            # 等 Disqus 注入评论数；超时（如 disqus.com 不可达）则用现有结果
            try:
                page.wait_for_function(DISQUS_READY_JS, timeout=10_000)
            except Exception:
                log("[Playwright]   Disqus 评论数未完全加载，继续")

            n_new = 0
            for it in page.evaluate(LIST_EXTRACT_JS):
                norm = normalize_url(it["url"])
                if not norm or norm in seen:
                    continue
                seen.add(norm)
                m = re.search(r"[\d,]+", it["comments"])
                posts.append({
                    "url": norm,
                    "title": it["title"],
                    "author": re.sub(r"^by\s+", "", it["author"]).strip(),
                    "comment_count": int(m.group().replace(",", "")) if m else 0,
                    "identifier": it["identifier"],
                })
                n_new += 1
            log(f"[Playwright]   新增 {n_new} 条（累计 {len(posts)} 条）")
            time.sleep(random.uniform(*PAGE_DELAY))
        browser.close()
    fetch_comment_counts(posts)
    return posts


# --------------------------------------------------------------------------- #
# 第二步：DrissionPage 抓详情页（时间 / 正文 / 图片）
# --------------------------------------------------------------------------- #
def fetch_details(posts: list[dict]) -> dict:
    from DrissionPage import SessionPage

    sp = SessionPage()
    for k, v in HEADERS.items():
        sp.set.header(k, v)

    details = {}
    for idx, post in enumerate(posts, 1):
        url = post["url"]
        for attempt in range(3):  # 最多试 3 次
            try:
                sp.get(url, timeout=30)
                # 发布时间：优先 <time datetime="..."> 的 ISO 属性
                t = sp.ele("css:time.page-topper__date")
                time_iso = (t.attr("datetime") or t.text or "").strip() if t else ""
                # 正文转纯文本；正文图片转绝对地址
                body = sp.ele("css:div.article__body")
                imgs = []
                if body:
                    content = html_to_text(body.html)
                    for img in sp.eles("css:div.article__body img"):
                        src = img.attr("src") or img.attr("data-src") or ""
                        if src.strip():
                            imgs.append(urljoin(url, src.strip()))
                else:
                    content = ""
                details[url] = {"time": time_iso, "content": content, "images": imgs}
                break
            except Exception as exc:
                if attempt == 2:  # 三次都失败，字段留空
                    log(f"[DrissionPage]   抓取失败 {url}（{exc}）")
                    details[url] = {"time": "", "content": "", "images": []}
                time.sleep(2 * (attempt + 1))
        log(f"[DrissionPage] {idx}/{len(posts)} {url}")
        time.sleep(random.uniform(*DETAIL_DELAY))
    return details


# --------------------------------------------------------------------------- #
# 第三步：合并写 CSV
# --------------------------------------------------------------------------- #
def write_csv(posts: list[dict], details: dict, out_path: str) -> None:
    fieldnames = ["Title", "Author", "Comment Count", "Time",
                  "Article Content", "Images In Article"]
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for post in posts:
            d = details.get(post["url"], {})
            writer.writerow({
                "Title": post["title"],
                "Author": post["author"],
                "Comment Count": post["comment_count"],
                "Time": d.get("time", ""),
                "Article Content": d.get("content", ""),
                "Images In Article": json.dumps(d.get("images", []),
                                                ensure_ascii=False),
            })
    log(f"CSV 已写出: {path}（{len(posts)} 行）")


def main() -> None:
    ap = argparse.ArgumentParser(description="抓取 MIT Admissions 博客")
    ap.add_argument("--pages", type=int, default=3, help="扫描多少个列表页")
    ap.add_argument("--start-page", type=int, default=1, help="起始列表页")
    ap.add_argument("--limit", type=int, default=0, help="最多抓几篇（0=不限）")
    ap.add_argument("--out", default="output/mit_blogs.csv", help="输出 CSV 路径")
    args = ap.parse_args()

    posts = scan_list_pages(args.pages, args.start_page)
    if args.limit:
        posts = posts[:args.limit]
    log(f"去重后共 {len(posts)} 篇文章待抓取")

    details = fetch_details(posts)
    write_csv(posts, details, args.out)


if __name__ == "__main__":
    main()
