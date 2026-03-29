from datetime import datetime

from pydantic import BaseModel

from app.models.chat import MessageRole


class ChatSessionCreate(BaseModel):
    pass  # user_id comes from path / auth context


class ChatSessionRead(BaseModel):
    id: int
    user_id: int
    started_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    message: ChatMessageRead  # the assistant reply
