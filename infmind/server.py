"""∞Mind — HTTP 層.

脳ゾーンマップと分析マップはブラウザで描く。Claude への鍵はサーバ側に留め、
ブラウザへは決して渡さない。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .mind import InfMind

WEB = Path(__file__).parent / "web"

app = FastAPI(title="∞Mind", version=__version__, docs_url="/api/docs")

_mind: Optional[InfMind] = None


def mind() -> InfMind:
    global _mind
    if _mind is None:
        _mind = InfMind()
        if os.environ.get("INFMIND_SEED", "1") not in ("0", "false", ""):
            _mind.seed()
    return _mind


# ── リクエスト ────────────────────────────────────────────────────
class Message(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Observation(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class Key(BaseModel):
    api_key: str = Field(default="", max_length=200)


# ── L2/L3/L4 読み出し ─────────────────────────────────────────────
@app.get("/api/state")
def get_state():
    return mind().state()


@app.get("/api/analysis")
def get_analysis():
    return mind().analysis.to_dict()


@app.get("/api/via")
def get_via():
    from . import via
    return via.catalog()


@app.get("/api/report")
def get_report():
    return {"report": mind().report()}


@app.get("/api/greeting")
def get_greeting():
    return {"greeting": mind().greeting(), "online": mind().online}


# ── L1 入力 ───────────────────────────────────────────────────────
@app.post("/api/chat")
def post_chat(body: Message):
    m = mind()
    if not m.online:
        raise HTTPException(
            status_code=503,
            detail="Claude に接続していません。ANTHROPIC_API_KEY を設定するか /api/connect で鍵を渡してください。",
        )
    try:
        return m.converse(body.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc


@app.post("/api/observe")
def post_observe(body: Observation):
    """対話せずに観測だけ刻む。API キー無しでも全層が動く経路。"""
    m = mind()
    entry = m.observe(body.text, source="note")
    return {"entry": entry.to_dict(), "analysis": m.analysis.to_dict()}


# ── L4 統合 ───────────────────────────────────────────────────────
@app.post("/api/synthesize")
def post_synthesize():
    m = mind()
    if not m.online:
        raise HTTPException(status_code=503, detail="Claude に接続していません。")
    if m.analysis.entries == 0:
        raise HTTPException(status_code=400, detail="まだ観測がありません。")
    try:
        return {"synthesis": m.synthesize()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc


# ── 接続・初期化 ──────────────────────────────────────────────────
@app.post("/api/connect")
def post_connect(body: Key):
    ok = mind().connect(body.api_key)
    return {"online": ok}


@app.post("/api/seed")
def post_seed():
    m = mind()
    return {"seeded": m.seed(), "analysis": m.analysis.to_dict()}


@app.delete("/api/brain")
def delete_brain():
    m = mind()
    m.reset()
    return {"ok": True, "analysis": m.analysis.to_dict()}


# ── 静的配信 ──────────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/", StaticFiles(directory=str(WEB)), name="web")


def run(host: str = "127.0.0.1", port: int = 8800, reload: bool = False) -> None:
    import uvicorn
    uvicorn.run("infmind.server:app", host=host, port=port, reload=reload)
