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
    import threading
    import signal
    import sys
    
    # Flag to control server shutdown
    server_stop_event = threading.Event()
    
    def input_monitor():
        """Monitor for 'q' input to stop the server."""
        import sys
        import time
        
        print("💡 Server running. Type 'q' and press Enter to stop the server, or press Ctrl+C")
        
        # On Windows, use msvcrt for non-blocking input
        if sys.platform == "win32":
            try:
                import msvcrt
                while not server_stop_event.is_set():
                    try:
                        if msvcrt.kbhit():
                            key = msvcrt.getch()
                            if key == b'q' or key == b'Q':
                                print("\n🛑 Shutting down server...")
                                server_stop_event.set()
                                import os
                                os.kill(os.getpid(), signal.SIGINT)
                                break
                        time.sleep(0.1)
                    except (EOFError, KeyboardInterrupt):
                        break
            except ImportError:
                # Fallback if msvcrt not available
                pass
        else:
            # On Unix-like systems, use select for non-blocking input
            import select
            while not server_stop_event.is_set():
                try:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        user_input = sys.stdin.readline()
                        if user_input.strip().lower() == 'q':
                            print("\n🛑 Shutting down server...")
                            server_stop_event.set()
                            import os
                            os.kill(os.getpid(), signal.SIGINT)
                            break
                except (EOFError, KeyboardInterrupt):
                    break
    
    # Start input monitor in a separate thread
    input_thread = threading.Thread(target=input_monitor, daemon=True)
    input_thread.start()
    
    # Handle graceful shutdown on SIGINT (Ctrl+C)
    def signal_handler(sig, frame):
        if not server_stop_event.is_set():
            print("\n🛑 Shutting down server gracefully...")
            server_stop_event.set()
        # Allow Sanic to handle shutdown properly
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Suppress BrokenPipeError output on Windows
    import sys
    import io
    import contextlib
    
    original_stderr = sys.stderr
    
    def filtered_stderr_write(data):
        """Filter out BrokenPipeError messages on Windows."""
        if sys.platform == "win32":
            if "BrokenPipeError" in str(data) or "Die Pipe wird gerade geschlossen" in str(data):
                return  # Suppress the error message
        original_stderr.write(data)
    
    # Replace stderr temporarily
    class FilteredStderr:
        def write(self, data):
            filtered_stderr_write(data)
        def flush(self):
            original_stderr.flush()
    
    try:
        # Temporarily replace stderr to filter BrokenPipeError
        if sys.platform == "win32":
            sys.stderr = FilteredStderr()
        
        run_server(ip, int(port), False, password, ssl_cert, ssl_key, force_ssl)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
    except BrokenPipeError:
        # Windows-specific: Sanic's internal shutdown can cause this
        # It's safe to ignore as the server is already shutting down
        pass
    except SystemExit:
        # Expected when shutting down via signal
        pass
    finally:
        # Restore original stderr
        if sys.platform == "win32":
            sys.stderr = original_stderr
        server_stop_event.set()

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
        # Validate required arguments - check .env if CLI args are missing
        ip_address = args.ip_address or os.getenv('CLIENT_SERVER')
        if not ip_address:
            parser.error("ip_address is required (or set CLIENT_SERVER in .env)")
        
        username = args.username or os.getenv('CLIENT_USERNAME')
        if not username:
            parser.error("username is required (or set CLIENT_USERNAME in .env)")
        
        password = args.password or os.getenv('CLIENT_PASSWORD')
        token = args.token or os.getenv('CLIENT_TOKEN')
        if not password and not token:
            parser.error("password or --token is required (or set CLIENT_PASSWORD/CLIENT_TOKEN in .env)")
        
        # Use values from args or fallback to .env
        final_token = token if token else None
        use_ssl = getattr(args, 'ssl', use_ssl_default)
        final_password = password if password else None
        port = args.port or os.getenv('CLIENT_PORT', '1000')
        room_id = args.room if args.room else os.getenv('CLIENT_ROOM', 'default')
        renderer_mode = args.renderer if args.renderer else os.getenv('RENDERER_MODE')
        language = args.language if args.language else os.getenv('CMD_CHAT_LANGUAGE')
        await run_client(username, ip_address, int(port), final_password, final_token, use_ssl, room_id, renderer_mode, language)

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()
