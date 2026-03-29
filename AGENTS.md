# AGENTS.md — HealthcareAssistant

Instruction file for AI coding agents working on this project.

---

## 1. Project Overview

**HealthcareAssistant** is a personal health tracker app targeting middle-aged adults (30–50) who are proactively managing their health or dealing with health concerns.

### Core Features
- **Data Collection**: Users submit health data (caloric intake, weight, sleep, etc.) via questionnaires. Frequency is configurable per-user (daily / weekly / monthly).
- **Analysis & Alerts**: The backend processes historical data using statistical methods and LLM inference to generate insights and flag abnormal readings.
- **LLM Chatbox**: A persistent chat interface where users can ask health-related questions at any time, grounded in their personal health data.

### MVP Scope
- Questionnaire-based data input (no wearables/API integrations yet)
- Statistical + LLM-driven analysis and advice
- Alert system for out-of-range metrics
- LLM chat interface

---

## 2. Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Frontend     | Next.js (TypeScript)                |
| Backend API  | FastAPI (Python)                    |
| Database     | SQLite (via SQLAlchemy)             |
| LLM Service  | OpenAI-compatible protocol (provider-agnostic; supports Gemini, DeepSeek, OpenAI, etc.) |
| Auth         | TBD                                 |

### LLM Integration Note
Always use the **OpenAI-compatible client interface** (`openai` Python SDK with configurable `base_url` + `api_key`). Never hardcode a provider. The active provider is controlled via environment variables:
```
LLM_BASE_URL=https://...
LLM_API_KEY=...
LLM_MODEL=...
```

---

## 3. Repository Structure

This is a **monorepo** with frontend and backend co-located.

```
HealthcareAssistant/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/            # Next.js App Router pages
│   │   │   ├── components/     # Reusable UI components
│   │   │   ├── hooks/          # Custom React hooks
│   │   │   ├── lib/            # API client, utilities
│   │   │   └── types/          # Shared frontend types (TypeScript)
│   │   ├── public/
│   │   ├── next.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── main.py         # FastAPI app entrypoint
│       │   ├── routers/        # Route handlers (one file per domain)
│       │   ├── models/         # SQLAlchemy ORM models
│       │   ├── schemas/        # Pydantic request/response schemas
│       │   ├── services/       # Business logic layer
│       │   ├── llm/            # LLM client wrapper + prompt templates
│       │   ├── db.py           # DB session + engine setup
│       │   └── config.py       # Settings (loaded from .env)
│       ├── tests/
│       ├── pyproject.toml
│       └── .env.example
│
├── .husky/                     # Git hooks (pre-commit: lint + format)
├── AGENTS.md                   # This file
├── README.md
└── package.json                # Root (manages husky + lint-staged)
```

---

## 4. Coding Conventions

### General
- **Type everything**, but don't over-engineer generic types. Prefer simple, readable types over overly abstract ones.
- Keep functions small and focused. Prefer flat over nested logic.

### TypeScript (Frontend)
- Use `interface` for object shapes, `type` for unions/aliases.
- Avoid `any`; use `unknown` when type is genuinely unknown.
- Formatter: **Prettier** | Linter: **ESLint** (Next.js default config)

### Python (Backend)
- Use **type hints** on all function signatures and class attributes.
- Formatter: **Ruff format** | Linter: **Ruff**
- Follow PEP 8. Prefer dataclasses or Pydantic models over raw dicts.

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <short summary>

feat(api): add weekly questionnaire endpoint
fix(web): correct calorie chart rendering
docs: update AGENTS.md
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

---

## 5. Testing

- **Backend**: Use `pytest`. Place tests in `apps/api/tests/`. Mirror the `app/` structure.
- **Frontend**: Use `jest` + `@testing-library/react` for component tests.
- Coverage is not required for the MVP. Focus on testing critical business logic (e.g., analysis services, LLM prompt construction).
- Run backend tests: `cd apps/api && pytest`
- Run frontend tests: `cd apps/web && npm test`

---

## 6. Agent Rules

- **Never commit** unless the user explicitly asks you to commit.
- **Never modify `.env` files directly.** Only edit `.env.example` to document new variables.
- **Never run database migrations automatically.** Describe what migration is needed; let the user run it.
- When adding a new API endpoint, always create the corresponding Pydantic schema in `schemas/` and the business logic in `services/`, not inline in the router.
- When modifying LLM prompts, place them as constants or templates in `apps/api/app/llm/` — never inline in service or router files.
- If a task is ambiguous, ask before implementing. Do not make significant architectural decisions unilaterally.
