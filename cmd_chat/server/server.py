import asyncio
import json
import rsa
import time
from collections import defaultdict
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
    _generate_update_payload,
    _generate_full_update_payload
)

app = Sanic("app")
app.config.OAS = False

MESSAGES_MEMORY_DB: list[Message] = []
USERS: dict[str, str] = {}
# Individual symmetric keys per client: {user_key: symmetric_key}
CLIENT_KEYS: dict[str, bytes] = {}
# Room keys: {room_id: symmetric_key}
ROOM_KEYS: dict[str, bytes] = {}
# User room assignments: {user_key: room_id}
USER_ROOMS: dict[str, str] = {}
# User nicknames: {user_key: nickname}
USER_NICKNAMES: dict[str, str] = {}
# Authentication token manager
TOKEN_MANAGER = TokenManager()
# Rate limiting: {user_key: [timestamps]}
MESSAGE_RATE_LIMIT: dict[str, list[float]] = defaultdict(list)
# Rate limit configuration: max 10 messages per 60 seconds
MAX_MESSAGES_PER_WINDOW = 10
RATE_LIMIT_WINDOW = 60.0
# Heartbeat configuration
HEARTBEAT_INTERVAL = 30.0
HEARTBEAT_TIMEOUT = 60.0


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

def _check_rate_limit(user_key: str) -> bool:
    """Check if user is within rate limit. Returns True if allowed."""
    now = time.time()
    # Clean old timestamps outside the window
    MESSAGE_RATE_LIMIT[user_key] = [
        ts for ts in MESSAGE_RATE_LIMIT[user_key]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    # Check if limit exceeded
    if len(MESSAGE_RATE_LIMIT[user_key]) >= MAX_MESSAGES_PER_WINDOW:
        return False
    # Add current timestamp
    MESSAGE_RATE_LIMIT[user_key].append(now)
    return True

async def _handle_command(command: str, user_key: str, username: str, ws: Websocket) -> bool:
    """Handle chat commands. Returns True if command was handled."""
    parts = command.split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    # Get client language from request (default to English)
    # Note: Language is client-side, so we use English for server responses
    # Client will translate server responses using its own translation system
    
    if cmd == "/help":
        help_text = """
Available commands:
  /help          - Show this help message
  /nick <name>   - Change your nickname
  /rooms         - List all available rooms
  /room <id>     - Switch to a different room
  /clear         - Clear chat (client-side)
  /quit          - Disconnect from chat

💡 To send a message: Just type your message and press Enter (no / needed)
        """
        await ws.send(json.dumps({
            "type": "command",
            "command": "help",
            "message": help_text
        }))
        return True
    
    elif cmd == "/nick":
        if args:
            USER_NICKNAMES[user_key] = args.strip()
            USERS[user_key] = args.strip()
            await ws.send(json.dumps({
                "type": "command",
                "command": "nick",
                "message": f"Nickname changed to: {args.strip()}"
            }))
        else:
            await ws.send(json.dumps({
                "type": "command",
                "command": "error",
                "message": "Usage: /nick <name>"
            }))
        return True
    
    elif cmd == "/room":
        if args:
            room_id = args.strip()
            if room_id not in ROOM_KEYS:
                ROOM_KEYS[room_id] = Fernet.generate_key()
            USER_ROOMS[user_key] = room_id
            await ws.send(json.dumps({
                "type": "command",
                "command": "room",
                "message": f"Switched to room: {room_id}",
                "room_id": room_id
            }))
        else:
            await ws.send(json.dumps({
                "type": "command",
                "command": "error",
                "message": "Usage: /room <room_id>"
            }))
        return True
    
    elif cmd == "/rooms":
        # List all available rooms
        available_rooms = list(ROOM_KEYS.keys())
        if available_rooms:
            rooms_text = ", ".join(available_rooms)
            await ws.send(json.dumps({
                "type": "command",
                "command": "rooms",
                "message": f"Available rooms: {rooms_text}",
                "rooms": available_rooms
            }))
        else:
            await ws.send(json.dumps({
                "type": "command",
                "command": "rooms",
                "message": "No other rooms available. Use /room <id> to create a new room.",
                "rooms": []
            }))
        return True
    
    elif cmd == "/clear":
        await ws.send(json.dumps({
            "type": "command",
            "command": "clear"
        }))
        return True
    
    elif cmd == "/quit":
        await ws.send(json.dumps({
            "type": "command",
            "command": "quit"
        }))
        await ws.close()
        return True
    
    return False

def attach_endpoints(app: Sanic):
    @app.websocket("/talk")
    async def talk_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        is_valid, username = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
            await ws.close(code=4001, reason="unauthorized")
            return
        
        username = username or _get_str_arg(request, "username") or "unknown"
        user_key = f"{request.ip}, {username}"
        last_heartbeat = time.time()
        
        async def send_heartbeat():
            """Send periodic heartbeat to keep connection alive."""
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                try:
                    await ws.send(json.dumps({"type": "ping", "timestamp": time.time()}))
                except Exception:
                    break
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        try:
            while True:
                try:
                    # Check for timeout
                    if time.time() - last_heartbeat > HEARTBEAT_TIMEOUT:
                        await ws.close(code=4000, reason="timeout")
                        break
                    
                    serialized_message: dict = await _get_bytes_and_serialize(ws)
                    
                    # Handle heartbeat pong
                    if serialized_message.get("type") == "pong":
                        last_heartbeat = time.time()
                        continue
                    
                    await _check_ws_for_close_status(serialized_message, ws)
                    
                    # Handle commands
                    text = serialized_message.get("text")
                    if text and text.startswith("/"):
                        command_result = await _handle_command(text, user_key, username, ws)
                        if command_result:
                            continue
                    
                    if text is None:
                        continue
                    
                    # Rate limiting check
                    if not _check_rate_limit(user_key):
                        await ws.send(json.dumps({
                            "status": "error",
                            "message": "Rate limit exceeded. Please slow down."
                        }))
                        continue
                    
                    # Get user's room
                    room_id = USER_ROOMS.get(user_key, "default")
                    new_message = await _generate_new_message(text, username, room_id)
                    MESSAGES_MEMORY_DB.append(new_message)
                    await ws.send(json.dumps({"status": "ok"}))
                    last_heartbeat = time.time()
                    await asyncio.sleep(0.01)
                except asyncio.CancelledError:
                    # Task was cancelled, break gracefully
                    break
                except Exception as e:
                    # Clean error handling - don't expose stack traces
                    await ws.send(json.dumps({
                        "status": "error",
                        "message": "An error occurred processing your message"
                    }))
                    break
        finally:
            # Cancel heartbeat task gracefully
            if not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await asyncio.wait_for(heartbeat_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

    @app.websocket("/update")
    async def update_ws_view(request: Request, ws: Websocket) -> HTTPResponse:
        is_valid, username = _check_auth(request, app.ctx.ADMIN_PASSWORD, TOKEN_MANAGER)
        if not is_valid:
            await ws.close(code=4001, reason="unauthorized")
            return
        
        last_heartbeat = time.time()
        
        async def send_heartbeat():
            """Send periodic heartbeat to keep connection alive."""
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                try:
                    await ws.send(json.dumps({"type": "ping", "timestamp": time.time()}))
                except Exception:
                    break
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        try:
            while True:
                try:
                    # Check for timeout
                    if time.time() - last_heartbeat > HEARTBEAT_TIMEOUT:
                        await ws.close(code=4000, reason="timeout")
                        break
                    
                    # Try to receive heartbeat pong (non-blocking check)
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.1)
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        msg = json.loads(raw)
                        if msg.get("type") == "pong":
                            last_heartbeat = time.time()
                            continue
                    except asyncio.TimeoutError:
                        pass
                    except Exception:
                        pass
                    
                    # Get room_id from request or use default
                    room_id = _get_str_arg(request, "room_id") or "default"
                    last_sequence = int(_get_str_arg(request, "last_sequence") or 0)
                    
                    # Use delta updates if last_sequence provided, otherwise full update
                    if last_sequence > 0:
                        payload = await _generate_update_payload(MESSAGES_MEMORY_DB, USERS, room_id, last_sequence, USER_ROOMS)
                    else:
                        payload = await _generate_full_update_payload(MESSAGES_MEMORY_DB, USERS, room_id, USER_ROOMS)
                    
                    await ws.send(payload.encode())
                    await asyncio.sleep(0.05)
                except Exception:
                    # Clean error handling
                    break
        finally:
            # Cancel heartbeat task gracefully
            if not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await asyncio.wait_for(heartbeat_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

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
        except Exception:
            # Clean error handling - don't expose exception details
            return response.text("invalid public key format", status=400)

        username = _get_str_arg(request, "username") or "unknown"
        room_id = _get_str_arg(request, "room_id") or "default"
        user_key = f"{request.ip}, {username}"
        
        # Generate per-client symmetric key
        client_key = Fernet.generate_key()
        CLIENT_KEYS[user_key] = client_key
        
        # Ensure room exists and has a key
        if room_id not in ROOM_KEYS:
            ROOM_KEYS[room_id] = Fernet.generate_key()
        
        # Assign user to room
        USER_ROOMS[user_key] = room_id
        USER_NICKNAMES[user_key] = username
        
        if user_key not in USERS:
            USERS[user_key] = username
        
        # Encrypt the client key with RSA
        encrypted_data = rsa.encrypt(client_key, public_key)

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
    import sys
    
    app = Sanic(app_name)
    app.ctx.ADMIN_PASSWORD = admin_password
    if admin_password:
        TOKEN_MANAGER.set_admin_password(admin_password)
    attach_endpoints(app)
    
    # Set up exception handler for Windows BrokenPipeError during shutdown
    if sys.platform == "win32":
        @app.before_server_start
        async def setup_exception_handler(app, loop):
            def exception_handler(loop, context):
                exception = context.get('exception')
                # Ignore BrokenPipeError and KeyboardInterrupt during shutdown (known Sanic issue on Windows)
                if isinstance(exception, (BrokenPipeError, KeyboardInterrupt)):
                    return
                # Use default handler for other exceptions
                if hasattr(loop, 'default_exception_handler'):
                    loop.default_exception_handler(context)
                else:
                    loop.call_exception_handler(context)
            
            loop.set_exception_handler(exception_handler)
    
    return app


def run_server(
    host: str,
    port: int,
    dev: bool = False,
    admin_password: str | None = None,
    ssl_cert: str | None = None,
    ssl_key: str | None = None,
    force_ssl: bool = False
) -> None:
    """Start server with optional TLS/SSL support. If force_ssl is True, require SSL certificates."""
    import sys
    import io
    import contextlib
    
    loader = AppLoader(factory=partial(create_app, "CMD_SERVER", admin_password))
    app = loader.load()
    
    # Force SSL in production if requested
    if force_ssl and (not ssl_cert or not ssl_key):
        raise ValueError("SSL certificates are required when force_ssl=True. Provide --ssl-cert and --ssl-key.")
    
    # Configure SSL if certificates are provided
    ssl_context = None
    if ssl_cert and ssl_key:
        import ssl
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
    
    app.prepare(host=host, port=port, dev=dev, ssl=ssl_context)
    
    # Display connection information
    import socket
    protocol = "https" if ssl_context else "http"
    ws_protocol = "wss" if ssl_context else "ws"
    
    # Get local IP address for connection
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = host if host != "0.0.0.0" else "localhost"
    
    print("\n" + "="*60)
    print("  🚀 CMD CHAT SERVER STARTED")
    print("="*60)
    print(f"  Server Address: {local_ip}:{port}")
    print(f"  Protocol: {protocol}:// (WebSocket: {ws_protocol}://)")
    print(f"  Connect with: python cmd_chat.py connect {local_ip} {port} <username> <password>")
    print("="*60 + "\n")
    
    # Suppress BrokenPipeError on Windows during shutdown
    # This is a known issue with Sanic's multiprocessing on Windows
    try:
        Sanic.serve(primary=app, app_loader=loader)
    except (BrokenPipeError, SystemExit, KeyboardInterrupt):
        # Expected during shutdown - these are normal
        pass
    except Exception as e:
        # Only re-raise if it's not a shutdown-related error on Windows
        if sys.platform == "win32" and isinstance(e, BrokenPipeError):
            pass  # Ignore BrokenPipeError on Windows
        else:
            raise
