from dataclasses import asdict

import json
import base64

from sanic import Sanic, Request, response, Websocket
from sanic.response import HTTPResponse, json as json_response

from .models import Message, UserSession
from .helpers import (
    get_client_ip,
    send_state,
    utcnow,
)


async def srp_init(request: Request, app: Sanic) -> HTTPResponse:
    try:
        data = request.json or {}
        username = data.get("username", "unknown")
        client_public_b64 = data.get("A")

        if not client_public_b64:
            return response.json({"error": "Missing A"}, status=400)

        client_public = base64.b64decode(client_public_b64)

        if app.ctx.session_store.username_exists(username):
            return response.json({"error": "Username taken"}, status=409)

        user_id, B, salt = app.ctx.srp_manager.init_auth(username, client_public)

        return response.json(
            {
                "user_id": user_id,
                "B": base64.b64encode(B).decode(),
                "salt": base64.b64encode(salt).decode(),
            }
        )

    except Exception:
        return response.json({"error": "SRP init failed"}, status=500)


async def srp_verify(request: Request, app: Sanic) -> HTTPResponse:
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        client_proof_b64 = data.get("M")
        username = data.get("username", "unknown")

        if not user_id or not client_proof_b64:
            return response.json({"error": "Missing user_id or M"}, status=400)

        client_proof = base64.b64decode(client_proof_b64)

        H_AMK, session_key = app.ctx.srp_manager.verify_auth(user_id, client_proof)

        fernet_key = base64.urlsafe_b64encode(session_key[:32])

        session = UserSession(
            user_id=user_id,
            ip=get_client_ip(request),
            username=username,
            fernet_key=fernet_key,
        )
        app.ctx.session_store.add(session)


        return response.json(
            {
                "H_AMK": base64.b64encode(H_AMK).decode(),
                "session_key": base64.b64encode(fernet_key).decode(),
            }
        )

    except ValueError as e:
        return response.json({"error": str(e)}, status=401)
    except Exception:
        return response.json({"error": "SRP verify failed"}, status=500)


async def chat_ws(request: Request, ws: Websocket, app: Sanic) -> None:
    user_id = request.args.get("user_id")

    if not user_id:
        await ws.close(code=4002, reason="user_id required")
        return

    session = app.ctx.session_store.get(user_id)
    if not session:
        await ws.close(code=4002, reason="Invalid session")
        return

    manager = app.ctx.connection_manager
    await manager.connect(user_id, ws)

    try:
        await send_state(ws, app)

        async for data in ws:
            if data is None:
                break

            app.ctx.session_store.update_activity(user_id)

            message = Message(
                text=str(data),
                user_ip=session.ip,
                username=session.username,
            )
            app.ctx.message_store.add(message)

            await manager.broadcast(
                json.dumps(
                    {
                        "type": "message",
                        "data": asdict(message),
                    }
                )
            )

    except Exception:
        pass
    finally:
        await manager.disconnect(user_id)
        await manager.broadcast(
            json.dumps(
                {
                    "type": "user_left",
                    "user_id": user_id,
                }
            )
        )


async def health(request: Request, app: Sanic) -> HTTPResponse:
    return json_response(
        {
            "status": "ok",
            "messages": app.ctx.message_store.count(),
            "users": app.ctx.session_store.count(),
            "timestamp": utcnow().isoformat(),
        }
    )


async def clear_messages(request: Request, app: Sanic) -> HTTPResponse:
    user_id = request.args.get("user_id")
    if not user_id or not app.ctx.session_store.get(user_id):
        return response.json({"error": "Unauthorized"}, status=401)

    app.ctx.message_store.clear()
    return json_response({"status": "cleared"})
