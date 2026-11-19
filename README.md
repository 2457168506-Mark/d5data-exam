# 五维数据笔试题&#x20;

按岗位与能力完成了以下 5 道题，各题代码在本仓库对应目录下，均可独立运行。

github地址：<https://github.com/2457168506-Mark/d5data-exam.git>

| 题目       | 目录                                | 技术栈                                 |
| -------- | --------------------------------- | ----------------------------------- |
| 前端       | `frontend/`                       | 原生 HTML / CSS / JavaScript          |
| 后端       | `springboot-security-helloworld/` | Spring Boot 3.2.0 + Spring Security |
| 爬虫       | `crawler/`                        | Python + Playwright + DrissionPage  |
| Python   | `fastapi_streaming/`              | FastAPI + SSE                       |
| AI Agent | `AI agent全栈开发/`                   | Python（最大余数法修复 + 测试）                |

***

## 一、前端：简历上传页面（`frontend/`）

按 [Figma 设计稿](https://www.figma.com/design/D0jjN7Twkq0DGm3ZJvQabz/%E5%89%8D%E7%AB%AF%E5%B7%A5%E7%A8%8B%E5%B8%88%EF%BC%88%E5%AE%9E%E4%B9%A0%EF%BC%89?node-id=0-1\&p=f) 实现的 "Upload Your Resume" 页面，无框架、无构建步骤。

**运行**：浏览器直接打开 `frontend/index.html`，或 `cd frontend ; python -m http.server 8000`。

**要点**：

- 样式还原：色板逐项取自 Figma（卡片 `#F8FBF9`、上传区 `#F2FAFF`、虚线边框 `#85A7FF`、主色 `#1B5AFF`），虚线上传区、按钮 hover/active、进度点 。插画ai生图后`realesrgan-x4plus-anime` 模型 4 倍放大到 1452×1240，清晰展示
- 语义化：`main` / `section[aria-labelledby]` / 进度用 `ol` / 原生 `button`；上传区支持键盘操作（Enter/Space）
- 交互：点击或拖拽上传 → 显示文件名、进度变 `√ – √ – √`；"Last step" 清空并复位；限制 `.pdf,.doc,.docx,.txt,.rtf`
- 响应式：≤920px 上下堆叠、≤420px 按钮纵排，390px 视口无横向溢出
- 已用 Playwright（本机 Edge）自动化验收：计算样式断言、事件计数（一次点击恰好触发一次选择框）、完整上传/重置流程、移动端 390×844 模拟

***

## 二、后端：Spring Security Hello World（`springboot-security-helloworld/`）

Spring Boot 3.2.0 项目：受 Spring Security 保护的 `GET /hello` 返回 `"Hello World"`，附带用户名密码登录接口（`test` / `123456`）。

**运行**：`cd springboot-security-helloworld ; ./mvnw spring-boot:run`

**要点**：

- 所有请求需认证，未登录 302 到内置登录页；`POST /login` 为用户名密码登录接口,登录后访问`/hello`
- 账号存于内存（`InMemoryUserDetailsManager`），密码 BCrypt 加密存储；会话 Cookie 认证，无额外 JWT 复杂度
- 已打包并跑通测试（`target/` 下含 jar 与测试报告），curl 带会话 Cookie 可验证 `/hello`

***

## 三、爬虫：MIT 招生博客（`crawler/`）

按要求同时使用 Playwright 与 DrissionPage 抓取 <https://mitadmissions.org/blogs/>，输出 CSV。

**运行**（以 Python 虚拟环境为基底，下同）：

```bash
cd crawler
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
python mit_blogs_crawler.py --pages 3 --out output/mit_blogs.csv
```

已含爬取结果 `output/mit_blogs.csv`，可直接查看。

**要点**：

- 分工：Playwright 负责渲染列表页、翻页、读取 Disqus 异步注入的评论数；DrissionPage 的 requests 会话抓详情页，提取时间 / 正文 / 正文图片
- 表头完全符合要求：`Title | Author | Comment Count | Time | Article Content | Images In Article`（图片为绝对地址 JSON 数组）
- 输出 `utf-8-sig` 编码，Excel 打开不乱码；礼貌爬取（详情页 1.5\~3.5s、翻页 2\~4s 随机间隔）

***

## 四、Python：FastAPI 流式接口（`fastapi_streaming/`）

`GET /stream` 用 SSE（`text/event-stream`）逐段推送文本，附浏览器演示页与验证脚本。

```bash
cd fastapi_streaming
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

浏览器打开 <http://127.0.0.1:8000/> 查看演示页；`client_verify.py` 为无浏览器验证脚本（虚拟环境下 `python client_verify.py` 运行）。

**要点**：

- 异步生成器 + `StreamingResponse`，每 yield 一次客户端立刻收到一条消息，结尾推送 `[DONE]`
- 用 `asyncio.sleep` 模拟生成耗时（而非 `time.sleep`，避免阻塞事件循环）
- `index.html` 用原生 `EventSource` 消费，直观看到逐条到达的效果

***

## 五、AI Agent：奖池分账修复（`AI agent全栈开发/`）

修复 `split_pool` 按权重分账时因独立取整导致总金额与奖池不等的问题，保留原实现 `split_pool_0` 用于对照。

```bash
cd AI agent全栈开发
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux 用 source .venv/bin/activate
python test_pool_split.py
```

**要点**：

- 根因：每人独立取整、未处理尾差（如 `pool=10000, weights=[1,1,1]` 时合计 9999，少发 1 分）
- 方案：最大余数法——先分整数部分，剩余按余数从大到小逐人补 1 分；余数相同保持原顺序，结果确定
- 验证：固定用例 + 边界用例（零权重 / 单人 / 极端权重 / 池为 0）+ 500 轮随机测试，满足总和不变式、每人误差 ≤1 分、结果固定
- 详细说明见该目录下 `README.md`（含问题复现、修改方法、两次运行输出、AI 使用情况）

