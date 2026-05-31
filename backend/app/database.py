"""
SQLAlchemy async engine and session factory.
Uses asyncpg for async PostgreSQL access.
Falls back to aiosqlite for tests when DATABASE_URL points to sqlite.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# ── Clean the Database URL ──
# Neon adds `?sslmode=require` by default, but asyncpg rejects this parameter in the URL.
# We strip it out and pass `ssl=True` via connect_args instead.
db_url = settings.DATABASE_URL
_connect_args = {}

if db_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
else:
    # It's PostgreSQL (asyncpg)
    if "?sslmode=require" in db_url:
        db_url = db_url.replace("?sslmode=require", "")
        _connect_args["ssl"] = True
    elif "neon.tech" in db_url:
        # Neon always requires SSL
        _connect_args["ssl"] = True

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

# Session factory — dependency-injected into route handlers
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (used at startup for dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
