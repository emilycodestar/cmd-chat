import asyncio
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from cmd_chat.server.server import run_server
from cmd_chat.client.client import Client

# Load .env file if it exists
env_path = Path.cwd() / '.env'
if env_path.exists():
    load_dotenv(env_path)

def run_http_server(
    ip: str,
    port: int,
    password: str | None,
    ssl_cert: str | None = None,
    ssl_key: str | None = None,
    force_ssl: bool = False
) -> None:
    run_server(ip, int(port), False, password, ssl_cert, ssl_key, force_ssl)

async def run_client(
    username: str,
    server: str,
    port: int,
    password: str | None,
    token: str | None = None,
    use_ssl: bool = False,
    room_id: str = "default",
    renderer_mode: str | None = None,
    language: str | None = None
) -> None:
    # Set language environment variable if provided
    if language:
        import os
        os.environ["CMD_CHAT_LANGUAGE"] = language
    
    Client(
        server=server,
        port=port,
        username=username,
        password=password,
        token=token,
        use_ssl=use_ssl,
        room_id=room_id,
        renderer_mode=renderer_mode
    ).run()

async def run() -> None:
    parser = argparse.ArgumentParser(description='Command-line chat application')
    subparsers = parser.add_subparsers(dest='command', required=True)

    serve_p = subparsers.add_parser('serve', help='Run server')
    serve_p.add_argument('ip_address', nargs='?', default=os.getenv('SERVER_HOST', '0.0.0.0'), help='Server IP address (default: from .env or 0.0.0.0)')
    serve_p.add_argument('port', nargs='?', default=os.getenv('SERVER_PORT', '1000'), help='Server port (default: from .env or 1000)')
    serve_p.add_argument('--password', '-p', default=os.getenv('ADMIN_PASSWORD'), help='Admin password required for clients (can be set in .env)')
    serve_p.add_argument('--ssl-cert', default=os.getenv('SSL_CERT_PATH'), help='Path to SSL certificate file for HTTPS/WSS (can be set in .env)')
    serve_p.add_argument('--ssl-key', default=os.getenv('SSL_KEY_PATH'), help='Path to SSL key file for HTTPS/WSS (can be set in .env)')
    force_ssl_default = os.getenv('FORCE_SSL', 'false').lower() == 'true'
    serve_p.add_argument('--force-ssl', action='store_true', help='Force SSL/TLS (require certificates, can be set in .env via FORCE_SSL=true)')

    connect_p = subparsers.add_parser('connect', help='Connect to server')
    connect_p.add_argument('ip_address', nargs='?', default=os.getenv('CLIENT_SERVER'), help='Server IP address (default: from .env)')
    connect_p.add_argument('port', nargs='?', default=os.getenv('CLIENT_PORT', '1000'), help='Server port (default: from .env or 1000)')
    connect_p.add_argument('username', nargs='?', default=os.getenv('CLIENT_USERNAME'), help='Username (default: from .env)')
    connect_p.add_argument('password', nargs='?', default=os.getenv('CLIENT_PASSWORD'), help='Password to auth on server (optional if using token, can be set in .env)')
    connect_p.add_argument('--token', '-t', default=os.getenv('CLIENT_TOKEN'), help='Authentication token (alternative to password, can be set in .env)')
    use_ssl_default = os.getenv('CLIENT_USE_SSL', 'false').lower() == 'true'
    connect_p.add_argument('--ssl', action='store_true', help='Use SSL/TLS (wss:// instead of ws://, can be set in .env via CLIENT_USE_SSL=true)')
    connect_p.add_argument('--room', '-r', default=os.getenv('CLIENT_ROOM', 'default'), help='Room ID to join (default: from .env or default)')
    connect_p.add_argument('--renderer', choices=['rich', 'minimal', 'json'], default=os.getenv('RENDERER_MODE'), help='Renderer mode (rich, minimal, json, can be set in .env)')
    connect_p.add_argument('--language', '-l', choices=['en', 'fr', 'es', 'zh', 'ja', 'de', 'ru', 'et', 'pt', 'ko', 'ca', 'eu', 'gl'], default=os.getenv('CMD_CHAT_LANGUAGE'), help='Language code (can be set in .env)')

    args = parser.parse_args()

    if args.command == 'serve':
        # Validate required arguments
        if not args.password:
            parser.error("--password is required (or set ADMIN_PASSWORD in .env)")
        
        ssl_cert = args.ssl_cert if args.ssl_cert else None
        ssl_key = args.ssl_key if args.ssl_key else None
        force_ssl = getattr(args, 'force_ssl', force_ssl_default)
        run_http_server(args.ip_address, args.port, args.password, ssl_cert, ssl_key, force_ssl)
    elif args.command == 'connect':
        # Validate required arguments
        if not args.ip_address:
            parser.error("ip_address is required (or set CLIENT_SERVER in .env)")
        if not args.username:
            parser.error("username is required (or set CLIENT_USERNAME in .env)")
        if not args.password and not args.token:
            parser.error("password or --token is required (or set CLIENT_PASSWORD/CLIENT_TOKEN in .env)")
        
        token = args.token if args.token else None
        use_ssl = getattr(args, 'ssl', use_ssl_default)
        password = args.password if args.password else None
        room_id = args.room if args.room else 'default'
        renderer_mode = args.renderer if args.renderer else None
        language = args.language if args.language else None
        await run_client(args.username, args.ip_address, int(args.port), password, token, use_ssl, room_id, renderer_mode, language)

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()
