"""外部 API：模型、搜索、网页读取。"""
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def post(path, payload):
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(base_url.rstrip("/") + path, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def chat(system, user, json_output=False):
    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "reasoning_effort": "none",
        "max_tokens": 1800,
    }
    if json_output:
        payload["response_format"] = {"type": "json_object"}
    result = await post("/chat/completions", payload)
    return result["choices"][0]["message"]["content"]


async def search(query):
    result = await post("/v1/tools/search", {"query": query, "count": 3, "need_content": False})
    return result["results"][:3]


async def fetch(url):
    try:
        page = await post("/v1/tools/fetch", {"url": url})
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            return {"error": "Fetch 404：未能获取可用正文"}
        raise
    text = (page.get("content") or "").strip()
    if not text:
        return {"error": "网页未返回正文"}
    return {**page, "content": text}
