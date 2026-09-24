from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, delete, or_, select

from app.core.dependencies import CurrentUser, DbSession
from app.modules.auth.models import User
from app.modules.thoughts.models import Comment, CommentLike, Thought, ThoughtLike
from app.modules.thoughts.schemas import (
    AuthorSummary,
    CommentCreateRequest,
    CommentResponse,
    ForkCreateRequest,
    ThoughtCreateRequest,
    ThoughtDetailResponse,
    ThoughtResponse,
    ThoughtUpdateRequest,
)
from app.modules.notifications.models import Notification, NotificationType

router = APIRouter(prefix="/thoughts", tags=["thoughts"])


def author_summary(user: User) -> AuthorSummary:
    return AuthorSummary.model_validate(user)


def thought_response(thought: Thought) -> ThoughtResponse:
    return ThoughtResponse(
        id=thought.id,
        parent_thought_id=thought.parent_thought_id,
        title=thought.title,
        body=thought.body,
        fork_type=thought.fork_type,
        author=author_summary(thought.author),
        like_count=thought.like_count,
        comment_count=thought.comment_count,
        fork_count=thought.fork_count,
        created_at=thought.created_at,
        updated_at=thought.updated_at,
        is_deleted=thought.is_deleted,
    )


def comment_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        thought_id=comment.thought_id,
        body=comment.body,
        author=author_summary(comment.author),
        like_count=comment.like_count,
        created_at=comment.created_at,
        is_deleted=comment.is_deleted,
    )


async def get_thought_or_404(session: DbSession, thought_id: UUID) -> Thought:
    thought = await session.scalar(select(Thought).where(Thought.id == thought_id, Thought.is_deleted.is_(False)))
    if thought is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thought not found")
    return thought


@router.post("", response_model=ThoughtResponse, status_code=status.HTTP_201_CREATED)
async def create_thought(request: ThoughtCreateRequest, user: CurrentUser, session: DbSession) -> ThoughtResponse:
    thought = Thought(author_id=user.id, title=request.title, body=request.body)
    session.add(thought)
    await session.commit()
    await session.refresh(thought)
    thought.author = user
    return thought_response(thought)


