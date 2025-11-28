import json
import time
import threading

from websocket import create_connection, WebSocketConnectionClosedException

from cmd_chat.client.core.crypto import RSAService
from cmd_chat.client.core.default_renderer import DefaultClientRenderer
from cmd_chat.client.core.rich_renderer import RichClientRenderer

from cmd_chat.client.config import RENDER_TIME


class Client(RSAService, RichClientRenderer):

    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str | None = None,
        token: str | None = None,
        use_ssl: bool = False
    ):
        super().__init__()
        self.server = server
        self.port = port
        self.username = username
        self.password = password or ""
        self.token = token
        self.use_ssl = use_ssl
        
        # Detectar protocolo baseado em SSL
        http_proto = "https" if use_ssl else "http"
        ws_proto = "wss" if use_ssl else "ws"
        
        self.base_url = f"{http_proto}://{self.server}:{self.port}"
        self.ws_url = f"{ws_proto}://{self.server}:{self.port}"
        self.close_response = json.dumps({
            "action": "close",
            "username": self.username
        })
        self.__stop_threads = False

    def _ws_full(self, path: str) -> str:
        """Constrói URL WebSocket completa com autenticação"""
        if self.token:
            return f"{self.ws_url}{path}?token={self.token}"
        elif self.password:
            return f"{self.ws_url}{path}?password={self.password}"
        return f"{self.ws_url}{path}"

    def _connect_ws(self, path: str, retries: int = 5, backoff: float = 0.5):
        last_exc: Exception = ConnectionError("Failed to connect")
        for attempt in range(retries):
            try:
                return create_connection(self._ws_full(path))
            except Exception as exc:
                last_exc = exc
                time.sleep(backoff * (2 ** attempt))
        print(f"Can't connect to {path}: {last_exc}")
        raise last_exc

    def send_info(self):
        ws = self._connect_ws("/talk")
        try:
            while not self.__stop_threads:
                try:
                    user_input = input("You're message: ")
                    
                    if user_input.strip() == "":
                        continue  # Ignorar mensagens vazias
                    
                    if user_input == "q":
                        self.__stop_threads = True
                        try:
                            if ws:
                                ws.send(self.close_response)
                                ws.close()
                        except Exception:
                            pass
                        break
                    
                    # Message length validation (max 10KB)
                    if len(user_input) > 10_240:
                        print("Error: Message too long (max 10KB)")
                        continue
                    
                    message = f'{self.username}: {user_input}'
                    socket_message = json.dumps({
                        "text": self._encrypt(message),
                        "username": self.username
                    })
                    ws.send(socket_message)
                except (WebSocketConnectionClosedException, ConnectionResetError, ConnectionAbortedError, OSError):
                    try:
                        if ws:
                            try:
                                ws.close()
                            except Exception:
                                pass
                        ws = self._connect_ws("/talk")
                        continue
                    except Exception:
                        print("Can't establish channel")
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
                        print("Warning: Message too large, skipping")
                        continue
                    
                    response = json.loads(raw)
                    
                    # Sempre atualizar se houver mudanças
                    if last_try != response:
                        last_try = response
                        # Atualizar tela sempre que houver mudanças
                        self.clear_console()
                        if len(response.get("messages", [])) > 0:
                            self.print_chat(response=last_try)
                except (WebSocketConnectionClosedException, ConnectionResetError, ConnectionAbortedError, OSError):
                    try:
                        if ws:
                            try:
                                ws.close()
                            except Exception:
                                pass
                        ws = self._connect_ws("/update")
                        continue
                    except Exception:
                        print("Connection lost: can't establish update channel")
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
        self._request_key(
            url=f"{self.base_url}/get_key",
            username=self.username,
            password=self.password,
            token=self.token
        )
        self._remove_keys()

    def run(self):
        self._validate_keys()
        threads = [
            threading.Thread(target=self.send_info, daemon=True),
            threading.Thread(target=self.update_info, daemon=True)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
