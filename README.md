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

3. **Start the server:**
   ```bash
   python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_SECURE_PASSWORD
   ```

4. **Connect a client:**
   ```bash
   python cmd_chat.py connect localhost 1000 USERNAME YOUR_SECURE_PASSWORD
   ```

---

## 📖 Usage

### Server Commands

```bash
# Basic server startup
python cmd_chat.py serve <IP_ADDRESS> <PORT> --password <PASSWORD>

# With SSL/TLS support
python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_PASSWORD \
    --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem
```

### Client Commands

```bash
# Connect with password
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD>

# Connect with token (more secure)
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> --token <TOKEN>

# Connect with SSL/TLS
python cmd_chat.py connect <SERVER_IP> <PORT> <USERNAME> <PASSWORD> --ssl
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

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_MESSAGES_PER_WINDOW` | 10 | Maximum messages per rate limit window |
| `RATE_LIMIT_WINDOW` | 60.0 | Rate limit window in seconds |
| `HEARTBEAT_INTERVAL` | 30.0 | Heartbeat ping interval in seconds |
| `HEARTBEAT_TIMEOUT` | 60.0 | Connection timeout in seconds |
| `MAX_MESSAGE_SIZE` | 10KB | Maximum message size |
| `MAX_PAYLOAD_SIZE` | 1MB | Maximum WebSocket payload size |

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

- **VoxHash Technologies** - [GitHub](https://github.com/VoxHash)

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
