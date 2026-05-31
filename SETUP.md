# AI Job Assistant — Setup & Running Instructions

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 14+ | Or use SQLite (default for dev) |
| Redis | 7+ | Required only for background tasks (Celery) |

---

## 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (needed for LinkedIn, Naukri, Indeed, Glassdoor scraping)
playwright install chromium
```

### Environment Variables

Create `backend/.env`:

```env
# Required
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite+aiosqlite:///./jobs.db

# Optional — for PostgreSQL instead of SQLite:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jobai

# Optional — enables AI-powered matching & cover letters
OPENAI_API_KEY=sk-your-openai-key

# Optional — enables email notifications
SENDGRID_API_KEY=SG.your-sendgrid-key
NOTIFICATION_FROM_EMAIL=you@example.com

# Optional — background task queue
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Run the Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**. Docs at **http://localhost:8000/docs**.

### (Optional) Run Celery Worker

Only needed if you want automatic background scraping & notifications:

```bash
cd backend
celery -A app.tasks worker --loglevel=info
celery -A app.tasks beat --loglevel=info
```

---

## 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at **http://localhost:5173**.

---

## 3. Quick Start (Windows)

Double-click `run_production.bat` to start the backend server.  
Then open a separate terminal and run:

```bash
cd frontend && npm run dev
```

---

## 4. Supported Job Scrapers

### Job Boards (search by keywords + location)
| Platform | Notes |
|----------|-------|
| LinkedIn | Requires Playwright; scrapes public job listings |
| Naukri | India-focused job board |
| Indeed | Global job board |
| Glassdoor | Jobs + company reviews |
| RemoteOK | Remote-only jobs (JSON API) |
| Arbeitnow | European remote/hybrid jobs (JSON API) |

### ATS Platforms (search by company slug)
| Platform | Example slug |
|----------|-------------|
| Greenhouse | `figma`, `netflix`, `airbnb` |
| Lever | `netflix`, `stripe` |
| Ashby | `notion`, `linear` |
| SmartRecruiters | `siemens`, `visa` |
| BambooHR | `company-name` |
| Workable | `company-name` |
| JazzHR | `company-name` |
| Workday | `company-name` |

---

## 5. Features

- **Job Feed** — Browse, search, and filter scraped job listings
- **Multi-source Scraping** — 14 job platforms supported via UI or API
- **AI Matching** — Upload your resume and get match scores per job (requires OpenAI key)
- **Resume Optimizer** — AI suggestions to tailor your resume per job
- **Cover Letter Generator** — One-click AI cover letters
- **Networking Suggestions** — Find relevant contacts at target companies
- **Notifications** — Deadline alerts and new match notifications
- **Preferences** — Set desired roles, locations, salary range, and remote preference

---

## 6. Project Structure

```
backend/
  app/
    main.py          — FastAPI application entry point
    models.py        — SQLAlchemy database models
    routers/         — API route handlers
    services/        — Business logic (scraping, AI, parsing)
    tasks.py         — Celery background tasks
  requirements.txt
frontend/
  src/
    App.tsx          — React app with routing
    pages/           — Page components
    components/      — Reusable UI components
    api/             — Axios API client
docker-compose.yml   — Docker setup (PostgreSQL + Redis)
```

---

## 7. Docker (Alternative)

```bash
docker-compose up -d
```

This starts PostgreSQL and Redis. You still need to run the backend and frontend separately (or add them to the compose file).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `playwright install` fails | Run as admin; ensure you have internet access |
| SQLite locked errors | Use PostgreSQL for production |
| OpenAI errors | Verify `OPENAI_API_KEY` is set; the app falls back to keyword matching without it |
| Redis connection refused | Install and start Redis, or skip Celery (scraping works without it via the UI) |
| CORS errors | The backend allows `localhost:5173` by default; adjust `main.py` if using a different port |
