"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import app.models  # noqa: F401 — ensures all ORM models are registered
from app.db import Base, SessionLocal, engine
from app.routers import alerts, apple_health, chat, clinical, health_records, monitor, stats, users


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[type-arg]
    # Create all SQLite tables on startup
    Base.metadata.create_all(bind=engine)

    # Start the daily health monitor as a background job
    scheduler = AsyncIOScheduler()

    def run_daily_monitor() -> None:
        from app.services.monitor import run_monitor

        db: Session = SessionLocal()
        try:
            # Run monitor for user 1 (MVP: single user)
            run_monitor(db, user_id=1)
        finally:
            db.close()

    scheduler.add_job(run_daily_monitor, "interval", hours=24, id="daily_monitor")
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="HealthcareAssistant API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api/v1
_PREFIX = "/api/v1"
app.include_router(users.router, prefix=_PREFIX)
app.include_router(health_records.router, prefix=_PREFIX)
app.include_router(clinical.router, prefix=_PREFIX)
app.include_router(stats.router, prefix=_PREFIX)
app.include_router(alerts.router, prefix=_PREFIX)
app.include_router(chat.router, prefix=_PREFIX)
app.include_router(monitor.router, prefix=_PREFIX)
app.include_router(apple_health.router, prefix=_PREFIX)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