@router.get("", response_model=list[ThoughtResponse])
async def list_thoughts(
    session: DbSession,
    sort: str = Query(default="top", pattern="^(top|recent)$"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> list[ThoughtResponse]:
    query = select(Thought).where(Thought.is_deleted.is_(False), Thought.parent_thought_id.is_(None))
    if sort == "recent":
        query = query.order_by(desc(Thought.created_at))
    else:
        query = query.order_by(desc(Thought.like_count), desc(Thought.comment_count), desc(Thought.created_at))
    thoughts = (await session.scalars(query.offset(offset).limit(limit))).all()
    return [thought_response(thought) for thought in thoughts]


@router.get("/search", response_model=list[ThoughtResponse])
async def search_thoughts(
    session: DbSession, q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=30, ge=1, le=50),
) -> list[ThoughtResponse]:
    query = f"%{q.strip()}%"
    thoughts = (await session.scalars(select(Thought).where(
        Thought.is_deleted.is_(False), Thought.parent_thought_id.is_(None),
        or_(Thought.title.ilike(query), Thought.body.ilike(query)),
    ).order_by(desc(Thought.like_count), desc(Thought.created_at)).limit(limit))).all()
    return [thought_response(thought) for thought in thoughts]


@router.get("/{thought_id}", response_model=ThoughtDetailResponse)
async def get_thought(thought_id: UUID, session: DbSession) -> ThoughtDetailResponse:
    thought = await get_thought_or_404(session, thought_id)
    comments = (
        await session.scalars(
            select(Comment)
            .where(Comment.thought_id == thought.id, Comment.is_deleted.is_(False))
            .order_by(desc(Comment.like_count), desc(Comment.created_at))
        )
    ).all()
    forks = (
        await session.scalars(
            select(Thought)
            .where(Thought.parent_thought_id == thought.id, Thought.is_deleted.is_(False))
            .order_by(desc(Thought.like_count), desc(Thought.created_at))
        )
    ).all()
    return ThoughtDetailResponse(
        **thought_response(thought).model_dump(),
        comments=[comment_response(comment) for comment in comments],
        forks=[thought_response(fork) for fork in forks],
    )


@router.patch("/{thought_id}", response_model=ThoughtResponse)
async def update_thought(
    thought_id: UUID, request: ThoughtUpdateRequest, user: CurrentUser, session: DbSession
) -> ThoughtResponse:
    thought = await get_thought_or_404(session, thought_id)
    if thought.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can edit this thought")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(thought, field, value)
    await session.commit()
    await session.refresh(thought)
    return thought_response(thought)


@router.delete("/{thought_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thought(thought_id: UUID, user: CurrentUser, session: DbSession) -> None:
    thought = await get_thought_or_404(session, thought_id)
    if thought.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can delete this thought")
    thought.is_deleted = True
    await session.commit()


@router.post("/{thought_id}/fork", response_model=ThoughtResponse, status_code=status.HTTP_201_CREATED)
async def fork_thought(
    thought_id: UUID, request: ForkCreateRequest, user: CurrentUser, session: DbSession
) -> ThoughtResponse:
    parent = await get_thought_or_404(session, thought_id)
    fork = Thought(
        author_id=user.id,
        parent_thought_id=parent.id,
        title=request.title,
        body=request.body,
        fork_type=request.fork_type,
    )
    parent.fork_count += 1
    if parent.author_id != user.id:
        session.add(Notification(
            user_id=parent.author_id, actor_id=user.id, type=NotificationType.FORK,
            message=f"{user.display_name} forked your thought", target_id=parent.id,
        ))
    session.add(fork)
    await session.commit()
    await session.refresh(fork)
    fork.author = user
    return thought_response(fork)


@router.post("/{thought_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    thought_id: UUID, request: CommentCreateRequest, user: CurrentUser, session: DbSession
) -> CommentResponse:
    thought = await get_thought_or_404(session, thought_id)
    comment = Comment(thought_id=thought.id, author_id=user.id, body=request.body)
    thought.comment_count += 1
    if thought.author_id != user.id:
        session.add(Notification(
            user_id=thought.author_id, actor_id=user.id, type=NotificationType.COMMENT,
            message=f"{user.display_name} commented on your thought", target_id=thought.id,
        ))
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    comment.author = user
    return comment_response(comment)


@router.post("/{thought_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_thought(thought_id: UUID, user: CurrentUser, session: DbSession) -> None:
    thought = await get_thought_or_404(session, thought_id)
    existing = await session.scalar(
        select(ThoughtLike).where(ThoughtLike.thought_id == thought.id, ThoughtLike.user_id == user.id)
    )
    if existing is None:
        session.add(ThoughtLike(thought_id=thought.id, user_id=user.id))
        thought.like_count += 1
        if thought.author_id != user.id:
            session.add(Notification(
                user_id=thought.author_id, actor_id=user.id, type=NotificationType.LIKE,
                message=f"{user.display_name} liked your thought", target_id=thought.id,
            ))
        await session.commit()


@router.delete("/{thought_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_thought(thought_id: UUID, user: CurrentUser, session: DbSession) -> None:
    thought = await get_thought_or_404(session, thought_id)
    result = await session.execute(
        delete(ThoughtLike).where(ThoughtLike.thought_id == thought.id, ThoughtLike.user_id == user.id)
    )
    if result.rowcount:
        thought.like_count = max(0, thought.like_count - 1)
        await session.commit()


@router.post("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_comment(comment_id: UUID, user: CurrentUser, session: DbSession) -> None:
    comment = await session.scalar(select(Comment).where(Comment.id == comment_id, Comment.is_deleted.is_(False)))
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    existing = await session.scalar(
        select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.user_id == user.id)
    )
    if existing is None:
        session.add(CommentLike(comment_id=comment.id, user_id=user.id))
        comment.like_count += 1
        await session.commit()


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_comment(comment_id: UUID, user: CurrentUser, session: DbSession) -> None:
    comment = await session.scalar(select(Comment).where(Comment.id == comment_id, Comment.is_deleted.is_(False)))
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    result = await session.execute(
        delete(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.user_id == user.id)
    )
    if result.rowcount:
        comment.like_count = max(0, comment.like_count - 1)
        await session.commit()
