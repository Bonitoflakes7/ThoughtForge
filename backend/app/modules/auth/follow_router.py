from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.core.dependencies import CurrentUser, DbSession
from app.modules.auth.models import Follow, User
from app.modules.notifications.models import Notification, NotificationType

router = APIRouter(prefix="/users", tags=["follows"])


@router.post("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def follow_user(username: str, user: CurrentUser, session: DbSession) -> None:
    target = await session.scalar(select(User).where(User.username == username.lower()))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself")
    exists = await session.scalar(
        select(Follow).where(Follow.follower_id == user.id, Follow.following_id == target.id)
    )
    if exists is None:
        session.add(Follow(follower_id=user.id, following_id=target.id))
        session.add(Notification(
            user_id=target.id, actor_id=user.id, type=NotificationType.FOLLOW,
            message=f"{user.display_name} started following you", target_id=user.id,
        ))
        await session.commit()


@router.delete("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(username: str, user: CurrentUser, session: DbSession) -> None:
    target = await session.scalar(select(User).where(User.username == username.lower()))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.execute(delete(Follow).where(Follow.follower_id == user.id, Follow.following_id == target.id))
    await session.commit()
