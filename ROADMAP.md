## 🗺️ Roadmap

### 1. Core stability

- [ ] Switch from `ast.literal_eval` to `json` for messages.
- [ ] Add proper reconnect with heartbeat (ping/pong, timeouts).
- [ ] Clean error handling (no leaking stack traces to clients).
- [ ] Limit message size and frequency (basic anti-spam).

### 2. Security improvements

- [ ] Per-client symmetric keys instead of one global key.
- [ ] Upgrade RSA 512 → 2048 (or curve25519 ECDH + HKDF).
- [ ] Replace shared password with invite tokens or session-based bearer tokens.
- [ ] Force WSS (TLS) for production.

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

### 7. Privacy & audit

- [ ] Disable sensitive logs (no passwords/tokens in logs).
- [ ] Minimal server metrics: connected users, msg/sec.
- [ ] Configurable retention (in-memory only vs file-based).
