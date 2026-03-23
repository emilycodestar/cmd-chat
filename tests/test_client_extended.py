import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import base64
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from cmd_chat.client.client import Client


@pytest.fixture
def client():
    return Client(
        server="127.0.0.1",
        port=3000,
        username="testuser",
        password="testpassword",
    )


@pytest.fixture
def room_salt():
    return os.urandom(16)


@pytest.fixture
def room_fernet(room_salt):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=room_salt,
        info=b"cmd-chat-room-key",
    )
    room_key = hkdf.derive(b"testpassword")
    return Fernet(base64.urlsafe_b64encode(room_key))


class TestClientProperties:
    def test_password_encoding_unicode(self):
        client = Client("localhost", 3000, "user", "пароль123")
        assert client.password == "пароль123".encode()

    def test_password_encoding_special_chars(self):
        client = Client("localhost", 3000, "user", "p@$$w0rd!#%")
        assert client.password == b"p@$$w0rd!#%"

    def test_initial_state(self, client):
        assert client.reader is None
        assert client.writer is None
        assert client.connected is False
        assert client.running is False
        assert client.messages == []
        assert client.users == []


class TestSRPAuthentication:
    @pytest.mark.asyncio
    async def test_srp_authenticate_success(self, client, room_salt):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        init_response = (
            json.dumps(
                {
                    "user_id": "test-user-id-12345",
                    "B": base64.b64encode(os.urandom(256)).decode(),
                    "salt": base64.b64encode(os.urandom(16)).decode(),
                    "room_salt": base64.b64encode(room_salt).decode(),
                }
            )
            + "\n"
        )

        verify_response = (
            json.dumps(
                {
                    "H_AMK": base64.b64encode(os.urandom(32)).decode(),
                    "session_key": base64.b64encode(Fernet.generate_key()).decode(),
                }
            )
            + "\n"
        )

        mock_reader.readline = AsyncMock(
            side_effect=[
                init_response.encode(),
                verify_response.encode(),
            ]
        )

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_usr.process_challenge.return_value = os.urandom(32)
            mock_usr.verify_session.return_value = None
            mock_usr.authenticated.return_value = True
            mock_srp_user.return_value = mock_usr

            await client.srp_authenticate()

        assert client.user_id == "test-user-id-12345"
        assert client.room_fernet is not None
        assert client.fernet is not None

    @pytest.mark.asyncio
    async def test_srp_authenticate_init_error(self, client):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        error_response = json.dumps({"error": "Username taken"}) + "\n"
        mock_reader.readline = AsyncMock(return_value=error_response.encode())

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_srp_user.return_value = mock_usr

            with pytest.raises(ValueError, match="Username taken"):
                await client.srp_authenticate()

    @pytest.mark.asyncio
    async def test_srp_authenticate_verify_error(self, client, room_salt):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        init_response = (
            json.dumps(
                {
                    "user_id": "test-user-id",
                    "B": base64.b64encode(os.urandom(256)).decode(),
                    "salt": base64.b64encode(os.urandom(16)).decode(),
                    "room_salt": base64.b64encode(room_salt).decode(),
                }
            )
            + "\n"
        )

        verify_error = json.dumps({"error": "Authentication failed"}) + "\n"

        mock_reader.readline = AsyncMock(
            side_effect=[
                init_response.encode(),
                verify_error.encode(),
            ]
        )

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_usr.process_challenge.return_value = os.urandom(32)
            mock_srp_user.return_value = mock_usr

            with pytest.raises(ValueError, match="Authentication failed"):
                await client.srp_authenticate()

    @pytest.mark.asyncio
    async def test_srp_authenticate_challenge_none(self, client, room_salt):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        init_response = (
            json.dumps(
                {
                    "user_id": "test-user-id",
                    "B": base64.b64encode(os.urandom(256)).decode(),
                    "salt": base64.b64encode(os.urandom(16)).decode(),
                    "room_salt": base64.b64encode(room_salt).decode(),
                }
            )
            + "\n"
        )

        mock_reader.readline = AsyncMock(return_value=init_response.encode())

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_usr.process_challenge.return_value = None
            mock_srp_user.return_value = mock_usr

            with pytest.raises(ValueError, match="SRP challenge processing failed"):
                await client.srp_authenticate()

    @pytest.mark.asyncio
    async def test_srp_authenticate_server_not_authenticated(self, client, room_salt):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        init_response = (
            json.dumps(
                {
                    "user_id": "test-user-id",
                    "B": base64.b64encode(os.urandom(256)).decode(),
                    "salt": base64.b64encode(os.urandom(16)).decode(),
                    "room_salt": base64.b64encode(room_salt).decode(),
                }
            )
            + "\n"
        )

        verify_response = (
            json.dumps(
                {
                    "H_AMK": base64.b64encode(os.urandom(32)).decode(),
                    "session_key": base64.b64encode(Fernet.generate_key()).decode(),
                }
            )
            + "\n"
        )

        mock_reader.readline = AsyncMock(
            side_effect=[
                init_response.encode(),
                verify_response.encode(),
            ]
        )

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_usr.process_challenge.return_value = os.urandom(32)
            mock_usr.verify_session.return_value = None
            mock_usr.authenticated.return_value = False
            mock_srp_user.return_value = mock_usr

            with pytest.raises(ValueError, match="Server authentication failed"):
                await client.srp_authenticate()

    @pytest.mark.asyncio
    async def test_srp_authenticate_connection_closed(self, client):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        client.reader = mock_reader
        client.writer = mock_writer

        mock_reader.readline = AsyncMock(return_value=b"")

        with patch("cmd_chat.client.client.srp.User") as mock_srp_user:
            mock_usr = MagicMock()
            mock_usr.start_authentication.return_value = (None, os.urandom(256))
            mock_srp_user.return_value = mock_usr

            with pytest.raises(ConnectionError):
                await client.srp_authenticate()


