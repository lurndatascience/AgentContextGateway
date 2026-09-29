import logging
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import agents
from app.config import get_settings
from app.contract import ContextPackage, ContextRequest, Principal
from app.db import Item, get_db
from app.resolve import resolve

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
app = FastAPI(title="Agent Context Gateway", version="1.0")


DEMO_LEVELS = {"public": ["public"], "internal": ["public", "internal"], "finance": ["public", "internal", "private"]}


def principal(x_api_key: str = Header(default=""), x_demo_level: str = Header(default="")) -> Principal:
    # Scopes come from the key, never from the request body. In demo mode the showcase page may
    # pick an access level instead, so visitors can compare what each level is allowed to see.
    s = get_settings()
    if p := s.principals.get(x_api_key):
        return Principal(**p)
    if s.demo_mode and x_demo_level in DEMO_LEVELS:
        return Principal(agent=f"demo-{x_demo_level}", scopes=DEMO_LEVELS[x_demo_level])
    raise HTTPException(401, "unknown API key")


class AgentBody(BaseModel):
    text: str
    as_of: datetime | None = None


@app.get("/health")
def health(db: Session = Depends(get_db)):
    s = get_settings()
    return {"ok": True, "items": db.scalar(select(func.count(Item.id))), "llm": bool(s.openai_api_key),
            "channels": s.channels, "default_channels": s.default_channels, "rerank": bool(s.openai_api_key and s.rerank_enabled)}


@app.post("/context", response_model=ContextPackage)
def context(req: ContextRequest, p: Principal = Depends(principal), db: Session = Depends(get_db)):
    return resolve(db, req, p)


@app.post("/agents/answer")
def agent_answer(body: AgentBody, p: Principal = Depends(principal), db: Session = Depends(get_db)):
    return agents.answer(db, body.text, p, body.as_of)


@app.post("/agents/brief")
def agent_brief(body: AgentBody, p: Principal = Depends(principal), db: Session = Depends(get_db)):
    return agents.brief(db, body.text, p, body.as_of)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
