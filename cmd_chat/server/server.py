import asyncio
import json
import base64
import os
from dataclasses import asdict
from contextlib import suppress
from typing import Optional
from asyncio import StreamReader, StreamWriter

from .models import Message, UserSession
from .stores import MessageStore, UserSessionStore
from .managers import ConnectionManager
from .srp_auth import SRPAuthManager

b64e = lambda x: base64.b64encode(x).decode()
b64d = base64.b64decode
b64u = base64.urlsafe_b64encode


class ChatServer:
    __slots__ = (
        "message_store",
        "session_store",
        "connection_manager",
        "srp_manager",
        "room_salt",
        "_cleanup_task",
    )

    def __init__(self, password: str):
        self.message_store = MessageStore()
        self.session_store = UserSessionStore()
        self.connection_manager = ConnectionManager()
        self.srp_manager = SRPAuthManager(password)
        self.room_salt = os.urandom(0x10)
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self, host: str, port: int):
        server = await asyncio.start_server(self._handle_client, host, port)
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        addr = server.sockets[0].getsockname()
        print(f"[*] Server running on {addr[0]}:{addr[1]}")
        async with server:
            await server.serve_forever()

    async def stop(self):
        self._cleanup_task and (
            self._cleanup_task.cancel(),
            await asyncio.gather(self._cleanup_task, return_exceptions=1),
        )

    async def _cleanup_loop(self):
        while 1:
            await asyncio.sleep(0x12C)
            self.session_store.cleanup_stale()

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
        addr = writer.get_extra_info("peername")
        client_ip = addr[0] if addr else "unknown"
        user_id = None

        try:
            session = await self._handle_auth(reader, writer, client_ip)
            if not session:
                return
            user_id = session.user_id
            await self._handle_chat(reader, writer, session)

        except (asyncio.IncompleteReadError, ConnectionResetError, OSError):
            pass
        except Exception as e:
            print(f"[!] Client error: {e}")
        finally:
            user_id and (
                await self.connection_manager.disconnect(user_id),
                self.session_store.remove(user_id),
                await self.connection_manager.broadcast(
                    json.dumps({"type": "user_left", "user_id": user_id})
                ),
            )
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

    async def _handle_auth(
        self, reader: StreamReader, writer: StreamWriter, client_ip: str
    ) -> Optional[UserSession]:

        readline = lambda: asyncio.wait_for(reader.readline(), 0x1E)

        line = await readline()
        if not line:
            return None

        try:
            data = json.loads(line.decode())
        except json.JSONDecodeError:
            return await self._send_error(writer, "Invalid JSON")

        if data.get("cmd") != "srp_init":
            return await self._send_error(writer, "Expected srp_init")

        username = data.get("username", "unknown")
        client_public_b64 = data.get("A")

        if not client_public_b64:
            return await self._send_error(writer, "Missing A")

        if self.session_store.username_exists(username):
            return await self._send_error(writer, "Username taken")

        try:
            client_public = b64d(client_public_b64)
            user_id, B, salt = self.srp_manager.init_auth(username, client_public)
        except Exception:
            return await self._send_error(writer, "SRP init failed")

        await self._send_json(
            writer,
            {
                "user_id": user_id,
                "B": b64e(B),
                "salt": b64e(salt),
                "room_salt": b64e(self.room_salt),
            },
        )

        line = await readline()
        if not line:
            return None

        try:
            data = json.loads(line.decode())
        except json.JSONDecodeError:
            return await self._send_error(writer, "Invalid JSON")

        if data.get("cmd") != "srp_verify":
            return await self._send_error(writer, "Expected srp_verify")

        recv_user_id = data.get("user_id")
        client_proof_b64 = data.get("M")

        if recv_user_id != user_id or not client_proof_b64:
            return await self._send_error(writer, "Invalid verify request")

        try:
            client_proof = b64d(client_proof_b64)
            H_AMK, session_key = self.srp_manager.verify_auth(user_id, client_proof)
        except ValueError as e:
            return await self._send_error(writer, str(e))

        fernet_key = b64u(session_key[:0x20])

        session = UserSession(
            user_id=user_id,
            ip=client_ip,
            username=username,
            fernet_key=fernet_key,
        )
        self.session_store.add(session)

        await self._send_json(
            writer,
            {
                "H_AMK": b64e(H_AMK),
                "session_key": base64.b64encode(fernet_key).decode(),
            },
        )

        return session

    async def _handle_chat(
        self, reader: StreamReader, writer: StreamWriter, session: UserSession
    ):
        user_id = session.user_id

        await self.connection_manager.connect(user_id, writer)

        messages = self.message_store.get_all()
        users = self.session_store.get_all()

        await self._send_json(
            writer,
            {
                "type": "init",
                "messages": [asdict(m) for m in messages],
                "users": [
                    {"user_id": u.user_id, "username": u.username} for u in users
                ],
            },
        )

        await self.connection_manager.broadcast(
            json.dumps(
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "username": session.username,
                }
            ),
            exclude_user=user_id,
        )

        while 1:
            line = await reader.readline()
            if not line:
                break

            self.session_store.update_activity(user_id)

            try:
                data = json.loads(line.decode())
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            match msg_type:
                case "message":
                    text = data.get("text", "")
                    message = Message(
                        text=text,
                        user_ip=session.ip,
                        username=session.username,
                    )
                    self.message_store.add(message)
                    await self.connection_manager.broadcast(
                        json.dumps({"type": "message", "data": asdict(message)})
                    )

                case "clear":
                    self.message_store.clear()
                    await self.connection_manager.broadcast(
                        json.dumps({"type": "cleared"})
                    )

    async def _send_json(self, writer: StreamWriter, data: dict):
        writer.write((json.dumps(data) + "\n").encode())
        await writer.drain()

    async def _send_error(self, writer: StreamWriter, error: str) -> None:
        await self._send_json(writer, {"error": error})
        return None


def run_server(
    host: str = "0.0.0.0",
    port: int = 0x1F40,
    password: Optional[str] = None,
):
    server = ChatServer(password or "")
    try:
        asyncio.run(server.start(host, port))
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
