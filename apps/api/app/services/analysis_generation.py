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


def _format_basic_fallback(stats: dict[str, Any]) -> dict[str, str]:
    latest_weight = stats.get("latest_weight_kg")
    avg_7d = stats.get("avg_weight_7d")
    if latest_weight is None:
        return {
            "7d": "No body metrics are logged yet, so there is nothing to analyze.",
            "30d": "Add height and weight entries to unlock body trend analysis.",
        }

    return {
        "7d": (
            f"Your latest recorded weight is {latest_weight} kg. "
            "This is an early baseline, so more entries will make "
            "weekly analysis more useful."
        ),
        "30d": (
            "Your current 30-day average weight is "
            f"{avg_7d if avg_7d is not None else latest_weight} kg. "
            "With only a small amount of history, the monthly trend "
            "is still forming."
        ),
    }


def _format_diet_fallback(stats: dict[str, Any]) -> dict[str, str]:
    avg_calories = stats.get("avg_calories_7d")
    if avg_calories is None:
        return {
            "7d": (
                "No diet logs are available yet, so calorie and macro "
                "analysis is not ready."
            ),
            "30d": "Log meals or calories to build a nutrition trend over time.",
        }

    protein = stats.get("avg_protein_g_7d")
    carbs = stats.get("avg_carbs_g_7d")
    fat = stats.get("avg_fat_g_7d")
    return {
        "7d": (
            f"Your current average intake is about {avg_calories} kcal/day. "
            "Macros are tracking around "
            f"protein {protein} g, carbs {carbs} g, and fat {fat} g."
        ),
        "30d": (
            "Nutrition history is still limited, so treat this as "
            "an early baseline rather than a stable long-term pattern."
        ),
    }


def _format_exercise_fallback(stats: dict[str, Any]) -> dict[str, str]:
    avg_duration = stats.get("avg_duration_7d")
    if avg_duration is None:
        return {
            "7d": (
                "No exercise entries are logged yet, so activity "
                "analysis is not available."
            ),
            "30d": (
                "Add workouts to start building exercise duration "
                "and intensity trends."
            ),
        }

    intensity = stats.get("intensity_distribution", {})
    return {
        "7d": (
            "Your recent exercise average is "
            f"{avg_duration} minutes per logged session. "
            "Current intensity mix is "
            f"low {intensity.get('low', 0)}, "
            f"medium {intensity.get('medium', 0)}, "
            f"and high {intensity.get('high', 0)}."
        ),
        "30d": (
            "This looks like the beginning of your activity baseline. "
            "More workouts will make the monthly trend much more reliable."
        ),
    }


def _format_sleep_fallback(stats: dict[str, Any]) -> dict[str, str]:
    avg_sleep = stats.get("avg_sleep_duration_7d")
    if avg_sleep is None:
        return {
            "7d": (
                "No sleep entries are logged yet, so there is not enough "
                "data for sleep analysis."
            ),
            "30d": (
                "Add a few nights of sleep logs to see duration "
                "and quality patterns."
            ),
        }

    quality = stats.get("avg_quality_7d")
    return {
        "7d": (
            f"Your recent average sleep duration is {avg_sleep} hours, "
            f"with an average quality score of {quality}/5."
        ),
        "30d": (
            "This is an early sleep baseline. "
            "More nights of data will help surface consistency and trend changes."
        ),
    }


def _build_fallback_dashboard_analysis_payload(stats: dict[str, Any]) -> dict[str, Any]:
    basic = _format_basic_fallback(stats.get("basic", {}))
    diet = _format_diet_fallback(stats.get("diet", {}))
    exercise = _format_exercise_fallback(stats.get("exercise", {}))
    sleep = _format_sleep_fallback(stats.get("sleep", {}))

    available_categories = [
        name
        for name, block in {
            "body": stats.get("basic", {}).get("latest_weight_kg"),
            "diet": stats.get("diet", {}).get("avg_calories_7d"),
            "exercise": stats.get("exercise", {}).get("avg_duration_7d"),
            "sleep": stats.get("sleep", {}).get("avg_sleep_duration_7d"),
        }.items()
        if block is not None
    ]
    if available_categories:
        category_text = ", ".join(available_categories)
        overall_summary = (
            "We already have enough data to start a baseline analysis "
            f"for {category_text}. "
            "These summaries are intentionally lightweight for now "
            "and will become more specific as you log more entries."
        )
    else:
        overall_summary = (
            "No analyzed health trends are available yet. "
            "Once you start logging entries, this dashboard will summarize "
            "early patterns for you."
        )

    return {
        "basic": basic,
        "diet": diet,
        "exercise": exercise,
        "sleep": sleep,
        "overall_summary": overall_summary,
    }


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
    except Exception as exc:
        db.rollback()
        logger.warning(
            "Dashboard analysis LLM unavailable for user_id=%s; "
            "using local fallback summaries: %s",
            user_id,
            exc,
        )
        fallback_payload = _build_fallback_dashboard_analysis_payload(stats)
        _persist_indicator_analysis(db, user_id, fallback_payload)
        _persist_overall_analysis(db, user_id, fallback_payload)
        db.commit()
