"""Chat router — session management and message exchange."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.llm.chat_service import send_chat_message
from app.models.chat import ChatMessage, ChatSession
from app.models.user import UserProfile
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatResponse,
    ChatSessionRead,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    """Start a new chat session."""
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(
    limit: int = 20,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    return db.scalars(  # type: ignore[return-value]
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.started_at.desc())
        .limit(limit)
    ).all()


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def post_message(
    session_id: int,
    payload: ChatMessageCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a user message and receive an AI assistant reply."""
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    assistant_msg = await send_chat_message(db, session_id, current_user.id, payload.content)
    return ChatResponse(message=ChatMessageRead.model_validate(assistant_msg))


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def get_messages(
    session_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return db.scalars(  # type: ignore[return-value]
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