class TestDecryptMessage:
    def test_decrypt_multiple_messages(self, client, room_fernet, room_salt):
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        room_key = hkdf.derive(client.password)
        client.room_fernet = Fernet(base64.urlsafe_b64encode(room_key))

        messages = ["Hello", "World", "Test123", "Привет мир"]
        for original in messages:
            encrypted = room_fernet.encrypt(original.encode()).decode()
            msg = {"text": encrypted, "username": "other"}
            decrypted = client.decrypt_message(msg)
            assert decrypted["text"] == original

    def test_decrypt_preserves_other_fields(self, client, room_fernet, room_salt):
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        room_key = hkdf.derive(client.password)
        client.room_fernet = Fernet(base64.urlsafe_b64encode(room_key))

        encrypted = room_fernet.encrypt(b"test").decode()
        msg = {
            "text": encrypted,
            "username": "sender",
            "timestamp": "2024-01-01T12:00:00",
            "id": "msg-123",
            "user_ip": "192.168.1.1",
        }

        decrypted = client.decrypt_message(msg)

        assert decrypted["text"] == "test"
        assert decrypted["username"] == "sender"
        assert decrypted["timestamp"] == "2024-01-01T12:00:00"
        assert decrypted["id"] == "msg-123"
        assert decrypted["user_ip"] == "192.168.1.1"

    def test_decrypt_wrong_key_marks_failed(self, client):
        fernet1 = Fernet(Fernet.generate_key())
        encrypted = fernet1.encrypt(b"secret").decode()
        client.room_fernet = Fernet(Fernet.generate_key())

        msg = {"text": encrypted, "username": "other"}
        decrypted = client.decrypt_message(msg)

        assert decrypted["text"] == "[decrypt failed]"

    def test_decrypt_corrupted_ciphertext(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())

        msg = {"text": "YWJjZGVmZ2hpamtsbW5vcA==", "username": "other"}
        decrypted = client.decrypt_message(msg)

        assert decrypted["text"] == "[decrypt failed]"

    def test_decrypt_none_text(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())

        msg = {"text": None, "username": "other"}
        result = client.decrypt_message(msg)

        assert result["text"] is None


