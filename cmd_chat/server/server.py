import asyncio
import rsa
from cryptography.fernet import Fernet
from functools import partial
from sanic.worker.loader import AppLoader
from sanic.response import HTTPResponse
from sanic import Sanic, Request, response, Websocket
from cmd_chat.server.models import Message
from cmd_chat.server.auth import TokenManager
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
# Individual symmetric keys per client: {user_key: symmetric_key}
CLIENT_KEYS: dict[str, bytes] = {}
# Shared key for the default chat room (everyone can decrypt)
SHARED_ROOM_KEY = Fernet.generate_key()
# Authentication token manager
TOKEN_MANAGER = TokenManager()


def _check_auth(request: Request, expected_password: str | None, token_manager: TokenManager) -> tuple[bool, str | None]:
    """Validate authentication via token first, then password."""
    # Prefer token authentication when provided
    token = request.args.get("token") or request.form.get("token") if hasattr(request, "form") else None
    if token:
        token_obj = token_manager.validate_token(token, request.ip)
        if token_obj:
            return True, token_obj.username
    
    # Fallback to password for backwards compatibility
    if not expected_password:
        return True, None
    q = request.args.get("password")
    f = request.form.get("password") if hasattr(request, "form") else None
    is_valid = (q or f) == expected_password
    return is_valid, None

def _get_str_arg(request: Request, name: str) -> str | None:
    return request.form.get(name) or request.args.get(name)

def attach_endpoints(app: Sanic):
    @app.websocket("/talk")
    async def talk_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        is_valid, username = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
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
            await asyncio.sleep(0.01)

    @app.websocket("/update")
    async def update_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        is_valid, username = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
            await ws.close(code=4001, reason="unauthorized")
            return
        while True:
            payload = await _generate_update_payload(MESSAGES_MEMORY_DB, USERS)
            await ws.send(payload.encode())
            await asyncio.sleep(0.05)

    @app.route('/get_key', methods=['GET', 'POST'])
    async def get_key_view(request: Request) -> HTTPResponse:
        is_valid, auth_username = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
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

        username = _get_str_arg(request, "username") or "unknown"
        user_key = f"{request.ip}, {username}"
        
        # Usar chave compartilhada da sala para que todos possam descriptografar
        # Em uma implementação futura, isso seria por sala/canal
        encrypted_data = rsa.encrypt(SHARED_ROOM_KEY, public_key)
        
        if user_key not in USERS:
            USERS[user_key] = username
            CLIENT_KEYS[user_key] = SHARED_ROOM_KEY  # Rastrear para métricas

        return response.raw(encrypted_data)
    
    @app.route('/generate_token', methods=['POST'])
    async def generate_token_view(request: Request) -> HTTPResponse:
        """Endpoint responsible for issuing new access tokens."""
        admin_password = _get_str_arg(request, "admin_password")
        username = _get_str_arg(request, "username")
        ttl_str = _get_str_arg(request, "ttl")
        
        if not admin_password or not username:
            return response.json({"error": "admin_password and username required"}, status=400)
        
        ttl = int(ttl_str) if ttl_str else None
        token = TOKEN_MANAGER.generate_token(
            username=username,
            admin_password=admin_password,
            ttl=ttl,
            ip_address=request.ip
        )
        
        if not token:
            return response.json({"error": "unauthorized"}, status=401)
        
        return response.json({
            "token": token,
            "username": username,
            "expires_in": ttl or TOKEN_MANAGER.default_ttl
        })
    
    @app.route('/revoke_token', methods=['POST'])
    async def revoke_token_view(request: Request) -> HTTPResponse:
        """Endpoint that revokes previously generated tokens."""
        is_valid, _ = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
            return response.json({"error": "unauthorized"}, status=401)
        
        token = _get_str_arg(request, "token")
        if not token:
            return response.json({"error": "token required"}, status=400)
        
        revoked = TOKEN_MANAGER.revoke_token(token)
        return response.json({"revoked": revoked})
    
    @app.route('/health', methods=['GET'])
    async def health_check(request: Request) -> HTTPResponse:
        """Health check endpoint"""
        return response.json({
            "status": "healthy",
            "active_users": len(USERS),
            "messages_count": len(MESSAGES_MEMORY_DB),
            "active_tokens": TOKEN_MANAGER.get_active_tokens_count()
        })


def create_app(app_name: str, admin_password: str | None) -> Sanic:
    app = Sanic(app_name)
    app.ctx.ADMIN_PASSWORD = admin_password
    if admin_password:
        TOKEN_MANAGER.set_admin_password(admin_password)
    attach_endpoints(app)
    return app


def run_server(
    host: str,
    port: int,
    dev: bool = False,
    admin_password: str | None = None,
    ssl_cert: str | None = None,
    ssl_key: str | None = None
) -> None:
    """Inicia o servidor com suporte opcional para TLS/SSL"""
    loader = AppLoader(factory=partial(create_app, "CMD_SERVER", admin_password))
    app = loader.load()
    
    # Configurar SSL se certificados forem fornecidos
    ssl_context = None
    if ssl_cert and ssl_key:
        import ssl
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
    
    app.prepare(host=host, port=port, dev=dev, ssl=ssl_context)
    Sanic.serve(primary=app, app_loader=loader)
