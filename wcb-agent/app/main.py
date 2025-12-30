"""FastAPI application for the WCB agent."""
from __future__ import annotations

from fastapi import FastAPI

from app.routers import cases

app = FastAPI(title="WCB Agent", version="0.1.0")
app.include_router(cases.router)
