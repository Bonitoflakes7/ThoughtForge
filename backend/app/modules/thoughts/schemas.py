import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.thoughts.models import ForkType


class ThoughtCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10000)


class ForkCreateRequest(ThoughtCreateRequest):
    fork_type: ForkType


class ThoughtUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    body: str | None = Field(default=None, min_length=1, max_length=10000)


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class AuthorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str


class CommentResponse(BaseModel):
    id: uuid.UUID
    thought_id: uuid.UUID
    body: str
    author: AuthorSummary
    like_count: int
    created_at: datetime
    is_deleted: bool


class ThoughtResponse(BaseModel):
    id: uuid.UUID
    parent_thought_id: uuid.UUID | None
    title: str
    body: str
    fork_type: ForkType | None
    author: AuthorSummary
    like_count: int
    comment_count: int
    fork_count: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class ThoughtDetailResponse(ThoughtResponse):
    comments: list[CommentResponse]
    forks: list[ThoughtResponse]
