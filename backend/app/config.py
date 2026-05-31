"""
Application configuration — reads from .env via pydantic-settings.
All secrets and tunables are centralised here.
"""

from pydantic_settings import BaseSettings
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # JOB AI/


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./jobai.db"
    DATABASE_URL_SYNC: str = "sqlite:///./jobai.db"

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440  # 24 hours

    # ── OpenAI (optional) ─────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── SendGrid (optional) ───────────────────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@jobai.local"

    # ── CORS ──────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    # ── File uploads ──────────────────────────────────────────
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent / "uploads")

    class Config:
        env_file = str(_PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
