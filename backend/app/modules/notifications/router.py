from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.core.dependencies import CurrentUser, DbSession
from app.modules.notifications.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(user: CurrentUser, session: DbSession, limit: int = 50):
    items = (await session.scalars(
        select(Notification).where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc()).limit(min(limit, 100))
    )).all()
    unread_count = sum(1 for item in items if not item.is_read)
    return {"items": [{
        "id": item.id, "type": item.type, "message": item.message,
        "actor": {"id": item.actor.id, "username": item.actor.username, "display_name": item.actor.display_name},
        "target_id": item.target_id, "is_read": item.is_read, "created_at": item.created_at,
    } for item in items], "unread_count": unread_count}


@router.post("/{notification_id}/read", status_code=204)
async def mark_notification_read(notification_id: UUID, user: CurrentUser, session: DbSession) -> None:
    result = await session.execute(update(Notification).where(
        Notification.id == notification_id, Notification.user_id == user.id
    ).values(is_read=True))
    if not result.rowcount:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.commit()


@router.post("/read-all", status_code=204)
async def mark_all_notifications_read(user: CurrentUser, session: DbSession) -> None:
    await session.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    await session.commit()
