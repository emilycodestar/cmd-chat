import asyncio
from contextlib import suppress
from cryptography.fernet import Fernet
from sanic import Sanic
from sanic_ext import Extend

from .managers import ConnectionManager
from .stores import MessageStore, UserSessionStore
from .srp_auth import SRPAuthManager

from .routes import register_routes


def create_app(password: str = "", name: str = "cmd-chat-server") -> Sanic:
    app = Sanic(name)
    Extend(app)

    app.ctx.message_store = MessageStore()
    app.ctx.session_store = UserSessionStore()
    app.ctx.connection_manager = ConnectionManager()
    app.ctx.srp_manager = SRPAuthManager(password)
    app.ctx.fernet_key = Fernet.generate_key()
    app.ctx.cleanup_task = None

    register_lifecycle(app)
    register_routes(app)

    return app


def register_lifecycle(app: Sanic) -> None:
    @app.before_server_start
    async def setup(app: Sanic):
        app.ctx.cleanup_task = asyncio.create_task(cleanup_stale_sessions(app))

    @app.after_server_stop
    async def teardown(app: Sanic):
        if app.ctx.cleanup_task:
            app.ctx.cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await app.ctx.cleanup_task


async def cleanup_stale_sessions(app: Sanic) -> None:
    while True:
        with suppress(asyncio.CancelledError):
            await asyncio.sleep(300)
            app.ctx.session_store.cleanup_stale()
