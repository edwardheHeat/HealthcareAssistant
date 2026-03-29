"""Chat router — session management and message exchange."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
<<<<<<< HEAD
from app.dependencies import get_current_user
from app.llm.chat_service import send_chat_message
from app.models.chat import ChatMessage, ChatSession
from app.models.user import UserProfile
=======
from app.llm.chat_service import get_or_create_session, send_chat_message
from app.models.chat import ChatMessage, ChatSession
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatResponse,
    ChatSessionRead,
)

router = APIRouter(prefix="/chat", tags=["chat"])

<<<<<<< HEAD

@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    """Start a new chat session."""
    session = ChatSession(user_id=current_user.id)
=======
_DEFAULT_USER_ID = 1


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(db: Session = Depends(get_db)) -> ChatSession:
    """Start a new chat session."""
    session = ChatSession(user_id=_DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(
    limit: int = 20,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    return db.scalars(  # type: ignore[return-value]
        select(ChatSession)
<<<<<<< HEAD
        .where(ChatSession.user_id == current_user.id)
=======
        .where(ChatSession.user_id == _DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
        .order_by(ChatSession.started_at.desc())
        .limit(limit)
    ).all()


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def post_message(
    session_id: int,
    payload: ChatMessageCreate,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a user message and receive an AI assistant reply."""
    session = db.get(ChatSession, session_id)
<<<<<<< HEAD
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    assistant_msg = await send_chat_message(db, session_id, current_user.id, payload.content)
=======
    if session is None or session.user_id != _DEFAULT_USER_ID:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    assistant_msg = await send_chat_message(db, session_id, _DEFAULT_USER_ID, payload.content)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    return ChatResponse(message=ChatMessageRead.model_validate(assistant_msg))


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def get_messages(
    session_id: int,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
=======
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != _DEFAULT_USER_ID:
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return db.scalars(  # type: ignore[return-value]
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
