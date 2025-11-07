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
        return self.fernet.encrypt(message.encode()).decode("utf-8")

    def _decrypt(self, message: str) -> str:
        return self.fernet.decrypt(message.encode()).decode("utf-8")

    def _request_key(self, url: str, username: str, password: str | None = None):
        pubkey_bytes = self.public_key.save_pkcs1()
        r = requests.post(
            url,
            files={"pubkey": ("public.pem", pubkey_bytes)},
            data={"username": username, "password": password or ""},
            stream=True,
        )
        r.raise_for_status()
        # read the full response content (server returns encrypted symmetric key)
        message = r.content
        self.symmetric_key = rsa.decrypt(message, self.private_key)
        self.fernet = Fernet(self.symmetric_key)

    def _generate_keys(self):
        self.public_key, self.private_key = rsa.newkeys(512)

    def _get_generated_keys(self):
        return self.private_key, self.public_key

    def _remove_keys(self):
        self.public_key = None
        self.private_key = None