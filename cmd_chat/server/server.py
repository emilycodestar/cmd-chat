import asyncio
import rsa
from cryptography.fernet import Fernet
from functools import partial
from sanic.worker.loader import AppLoader
from sanic.response import HTTPResponse
from sanic import Sanic, Request, response, Websocket
from cmd_chat.server.models import Message
from cmd_chat.server.services import (
    _get_bytes_and_serialize,
    _check_ws_for_close_status,
    _generate_new_message,
    _generate_update_payload
)

app = Sanic("app")
app.config.OAS = False

MESSAGES_MEMORY_DB: list[Message] = []
USERS: dict[str, str] = {}
PUBLIC_KEY = Fernet.generate_key()


def _check_password(request: Request, expected: str | None) -> bool:
    if not expected:
        return True
    q = request.args.get("password")
    f = request.form.get("password") if hasattr(request, "form") else None
    return (q or f) == expected

def _get_str_arg(request: Request, name: str) -> str | None:
    return request.form.get(name) or request.args.get(name)

def attach_endpoints(app: Sanic):
    @app.websocket("/talk")
    async def talk_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        if not _check_password(request, app.ctx.ADMIN_PASSWORD):
            await ws.close(code=4001, reason="unauthorized")
            return
        while True:
            serialized_message: dict = await _get_bytes_and_serialize(ws)
            await _check_ws_for_close_status(serialized_message, ws)
            text = serialized_message.get("text")
            if text is None:
                continue
            new_message = await _generate_new_message(text)
            MESSAGES_MEMORY_DB.append(new_message)
            await ws.send(str({"status": "ok"}))
            await asyncio.sleep(0.2)

    @app.websocket("/update")
    async def update_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        if not _check_password(request, app.ctx.ADMIN_PASSWORD):
            await ws.close(code=4001, reason="unauthorized")
            return
        while True:
            payload = await _generate_update_payload(MESSAGES_MEMORY_DB, USERS)
            await ws.send(payload.encode())
            await asyncio.sleep(0.2)

    @app.route('/get_key', methods=['GET', 'POST'])
    async def get_key_view(request: Request) -> HTTPResponse:
        if not _check_password(request, app.ctx.ADMIN_PASSWORD):
            return response.text("unauthorized", status=401)

        pubkey_bytes: bytes | None = None

        if "pubkey" in request.files and request.files.get("pubkey"):
            f = request.files.get("pubkey")
            if isinstance(f, list):
                f = f[0]
            pubkey_bytes = f.body

        if pubkey_bytes is None:
            raw = request.form.get("pubkey")
            if raw:
                pubkey_bytes = raw if isinstance(raw, bytes) else str(raw).encode()

        if pubkey_bytes is None:
            raw = request.args.get("pubkey")
            if raw:
                pubkey_bytes = raw.encode()

        if not pubkey_bytes:
            return response.text("bad request: pubkey is required", status=400)

        try:
            public_key = rsa.PublicKey.load_pkcs1(pubkey_bytes)
        except Exception as e:
            return response.text(f"bad pubkey: {e}", status=400)

        encrypted_data = rsa.encrypt(PUBLIC_KEY, public_key)

        username = _get_str_arg(request, "username") or "unknown"
        user_key = f"{request.ip}, {username}"
        if user_key not in USERS:
            USERS[user_key] = PUBLIC_KEY

        return response.raw(encrypted_data)


def create_app(app_name: str, admin_password: str | None) -> Sanic:
    app = Sanic(app_name)
    app.ctx.ADMIN_PASSWORD = admin_password
    attach_endpoints(app)
    return app


def run_server(host: str, port: int, dev: bool = False, admin_password: str | None = None) -> None:
    loader = AppLoader(factory=partial(create_app, "CMD_SERVER", admin_password))
    app = loader.load()
    app.prepare(host=host, port=port, dev=dev)
    Sanic.serve(primary=app, app_loader=loader)
