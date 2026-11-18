"""运行 python -m uvicorn src.app:app，然后打开 /docs。"""
from typing import Literal

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse

from .agent import run_research

app = FastAPI(title="投研证据链 · Lite")


@app.post("/research", response_class=FileResponse)
async def research(
    question: str = Body(..., embed=True, examples=["半导体封装产业链有哪些环节？"]),
    dataset: Literal["web", "shennan"] = Body("web", description="web 按问题检索网页；shennan 返回固定的深南电路年报复算表"),
):
    try:
        path = await run_research(question, dataset)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return FileResponse(path, filename="report.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
