"""客户端验证:逐行打印到达时间。总耗时明显大于首字节耗时,说明是逐段到达。"""
import time
import urllib.request

start = time.perf_counter()
first = None
with urllib.request.urlopen("http://127.0.0.1:8000/stream?prompt=test") as r:
    print("Content-Type:", r.headers["Content-Type"])
    for line in r:  # 流式响应:服务端每发一片,这里就能读到一行
        now = time.perf_counter()
        first = first or now
        print(f"+{(now - start) * 1000:7.1f} ms | {line.decode().strip()[:50]}")

total, ttfb = (time.perf_counter() - start) * 1000, (first - start) * 1000
print(f"\n首字节 {ttfb:.0f} ms,总耗时 {total:.0f} ms")
assert total > ttfb + 500, "内容疑似一次性返回!"
print("分片逐段到达,流式验证通过。")