class TestReceiveLoop:
    @pytest.mark.asyncio
    async def test_receive_multiple_messages_sequence(self, client, room_fernet):
        client.room_fernet = room_fernet
        client.running = True
        client.messages = []

        msg1 = room_fernet.encrypt(b"First").decode()
        msg2 = room_fernet.encrypt(b"Second").decode()
        msg3 = room_fernet.encrypt(b"Third").decode()

        messages = [
            (
                json.dumps(
                    {"type": "message", "data": {"text": msg1, "username": "user1"}}
                )
                + "\n"
            ).encode(),
            (
                json.dumps(
                    {"type": "message", "data": {"text": msg2, "username": "user2"}}
                )
                + "\n"
            ).encode(),
            (
                json.dumps(
                    {"type": "message", "data": {"text": msg3, "username": "user1"}}
                )
                + "\n"
            ).encode(),
            b"",
        ]

        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=messages)
        client.reader = mock_reader

        with patch.object(client, "render_messages"):
            await client.receive_loop()

        assert len(client.messages) == 3
        assert client.messages[0]["text"] == "First"
        assert client.messages[1]["text"] == "Second"
        assert client.messages[2]["text"] == "Third"

    @pytest.mark.asyncio
    async def test_receive_init_message(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True
        client.messages = []
        client.users = []

        init_msg = (
            json.dumps(
                {
                    "type": "init",
                    "messages": [],
                    "users": [
                        {"user_id": "1", "username": "alice"},
                        {"user_id": "2", "username": "bob"},
                    ],
                }
            )
            + "\n"
        )

        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=[init_msg.encode(), b""])
        client.reader = mock_reader

        with patch.object(client, "render_messages"):
            await client.receive_loop()

        assert len(client.users) == 2
        assert client.users[0]["username"] == "alice"
        assert client.users[1]["username"] == "bob"
        assert client.connected is True

    @pytest.mark.asyncio
    async def test_receive_user_joined(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True
        client.users = [{"user_id": "1", "username": "alice"}]

        join_msg = (
            json.dumps(
                {
                    "type": "user_joined",
                    "user_id": "2",
                    "username": "bob",
                }
            )
            + "\n"
        )

        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=[join_msg.encode(), b""])
        client.reader = mock_reader

        with patch.object(client, "render_messages"):
            await client.receive_loop()

        assert len(client.users) == 2
        assert client.users[1]["username"] == "bob"

    @pytest.mark.asyncio
    async def test_receive_user_left(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True
        client.users = [
            {"user_id": "1", "username": "alice"},
            {"user_id": "2", "username": "bob"},
        ]

        leave_msg = json.dumps({"type": "user_left", "user_id": "1"}) + "\n"

        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=[leave_msg.encode(), b""])
        client.reader = mock_reader

        with patch.object(client, "render_messages"):
            await client.receive_loop()

        assert len(client.users) == 1
        assert client.users[0]["username"] == "bob"

    @pytest.mark.asyncio
    async def test_receive_cleared(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True
        client.messages = [{"text": "old", "username": "user"}]

        clear_msg = json.dumps({"type": "cleared"}) + "\n"

        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=[clear_msg.encode(), b""])
        client.reader = mock_reader

        with patch.object(client, "render_messages"):
            await client.receive_loop()

        assert client.messages == []


