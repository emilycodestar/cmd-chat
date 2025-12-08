import json
import time
import threading
import os
from pathlib import Path
from websocket import create_connection, WebSocketConnectionClosedException

from cmd_chat.client.core.crypto import RSAService
from cmd_chat.client.core.default_renderer import DefaultClientRenderer
from cmd_chat.client.core.rich_renderer import RichClientRenderer
from cmd_chat.client.core.json_renderer import JsonClientRenderer

from cmd_chat.client.config import (
    RENDER_TIME, 
    MESSAGES_TO_SHOW, 
    ENABLE_LOCAL_HISTORY,
    RENDERER_MODE,
    LANGUAGE
)
from cmd_chat.client.i18n.translations import get_translator, t


class Client(RSAService):
    """Enhanced client with support for commands, rooms, renderers, and local history."""

    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str | None = None,
        token: str | None = None,
        use_ssl: bool = False,
        room_id: str = "default",
        renderer_mode: str | None = None
    ):
        super().__init__()
        self.server = server
        self.port = port
        self.username = username
        self.password = password or ""
        self.token = token
        self.use_ssl = use_ssl
        self.room_id = room_id
        self.last_sequence = 0
        self.reconnecting = False
        self.welcome_shown = False  # Track if welcome message has been shown
        self.welcome_cleared = False  # Track if user explicitly cleared welcome
        
        # Select renderer based on mode
        renderer = renderer_mode or RENDERER_MODE
        if renderer == "json":
            self.renderer = JsonClientRenderer()
        elif renderer == "minimal":
            self.renderer = DefaultClientRenderer()
        else:
            self.renderer = RichClientRenderer()
        
        # Set username for renderer
        self.renderer.username = self.username
        # Pass decrypt method to renderer
        self.renderer._decrypt = self._decrypt
        
        # Local history
        self.local_history_enabled = ENABLE_LOCAL_HISTORY
        self.history_file = Path.home() / ".cmd_chat_history.json" if self.local_history_enabled else None
        
        # Protocol setup
        http_proto = "https" if use_ssl else "http"
        ws_proto = "wss" if use_ssl else "ws"
        
        self.base_url = f"{http_proto}://{self.server}:{self.port}"
        self.ws_url = f"{ws_proto}://{self.server}:{self.port}"
        self.close_response = json.dumps({
            "action": "close",
            "username": self.username
        })
        self.__stop_threads = False
        self.last_heartbeat = time.time()
        
        # Initialize translation manager
        self.translator = get_translator()
        if language := os.getenv("CMD_CHAT_LANGUAGE"):
            self.translator.set_language(language)

    def _ws_full(self, path: str, room_id: str | None = None) -> str:
        """Build full WebSocket URL with authentication and room."""
        params = []
        if self.token:
            params.append(f"token={self.token}")
        elif self.password:
            params.append(f"password={self.password}")
        if room_id:
            params.append(f"room_id={room_id}")
        elif self.room_id:
            params.append(f"room_id={self.room_id}")
        if self.last_sequence > 0:
            params.append(f"last_sequence={self.last_sequence}")
        
        query = "&".join(params)
        return f"{self.ws_url}{path}?{query}" if query else f"{self.ws_url}{path}"

    def _connect_ws(self, path: str, retries: int = 5, backoff: float = 0.5, show_status: bool = True):
        """Connect to WebSocket with reconnection status indicator."""
        last_exc: Exception = ConnectionError("Failed to connect")
        for attempt in range(retries):
            if attempt > 0 and show_status and not self.reconnecting:
                self.reconnecting = True
                if RENDERER_MODE != "json":
                    print(t("reconnecting"), end="\r")
            
            try:
                ws = create_connection(self._ws_full(path, self.room_id))
                if self.reconnecting and RENDERER_MODE != "json":
                    print(t("reconnected") + " " * 20)
                    self.reconnecting = False
                return ws
            except Exception as exc:
                last_exc = exc
                time.sleep(backoff * (2 ** attempt))
        
        if self.reconnecting:
            self.reconnecting = False
        print(t("connection_failed").format(path=path, error=str(last_exc)))
        raise last_exc

    def _handle_command(self, command: str, ws) -> bool:
        """Handle client-side commands. Returns True if command was handled."""
        if command.startswith("/"):
            ws.send(json.dumps({
                "text": command,
                "username": self.username
            }))
            return True
        return False

    def _save_to_history(self, message_data: dict):
        """Save message to local encrypted history."""
        if not self.local_history_enabled or not self.history_file:
            return
        
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            
            history.append({
                "timestamp": time.time(),
                "room_id": self.room_id,
                "data": message_data
            })
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f)
        except Exception:
            pass  # Silently fail history saving

    def send_info(self):
        ws = self._connect_ws("/talk")
        try:
            # Show welcome message on first connection
            if RENDERER_MODE != "json" and not self.welcome_shown:
                print(f"\n{t('welcome_message')}")
                print(t("current_room").format(room_id=self.room_id))
                print(t("welcome_instructions"))
                print()  # Empty line for spacing
                self.welcome_shown = True
            
            while not self.__stop_threads:
                try:
                    user_input = input(t("input_prompt") if RENDERER_MODE != "json" else "")
                    
                    if user_input.strip() == "":
                        continue
                    
                    if user_input == "q" or user_input == "/quit":
                        self.__stop_threads = True
                        try:
                            if ws:
                                ws.send(self.close_response)
                                ws.close()
                        except Exception:
                            pass
                        break
                    
                    # Handle commands
                    if user_input.startswith("/"):
                        self._handle_command(user_input, ws)
                        # Check for command response
                        try:
                            ws.settimeout(2.0)  # Increased timeout for command responses
                            raw = ws.recv()
                            if isinstance(raw, bytes):
                                raw = raw.decode("utf-8")
                            msg = json.loads(raw)
                            
                            if msg.get("type") == "command":
                                cmd = msg.get("command")
                                
                                # Handle quit command first
                                if cmd == "quit":
                                    if RENDERER_MODE != "json":
                                        print(t("command_quit"))
                                    self.__stop_threads = True
                                    break
                                
                                # Handle room switch
                                elif cmd == "room":
                                    new_room_id = msg.get("room_id", self.room_id)
                                    if new_room_id != self.room_id:
                                        # Room changed - need to get new room key
                                        self.room_id = new_room_id
                                        try:
                                            # Request new key for the new room
                                            self._request_key(
                                                url=f"{self.base_url}/get_key?room_id={self.room_id}",
                                                username=self.username,
                                                password=self.password,
                                                token=self.token,
                                                room_id=self.room_id
                                            )
                                        except Exception as e:
                                            if RENDERER_MODE != "json":
                                                print(f"Warning: Failed to get new room key: {e}")
                                            # Continue anyway - old key might still work for some messages
                                
                                # Handle clear command
                                elif cmd == "clear" and RENDERER_MODE != "json":
                                    self.renderer.clear_console()
                                    self.welcome_cleared = True
                                
                                # Display command messages
                                if RENDERER_MODE != "json":
                                    cmd_msg = msg.get("message", "")
                                    if cmd_msg:  # Only print if there's a message
                                        # Map command responses to translation keys
                                        if cmd == "help":
                                            # Help message is already formatted, just print it
                                            print(cmd_msg.strip())
                                        elif cmd == "rooms":
                                            # List rooms command
                                            rooms = msg.get("rooms", [])
                                            if rooms:
                                                rooms_str = ", ".join(rooms)
                                                print(t("rooms_list").format(rooms=rooms_str))
                                            else:
                                                print(t("no_rooms_available"))
                                        elif cmd == "nick" and "changed to:" in cmd_msg:
                                            name = cmd_msg.split(":")[-1].strip()
                                            print(t("command_nick_changed").format(name=name))
                                        elif cmd == "room" and "Switched to room:" in cmd_msg:
                                            room_id = msg.get("room_id") or cmd_msg.split(":")[-1].strip()
                                            print(t("command_room_switched").format(room_id=room_id))
                                        elif cmd == "error" and "Usage:" in cmd_msg:
                                            if "/nick" in cmd_msg:
                                                print(t("command_nick_usage"))
                                            elif "/room" in cmd_msg:
                                                print(t("command_room_usage"))
                                            else:
                                                print(cmd_msg)
                                        else:
                                            # Print other command messages as-is
                                            print(cmd_msg)
                        except Exception as e:
                            # Log error for debugging but don't crash
                            if RENDERER_MODE != "json":
                                import traceback
                                print(f"Error handling command response: {e}")
                        continue
                    
                    # Message length validation (max 10KB)
                    if len(user_input) > 10_240:
                        print(t("message_too_long"))
                        continue
                    
                    message = f'{self.username}: {user_input}'
                    socket_message = json.dumps({
                        "text": self._encrypt(message),
                        "username": self.username
                    })
                    ws.send(socket_message)
                    self.last_heartbeat = time.time()
                    
                    # Save to local history
                    if self.local_history_enabled:
                        self._save_to_history({
                            "text": message,
                            "username": self.username,
                            "room_id": self.room_id
                        })
                    
                    # Check for response (including heartbeats)
                    try:
                        ws.settimeout(0.5)
                        raw = ws.recv()
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        msg = json.loads(raw)
                        
                        # Handle heartbeat ping
                        if msg.get("type") == "ping":
                            ws.send(json.dumps({"type": "pong", "timestamp": msg.get("timestamp")}))
                            self.last_heartbeat = time.time()
                        # Handle error messages
                        elif msg.get("status") == "error":
                            if RENDERER_MODE != "json":
                                error_msg = msg.get('message', t("unknown_error"))
                                print(t("server_error").format(message=error_msg))
                    except Exception:
                        pass
                except (WebSocketConnectionClosedException, ConnectionResetError, ConnectionAbortedError, OSError):
                    try:
                        if ws:
                            try:
                                ws.close()
                            except Exception:
                                pass
                        ws = self._connect_ws("/talk", show_status=True)
                        self.last_heartbeat = time.time()
                        continue
                    except Exception:
                        print(t("cant_establish_channel"))
                        self.__stop_threads = True
                        break
                except KeyboardInterrupt:
                    self.__stop_threads = True
                    try:
                        ws.send(self.close_response)
                        ws.close()
                    except Exception:
                        pass
                    break
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def update_info(self):
        ws = self._connect_ws("/update")
        last_try = None
        try:
            while not self.__stop_threads:
                try:
                    time.sleep(RENDER_TIME)
                    raw = ws.recv()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    
                    # Payload size validation (max 1MB)
                    if len(raw) > 1_048_576:
                        if RENDERER_MODE != "json":
                            print(t("message_too_large"))
                        continue
                    
                    response = json.loads(raw)
                    
                    # Handle heartbeat ping
                    if response.get("type") == "ping":
                        ws.send(json.dumps({"type": "pong", "timestamp": response.get("timestamp")}))
                        self.last_heartbeat = time.time()
                        continue
                    
                    # Update last_sequence for delta updates
                    if "last_sequence" in response:
                        self.last_sequence = response["last_sequence"]
                    
                    # Update room_id if changed
                    if "room_id" in response:
                        self.room_id = response["room_id"]
                    
                    # Filter messages based on buffer size
                    messages = response.get("messages", [])
                    if len(messages) > MESSAGES_TO_SHOW:
                        messages = messages[-MESSAGES_TO_SHOW:]
                        response["messages"] = messages
                    
                    # Update if there are changes
                    if last_try != response:
                        last_try = response.copy()
                        
                        # Save to local history
                        if self.local_history_enabled and messages:
                            for msg in messages:
                                self._save_to_history(msg)
                        
                        # Render chat
                        if RENDERER_MODE != "json":
                            self.renderer.clear_console()
                            # Re-print welcome message after clearing (unless user explicitly cleared it)
                            if not self.welcome_cleared and self.welcome_shown:
                                print(f"\n{t('welcome_message')}")
                                print(t("current_room").format(room_id=self.room_id))
                                print(t("welcome_instructions"))
                                print()  # Empty line for spacing
                        if len(messages) > 0:
                            self.renderer.print_chat(response=last_try)
                    
                    self.last_heartbeat = time.time()
                except (WebSocketConnectionClosedException, ConnectionResetError, ConnectionAbortedError, OSError):
                    try:
                        if ws:
                            try:
                                ws.close()
                            except Exception:
                                pass
                        ws = self._connect_ws("/update", show_status=True)
                        self.last_heartbeat = time.time()
                        continue
                    except Exception:
                        if RENDERER_MODE != "json":
                            print(t("connection_lost"))
                        self.__stop_threads = True
                        break
                except KeyboardInterrupt:
                    self.__stop_threads = True
                    try:
                        ws.send(self.close_response)
                        ws.close()
                    except Exception:
                        pass
                    break
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _validate_keys(self) -> None:
        """Validate and exchange keys with server."""
        self._request_key(
            url=f"{self.base_url}/get_key?room_id={self.room_id}",
            username=self.username,
            password=self.password,
            token=self.token,
            room_id=self.room_id
        )
        self._remove_keys()

    def run(self):
        """Run the client."""
        self._validate_keys()
        threads = [
            threading.Thread(target=self.send_info, daemon=True),
            threading.Thread(target=self.update_info, daemon=True)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
