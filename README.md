# HealthcareAssistant

A personal AI-powered health tracker for proactive health management.
Log your daily metrics, view statistics on your dashboard, and chat with an AI assistant that knows your health data.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd apps/api
pip install -e ".[dev]"
cp .env.example .env          # then fill in LLM_* values (see below)
uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

App: http://localhost:3000

### 3. LLM credentials (`.env`)

```env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai  # Gemini
LLM_API_KEY=your-api-key-here
LLM_MODEL=gemini-2.0-flash
```

> See `docs/SETUP.md` for the full setup guide.
