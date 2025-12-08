import rsa
import requests
from cryptography.fernet import Fernet

from cmd_chat.client.core.abs.abs_crypto import CryptoService


class RSAService(CryptoService):
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.symmetric_key = None
        self.fernet = None
        self._generate_keys()

    def _encrypt(self, message: str) -> str:
        try:
            if not self.fernet:
                raise ValueError("Encryption not initialized")
            return self.fernet.encrypt(message.encode()).decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Encryption failed: {e}")

    def _decrypt(self, message: str) -> str:
        try:
            if not self.fernet:
                raise ValueError("Decryption not initialized")
            return self.fernet.decrypt(message.encode()).decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Decryption failed: {e}")

    def _request_key(self, url: str, username: str, password: str | None = None, token: str | None = None, room_id: str | None = None):
        try:
            pubkey_bytes = self.public_key.save_pkcs1()
            
            # Preparar dados de autenticação
            data = {"username": username}
            if token:
                data["token"] = token
            elif password:
                data["password"] = password
            if room_id:
                data["room_id"] = room_id
            
            r = requests.post(
                url,
                files={"pubkey": ("public.pem", pubkey_bytes)},
                data=data,
                stream=True,
                timeout=10,
                verify=True  # Verificar certificados SSL
            )
            r.raise_for_status()
            
            # read the full response content (server returns encrypted symmetric key)
            message = r.content
            if not message:
                raise ValueError("Empty response from server")
            
            self.symmetric_key = rsa.decrypt(message, self.private_key)
            self.fernet = Fernet(self.symmetric_key)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to exchange keys with server: {e}")
        except Exception as e:
            raise RuntimeError(f"Key exchange failed: {e}")

    def _generate_keys(self):
        self.public_key, self.private_key = rsa.newkeys(2048)

    def _get_generated_keys(self):
        return self.private_key, self.public_key

    def _remove_keys(self):
        self.public_key = None
        self.private_key = None