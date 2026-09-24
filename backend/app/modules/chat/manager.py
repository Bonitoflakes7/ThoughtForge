import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self.user_connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, conversation_id: UUID, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[conversation_id].add(websocket)
        self.user_connections[user_id].add(websocket)

    def disconnect(self, conversation_id: UUID, user_id: UUID, websocket: WebSocket) -> None:
        self.connections[conversation_id].discard(websocket)
        self.user_connections[user_id].discard(websocket)
        if not self.connections[conversation_id]:
            self.connections.pop(conversation_id, None)
        if not self.user_connections[user_id]:
            self.user_connections.pop(user_id, None)

    def is_online(self, user_id: UUID) -> bool:
        return bool(self.user_connections.get(user_id))

    async def broadcast(self, conversation_id: UUID, payload: dict[str, Any], exclude: WebSocket | None = None) -> None:
        for websocket in list(self.connections.get(conversation_id, set())):
            if websocket is not exclude:
                try:
                    await websocket.send_text(json.dumps(payload, default=str))
                except Exception:
                    # A browser may close between the snapshot and the send.
                    continue


chat_manager = ChatConnectionManager()
