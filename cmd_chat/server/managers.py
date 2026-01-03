import asyncio
from typing import Optional
from sanic import Websocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, Websocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: Websocket) -> None:
        async with self._lock:
            self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str) -> None:
        async with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]

    async def broadcast(self, message: str, exclude_user: Optional[str] = None) -> None:
        async with self._lock:
            disconnected = []
            for user_id, connection in list(self.active_connections.items()):
                if exclude_user and user_id == exclude_user:
                    continue
                try:
                    await connection.send(message)
                except Exception:
                    disconnected.append(user_id)

            for user_id in disconnected:
                if user_id in self.active_connections:
                    del self.active_connections[user_id]

    async def send_personal(self, user_id: str, message: str) -> bool:
        async with self._lock:
            if connection := self.active_connections.get(user_id):
                try:
                    await connection.send(message)
                    return True
                except Exception:
                    return False
        return False
