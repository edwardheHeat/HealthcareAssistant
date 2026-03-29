"""Generate and persist dashboard analysis summaries after health updates."""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.llm.client import get_sync_llm_client
from app.llm.prompts import (
    _DASHBOARD_ANALYSIS_SYSTEM_TEMPLATE,
    build_dashboard_analysis_user_prompt,
)
from app.models.analysis import IndicatorAnalysis, OverallAnalysis
from app.models.user import UserProfile
from app.services.analysis_service import compute_dashboard_stat_blocks

logger = logging.getLogger(__name__)

_ANALYSIS_CATEGORIES = ("basic", "diet", "exercise", "sleep")
_ANALYSIS_PERIODS = ("7d", "30d")


def _extract_json_payload(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response did not contain a JSON object.")

    return json.loads(text[start : end + 1])


def _generate_dashboard_analysis_payload(
    user: UserProfile,
    stats: dict[str, Any],
) -> dict[str, Any]:
    client = get_sync_llm_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": _DASHBOARD_ANALYSIS_SYSTEM_TEMPLATE,
            },
            {
                "role": "user",
                "content": build_dashboard_analysis_user_prompt(user, stats),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    return _extract_json_payload(content)


def _persist_indicator_analysis(
    db: Session,
    user_id: int,
    payload: dict[str, Any],
) -> None:
    for category in _ANALYSIS_CATEGORIES:
        category_payload = payload.get(category, {})
        if not isinstance(category_payload, dict):
            continue

        for period_type in _ANALYSIS_PERIODS:
            analysis_text = category_payload.get(period_type)
            if not isinstance(analysis_text, str) or not analysis_text.strip():
                continue

            db.add(
                IndicatorAnalysis(
                    user_id=user_id,
                    category=category,
                    period_type=period_type,
                    analysis_text=analysis_text.strip(),
                )
            )


def _persist_overall_analysis(
    db: Session,
    user_id: int,
    payload: dict[str, Any],
) -> None:
    summary = payload.get("overall_summary")
    if not isinstance(summary, str) or not summary.strip():
        return

    db.add(
        OverallAnalysis(
            user_id=user_id,
            summary_text=summary.strip(),
        )
    )


def refresh_dashboard_analysis(db: Session, user_id: int) -> None:
    """Regenerate stored dashboard analysis after health data changes."""
    user = db.get(UserProfile, user_id)
    if user is None:
        logger.warning(
            "Skipping dashboard analysis refresh: user %s not found", user_id
        )
        return

    stats = compute_dashboard_stat_blocks(user_id, db)

    try:
        payload = _generate_dashboard_analysis_payload(user, stats)
        _persist_indicator_analysis(db, user_id, payload)
        _persist_overall_analysis(db, user_id, payload)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Dashboard analysis refresh failed for user_id=%s; "
            "keeping saved health data.",
            user_id,
        )
