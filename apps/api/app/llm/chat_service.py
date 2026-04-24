"""Chat service with health context injection."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.client import get_llm_client
from app.llm.prompts import build_chat_system_prompt
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.medical import ClinicalHistoryEntry
from app.models.user import UserProfile
from app.services.analysis_service import get_apple_health_summary
from app.services.stats import build_user_stats_context

logger = logging.getLogger(__name__)


async def get_or_create_session(db: Session, user_id: int) -> ChatSession:
    session = db.scalars(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.started_at.desc())
        .limit(1)
    ).first()
    if session is None:
        session = ChatSession(user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _build_fallback_sections(
    stats: dict,
    clinical_entries: list[ClinicalHistoryEntry],
) -> list[str]:
    sections: list[str] = []

    bmi = stats.get("bmi")
    weight_trend = stats.get("weight_trend")
    if bmi is not None:
        sections.append(
            f"Your latest recorded BMI is {bmi}, and your recent weight "
            f"trend looks {weight_trend}."
        )

    diet = stats.get("diet", {})
    avg_calories = diet.get("avg_calories_7d")
    calorie_balance = diet.get("calorie_deficit_surplus_vs_tdee")
    if avg_calories is not None:
        balance_text = (
            f"about {abs(calorie_balance)} kcal/day below your estimated needs"
            if isinstance(calorie_balance, (int, float)) and calorie_balance < 0
            else (
                f"about {calorie_balance} kcal/day above your estimated needs"
                if isinstance(calorie_balance, (int, float))
                else "close to your estimated needs"
            )
        )
        sections.append(
            f"Over the last week, your logged diet averages {avg_calories} "
            f"kcal/day, which is {balance_text}."
        )

    sleep = stats.get("sleep", {})
    avg_sleep = sleep.get("avg_duration_hrs_7d")
    avg_quality = sleep.get("avg_quality_7d")
    if avg_sleep is not None:
        quality_text = (
            f" with an average quality score of {avg_quality}/5"
            if avg_quality is not None
            else ""
        )
        sections.append(
            f"Your recent sleep average is {avg_sleep} hours{quality_text}."
        )

    exercise = stats.get("exercise", {})
    cardio_sessions = exercise.get("cardio_sessions_per_week")
    activity_trend = exercise.get("activity_trend")
    if exercise.get("last_recorded_at") is not None and cardio_sessions is not None:
        sections.append(
            f"You have logged {cardio_sessions} cardio-style session(s) this "
            f"week, and your activity trend is {activity_trend}."
        )

    if clinical_entries:
        recent_conditions = ", ".join(
            entry.illness_name for entry in clinical_entries[:3]
        )
        sections.append(
            f"Your saved clinical history includes: {recent_conditions}."
        )

    return sections


def _build_fallback_chat_reply(
    user: UserProfile | None,
    user_text: str,
    stats: dict,
    clinical_entries: list[ClinicalHistoryEntry],
) -> str:
    first_name = user.name.split()[0] if user and user.name else "there"
    sections = _build_fallback_sections(stats, clinical_entries)

    if sections:
        summary = " ".join(sections[:3])
        return (
            f"{first_name}, I can't reach the AI service right now, but I can still "
            f"give you a quick summary based on your saved data. For your question "
            f"about \"{user_text}\", here is what I can confirm: {summary} "
            "If you want a deeper interpretation, try again after the AI "
            "connection is restored."
        )

    return (
        f"{first_name}, I can't reach the AI service right now, and I also do not "
        "have enough saved health data yet to answer that well. Keep logging body, "
        "diet, sleep, or exercise entries, then try the question again."
    )


async def send_chat_message(
    db: Session,
    session_id: int,
    user_id: int,
    user_text: str,
) -> ChatMessage:
    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.user,
        content=user_text,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    user = db.get(UserProfile, user_id)
    stats = build_user_stats_context(db, user_id)
    apple_health = get_apple_health_summary(user_id, db)
    clinical_entries = db.scalars(
        select(ClinicalHistoryEntry)
        .where(ClinicalHistoryEntry.user_id == user_id)
        .order_by(
            ClinicalHistoryEntry.diagnosis_date.desc(),
            ClinicalHistoryEntry.id.desc(),
        )
    ).all()
    system_prompt = build_chat_system_prompt(  # type: ignore[arg-type]
        user,
        stats,
        clinical_entries,
        apple_health=apple_health,
    )

    history = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": msg.role.value, "content": msg.content} for msg in history
    ]

    client = get_llm_client()
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,  # type: ignore[arg-type]
        )
        reply_text = response.choices[0].message.content or ""
    except Exception as exc:
        logger.warning(
            "LLM chat unavailable for user_id=%s session_id=%s; using local "
            "fallback reply: %s",
            user_id,
            session_id,
            exc,
        )
        reply_text = _build_fallback_chat_reply(
            user,
            user_text,
            stats,
            clinical_entries,
        )

    assistant_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.assistant,
        content=reply_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg
