# CMD CHAT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-encrypted-green.svg)](https://github.com/VoxHash/cmd-chat)

**CMD CHAT** is a modern, secure command-line chat application with end-to-end encryption.  
A fully anonymous chat between clients, impossible to intercept or hand over.  
All data exists only in RAM and is wiped after the session ends.  
No logs, no traces, no compromise.

---

## 🔒 Key Features

- **Full anonymity** - No user tracking or identification
- **End-to-End encryption** - RSA 2048-bit + Fernet symmetric encryption
- **Memory-only storage** - Data stored only in RAM, deleted on exit
- **No logging** - No persistence on disk, no traces left behind
- **Rate limiting** - Built-in anti-spam protection
- **Heartbeat/ping-pong** - Automatic reconnection with timeout handling
- **Token-based auth** - Secure token authentication system
- **Clean error handling** - No stack traces exposed to clients
- **Multiple rooms** - Support for isolated chat rooms/channels
- **Chat commands** - Built-in commands (/nick, /clear, /help, /quit, /room, /rooms)
- **Per-client keys** - Each client gets a unique encryption key
- **Delta updates** - Only new messages sent (not full history)
- **Customizable renderers** - Rich, minimal, or JSON output modes
- **Local history** - Optional encrypted message history
- **Internationalization** - 13 supported languages (en, fr, es, zh, ja, de, ru, et, pt, ko, ca, eu, gl)
- **Easy to run** - Simple Python CLI interface

---

## ⚙️ How It Works

1. The client generates an RSA 2048-bit key pair.
2. The server creates a symmetric encryption key.
3. The client sends its public key to the server.
4. The server encrypts the symmetric key with the client's public key and sends it back.
5. The client decrypts and confirms the key.
6. From that point, all communication is done via symmetric encryption (Fernet).

Everything happens in memory only. Nothing is written to disk.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VoxHash/cmd-chat.git
   cd cmd-chat
   ```

2. **Create a virtual environment and install dependencies:**
   
   **Linux / macOS:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   
   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure (optional):** Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start the server:**
   ```bash
   # With .env file configured:
   python cmd_chat.py serve
   
   # Or with command-line arguments:
   python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_SECURE_PASSWORD
   ```
   
   The server will display connection information including the IP address and port:
   ```
   ============================================================
     🚀 CMD CHAT SERVER STARTED
   ============================================================
     Server Address: 192.168.1.100:1000
     Protocol: http:// (WebSocket: ws://)
     Connect with: python cmd_chat.py connect 192.168.1.100 1000 <username> <password>
   ============================================================
   ```

5. **Connect a client:**
   ```bash
   # With .env file configured:
   python cmd_chat.py connect
   
   # Or with command-line arguments:
   python cmd_chat.py connect localhost 1000 USERNAME YOUR_SECURE_PASSWORD
   ```

6. **Start chatting:**
   - Once connected, you'll see a welcome message with instructions
   - **To send a message:** Simply type your message and press Enter
   - **To use commands:** Type commands starting with `/` (e.g., `/help`, `/nick MyName`)
   - **To quit:** Type `q` or `/quit`

---

## 📖 Usage

### Configuration via .env File

You can configure the application using a `.env` file, making CLI arguments optional:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your settings
# Then run without arguments:
python cmd_chat.py serve
python cmd_chat.py connect
```

**Priority order:** CLI arguments > .env file > defaults

### Server Commands

```bash
# Basic server startup (with .env configured)
python cmd_chat.py serve

# Or with command-line arguments
python cmd_chat.py serve <IP_ADDRESS> <PORT> --password <PASSWORD>

# With SSL/TLS support
python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_PASSWORD \
    --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem

# Force SSL/TLS (require certificates)
python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_PASSWORD \
    --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem --force-ssl
```

### Client Commands

```bash
# Connect with password
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD>

# Connect with token (more secure)
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> --token <TOKEN>

# Connect with SSL/TLS
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --ssl

# Connect to a specific room
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --room myroom

# Connect with JSON renderer (for automation)
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --renderer json

# Connect with minimal renderer
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --renderer minimal

# Connect with specific language
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --language fr

# Supported languages: en, fr, es, zh, ja, de, ru, et, pt, ko, ca, eu, gl
```

### Token Generation

To generate an authentication token:

```bash
curl -X POST http://localhost:1000/generate_token \
  -d "admin_password=YOUR_PASSWORD" \
  -d "username=alice" \
  -d "ttl=3600"
```

---

## ⚙️ Configuration

### .env File Support

