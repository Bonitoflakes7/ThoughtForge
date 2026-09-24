import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.moderation.models import ModerationAction, ReportStatus, ReportTarget
from app.modules.auth.models import UserRole


class ReportCreateRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=80)
    details: str | None = Field(default=None, max_length=1000)


class ReportResponse(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: ReportTarget
    target_id: uuid.UUID
    reason: str
    details: str | None
    status: ReportStatus
    resolution_note: str | None
    created_at: datetime
    resolved_by_id: uuid.UUID | None


class ReportResolutionRequest(BaseModel):
    action: ModerationAction
    note: str | None = Field(default=None, max_length=1000)


class ReportQueueResponse(BaseModel):
    reports: list[ReportResponse]
    open_count: int


class RoleUpdateRequest(BaseModel):
    role: UserRole


class AccountStatusUpdateRequest(BaseModel):
    is_active: bool
