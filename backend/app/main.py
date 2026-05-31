"""
FastAPI application entry-point.
Mounts all routers, configures CORS, and runs DB init on startup.
Serves both API and static frontend files for production deployment.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import init_db
from .routers import (
    auth_router,
    resume_router,
    preferences_router,
    jobs_router,
    matches_router,
    notifications_router,
    scraping_router,
)

# Path to frontend dist folder
# In production (Render): built to backend/frontend_dist by the build script
# In local dev: not used (Vite dev server handles frontend)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend_dist"
if not FRONTEND_DIR.exists():
    # Fallback: try the standard Vite output path
    FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    # Ensure upload directory exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # Create tables (dev convenience — use Alembic in production)
    await init_db()
    yield


app = FastAPI(
    title="AI Job Discovery & Application Assistant",
    version="1.0.0",
    description="Discover, match, and apply to jobs with AI assistance.",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
# Allow all origins in dev; in production restrict to the deployed frontend URL
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    settings.FRONTEND_URL,
    "https://ai-job-assistant.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ─────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(resume_router.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(preferences_router.router, prefix="/api/preferences", tags=["Preferences"])
app.include_router(jobs_router.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(matches_router.router, prefix="/api/matches", tags=["Matches"])
app.include_router(notifications_router.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(scraping_router.router, prefix="/api/scraping", tags=["Scraping"])


@app.get("/api/health")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "AI Job Assistant"}


# ── Serve Frontend Static Files ─────────────────────────────
# Mount static assets (JS, CSS, images)
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve frontend SPA - return index.html for all non-API routes."""
        # Check if it's a static file request
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Return index.html for SPA routing
        return FileResponse(FRONTEND_DIR / "index.html")
