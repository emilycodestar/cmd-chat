"""Token-based authentication utilities for CMD CHAT."""
import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """Authentication token data container."""
    token: str
    username: str
    created_at: float
    expires_at: float
    ip_address: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Return True when the token is past its expiration."""
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        """Return True when the token is still valid."""
        return not self.is_expired()


class TokenManager:
    """Manager responsible for issuing and tracking tokens."""
    
    def __init__(self, default_ttl: int = 86400):  # 24 horas padrão
        self.tokens: Dict[str, Token] = {}
        self.default_ttl = default_ttl
        self.admin_password: Optional[str] = None
    
    def set_admin_password(self, password: str):
        """Configure the admin password used when creating tokens."""
        self.admin_password = password
    
    def generate_token(
        self,
        username: str,
        admin_password: str,
        ttl: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Optional[str]:
        """Create and persist a new access token."""
        if self.admin_password and admin_password != self.admin_password:
            return None
        
        token_str = str(uuid.uuid4())
        ttl = ttl or self.default_ttl
        now = time.time()
        
        token = Token(
            token=token_str,
            username=username,
            created_at=now,
            expires_at=now + ttl,
            ip_address=ip_address
        )
        
        self.tokens[token_str] = token
        return token_str
    
    def validate_token(self, token_str: str, ip_address: Optional[str] = None) -> Optional[Token]:
        """Validate a token string and optionally check the originating IP."""
        token = self.tokens.get(token_str)
        
        if not token:
            return None
        
        # Remove token expirado
        if token.is_expired():
            self.revoke_token(token_str)
            return None
        
        # Optional IP validation to bind tokens to a specific remote address
        if token.ip_address and ip_address and token.ip_address != ip_address:
            return None
        
        return token
    
    def revoke_token(self, token_str: str) -> bool:
        """Revoke the provided token."""
        if token_str in self.tokens:
            del self.tokens[token_str]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Clean expired tokens and return how many were removed."""
        expired = [
            token_str for token_str, token in self.tokens.items()
            if token.is_expired()
        ]
        
        for token_str in expired:
            del self.tokens[token_str]
        
        return len(expired)
    
    def get_active_tokens_count(self) -> int:
        """Return the amount of active tokens."""
        return len([t for t in self.tokens.values() if t.is_valid()])
    
    def list_active_users(self) -> list[str]:
        """List usernames that currently have valid tokens."""
        return list(set(
            token.username for token in self.tokens.values()
            if token.is_valid()
        ))
