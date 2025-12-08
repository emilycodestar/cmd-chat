import asyncio
import argparse
from cmd_chat.server.server import run_server
from cmd_chat.client.client import Client

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
    renderer_mode: str | None = None
) -> None:
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
    serve_p.add_argument('ip_address')
    serve_p.add_argument('port')
    serve_p.add_argument('--password', '-p', required=True, help='Admin password required for clients')
    serve_p.add_argument('--ssl-cert', help='Path to SSL certificate file for HTTPS/WSS')
    serve_p.add_argument('--ssl-key', help='Path to SSL key file for HTTPS/WSS')
    serve_p.add_argument('--force-ssl', action='store_true', help='Force SSL/TLS (require certificates)')

    connect_p = subparsers.add_parser('connect', help='Connect to server')
    connect_p.add_argument('ip_address')
    connect_p.add_argument('port')
    connect_p.add_argument('username')
    connect_p.add_argument('password', nargs='?', help='Password to auth on server (optional if using token)')
    connect_p.add_argument('--token', '-t', help='Authentication token (alternative to password)')
    connect_p.add_argument('--ssl', action='store_true', help='Use SSL/TLS (wss:// instead of ws://)')
    connect_p.add_argument('--room', '-r', default='default', help='Room ID to join (default: default)')
    connect_p.add_argument('--renderer', choices=['rich', 'minimal', 'json'], help='Renderer mode (rich, minimal, json)')

    args = parser.parse_args()

    if args.command == 'serve':
        ssl_cert = getattr(args, 'ssl_cert', None)
        ssl_key = getattr(args, 'ssl_key', None)
        force_ssl = getattr(args, 'force_ssl', False)
        run_http_server(args.ip_address, args.port, args.password, ssl_cert, ssl_key, force_ssl)
    elif args.command == 'connect':
        token = getattr(args, 'token', None)
        use_ssl = getattr(args, 'ssl', False)
        password = args.password if hasattr(args, 'password') else None
        room_id = getattr(args, 'room', 'default')
        renderer_mode = getattr(args, 'renderer', None)
        await run_client(args.username, args.ip_address, int(args.port), password, token, use_ssl, room_id, renderer_mode)

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()
