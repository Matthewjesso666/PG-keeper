from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from pg_keeper.chatbot import chat
from pg_keeper.config import Settings
from pg_keeper.drafting import draft_response

app = FastAPI(title="PG Keeper API", version="0.1.0")


class ChatRequest(BaseModel):
    query: str
    collection: str = "case-vault"
    top_k: int = 4


class DraftRequest(BaseModel):
    prompt: str
    tone: str = "professional"
    length: str = "short"


def get_settings() -> Settings:
    return Settings.from_env()


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
):
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return settings


@app.post("/chat")
async def chat_endpoint(payload: ChatRequest, settings: Settings = Depends(require_api_key)):
    return chat(query=payload.query, settings=settings, collection_name=payload.collection, top_k=payload.top_k)


@app.post("/draft")
async def draft_endpoint(payload: DraftRequest, settings: Settings = Depends(require_api_key)):
    return {"draft": draft_response(prompt=payload.prompt, settings=settings, tone=payload.tone, length=payload.length)}


@app.get("/health")
async def health():
    return {"status": "ok"}