You can configure the application using a `.env` file, making CLI arguments optional. Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
# Edit .env with your settings
```

**Priority order:** CLI arguments > .env file > defaults

### Environment Variables

**Server Configuration:**
| Variable | Default | Description |
|---------|---------|-------------|
| `SERVER_HOST` | 0.0.0.0 | Server IP address |
| `SERVER_PORT` | 1000 | Server port |
| `ADMIN_PASSWORD` | - | Admin password (required) |
| `SSL_CERT_PATH` | - | Path to SSL certificate file |
| `SSL_KEY_PATH` | - | Path to SSL key file |
| `FORCE_SSL` | false | Force SSL/TLS (require certificates) |

**Client Configuration:**
| Variable | Default | Description |
|---------|---------|-------------|
| `CLIENT_SERVER` | - | Server IP address |
| `CLIENT_PORT` | 1000 | Server port |
| `CLIENT_USERNAME` | - | Username |
| `CLIENT_PASSWORD` | - | Password (or use CLIENT_TOKEN) |
| `CLIENT_TOKEN` | - | Authentication token |
| `CLIENT_USE_SSL` | false | Use SSL/TLS (wss://) |
| `CLIENT_ROOM` | default | Room ID to join |
| `CLIENT_RENDER_TIME` | 0.1 | Client render update interval in seconds |
| `CLIENT_MESSAGES_TO_SHOW` | 10 | Number of messages to display in buffer |
| `ENABLE_LOCAL_HISTORY` | false | Enable local encrypted message history |
| `RENDERER_MODE` | rich | Renderer mode: rich, minimal, or json |
| `CMD_CHAT_LANGUAGE` | en | Language code: en, fr, es, zh, ja, de, ru, et, pt, ko, ca, eu, gl |

### Server Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_MESSAGES_PER_WINDOW` | 10 | Maximum messages per rate limit window |
| `RATE_LIMIT_WINDOW` | 60.0 | Rate limit window in seconds |
| `HEARTBEAT_INTERVAL` | 30.0 | Heartbeat ping interval in seconds |
| `HEARTBEAT_TIMEOUT` | 60.0 | Connection timeout in seconds |
| `MAX_MESSAGE_SIZE` | 10KB | Maximum message size |
| `MAX_PAYLOAD_SIZE` | 1MB | Maximum WebSocket payload size |

## 💬 Chat Commands

Once connected, you can use these commands:

- `/help` - Show available commands
- `/nick <name>` - Change your nickname
- `/room <id>` - Switch to a different room
- `/rooms` - List all available rooms
- `/clear` - Clear the chat display (client-side)
- `/quit` - Disconnect from the chat

---

## 🔐 Security Features

- **RSA 2048-bit encryption** for key exchange
- **Fernet symmetric encryption** for message transport
- **Token-based authentication** with expiration
- **Rate limiting** to prevent spam and DoS attacks
- **Clean error handling** - no sensitive information leaked
- **Heartbeat mechanism** for connection health monitoring
- **Message size limits** to prevent resource exhaustion

---

## 📝 Examples

### Basic Chat Session

**Terminal 1 (Server):**
```bash
python cmd_chat.py serve 0.0.0.0 1000 --password MySecurePass123
```

**Terminal 2 (Client 1):**
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123
```

**Terminal 3 (Client 2):**
```bash
python cmd_chat.py connect localhost 1000 bob MySecurePass123
```

### Using Tokens

**Generate token:**
```bash
curl -X POST http://localhost:1000/generate_token \
  -d "admin_password=MySecurePass123" \
  -d "username=alice" \
  -d "ttl=86400"
```

**Connect with token:**
```bash
python cmd_chat.py connect localhost 1000 alice --token <GENERATED_TOKEN>
```

### Using Rooms

**Create/join a room:**
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123 --room general
python cmd_chat.py connect localhost 1000 bob MySecurePass123 --room general
```

**Switch rooms (while connected):**
```
/room dev-team
```

### Renderer Modes

**Rich mode (default):** Beautiful formatted output with colors and tables
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123
```

**Minimal mode:** Simple text output
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123 --renderer minimal
```

**JSON mode:** Machine-readable JSON output for automation
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123 --renderer json
```

### Language Selection

**Connect with French interface:**
```bash
python cmd_chat.py connect localhost 1000 alice MySecurePass123 --language fr
```

**Or set via environment variable:**
```bash
export CMD_CHAT_LANGUAGE=es
python cmd_chat.py connect localhost 1000 alice MySecurePass123
```

**Supported languages:**
- `en` - English (default)
- `fr` - French
- `es` - Spanish
- `zh` - Chinese
- `ja` - Japanese
- `de` - German
- `ru` - Russian
- `et` - Estonian
- `pt` - Portuguese
- `ko` - Korean
- `ca` - Catalan
- `eu` - Basque
- `gl` - Galician

---

## 🧪 Testing

Run the security test suite:

```bash
# Start the server first
python cmd_chat.py serve 0.0.0.0 1000 --password TestPass123

# In another terminal, run tests
python test/test_security.py
```

---

## 🛣️ Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- [VoxHash](https://github.com/VoxHash)
- [Emily 💞](emilycodestar)
- [himath rajapaksha](anorak999)
- [Sousa](ESousa97)
- [Ahmad Allahverdiyev](hmd37)
---

## 🙏 Acknowledgments

- Original concept and inspiration from the open-source community
- Built with security and privacy as top priorities

---

## 📧 Support

For support, email contact@voxhash.dev or open an issue on GitHub.

---

## ⚠️ Security Notice

This software is provided as-is for educational and personal use. While we take security seriously, always use strong passwords and consider the security implications of your deployment environment.
