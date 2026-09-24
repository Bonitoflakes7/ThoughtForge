import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.chat.models import ConversationType


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    usernames: list[str] = Field(min_length=1, max_length=50)


class ConversationMemberResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    is_admin: bool
    last_read_at: datetime | None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    type: ConversationType
    name: str | None
    members: list[ConversationMemberResponse]
    last_message_at: datetime | None
    unread_count: int = 0


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    sender_username: str
    sender_display_name: str
    body: str
    created_at: datetime
    edited_at: datetime | None
    is_deleted: bool
    read_by_count: int = 0


class MessageCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
