import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin


class ForkType(str, enum.Enum):
    SUPPORT = "support"
    CHALLENGE = "challenge"
    REFINE = "refine"
    EXTEND = "extend"


class Thought(TimestampMixin, Base):
    __tablename__ = "thoughts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_thought_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("thoughts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text())
    fork_type: Mapped[ForkType | None] = mapped_column(Enum(ForkType), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)

    author = relationship("User", lazy="joined")
    parent = relationship("Thought", remote_side=[id], back_populates="forks")
    forks = relationship("Thought", back_populates="parent")
    comments = relationship("Comment", back_populates="thought", cascade="all, delete-orphan")


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thought_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("thoughts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0)

    thought = relationship("Thought", back_populates="comments")
    author = relationship("User", lazy="joined")


class ThoughtLike(TimestampMixin, Base):
    __tablename__ = "thought_likes"
    __table_args__ = (UniqueConstraint("thought_id", "user_id", name="uq_thought_like"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thought_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("thoughts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class CommentLike(TimestampMixin, Base):
    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_like"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
