"""DukaanOS FastAPI Application Entrypoint."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dukaanos.src.dukaanos.backend.config import settings
from dukaanos.src.dukaanos.backend.database import engine, Base
from dukaanos.src.dukaanos.backend.api.router import api_router

# Initialize all database tables on startup
Base.metadata.create_all(bind=engine)

FRONTEND_HTML_PATH = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Intelligent Retail Operating System for Indian Grocery & Kirana Businesses.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
    }


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard():
    """Serves the interactive DukaanOS Shopkeeper UI."""
    if FRONTEND_HTML_PATH.exists():
        with open(FRONTEND_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>DukaanOS API Online</h1><p>Visit /docs for OpenAPI specifications.</p>", status_code=200)