class TestInputLoop:
    @pytest.mark.asyncio
    async def test_input_quit_command(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True

        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        client.writer = mock_writer

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(return_value="q")
            mock_loop.return_value.run_in_executor = mock_executor

            await client.input_loop()

        assert client.running is False

    @pytest.mark.asyncio
    async def test_input_keyboard_interrupt(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(side_effect=KeyboardInterrupt())
            mock_loop.return_value.run_in_executor = mock_executor

            await client.input_loop()

        assert client.running is False

    @pytest.mark.asyncio
    async def test_input_sends_encrypted_message(self, client, room_fernet):
        client.room_fernet = room_fernet
        client.running = True

        mock_writer = MagicMock()
        written_data = []
        mock_writer.write = MagicMock(side_effect=lambda d: written_data.append(d))
        mock_writer.drain = AsyncMock()
        client.writer = mock_writer

        inputs = iter(["hello", "q"])

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(side_effect=lambda _, __: next(inputs))
            mock_loop.return_value.run_in_executor = mock_executor

            await client.input_loop()

        assert len(written_data) == 1
        sent = json.loads(written_data[0].decode())
        assert sent["type"] == "message"
        decrypted = room_fernet.decrypt(sent["text"].encode()).decode()
        assert decrypted == "hello"

    @pytest.mark.asyncio
    async def test_input_whitespace_not_sent(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.running = True

        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        client.writer = mock_writer

        inputs = iter(["   ", "\t", "", "q"])

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(side_effect=lambda _, __: next(inputs))
            mock_loop.return_value.run_in_executor = mock_executor

            await client.input_loop()

        mock_writer.write.assert_not_called()


class TestRunAsync:
    @pytest.mark.asyncio
    async def test_run_connection_refused(self, client):
        with patch("asyncio.open_connection") as mock_connect:
            mock_connect.side_effect = ConnectionRefusedError()

            with patch.object(client.console, "clear"):
                with patch.object(client.console, "print"):
                    await client.run_async()

    @pytest.mark.asyncio
    async def test_run_timeout(self, client):
        with patch("asyncio.open_connection", side_effect=asyncio.TimeoutError()):
            with patch.object(client.console, "clear"):
                with patch.object(client.console, "print"):
                    await client.run_async()

    @pytest.mark.asyncio
    async def test_run_auth_failure(self, client):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)

            with patch.object(
                client, "srp_authenticate", new_callable=AsyncMock
            ) as mock_auth:
                mock_auth.side_effect = ValueError("Auth failed")

                with patch.object(client.console, "clear"):
                    with patch.object(client.console, "print"):
                        await client.run_async()


class TestRenderMessages:
    def test_render_own_message_green(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.username = "testuser"
        client.messages = [
            {"username": "testuser", "text": "my msg", "timestamp": "2024-01-01T12:00:00"}
        ]
        client.users = []

        printed = []
        with patch.object(client.console, "clear"):
            with patch.object(
                client.console, "print", side_effect=lambda *args, **kwargs: printed.append(args[0] if args else "")
            ):
                client.render_messages()

        msg_output = [p for p in printed if "my msg" in str(p)]
        assert len(msg_output) == 1
        assert "green" in str(msg_output[0])

    def test_render_other_message_cyan(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.username = "testuser"
        client.messages = [
            {"username": "other", "text": "their msg", "timestamp": "2024-01-01T12:00:00"}
        ]
        client.users = []

        printed = []
        with patch.object(client.console, "clear"):
            with patch.object(
                client.console, "print", side_effect=lambda *args, **kwargs: printed.append(args[0] if args else "")
            ):
                client.render_messages()

        msg_output = [p for p in printed if "their msg" in str(p)]
        assert len(msg_output) == 1
        assert "cyan" in str(msg_output[0])

    def test_render_users_online(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.messages = []
        client.users = [
            {"user_id": "1", "username": "alice"},
            {"user_id": "2", "username": "bob"},
        ]

        printed = []
        with patch.object(client.console, "clear"):
            with patch.object(
                client.console, "print", side_effect=lambda *args, **kwargs: printed.append(args[0] if args else "")
            ):
                client.render_messages()

        online_line = [p for p in printed if "Online:" in str(p)]
        assert "alice" in str(online_line[0])
        assert "bob" in str(online_line[0])

    def test_render_no_users_shows_none(self, client):
        client.room_fernet = Fernet(Fernet.generate_key())
        client.messages = []
        client.users = []

        printed = []
        with patch.object(client.console, "clear"):
            with patch.object(
                client.console, "print", side_effect=lambda *args, **kwargs: printed.append(args[0] if args else "")
            ):
                client.render_messages()

        online_line = [p for p in printed if "Online:" in str(p)]
        assert "none" in str(online_line[0])


class TestE2EEncryption:
    def test_same_password_same_key(self, room_salt):
        password = b"shared_secret"

        hkdf1 = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        key1 = base64.urlsafe_b64encode(hkdf1.derive(password))

        hkdf2 = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        key2 = base64.urlsafe_b64encode(hkdf2.derive(password))

        fernet1 = Fernet(key1)
        fernet2 = Fernet(key2)

        ciphertext = fernet1.encrypt(b"Hello from client 1")
        plaintext = fernet2.decrypt(ciphertext)

        assert plaintext == b"Hello from client 1"

    def test_different_password_cannot_decrypt(self, room_salt):
        hkdf1 = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        key1 = base64.urlsafe_b64encode(hkdf1.derive(b"correct_password"))

        hkdf2 = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        key2 = base64.urlsafe_b64encode(hkdf2.derive(b"wrong_password"))

        fernet1 = Fernet(key1)
        fernet2 = Fernet(key2)

        ciphertext = fernet1.encrypt(b"Secret message")

        with pytest.raises(Exception):
            fernet2.decrypt(ciphertext)


class TestEdgeCases:
    def test_empty_username(self):
        client = Client("localhost", 3000, "", "password")
        assert client.username == ""

    def test_very_long_message(self, client, room_fernet, room_salt):
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        room_key = hkdf.derive(client.password)
        client.room_fernet = Fernet(base64.urlsafe_b64encode(room_key))

        long_message = "x" * 10000
        encrypted = room_fernet.encrypt(long_message.encode()).decode()

        msg = {"text": encrypted, "username": "other"}
        decrypted = client.decrypt_message(msg)

        assert decrypted["text"] == long_message

    def test_unicode_message(self, client, room_fernet, room_salt):
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=room_salt,
            info=b"cmd-chat-room-key",
        )
        room_key = hkdf.derive(client.password)
        client.room_fernet = Fernet(base64.urlsafe_b64encode(room_key))

        unicode_msg = "Привет 世界 🎉 مرحبا"
        encrypted = room_fernet.encrypt(unicode_msg.encode()).decode()

        msg = {"text": encrypted, "username": "other"}
        decrypted = client.decrypt_message(msg)

        assert decrypted["text"] == unicode_msg

    def test_port_zero(self):
        client = Client("localhost", 0, "user", "pass")
        assert client.port == 0

    def test_ipv6_server(self):
        client = Client("::1", 3000, "user", "pass")
        assert client.server == "::1"
