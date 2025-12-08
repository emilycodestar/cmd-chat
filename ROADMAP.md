## 🗺️ Roadmap

### 1. Core stability ✅

- [x] Switch from `ast.literal_eval` to `json` for messages. *(Completed - Already using JSON)*
- [x] Add proper reconnect with heartbeat (ping/pong, timeouts). *(Completed v2.0.0)*
- [x] Clean error handling (no leaking stack traces to clients). *(Completed v2.0.0)*
- [x] Limit message size and frequency (basic anti-spam). *(Completed v2.0.0 - 10 messages per 60 seconds)*

### 2. Security improvements

- [ ] Per-client symmetric keys instead of one global key.
- [x] Upgrade RSA 512 → 2048 (or curve25519 ECDH + HKDF). *(Completed - Already using RSA 2048-bit)*
- [x] Replace shared password with invite tokens or session-based bearer tokens. *(Completed v2.0.0 - Token system implemented)*
- [ ] Force WSS (TLS) for production. *(SSL/TLS support available, but not enforced)*

### 3. Chat features

- [ ] Multiple rooms (room_id support).
- [ ] Commands (`/nick`, `/clear`, `/help`, `/quit`).
- [ ] Message timestamps + sequence numbers.
- [ ] Delta updates (only send new messages instead of full history).

### 4. UX / Client

- [ ] Local encrypted history (optional).
- [ ] Customizable renderers (rich, minimal, json mode).
- [ ] Quiet reconnection status indicator.
- [ ] Configurable message buffer length.
- [ ] Add i18n translation system to offer multiple language options on CLI

### 5. File & media

- [ ] File transfer via encrypted chunks.
- [ ] Inline images (optional, in rich renderer).

### 6. Deployment & Ops

- [ ] Dockerfile + docker-compose (server + client).
- [ ] Add uvloop + multiple Sanic workers.
- [ ] Graceful shutdown & restart.
- [ ] Systemd service unit for server.
- [x] CI/CD workflows (GitHub Actions). *(Completed v2.0.0)*

### 7. Privacy & audit

- [x] Disable sensitive logs (no passwords/tokens in logs). *(Completed v2.0.0 - Clean error handling)*
- [ ] Minimal server metrics: connected users, msg/sec.
- [x] Configurable retention (in-memory only vs file-based). *(Completed - Memory-only by default)*

---

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
