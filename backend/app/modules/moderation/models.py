import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin


class ReportTarget(str, enum.Enum):
    THOUGHT = "thought"
    COMMENT = "comment"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationAction(str, enum.Enum):
    DISMISS = "dismiss"
    HIDE = "hide"
    RESTORE = "restore"
    DEACTIVATE_USER = "deactivate_user"


class Report(TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_reporter_target"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[ReportTarget] = mapped_column(Enum(ReportTarget), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(index=True)
    reason: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.OPEN, index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id], lazy="joined")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], lazy="joined")


class ModerationLog(TimestampMixin, Base):
    __tablename__ = "moderation_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    moderator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[ModerationAction] = mapped_column(Enum(ModerationAction))
    target_type: Mapped[ReportTarget] = mapped_column(Enum(ReportTarget))
    target_id: Mapped[uuid.UUID] = mapped_column(index=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    moderator = relationship("User", lazy="joined")
