import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
import json
import base64
import srp

from cmd_chat.server.server import ChatServer
from cmd_chat.server.stores import MessageStore, UserSessionStore
from cmd_chat.server.managers import ConnectionManager
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


class TestSRPFlow:
    @pytest.mark.asyncio
    async def test_srp_init_success(self, server):
        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        init_request = (
            json.dumps(
                {
                    "cmd": "srp_init",
                    "username": "testuser",
                    "A": base64.b64encode(A).decode(),
                }
            )
            + "\n"
        )
        reader.feed_data(init_request.encode())
        reader.feed_eof()

        session = await server._handle_auth(reader, writer, "127.0.0.1")

        assert writer_transport.data
        response = json.loads(writer_transport.data.decode().strip())
        assert "user_id" in response
        assert "B" in response
        assert "salt" in response
        assert "room_salt" in response

    @pytest.mark.asyncio
    async def test_srp_init_missing_a(self, server):
        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        init_request = (
            json.dumps(
                {
                    "cmd": "srp_init",
                    "username": "testuser",
                }
            )
            + "\n"
        )
        reader.feed_data(init_request.encode())
        reader.feed_eof()

        session = await server._handle_auth(reader, writer, "127.0.0.1")

        assert session is None
        response = json.loads(writer_transport.data.decode().strip())
        assert "error" in response
        assert response["error"] == "Missing A"

    @pytest.mark.asyncio
    async def test_srp_init_username_taken(self, server):
        from cmd_chat.server.models import UserSession

        server.session_store.add(
            UserSession(user_id="existing", ip="127.0.0.1", username="testuser")
        )

        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        init_request = (
            json.dumps(
                {
                    "cmd": "srp_init",
                    "username": "testuser",
                    "A": base64.b64encode(A).decode(),
                }
            )
            + "\n"
        )
        reader.feed_data(init_request.encode())
        reader.feed_eof()

        session = await server._handle_auth(reader, writer, "127.0.0.1")

        assert session is None
        response = json.loads(writer_transport.data.decode().strip())
        assert response["error"] == "Username taken"

    @pytest.mark.asyncio
    async def test_srp_full_auth_flow(self, server):
        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        user_id, B, salt = server.srp_manager.init_auth("testuser", A)

        M = usr.process_challenge(salt, B)
        assert M is not None

        H_AMK, session_key = server.srp_manager.verify_auth(user_id, M)

        usr.verify_session(H_AMK)
        assert usr.authenticated()
        assert session_key is not None

    @pytest.mark.asyncio
    async def test_srp_verify_invalid_session(self, server):
        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        init_request = (
            json.dumps(
                {
                    "cmd": "srp_init",
                    "username": "testuser",
                    "A": base64.b64encode(A).decode(),
                }
            )
            + "\n"
        )

        verify_request = (
            json.dumps(
                {
                    "cmd": "srp_verify",
                    "user_id": "nonexistent",
                    "M": base64.b64encode(b"fake").decode(),
                }
            )
            + "\n"
        )

        reader.feed_data(init_request.encode())
        reader.feed_data(verify_request.encode())
        reader.feed_eof()

        session = await server._handle_auth(reader, writer, "127.0.0.1")

        assert session is None


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_receives_init_state(self, server):
        from cmd_chat.server.models import UserSession, Message

        server.message_store.add(Message(text="test msg", username="other"))
        session = UserSession(user_id="test-id", ip="127.0.0.1", username="testuser")
        server.session_store.add(session)

        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        reader.feed_eof()

        await server._handle_chat(reader, writer, session)

        response = json.loads(writer_transport.data.decode().split("\n")[0])
        assert response["type"] == "init"
        assert "messages" in response
        assert "users" in response

    @pytest.mark.asyncio
    async def test_chat_broadcast_message(self, server):
        from cmd_chat.server.models import UserSession

        session = UserSession(user_id="test-id", ip="127.0.0.1", username="testuser")
        server.session_store.add(session)

        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        message = json.dumps({"type": "message", "text": "hello"}) + "\n"
        reader.feed_data(message.encode())
        reader.feed_eof()

        await server._handle_chat(reader, writer, session)

        assert server.message_store.count() == 1

    @pytest.mark.asyncio
    async def test_chat_clear_messages(self, server):
        from cmd_chat.server.models import UserSession, Message

        server.message_store.add(Message(text="msg1", username="user1"))
        server.message_store.add(Message(text="msg2", username="user2"))

        session = UserSession(user_id="test-id", ip="127.0.0.1", username="testuser")
        server.session_store.add(session)

        reader = asyncio.StreamReader()
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        clear_cmd = json.dumps({"type": "clear"}) + "\n"
        reader.feed_data(clear_cmd.encode())
        reader.feed_eof()

        await server._handle_chat(reader, writer, session)

        assert server.message_store.count() == 0


