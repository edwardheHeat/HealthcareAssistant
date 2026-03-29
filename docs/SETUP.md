# HealthcareAssistant — Setup Guide

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (TypeScript, App Router) |
| Backend API | FastAPI (Python 3.11+) |
| Database | SQLite via SQLAlchemy (auto-created on startup) |
| LLM | OpenAI-compatible protocol (Gemini / OpenAI / DeepSeek) |

---

## Repository Structure

```
HealthcareAssistant/
├── apps/
│   ├── web/                        # Next.js frontend
│   │   └── src/
│   │       ├── app/                # Pages (dashboard, questionnaire, chat)
│   │       ├── components/         # UI components
│   │       ├── lib/                # API client (api.ts, apiClient.ts)
│   │       └── types/              # TypeScript types
│   │
│   └── api/                        # FastAPI backend
│       ├── app/
│       │   ├── main.py             # Entrypoint + router registration + lifespan
│       │   ├── db.py               # SQLite engine + session
│       │   ├── config.py           # Settings from .env
│       │   ├── models/             # SQLAlchemy ORM models (10 tables)
│       │   ├── schemas/            # Pydantic request/response schemas
│       │   ├── services/           # Business logic (MET, stats, monitor, analysis)
│       │   ├── routers/            # Route handlers (one file per domain)
│       │   └── llm/                # LLM client, prompt builder, chat service
│       ├── tests/
│       ├── pyproject.toml
│       └── .env.example
│
├── docs/
│   └── SETUP.md                    # This file
├── AGENTS.md
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **pip** or **uv**

---

## Backend Setup

### 1. Install dependencies

```bash
cd apps/api
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your LLM credentials:

```env
# Database (default is fine — SQLite file created automatically)
DATABASE_URL=sqlite:///./healthcareassistant.db

# Food image upload directory
UPLOAD_DIR=./uploads

# LLM provider (pick one below)
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_API_KEY=your-api-key-here
LLM_MODEL=gemini-2.0-flash
```

#### LLM Provider Reference

| Provider | `LLM_BASE_URL` | Example model |
|----------|----------------|---------------|
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.0-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |

### 3. Start the API server

```bash
cd apps/api
uvicorn app.main:app --reload
```

> **What happens on first start:** SQLite tables are created automatically.
> If you already have an older local SQLite file and the schema changes later,
> SQLAlchemy will not alter existing tables for you. Either reset the DB file or
> run the relevant manual migration script.

| URL | Description |
|-----|-------------|
| http://localhost:8000/health | Health check → `{"status": "ok"}` |
| http://localhost:8000/docs | Interactive Swagger UI |
| http://localhost:8000/redoc | ReDoc API reference |

---

## Frontend Setup

### 1. Install dependencies

```bash
cd apps/web
npm install
```

### 2. Start the dev server

```bash
npm run dev
```

App opens at **http://localhost:3000** and redirects to `/dashboard`.

---

## Creating Your First User

The MVP uses a single user (`id=1`). Before logging any health data, create the user profile via Swagger or curl:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane", "account_id": "jane01", "password": "secret123", "age": 35, "sex": "F"}'
```

After that, open the app and start entering data through **Log Health** (the questionnaire page).

---

## Running Tests

```bash
# Backend unit tests
cd apps/api
LLM_BASE_URL=https://example.com LLM_API_KEY=test LLM_MODEL=test pytest -v

# Frontend type check + build
cd apps/web
npm run build
```

---

## API Endpoints Overview

All backend routes are prefixed with `/api/v1`.

| Domain | Method | Path | Description |
|--------|--------|------|-------------|
| Users | POST | `/users` | Create user profile |
| Users | GET | `/users/me` | Get current user |
| Health | POST | `/health/basic-indicators` | Log height + weight |
| Health | POST | `/health/diet` | Log calories + macros + food photo |
| Health | POST | `/health/sleep` | Log sleep/wake times |
| Health | POST | `/health/exercise` | Log exercise (MET auto-computed) |
| Health | POST | `/health/period` | Log cycle data |
| Clinical | PUT | `/clinical/history` | Upsert clinical background |
| Clinical | POST | `/clinical/visits` | Add a clinic visit report |
| Stats | GET | `/stats` | Get all computed health statistics |
| Alerts | GET | `/alerts` | List alerts (pass `?unread_only=true`) |
| Alerts | PATCH | `/alerts/{id}/read` | Mark alert as read |
| Chat | POST | `/chat/sessions` | Start a new chat session |
| Chat | POST | `/chat/sessions/{id}/messages` | Send a message, get AI reply |
| Chat | GET | `/chat/sessions/{id}/messages` | Get message history |

---

## Architecture Notes

- **Database:** SQLite file at `apps/api/healthcareassistant.db` (auto-created). No migration tool needed for MVP. To reset, delete the file.
- **Schema changes on an existing DB:** `Base.metadata.create_all()` does not update existing tables. For example, if your local `alerts` table is missing the newer `severity` column, run `.\venv\Scripts\python.exe scripts\migrate_alerts_add_severity.py` from `apps/api`, or reset the SQLite file if you do not need existing data.
- **MET calculation:** Deterministic lookup table in `services/met.py` — no LLM involved.
- **Health monitor:** APScheduler async job runs every 24 hours inside the FastAPI process. Writes `Alert` rows for abnormal BMI/sleep/calories and stale metrics.
- **LLM context:** The system prompt for chat is rebuilt per session from live stats + clinical history. Chat message history is stored in SQLite and replayed to the LLM on each turn.
- **Food images:** Stored as files under `UPLOAD_DIR` (default `./uploads`). The path is saved in `diet_records`. LLM image analysis is not yet implemented (macros must be entered manually or left blank).
