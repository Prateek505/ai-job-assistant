# AI Job Discovery & Application Assistant - Detailed Documentation

## Overview

This is a full-stack web application that helps users discover job opportunities, match them to their resume using AI, optimize their resume for specific jobs, generate cover letters, and get networking suggestions. The app consists of a Python/FastAPI backend and a React/TypeScript frontend.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Components](#backend-components)
4. [Frontend Components](#frontend-components)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [AI Services](#ai-services)
8. [Job Scraping System](#job-scraping-system)
9. [Authentication Flow](#authentication-flow)
10. [Data Flow Diagrams](#data-flow-diagrams)
11. [Configuration](#configuration)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  React 18 + TypeScript + Vite                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │ Resume   │ │ Rankings │ │Networking│           │
│  │   Page   │ │  Upload  │ │   Page   │ │   Page   │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                   │
│       └────────────┴─────┬──────┴────────────┘                   │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │  API Client │ (Axios + JWT Interceptor)     │
│                   └──────┬──────┘                                │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  FastAPI + SQLAlchemy (Async)                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API ROUTERS                            │   │
│  │  /auth  /resumes  /jobs  /matches  /preferences          │   │
│  │         /notifications                                    │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │                      SERVICES                             │   │
│  │  AI Matcher │ Resume Parser │ Resume Optimizer           │   │
│  │  Cover Letter Generator │ Networking │ Notifier          │   │
│  │  Job Scraper                                              │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │PostgreSQL│  │  Redis   │  │ OpenAI   │
        │ Database │  │(Celery)  │  │   API    │
        └──────────┘  └──────────┘  └──────────┘
```

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | FastAPI 0.115 | Async REST API with automatic OpenAPI docs |
| ORM | SQLAlchemy 2.0 (async) | Database operations with asyncpg |
| Database | PostgreSQL 15 / SQLite | Persistent data storage |
| Task Queue | Celery 5.4 + Redis | Background job scraping |
| Auth | python-jose + bcrypt | JWT tokens + password hashing |
| AI | OpenAI API | Resume parsing, cover letters, optimizations |
| Scraping | Playwright + httpx | Career page scraping |
| Email | SendGrid | Notification emails |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React 18 | UI components |
| Language | TypeScript | Type safety |
| Build Tool | Vite | Fast development & builds |
| HTTP Client | Axios | API calls with interceptors |
| Routing | React Router v6 | SPA navigation |
| Notifications | react-hot-toast | User feedback |
| Icons | Lucide React | UI icons |

---

## Backend Components

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy engine & session
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT authentication utilities
│   ├── tasks.py             # Celery background tasks
│   │
│   ├── routers/             # API route handlers
│   │   ├── auth_router.py
│   │   ├── resume_router.py
│   │   ├── jobs_router.py
│   │   ├── matches_router.py
│   │   ├── preferences_router.py
│   │   └── notifications_router.py
│   │
│   └── services/            # Business logic
│       ├── ai_matcher.py        # Job-resume matching algorithm
│       ├── resume_parser.py     # PDF/DOCX text extraction
│       ├── resume_optimizer.py  # Resume improvement suggestions
│       ├── cover_letter.py      # Cover letter generation
│       ├── networking.py        # Networking contact suggestions
│       ├── notifier.py          # Email notifications
│       └── job_scraper.py       # Career page scraping
│
├── uploads/                 # Uploaded resume files
├── tests/                   # pytest test suite
└── requirements.txt
```

### Core Files Explained

#### `main.py` - Application Entry Point
- Initializes FastAPI with lifespan management
- Configures CORS middleware (allows all origins)
- Mounts all API routers under `/api/` prefix
- Auto-creates database tables on startup
- Serves frontend static files in production mode
- Provides `/api/health` endpoint for monitoring

#### `config.py` - Configuration Management
- Uses `pydantic-settings` to load from `.env`
- Centralizes all configurable values:
  - `DATABASE_URL` - PostgreSQL/SQLite connection
  - `REDIS_URL` - Celery broker
  - `JWT_SECRET` - Token signing key
  - `OPENAI_API_KEY` - AI features (optional)
  - `SENDGRID_API_KEY` - Email notifications (optional)
  - `FRONTEND_URL` - CORS origin
  - `UPLOAD_DIR` - Resume file storage path

#### `database.py` - Database Setup
- Creates async SQLAlchemy engine
- Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite)
- Provides `get_db()` dependency for FastAPI routes
- Handles session commit/rollback automatically
- `init_db()` creates tables from ORM models

#### `auth.py` - Authentication Utilities
- `hash_password()` - bcrypt password hashing
- `verify_password()` - bcrypt verification
- `create_access_token()` - JWT token generation with expiry
- `decode_token()` - JWT validation
- `get_current_user()` - FastAPI dependency that extracts user from JWT

---

## Database Schema

### Entity Relationship

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│     User     │      │    Resume    │      │  Preference  │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ id (PK)      │──┬──<│ user_id (FK) │      │ user_id (FK) │
│ email        │  │   │ filename     │      │ role_titles  │
│ hashed_pass  │  │   │ raw_text     │      │ locations    │
│ name         │  │   │ parsed_json  │      │ salary_min   │
│ created_at   │  │   │ embedding    │      │ salary_max   │
└──────────────┘  │   │ uploaded_at  │      │ exp_level    │
                  │   └──────────────┘      │ remote_pref  │
                  │                         │ priority_cos │
                  │   ┌──────────────┐      └──────────────┘
                  │   │  JobMatch    │
                  │   ├──────────────┤      ┌──────────────┐
                  ├──<│ user_id (FK) │      │     Job      │
                  │   │ job_id (FK)  │>────<├──────────────┤
                  │   │ score        │      │ id (PK)      │
                  │   │ skill_sim    │      │ title        │
                  │   │ exp_match    │      │ company      │
                  │   │ loc_pref     │      │ description  │
                  │   │ sal_pref     │      │ location     │
                  │   │ company_prio │      │ salary_range │
                  │   │ status       │      │ posting_date │
                  │   └──────────────┘      │ deadline     │
                  │                         │ app_link     │
                  │   ┌──────────────┐      │ source       │
                  │   │ Notification │      │ embedding    │
                  │   ├──────────────┤      └──────────────┘
                  └──<│ user_id (FK) │
                      │ type         │
                      │ title        │
                      │ message      │
                      │ read         │
                      │ job_id (FK)  │
                      └──────────────┘
```

### Model Details

#### User
- Stores user account information
- One-to-many relationship with Resumes, Matches, Notifications
- One-to-one relationship with Preferences

#### Resume
- Stores uploaded resume files
- `raw_text` - extracted plain text from PDF/DOCX
- `parsed_json` - structured data (skills, experience, education, projects)
- `embedding_vector` - for future semantic search

#### Preference
- User's job search preferences
- `role_titles` - list of desired job titles
- `locations` - preferred work locations
- `salary_min/max` - salary range
- `experience_level` - intern/junior/mid/senior/lead/principal
- `remote_preference` - remote/onsite/hybrid/any
- `priority_companies` - companies to prioritize in matching

#### Job
- Job listings scraped from career pages
- `source` - greenhouse/lever/career_page
- Deadline tracking for notifications

#### JobMatch
- Links users to jobs with computed match scores
- `score` - total weighted match score (0-100)
- Individual component scores for transparency
- `status` - new/saved/applied/rejected

#### Notification
- User alerts for new jobs, deadlines, priority companies
- `type` - categorizes notification
- `read` - tracks user engagement

---

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new account, returns JWT |
| POST | `/login` | Authenticate, returns JWT |
| GET | `/me` | Get current user info |

**Register/Login Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass",
  "name": "John Doe"  // register only
}
```

**Token Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Resumes (`/api/resumes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload PDF/DOCX resume |
| GET | `/` | List user's resumes |
| GET | `/{id}` | Get specific resume |

**Upload Flow:**
1. Accepts `multipart/form-data` with file
2. Validates file extension (PDF/DOCX only)
3. Saves file to `uploads/` directory
4. Extracts raw text using pdfplumber or python-docx
5. Parses structured data via OpenAI or fallback keywords
6. Stores record in database

### Jobs (`/api/jobs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List jobs with filters |
| GET | `/{id}` | Get job details |
| POST | `/` | Create job manually |
| GET | `/{id}/optimize-resume` | Get resume optimization tips |
| GET | `/{id}/cover-letter` | Generate cover letter |
| GET | `/{id}/networking` | Get networking suggestions |

**List Jobs Query Parameters:**
- `search` - title/description keyword search
- `location` - filter by location
- `company` - filter by company
- `skip` / `limit` - pagination

**Smart Sorting:** Jobs are automatically sorted by relevance to the user's resume and preferences using the AI matcher.

### Matches (`/api/matches`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List user's job matches |
| POST | `/refresh` | Re-compute all match scores |
| PUT | `/{id}/status` | Update match status |

**Refresh Flow:**
1. Gets user's latest resume and preferences
2. Fetches all jobs from database
3. Deletes existing matches
4. Computes new scores for each job
5. Creates JobMatch records

### Preferences (`/api/preferences`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get user preferences |
| PUT | `/` | Update preferences |

### Notifications (`/api/notifications`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List notifications (newest first) |
| PUT | `/{id}/read` | Mark as read |

---

## AI Services

### AI Matcher (`ai_matcher.py`)

Computes weighted match scores between a resume and job posting.

**Scoring Weights:**
| Component | Weight | Description |
|-----------|--------|-------------|
| Skill Similarity | 50% | Resume skills vs job requirements |
| Experience Match | 20% | Experience level alignment |
| Location Preference | 15% | Job location vs user preferences |
| Salary Preference | 10% | Salary range overlap |
| Company Priority | 5% | Company in user's priority list |

**Algorithm Details:**

1. **Skill Similarity (`_skill_similarity`)**
   - Extracts skills from `parsed_json.skills` and `parsed_json.technologies`
   - Falls back to raw text word matching if no structured skills
   - Calculates overlap ratio with job description
   - Returns 0-100 score

2. **Experience Match (`_experience_match`)**
   - Looks for experience keywords (senior, junior, lead, etc.)
   - Checks if keywords appear in both resume and job
   - Bonus points for number of experience entries
   - Base score: 60, Max: 100

3. **Location Preference (`_location_preference`)**
   - Matches job location against user's preferred locations
   - Special handling for "remote" jobs
   - Returns 100 for exact match, 40 for no match

4. **Salary Preference (`_salary_preference`)**
   - Extracts numbers from job salary_range string
   - Checks overlap with user's min/max preferences
   - Penalizes jobs below user's minimum

5. **Company Priority (`_company_priority`)**
   - Returns 100 if company is in user's priority list
   - Returns 30 otherwise

### Resume Parser (`resume_parser.py`)

Extracts text and structured data from resume files.

**Text Extraction:**
- PDF: Uses `pdfplumber` library
- DOCX: Uses `python-docx` library

**Structured Data Extraction:**

With OpenAI API:
```python
# Sends resume text to GPT-3.5-turbo
# Requests JSON with: skills, technologies, experience, education, projects
```

Without OpenAI (Fallback):
```python
# Searches for known tech skills in text
known_skills = ["python", "javascript", "react", "docker", ...]
found_skills = [s for s in known_skills if s in resume_text.lower()]
```

### Resume Optimizer (`resume_optimizer.py`)

Compares resume against a job and suggests improvements.

**Output:**
```json
{
  "missing_keywords": ["kubernetes", "ci/cd", "agile"],
  "missing_skills": ["docker", "aws"],
  "suggestions": [
    "Add experience with: docker, aws",
    "Include industry terms: kubernetes, ci/cd",
    "Tailor your summary to match the job title",
    "Quantify achievements with metrics"
  ],
  "optimized_text": "..."  // LLM-rewritten resume (with OpenAI)
}
```

### Cover Letter Generator (`cover_letter.py`)

Generates tailored cover letters for job applications.

**With OpenAI:**
- Sends resume and job description to GPT-3.5-turbo
- Requests 3-4 paragraph professional cover letter
- Highlights relevant skills and enthusiasm

**Without OpenAI (Template):**
```
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title}
position at {company}. With my background in {skills}, I believe
I would be a valuable addition to your team.
...
```

### Networking Assistant (`networking.py`)

Suggests contacts and connection messages for networking.

**Output:**
```json
{
  "company": "Acme Corp",
  "contacts": [
    {
      "name": "Hiring Manager",
      "role": "Engineering Manager",
      "department": "Engineering",
      "connection_message": "Hi! I'm excited about..."
    },
    // Team Member, Recruiter suggestions
  ],
  "tips": [
    "Research company's recent news",
    "Engage with company posts on LinkedIn",
    "Ask for informational interviews"
  ]
}
```

### Notifier (`notifier.py`)

Sends email notifications via SendGrid.

**With SendGrid API:**
- Constructs HTML email
- Sends via SendGrid client
- Logs success/failure

**Without SendGrid (Fallback):**
- Logs email content to console
- Prints to stdout for debugging

---

## Job Scraping System

### Supported Sources

1. **Greenhouse** (`scrape_greenhouse`)
   - Uses Greenhouse JSON API
   - URL: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`
   - No browser required

2. **Lever** (`scrape_lever`)
   - Uses Lever JSON API
   - URL: `https://api.lever.co/v0/postings/{slug}?mode=json`
   - No browser required

3. **Generic Career Pages** (`scrape_career_page`)
   - Uses Playwright browser automation
   - Attempts multiple CSS selectors to find job links
   - Extracts title, location, and application link

### Celery Background Tasks (`tasks.py`)

**Scheduled Tasks:**
| Task | Schedule | Description |
|------|----------|-------------|
| `scan_jobs` | Every 5 minutes | Scrape all configured companies |
| `send_deadline_alerts` | Daily | Alert users about approaching deadlines |

**Configured Companies:**
- 100+ Greenhouse companies (Google, Meta, Stripe, etc.)
- 40+ Lever companies (Netflix, Canva, Robinhood, etc.)

### Database Integration

`save_jobs_to_db()` handles:
- Deduplication by title + company + application_link
- Updates if description/location changed
- Tracks stats: new, updated, skipped, errors

---

## Frontend Components

### Directory Structure

```
frontend/src/
├── main.tsx                 # App entry point
├── App.tsx                  # Root component with routing
├── index.css                # Global styles
│
├── api/
│   ├── client.ts            # Axios instance with JWT interceptor
│   └── endpoints.ts         # Typed API functions
│
├── context/
│   └── AuthContext.tsx      # Authentication state management
│
├── components/
│   ├── Sidebar.tsx          # Navigation sidebar
│   ├── JobCard.tsx          # Job listing card
│   └── MatchScore.tsx       # Circular score ring
│
└── pages/
    ├── LoginPage.tsx        # Login/Register form
    ├── DashboardPage.tsx    # Overview with stats
    ├── ResumePage.tsx       # Resume upload & list
    ├── JobFeedPage.tsx      # Browse all jobs
    ├── JobDetailPage.tsx    # Job details + AI features
    ├── RankingsPage.tsx     # Ranked job matches
    ├── NetworkingPage.tsx   # Networking suggestions
    ├── NotificationsPage.tsx # User notifications
    └── PreferencesPage.tsx  # Job search preferences
```

### Core Components Explained

#### `App.tsx` - Root Component
- Wraps app in `AuthProvider` for global auth state
- Defines all routes with React Router
- `ProtectedRoute` component redirects to login if not authenticated
- Shows loading spinner while checking auth state

#### `AuthContext.tsx` - Auth State Management
- Stores `user`, `token`, `loading` state
- Persists token to `localStorage`
- Provides `login()`, `register()`, `logout()` functions
- Auto-loads user on mount if token exists

#### `client.ts` - API Client
- Creates Axios instance with base URL `/api`
- Request interceptor: Adds `Authorization: Bearer {token}` header
- Response interceptor: On 401, clears token and redirects to login

#### `endpoints.ts` - API Functions
- Typed interfaces for all data models
- Organized by domain: `authAPI`, `resumeAPI`, `jobsAPI`, etc.
- Each function returns axios response promise

### Page Components

#### `LoginPage.tsx`
- Toggle between login and register forms
- Validates email and password (min 6 chars)
- Shows toast notifications on success/error
- Animated gradient background

#### `DashboardPage.tsx`
- Loads resumes, jobs, matches, notifications on mount
- Displays 4 stat cards: Resumes, Jobs, Matches, Unread Alerts
- Shows top 3 matches with score visualization
- Shows recent 5 notifications

#### `JobDetailPage.tsx`
- Tab-based interface: Details, Resume Tips, Cover Letter, Networking
- Lazy loads AI-generated content when tab selected
- Copy cover letter to clipboard functionality
- "Apply Now" button with external link

#### `RankingsPage.tsx`
- Lists all job matches sorted by score (highest first)
- Shows rank number (#1, #2, etc.) with gradient badge
- Score breakdown: Skill, Exp, Loc, Sal, Company
- Status dropdown: New, Saved, Applied, Rejected
- "Refresh Matches" button to recompute scores

#### `PreferencesPage.tsx`
- Tag-based inputs for roles, locations, companies
- Add/remove tags with Enter key or + button
- Salary range inputs (min/max)
- Dropdowns for experience level and remote preference
- Save button persists to backend

---

## Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │     │Frontend │     │ Backend │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     │ Enter email/  │               │
     │ password      │               │
     │──────────────>│               │
     │               │               │
     │               │ POST /auth/   │
     │               │ login         │
     │               │──────────────>│
     │               │               │
     │               │               │ Verify credentials
     │               │               │ with bcrypt
     │               │               │
     │               │   JWT Token   │
     │               │<──────────────│
     │               │               │
     │               │ Store token   │
     │               │ in localStorage
     │               │               │
     │  Redirect to  │               │
     │  Dashboard    │               │
     │<──────────────│               │
     │               │               │
     │               │ GET /auth/me  │
     │               │ (with Bearer) │
     │               │──────────────>│
     │               │               │ Decode JWT
     │               │               │ Fetch user
     │               │  User data    │
     │               │<──────────────│
     │               │               │
```

**JWT Token Structure:**
```json
{
  "sub": "123",           // user_id
  "email": "user@ex.com",
  "exp": 1234567890       // expiry timestamp
}
```

**Token Expiry:** 24 hours (configurable via `JWT_EXPIRY_MINUTES`)

---

## Data Flow Diagrams

### Resume Upload Flow

```
User selects file
        │
        ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Frontend      │───>│ Backend       │───>│ File System   │
│ FormData      │    │ /resumes/     │    │ uploads/      │
└───────────────┘    │ upload        │    │ {uid}_{name}  │
                     └───────┬───────┘    └───────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │ Resume Parser │
                     │ (pdfplumber/  │
                     │  python-docx) │
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │ LLM / Fallback│
                     │ Structure     │
                     │ Extraction    │
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │ Database      │
                     │ Resume table  │
                     └───────────────┘
```

### Job Matching Flow

```
User clicks "Refresh Matches"
        │
        ▼
┌───────────────┐
│ Fetch latest  │
│ resume        │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Fetch user    │
│ preferences   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Fetch all     │
│ jobs          │
└───────┬───────┘
        │
        ▼
   ┌────────────┐
   │ For each   │◄──────────────┐
   │ job        │               │
   └─────┬──────┘               │
         │                      │
         ▼                      │
┌───────────────┐               │
│ AI Matcher    │               │
│ compute_      │               │
│ match_scores()│               │
└───────┬───────┘               │
        │                       │
        ▼                       │
┌───────────────┐               │
│ Create        │               │
│ JobMatch      │───────────────┘
│ record        │
└───────────────┘
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://jobai:jobai_secret@localhost:5432/jobai_db
DATABASE_URL_SYNC=postgresql://jobai:jobai_secret@localhost:5432/jobai_db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
JWT_SECRET=your-secure-random-key-change-in-production
JWT_EXPIRY_MINUTES=1440

# OpenAI (optional - enables AI features)
OPENAI_API_KEY=sk-...

# SendGrid (optional - enables email notifications)
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=noreply@yourapp.com

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

### Docker Compose (`docker-compose.yml`)

Provides infrastructure services:
- **PostgreSQL 15**: Database on port 5432
- **Redis 7**: Task queue broker on port 6379

```bash
docker-compose up -d  # Start services
```

### Running the Application

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker (optional):**
```bash
cd backend
celery -A app.tasks worker -l info
```

**Celery Beat (scheduled tasks):**
```bash
celery -A app.tasks beat -l info
```

---

## Key Features Summary

| Feature | Implementation |
|---------|---------------|
| User Authentication | JWT tokens with bcrypt password hashing |
| Resume Upload | PDF/DOCX parsing with text extraction |
| AI Resume Parsing | OpenAI GPT-3.5 or keyword-based fallback |
| Job Scraping | Greenhouse/Lever APIs + Playwright for generic sites |
| AI Job Matching | Weighted scoring algorithm (50/20/15/10/5) |
| Resume Optimization | Gap analysis + AI suggestions |
| Cover Letter Generation | AI-generated or template-based |
| Networking Suggestions | Contact types + message templates |
| Email Notifications | SendGrid or console logging |
| Background Tasks | Celery + Redis for scheduled scraping |

---

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation with request/response schemas.
