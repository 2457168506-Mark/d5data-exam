"""FastAPI 流式接口 Demo:GET /stream 用 SSE 逐段推送文本。

运行:uvicorn main:app --port 8000,浏览器打开 http://127.0.0.1:8000/
"""
import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

TEXTS = [
    "你好,这是一个 FastAPI 流式接口演示。当前信息第一条",
    "你好,这是一个 FastAPI 流式接口演示。当前信息第二条",
    "你好,这是一个 FastAPI 流式接口演示。当前信息第三条",
    "你好,这是一个 FastAPI 流式接口演示。当前信息第四条",
    "你好,这是一个 FastAPI 流式接口演示。当前信息第五条",
]


async def sse(prompt: str):
    """异步生成器:每 yield 一次,客户端立刻收到一条 SSE 消息。"""
    yield f"data: {prompt}\n\n"
    for text in TEXTS:
        yield f"data: {text}\n\n"
        await asyncio.sleep(0.3)  # 模拟生成耗时;换成 time.sleep 会阻塞事件循环
    yield "data: [DONE]\n\n"


@app.get("/")
async def index():
    return HTMLResponse(open("index.html", encoding="utf-8").read())


@app.get("/stream")
async def stream(prompt: str = "你好"):
    return StreamingResponse(sse(prompt), media_type="text/event-stream")
