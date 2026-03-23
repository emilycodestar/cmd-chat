import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os

from cmd_chat.server.server import ChatServer
from cmd_chat.server.managers import ConnectionManager
from cmd_chat.server.stores import MessageStore, UserSessionStore
from cmd_chat.server.srp_auth import SRPAuthManager


@pytest.fixture
def server():
    return ChatServer(password="testpassword")


@pytest.fixture
def message_store():
    return MessageStore()


@pytest.fixture
def session_store():
    return UserSessionStore()


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.fixture
def srp_manager():
    return SRPAuthManager("testpassword")
