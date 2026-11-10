"""DukaanOS FastAPI Application Entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dukaanos.src.dukaanos.backend.config import settings
from dukaanos.src.dukaanos.backend.database import engine, Base
from dukaanos.src.dukaanos.backend.api.router import api_router

# Initialize all database tables on startup
Base.metadata.create_all(bind=engine)

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


@app.get("/", tags=["Root"])
def root():
    """API root redirect information."""
    return {
        "message": "Welcome to DukaanOS Retail Intelligence Platform API",
        "docs": "/docs",
        "health": "/health",
    }

