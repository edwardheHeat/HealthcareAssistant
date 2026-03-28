"""Chat service — handles conversation turns with full context injection."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.client import get_llm_client
from app.llm.prompts import build_chat_system_prompt
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.clinical import ClinicalHistory
from app.models.user import UserProfile
from app.services.stats import build_user_stats_context


async def get_or_create_session(db: Session, user_id: int) -> ChatSession:
    """Return the most recent open session, or create a new one."""
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


async def send_chat_message(
    db: Session,
    session_id: int,
    user_id: int,
    user_text: str,
) -> ChatMessage:
    """Process a user message and return the assistant reply as a ChatMessage."""

    # Persist user message
    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.user,
        content=user_text,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build context
    user = db.get(UserProfile, user_id)
    stats = build_user_stats_context(db, user_id)
    clinical = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == user_id)
    ).first()
    system_prompt = build_chat_system_prompt(user, stats, clinical)  # type: ignore[arg-type]

    # Load conversation history for this session
    history = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": msg.role.value, "content": msg.content} for msg in history
    ]

    # Call LLM
    client = get_llm_client()
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,  # type: ignore[arg-type]
    )
    reply_text = response.choices[0].message.content or ""

    # Persist assistant reply
    assistant_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.assistant,
        content=reply_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg
