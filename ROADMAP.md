## 🗺️ Roadmap

### 1. Core stability ✅

- [x] Switch from `ast.literal_eval` to `json` for messages. *(Completed - Already using JSON)*
- [x] Add proper reconnect with heartbeat (ping/pong, timeouts). *(Completed v2.0.0)*
- [x] Clean error handling (no leaking stack traces to clients). *(Completed v2.0.0)*
- [x] Limit message size and frequency (basic anti-spam). *(Completed v2.0.0 - 10 messages per 60 seconds)*

### 2. Security improvements ✅

- [x] Per-client symmetric keys instead of one global key. *(Completed v3.0.0)*
- [x] Room-based encryption keys for message sharing. *(Completed v3.2.1 - All clients in same room share key)*
- [x] Upgrade RSA 512 → 2048 (or curve25519 ECDH + HKDF). *(Completed - Already using RSA 2048-bit)*
- [x] Replace shared password with invite tokens or session-based bearer tokens. *(Completed v2.0.0 - Token system implemented)*
- [x] Force WSS (TLS) for production. *(Completed v3.0.0 - --force-ssl option)*

### 3. Chat features ✅

- [x] Multiple rooms (room_id support). *(Completed v3.0.0)*
- [x] Commands (`/nick`, `/clear`, `/help`, `/quit`, `/room`). *(Completed v3.0.0)*
- [x] Message timestamps + sequence numbers. *(Completed v3.0.0)*
- [x] Delta updates (only send new messages instead of full history). *(Completed v3.0.0)*

### 4. UX / Client

- [x] Local encrypted history (optional). *(Completed v3.0.0)*
- [x] Customizable renderers (rich, minimal, json mode). *(Completed v3.0.0)*
- [x] Quiet reconnection status indicator. *(Completed v3.0.0)*
- [x] Configurable message buffer length. *(Completed v3.0.0)*
- [x] Add i18n translation system to offer multiple language options on CLI. *(Completed v3.1.0 - 13 languages)*

### 5. File & media

- [ ] File transfer via encrypted chunks.
- [ ] Inline images (optional, in rich renderer).

### 6. Deployment & Ops

- [ ] Dockerfile + docker-compose (server + client).
- [ ] Add uvloop + multiple Sanic workers.
- [ ] Graceful shutdown & restart.
- [ ] Systemd service unit for server.
- [ ] Create PyPI package
- [x] CI/CD workflows (GitHub Actions). *(Completed v2.0.0)*

### 7. Privacy & audit

- [x] Disable sensitive logs (no passwords/tokens in logs). *(Completed v2.0.0 - Clean error handling)*
- [ ] Minimal server metrics: connected users, msg/sec.
- [x] Configurable retention (in-memory only vs file-based). *(Completed - Memory-only by default)*

---

## 📝 Completed Features (v3.1.0)

**Internationalization:**
- ✅ Complete i18n translation system
- ✅ 13 supported languages (en, fr, es, zh, ja, de, ru, et, pt, ko, ca, eu, gl)
- ✅ CLI language selection (--language option)
- ✅ Environment variable support (CMD_CHAT_LANGUAGE)
- ✅ Automatic fallback to English

## 📝 Completed Features (v3.0.0)

**Security:**
- ✅ Per-client symmetric keys (unique key per client)
- ✅ Force SSL/TLS option for production
- ✅ Room-based key management

**Chat Features:**
- ✅ Multiple rooms/channels support
- ✅ Chat commands (/nick, /clear, /help, /quit, /room)
- ✅ Message timestamps and sequence numbers
- ✅ Delta updates (only new messages)

**UX/Client:**
- ✅ Local encrypted history (optional)
- ✅ Customizable renderers (rich, minimal, json)
- ✅ Quiet reconnection status indicator
- ✅ Configurable message buffer length

## 📝 Completed Features (v2.0.0)

**Core Stability:**
- ✅ JSON message parsing (replacing ast.literal_eval)
- ✅ Heartbeat/ping-pong mechanism with 30s interval and 60s timeout
- ✅ Clean error handling without stack trace exposure
- ✅ Rate limiting: 10 messages per 60 seconds per user
- ✅ Message size limits: 10KB per message, 1MB payload limit

**Security:**
- ✅ RSA 2048-bit encryption for key exchange
- ✅ Token-based authentication system with expiration
- ✅ SSL/TLS support (optional)

**Testing & CI/CD:**
- ✅ Comprehensive test suite (security, rate limiting, error handling, heartbeat, JSON parsing)
- ✅ GitHub Actions CI/CD workflows
- ✅ Multi-platform testing (Ubuntu, Windows, macOS)
- ✅ Python 3.10, 3.11, 3.12 support

**Documentation:**
- ✅ Comprehensive README.md
- ✅ Updated LICENSE
- ✅ Configuration examples (.env.example)
