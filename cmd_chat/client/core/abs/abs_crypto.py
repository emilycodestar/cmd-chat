from abc import ABC, abstractmethod

class CryptoService(ABC):

    @abstractmethod
    def _encrypt(self, message: str) -> str:
        raise NotImplementedError("Need to implement encrypt method")

    @abstractmethod
    def _decrypt(self, message: str) -> str:
        raise NotImplementedError("Need to implement decrypt method")

    @abstractmethod
    def _request_key(self, url: str, username: str, password: str | None = None):
        raise NotImplementedError("Need to implement request key method")

    @abstractmethod
    def _generate_keys(self):
        raise NotImplementedError("Need to implement generate keys method")

    @abstractmethod
    def _get_generated_keys(self) -> tuple:
        raise NotImplementedError("Need to implement get generated keys method")

    @abstractmethod
    def _remove_keys(self):
        raise NotImplementedError("Need to implement remove keys method")
