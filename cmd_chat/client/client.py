import asyncio
import json
import base64
from typing import Optional

import srp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

srp.rfc5054_enable()

BANNER = """
[bold cyan]   ██████╗███╗   ███╗██████╗      ██████╗██╗  ██╗ █████╗ ████████╗[/]
[bold cyan]  ██╔════╝████╗ ████║██╔══██╗    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝[/]
[bold cyan]  ██║     ██╔████╔██║██║  ██║    ██║     ███████║███████║   ██║   [/]
[bold cyan]  ██║     ██║╚██╔╝██║██║  ██║    ██║     ██╔══██║██╔══██║   ██║   [/]
[bold cyan]  ╚██████╗██║ ╚═╝ ██║██████╔╝    ╚██████╗██║  ██║██║  ██║   ██║   [/]
[bold cyan]   ╚═════╝╚═╝     ╚═╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   [/]
[dim]                written by [bold magenta]SNEAKYBEAKY[/] with [bold red]♥[/][/]
"""


class Client:
    def __init__(
        self, server: str, port: int, username: str, password: Optional[str] = None
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = (password or "").encode()
        self.user_id: Optional[str] = None
        self.fernet: Optional[Fernet] = None
        self.room_fernet: Optional[Fernet] = None

        self.console = Console()
        self.messages: list[dict] = []
        self.users: list[dict] = []
        self.connected = False
        self.running = False

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    def success(self, message: str) -> None:
        self.console.print(f"[green]✓ {message}[/]")

    def error(self, message: str) -> None:
        self.console.print(f"[red]✗ {message}[/]")

    def info(self, message: str) -> None:
        self.console.print(f"[cyan]• {message}[/]")

    async def send_json(self, data: dict) -> None:
        line = json.dumps(data) + "\n"
        self.writer.write(line.encode())
        await self.writer.drain()

    async def recv_json(self) -> dict:
        line = await self.reader.readline()
        if not line:
            raise ConnectionError("Connection closed")
        return json.loads(line.decode())

    async def srp_authenticate(self) -> None:
        self.info("Starting SRP handshake...")

        usr = srp.User(b"chat", self.password, hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        await self.send_json(
            {
                "cmd": "srp_init",
                "username": self.username,
                "A": base64.b64encode(A).decode(),
            }
        )

        init_data = await self.recv_json()
        if "error" in init_data:
            raise ValueError(init_data["error"])

        self.user_id = init_data["user_id"]
        B = base64.b64decode(init_data["B"])
        salt = base64.b64decode(init_data["salt"])
        room_salt = base64.b64decode(init_data["room_salt"])

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        room_key = hkdf.derive(self.password)
        self.room_fernet = Fernet(base64.urlsafe_b64encode(room_key))

        M = usr.process_challenge(salt, B)
        if M is None:
            raise ValueError("SRP challenge processing failed")

        await self.send_json(
            {
                "cmd": "srp_verify",
                "user_id": self.user_id,
                "M": base64.b64encode(M).decode(),
            }
        )

        verify_data = await self.recv_json()
        if "error" in verify_data:
            raise ValueError(verify_data["error"])

        H_AMK = base64.b64decode(verify_data["H_AMK"])
        usr.verify_session(H_AMK)

        if not usr.authenticated():
            raise ValueError("Server authentication failed")

        session_key = base64.b64decode(verify_data["session_key"])
        self.fernet = Fernet(session_key)

        self.success(f"SRP authenticated (session: {self.user_id[:8]}...)")

    def decrypt_message(self, msg: dict) -> dict:
        if "text" in msg and msg["text"]:
            try:
                decrypted = self.room_fernet.decrypt(msg["text"].encode()).decode()
                msg["text"] = decrypted
            except Exception:
                msg["text"] = "[decrypt failed]"
        return msg

    def render_messages(self) -> None:
        self.console.clear()
        self.console.print(BANNER)
        self.console.print()

        users_online = ", ".join(u.get("username", "?") for u in self.users) or "none"
        self.console.print(f"[dim]Online: {users_online}[/]")
        self.console.print("─" * 60)

        display_messages = (
            self.messages[-15:] if len(self.messages) > 15 else self.messages
        )

        for msg in display_messages:
            username = msg.get("username", "unknown")
            text = msg.get("text", "")
            timestamp = str(msg.get("timestamp", ""))[:19].replace("T", " ")
            style = "green" if username == self.username else "cyan"
            self.console.print(f"[dim]{timestamp}[/] [{style}]{username}[/]: {text}")

        if not display_messages:
            self.console.print("[dim italic]No messages yet...[/]")

        self.console.print("─" * 60)
        self.console.print("[dim]Type message and press Enter. 'q' to quit.[/]")

    async def receive_loop(self) -> None:
        try:
            while self.running:
                line = await self.reader.readline()
                if not line:
                    break

                data = json.loads(line.decode())
                msg_type = data.get("type", "")

                if msg_type == "init":
                    self.messages = [
                        self.decrypt_message(m) for m in data.get("messages", [])
                    ]
                    self.users = data.get("users", [])
                    self.connected = True
                    self.render_messages()
                elif msg_type == "message":
                    msg_data = self.decrypt_message(data.get("data", {}))
                    self.messages.append(msg_data)
                    self.render_messages()
                elif msg_type == "user_joined":
                    self.users.append(
                        {
                            "user_id": data.get("user_id"),
                            "username": data.get("username"),
                        }
                    )
                    self.render_messages()
                elif msg_type == "user_left":
                    left_id = data.get("user_id")
                    self.users = [u for u in self.users if u.get("user_id") != left_id]
                    self.render_messages()
                elif msg_type == "cleared":
                    self.messages = []
                    self.render_messages()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.connected = False

    async def input_loop(self) -> None:
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                text = await loop.run_in_executor(None, input)
                if text.lower() in ("q", "quit", "exit"):
                    self.running = False
                    break
                if text.strip():
                    encrypted = self.room_fernet.encrypt(text.encode()).decode()
                    await self.send_json({"type": "message", "text": encrypted})
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
            except asyncio.CancelledError:
                break

    async def run_async(self) -> None:
        self.console.clear()
        self.console.print(BANNER)
        self.console.print()

        try:
            self.info(f"Connecting to {self.server}:{self.port}...")
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.server, self.port), timeout=10.0
            )
            self.success("Connected")

            await self.srp_authenticate()
            self.running = True

            receive_task = asyncio.create_task(self.receive_loop())
            input_task = asyncio.create_task(self.input_loop())

            done, pending = await asyncio.wait(
                [receive_task, input_task], return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self.console.print("\n[yellow]Disconnected[/]")

        except asyncio.TimeoutError:
            self.error(f"Connection timeout to {self.server}:{self.port}")
        except ConnectionRefusedError:
            self.error(f"Cannot connect to {self.server}:{self.port}")
        except ConnectionError as e:
            self.error(f"Connection error: {e}")
        except ValueError as e:
            self.error(f"Authentication failed: {e}")
        except Exception:
            import traceback

            self.error("Error occurred")
            traceback.print_exc()
        finally:
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass

    def run(self) -> None:
        asyncio.run(self.run_async())