class TestStores:
    def test_message_store_add_and_get(self, message_store):
        from cmd_chat.server.models import Message

        msg = Message(text="test", username="user")
        message_store.add(msg)

        assert message_store.count() == 1
        assert message_store.get_all()[0].text == "test"

    def test_message_store_clear(self, message_store):
        from cmd_chat.server.models import Message

        message_store.add(Message(text="1", username="u"))
        message_store.add(Message(text="2", username="u"))
        message_store.clear()

        assert message_store.count() == 0

    def test_session_store_add_and_get(self, session_store):
        from cmd_chat.server.models import UserSession

        session = UserSession(user_id="123", ip="127.0.0.1", username="test")
        session_store.add(session)

        assert session_store.get("123") is not None
        assert session_store.get("123").username == "test"

    def test_session_store_remove(self, session_store):
        from cmd_chat.server.models import UserSession

        session = UserSession(user_id="123", ip="127.0.0.1", username="test")
        session_store.add(session)
        session_store.remove("123")

        assert session_store.get("123") is None

    def test_session_store_username_exists(self, session_store):
        from cmd_chat.server.models import UserSession

        session = UserSession(user_id="123", ip="127.0.0.1", username="alice")
        session_store.add(session)

        assert session_store.username_exists("alice") is True
        assert session_store.username_exists("bob") is False


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connection_manager):
        writer_transport = MockTransport()
        writer = MockStreamWriter(writer_transport)

        await connection_manager.connect("user1", writer)
        assert "user1" in connection_manager.active_connections

        await connection_manager.disconnect("user1")
        assert "user1" not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self, connection_manager):
        transport1 = MockTransport()
        writer1 = MockStreamWriter(transport1)
        transport2 = MockTransport()
        writer2 = MockStreamWriter(transport2)

        await connection_manager.connect("user1", writer1)
        await connection_manager.connect("user2", writer2)

        await connection_manager.broadcast('{"type":"test"}')

        assert b'{"type":"test"}' in transport1.data
        assert b'{"type":"test"}' in transport2.data

    @pytest.mark.asyncio
    async def test_broadcast_exclude_user(self, connection_manager):
        transport1 = MockTransport()
        writer1 = MockStreamWriter(transport1)
        transport2 = MockTransport()
        writer2 = MockStreamWriter(transport2)

        await connection_manager.connect("user1", writer1)
        await connection_manager.connect("user2", writer2)

        await connection_manager.broadcast('{"type":"test"}', exclude_user="user1")

        assert transport1.data == b""
        assert b'{"type":"test"}' in transport2.data

    @pytest.mark.asyncio
    async def test_send_personal(self, connection_manager):
        transport = MockTransport()
        writer = MockStreamWriter(transport)

        await connection_manager.connect("user1", writer)

        result = await connection_manager.send_personal("user1", '{"msg":"hi"}')

        assert result is True
        assert b'{"msg":"hi"}' in transport.data

    @pytest.mark.asyncio
    async def test_send_personal_nonexistent(self, connection_manager):
        result = await connection_manager.send_personal("nonexistent", '{"msg":"hi"}')
        assert result is False


class TestSRPAuthManager:
    def test_init_auth(self, srp_manager):
        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        user_id, B, salt = srp_manager.init_auth("testuser", A)

        assert user_id is not None
        assert B is not None
        assert salt is not None

    def test_verify_auth_success(self, srp_manager):
        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"testpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        user_id, B, salt = srp_manager.init_auth("testuser", A)
        M = usr.process_challenge(salt, B)

        H_AMK, session_key = srp_manager.verify_auth(user_id, M)

        assert H_AMK is not None
        assert session_key is not None

    def test_verify_auth_wrong_password(self, srp_manager):
        srp.rfc5054_enable()
        usr = srp.User(b"chat", b"wrongpassword", hash_alg=srp.SHA256)
        _, A = usr.start_authentication()

        user_id, B, salt = srp_manager.init_auth("testuser", A)
        M = usr.process_challenge(salt, B)

        with pytest.raises(ValueError, match="Authentication failed"):
            srp_manager.verify_auth(user_id, M)

    def test_verify_auth_invalid_session(self, srp_manager):
        with pytest.raises(ValueError, match="Invalid session"):
            srp_manager.verify_auth("nonexistent", b"fake")


class MockTransport:
    def __init__(self):
        self.data = b""
        self.closed = False

    def get_extra_info(self, name):
        if name == "peername":
            return ("127.0.0.1", 12345)
        return None

    def close(self):
        self.closed = True


class MockStreamWriter:
    def __init__(self, transport):
        self._transport = transport

    def write(self, data):
        self._transport.data += data

    async def drain(self):
        pass

    def close(self):
        self._transport.close()

    async def wait_closed(self):
        pass

    def get_extra_info(self, name):
        return self._transport.get_extra_info(name)
