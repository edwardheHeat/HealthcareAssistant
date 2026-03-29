"""Chat router — session management and message exchange."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm.chat_service import send_chat_message
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatResponse,
    ChatSessionRead,
)

router = APIRouter(prefix="/chat", tags=["chat"])

_DEFAULT_USER_ID = 1


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(db: Session = Depends(get_db)) -> ChatSession:
    """Start a new chat session."""
    session = ChatSession(user_id=_DEFAULT_USER_ID)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    return db.scalars(  # type: ignore[return-value]
        select(ChatSession)
        .where(ChatSession.user_id == _DEFAULT_USER_ID)
        .order_by(ChatSession.started_at.desc())
        .limit(limit)
    ).all()


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def post_message(
    session_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a user message and receive an AI assistant reply."""
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != _DEFAULT_USER_ID:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    assistant_msg = await send_chat_message(
        db,
        session_id,
        _DEFAULT_USER_ID,
        payload.content,
    )
    return ChatResponse(message=ChatMessageRead.model_validate(assistant_msg))


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != _DEFAULT_USER_ID:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return db.scalars(  # type: ignore[return-value]
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
