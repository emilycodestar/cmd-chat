import asyncio
from typing import Optional
from asyncio import StreamWriter


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, StreamWriter] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, writer: StreamWriter) -> None:
        async with self._lock:
            self.active_connections[user_id] = writer

    async def disconnect(self, user_id: str) -> None:
        async with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]

    async def broadcast(self, message: str, exclude_user: Optional[str] = None) -> None:
        data = (message + "\n").encode()
        async with self._lock:
            disconnected = []
            for user_id, writer in list(self.active_connections.items()):
                if exclude_user and user_id == exclude_user:
                    continue
                try:
                    writer.write(data)
                    await writer.drain()
                except Exception:
                    disconnected.append(user_id)

            for user_id in disconnected:
                self.active_connections.pop(user_id, None)

    async def send_personal(self, user_id: str, message: str) -> bool:
        data = (message + "\n").encode()
        async with self._lock:
            if writer := self.active_connections.get(user_id):
                try:
                    writer.write(data)
                    await writer.drain()
                    return True
                except Exception:
                    return False
        return False
