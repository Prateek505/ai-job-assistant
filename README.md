# AI Job Discovery & Application Assistant

An AI-powered web application that helps users discover job openings, match them to their resume, suggest resume improvements, and assist with applications and networking.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Task Queue | Celery + Redis |
| AI | OpenAI API (optional) |
| Scraping | Playwright |
| Email | SendGrid (optional) |

## Quick Start

### 1. Start Infrastructure
```bash
docker-compose up -d   # PostgreSQL + Redis
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### 4. Optional: Celery Worker
```bash
cd backend
celery -A app.tasks worker -l info
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis for Celery |
| `JWT_SECRET` | Yes | JWT signing key |
| `OPENAI_API_KEY` | No | Enables AI features (resume parsing, cover letters, etc.) |
| `SENDGRID_API_KEY` | No | Enables email notifications |

> The app works fully without OpenAI/SendGrid keys — AI features fall back to keyword-based analysis and emails are logged to console.

## Features

- **User Auth** — JWT-based registration and login
- **Resume Manager** — Upload PDF/DOCX, AI-powered parsing
- **Job Monitoring** — Scrapes Greenhouse, Lever, and custom career pages
- **AI Matching** — Weighted scoring (skills 50%, experience 20%, location 15%, salary 10%, company 5%)
- **Resume Optimization** — Missing keywords, skills, and AI-generated improvements
- **Cover Letters** — AI-generated tailored cover letters
- **Networking** — Contact suggestions and connection message templates
- **Notifications** — Email alerts for new jobs and deadlines
- **Deadline Tracking** — Approaching deadline alerts

## API Documentation

Once the backend is running, visit **http://localhost:8000/docs** for interactive Swagger UI.

## Testing

```bash
cd backend
pytest tests/ -v
```
