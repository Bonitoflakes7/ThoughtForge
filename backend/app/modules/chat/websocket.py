import jwt
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from app.core.database import session_factory
from app.core.security import decode_token
from app.modules.auth.models import User
from app.modules.chat.manager import chat_manager
from app.modules.chat.models import ConversationMember, Message, MessageRead


async def chat_websocket(websocket: WebSocket, conversation_id: str) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        user_id = decode_token(token)["sub"]
    except (KeyError, jwt.InvalidTokenError):
        await websocket.close(code=4401)
        return

    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
        conversation_uuid = UUID(conversation_id)
    except ValueError:
        await websocket.close(code=4400)
        return

    async with session_factory() as session:
        member = await session.scalar(select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_uuid, ConversationMember.user_id == user_uuid
        ))
        if member is None:
            await websocket.close(code=4403)
            return

    await chat_manager.connect(conversation_uuid, user_uuid, websocket)
    await chat_manager.broadcast(conversation_uuid, {"type": "presence", "user_id": str(user_uuid), "online": True})
    try:
        while True:
            payload = await websocket.receive_json()
            event_type = payload.get("type")
            if event_type in {"typing_start", "typing_stop"}:
                await chat_manager.broadcast(conversation_uuid, {
                    "type": event_type, "user_id": str(user_uuid),
                }, exclude=websocket)
            elif event_type == "read":
                async with session_factory() as session:
                    member = await session.scalar(select(ConversationMember).where(
                        ConversationMember.conversation_id == conversation_uuid,
                        ConversationMember.user_id == user_uuid,
                    ))
                    if member:
                        from datetime import datetime, timezone
                        member.last_read_at = datetime.now(timezone.utc)
                    messages = (await session.scalars(select(Message).where(
                        Message.conversation_id == conversation_uuid, Message.sender_id != user_uuid
                    ))).all()
                    message_ids = [item.id for item in messages]
                    existing = set((await session.scalars(select(MessageRead.message_id).where(
                        MessageRead.user_id == user_uuid, MessageRead.message_id.in_(message_ids)
                    ))).all()) if message_ids else set()
                    new_reads = [MessageRead(message_id=item.id, user_id=user_uuid) for item in messages if item.id not in existing]
                    session.add_all(new_reads)
                    await session.flush()
                    read_counts = {}
                    for item in messages:
                        read_counts[str(item.id)] = await session.scalar(
                            select(func.count(MessageRead.id)).where(MessageRead.message_id == item.id)
                        ) or 0
                    await session.commit()
                await chat_manager.broadcast(conversation_uuid, {
                    "type": "read", "user_id": str(user_uuid),
                    "message_ids": [str(item.id) for item in messages], "read_by_count": read_counts,
                }, exclude=websocket)
            elif event_type == "message" and str(payload.get("body", "")).strip():
                async with session_factory() as session:
                    message = Message(conversation_id=conversation_uuid, sender_id=user_uuid, body=str(payload["body"]).strip())
                    session.add(message)
                    await session.commit()
                    await session.refresh(message)
                    sender = await session.get(User, user_uuid)
                    output = {
                        "type": "message", "id": str(message.id), "conversation_id": str(conversation_uuid),
                        "sender_id": str(user_uuid), "sender_username": sender.username,
                        "sender_display_name": sender.display_name, "body": message.body,
                        "created_at": message.created_at.isoformat(), "read_by_count": 0,
                    }
                await chat_manager.broadcast(conversation_uuid, output)
    except (WebSocketDisconnect, RuntimeError):
        chat_manager.disconnect(conversation_uuid, user_uuid, websocket)
        await chat_manager.broadcast(conversation_uuid, {"type": "presence", "user_id": str(user_uuid), "online": False})
