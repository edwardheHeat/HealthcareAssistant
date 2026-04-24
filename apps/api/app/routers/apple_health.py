"""Apple Health import endpoints — processes step and sleep data from simulated HealthKit import.

In production, this system integrates with Apple Health via HealthKit through a native iOS
application. Due to browser privacy restrictions, this demo simulates the import process
using synchronized mock data.
"""

import json
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.llm.client import call_llm
from app.models.apple_health import AppleHealthSync
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apple-health", tags=["apple-health"])

_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class HealthDataPayload(BaseModel):
    steps: list[int]
    sleep: list[float]


class AskAIRequest(HealthDataPayload):
    question: str


def _compute_summaries(steps: list[int], sleep: list[float]) -> dict:
    total_steps = sum(steps)
    avg_sleep = round(sum(sleep) / len(sleep), 2) if sleep else 0.0

    midweek_drop = False
    if len(sleep) >= 5:
        midweek_avg = sum(sleep[i] for i in [2, 3, 4]) / 3
        midweek_drop = (avg_sleep - midweek_avg) > 0.5

    high_fluctuation = (max(steps) - min(steps)) > 4000 if steps else False

    return {
        "total_steps_7d": total_steps,
        "avg_sleep_hrs": avg_sleep,
        "midweek_sleep_drop": midweek_drop,
        "high_activity_fluctuation": high_fluctuation,
    }


def _build_data_context(steps: list[int], sleep: list[float], summaries: dict) -> str:
    step_lines = "\n".join(
        f"  {_DAYS[i] if i < len(_DAYS) else f'Day {i+1}'}: {s:,} steps"
        for i, s in enumerate(steps)
    )
    sleep_lines = "\n".join(
        f"  {_DAYS[i] if i < len(_DAYS) else f'Day {i+1}'}: {h} hrs"
        for i, h in enumerate(sleep)
    )

    patterns: list[str] = []
    if summaries["midweek_sleep_drop"]:
        patterns.append(
            "Midweek sleep drop detected (Wed–Fri sleep below weekly average by >30 min)."
        )
    if summaries["high_activity_fluctuation"]:
        patterns.append(
            "High activity fluctuation: step count varies by more than 4,000 steps across days."
        )
    pattern_text = (
        "\n".join(f"- {p}" for p in patterns)
        if patterns
        else "- No significant anomalies detected."
    )

    return (
        f"Apple Health Data (last 7 days):\n\n"
        f"Daily Steps:\n{step_lines}\n"
        f"Total: {summaries['total_steps_7d']:,} steps\n\n"
        f"Daily Sleep:\n{sleep_lines}\n"
        f"Average: {summaries['avg_sleep_hrs']} hrs/night\n\n"
        f"Detected Patterns:\n{pattern_text}"
    )


_INSIGHT_SYSTEM = """\
You are a compassionate personal health AI that analyzes Apple Health data.
Identify meaningful patterns in step count and sleep data, explain potential causes
(stress, schedule, weekend effect), and provide 2–3 specific actionable recommendations.
Be encouraging and non-judgmental. Keep the response to 3–5 sentences.
Do not diagnose medical conditions."""

_QA_SYSTEM = """\
You are a compassionate personal health AI that answers questions using Apple Health data.
Use the provided step count and sleep data to directly answer the user's question.
Identify relevant patterns in the data, and provide one specific actionable recommendation.
Be encouraging and non-judgmental. Keep the response focused and to 3–5 sentences.
Do not diagnose medical conditions."""


def _fallback_insight(summaries: dict) -> str:
    parts = [
        f"Over the last 7 days you logged {summaries['total_steps_7d']:,} total steps "
        f"and averaged {summaries['avg_sleep_hrs']} hours of sleep per night."
    ]
    if summaries["midweek_sleep_drop"]:
        parts.append(
            "There is a notable midweek sleep drop — consider setting a consistent "
            "bedtime on weeknights."
        )
    if summaries["high_activity_fluctuation"]:
        parts.append(
            "Your step count varies significantly day-to-day; try to maintain more "
            "consistent daily activity."
        )
    return " ".join(parts)


def _fallback_answer(question: str, summaries: dict) -> str:
    return (
        f"Based on your Apple Health data (7-day total: {summaries['total_steps_7d']:,} steps, "
        f"average sleep: {summaries['avg_sleep_hrs']} hrs/night), I cannot reach the AI service "
        f'right now to fully answer "{question}". Try again once the connection is restored.'
    )


@router.post("/sync")
def sync_apple_health(
    payload: HealthDataPayload,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Persist the simulated Apple Health import for this user."""
    record = AppleHealthSync(
        user_id=current_user.id,
        steps_json=json.dumps(payload.steps),
        sleep_json=json.dumps(payload.sleep),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "synced_at": record.synced_at.isoformat(),
        "steps": payload.steps,
        "sleep": payload.sleep,
    }


@router.get("/sync/latest")
def get_latest_sync(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict | None:
    """Return the most recent Apple Health sync for this user, or null."""
    record = db.scalars(
        select(AppleHealthSync)
        .where(AppleHealthSync.user_id == current_user.id)
        .order_by(AppleHealthSync.synced_at.desc())
        .limit(1)
    ).first()
    if record is None:
        return {}
    summaries = _compute_summaries(record.steps, record.sleep)
    return {
        "id": record.id,
        "synced_at": record.synced_at.isoformat(),
        "steps": record.steps,
        "sleep": record.sleep,
        "summaries": summaries,
    }


@router.post("/insight")
async def generate_insight(
    payload: HealthDataPayload,
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Generate a weekly health insight from imported Apple Health data."""
    summaries = _compute_summaries(payload.steps, payload.sleep)
    data_context = _build_data_context(payload.steps, payload.sleep, summaries)
    user_prompt = (
        f"{data_context}\n\n"
        "Please provide a concise weekly health insight based on this Apple Health data."
    )

    try:
        insight = await call_llm(_INSIGHT_SYSTEM, user_prompt)
    except Exception as exc:
        logger.warning("LLM unavailable for Apple Health insight: %s", exc)
        insight = _fallback_insight(summaries)

    return {"insight": insight, "summaries": summaries}


@router.post("/ask-ai")
async def ask_ai(
    payload: AskAIRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Answer a user question using their Apple Health data as context."""
    summaries = _compute_summaries(payload.steps, payload.sleep)
    data_context = _build_data_context(payload.steps, payload.sleep, summaries)
    user_prompt = f"{data_context}\n\nUser question: {payload.question}"

    try:
        answer = await call_llm(_QA_SYSTEM, user_prompt)
    except Exception as exc:
        logger.warning("LLM unavailable for Apple Health ask-ai: %s", exc)
        answer = _fallback_answer(payload.question, summaries)

    return {"answer": answer}
