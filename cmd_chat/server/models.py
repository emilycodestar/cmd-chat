from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    user_ip: str = ""
    username: str = ""


@dataclass
class UserSession:
    user_id: str
    ip: str
    username: str = "unknown"
    fernet_key: Optional[bytes] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_activity: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    active: bool = True

    def update_activity(self):
        self.last_activity = datetime.now(timezone.utc).isoformat()

    def is_stale(self, timeout_seconds: int = 3600) -> bool:
        last = datetime.fromisoformat(self.last_activity)
        return (datetime.now(timezone.utc) - last).total_seconds() > timeout_seconds
