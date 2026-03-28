# HealthcareAssistant — Project Setup Guide

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (TypeScript, App Router) |
| Backend API | FastAPI (Python 3.11+) |
| Database | SQLite via SQLAlchemy |
| LLM | OpenAI-compatible protocol (provider-agnostic) |

---

## Repository Structure

```
HealthcareAssistant/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   └── src/
│   │       ├── app/            # Pages & layouts (App Router)
│   │       ├── components/     # Reusable UI components
│   │       ├── hooks/          # Custom React hooks
│   │       ├── lib/            # API client, utilities
│   │       └── types/          # Shared TypeScript types
│   │
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── main.py         # App entrypoint + CORS
│       │   ├── db.py           # SQLite engine + session
│       │   ├── config.py       # Settings from .env
│       │   ├── routers/        # Route handlers (one file per domain)
│       │   ├── models/         # SQLAlchemy ORM models
│       │   ├── schemas/        # Pydantic request/response schemas
│       │   ├── services/       # Business logic
│       │   └── llm/
│       │       └── client.py   # LLM client wrapper
│       ├── tests/
│       ├── pyproject.toml
│       └── .env.example
│
├── .husky/pre-commit           # Git hook: lint + format
├── package.json                # Root: Husky + lint-staged
└── AGENTS.md                   # AI agent instructions
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- `pip` or `uv`

### 1. Install root dependencies (activates Git hooks)

```bash
npm install
```

### 2. Set up the backend

```bash
cd apps/api
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` and fill in your LLM credentials (see [LLM Configuration](#llm-configuration) below).

### 3. Run the backend

```bash
cd apps/api
uvicorn app.main:app --reload
```

- API base: http://localhost:8000
- Health check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs

### 4. Run the frontend

```bash
cd apps/web
npm run dev
```

- App: http://localhost:3000

---

## LLM Configuration

The backend uses the **OpenAI-compatible protocol** — no code changes needed to switch providers. Set these in `apps/api/.env`:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o
```

| Provider | `LLM_BASE_URL` |
|----------|----------------|
| OpenAI | `https://api.openai.com/v1` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` |
| DeepSeek | `https://api.deepseek.com/v1` |

---

## Running Tests

```bash
# Backend
cd apps/api && pytest

# Frontend
cd apps/web && npm test
```
