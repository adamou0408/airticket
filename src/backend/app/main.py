"""FastAPI application entry point.

Spec: specs/travel-planner-app/spec.md
Task: 1.1 — Backend project initialization
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import create_tables
    await create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow GitHub Pages frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://adamou0408.github.io",
        "http://localhost:5173",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
