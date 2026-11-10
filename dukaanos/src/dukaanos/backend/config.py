"""Application Configuration and Environment Settings."""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Central backend configuration."""

    APP_NAME: str = "DukaanOS Retail API"
    VERSION: str = "0.3.0"
    DEBUG: bool = False

    # Default to local SQLite database file, easily overridden by PostgreSQL URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dukaanos_retail.db")

    # Security & JWT Token configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dukaanos_super_secret_jwt_key_2026_kirana_ai")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]


settings = Settings()

