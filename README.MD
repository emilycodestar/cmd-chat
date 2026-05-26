<div align="center">

# 🤐 CMD-CHAT

### encrypted terminal chat. no servers. no logs. ram only.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

</div>

---

peer-to-peer encrypted chat that runs in your terminal. you host, you control. close the window — everything's gone.

## why

every "secure" messenger still stores metadata somewhere. this doesn't. it's just two terminals talking over an encrypted tunnel. nothing written to disk, ever.

## how it works

```
┌──────────────────────────────────────────────────────────────────┐
│                     TLS HANDSHAKE (transport)                    │
├──────────────────────────────────────────────────────────────────┤
│  CLIENT                                         SERVER           │
│    │                                              │              │
│    │══════════ TLS 1.2+ CONNECT ════════════════►│              │
│    │         (cert verified or --no-verify)       │              │
│    │                                              │              │
├──────────────────────────────────────────────────────────────────┤
│                        SRP AUTHENTICATION                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│    │─── {"cmd":"srp_init","username","A"} ──────► │              │
│    │         (A = client public ephemeral)        │              │
│    │                                              │              │
│    │◄──── {"user_id","B","salt","room_salt"} ──── │              │
│    │         (B = server public ephemeral)        │              │
│    │                                              │              │
│    │  [client derives room_key via HKDF:          │              │
│    │   room_key = HKDF(password, room_salt)]      │              │
│    │                                              │              │
│    │─── {"cmd":"srp_verify","user_id","M"} ─────► │              │
│    │         (M = client proof)                   │              │
│    │                                              │              │
│    │◄──────── {"H_AMK","session_key"} ─────────── │              │
│    │         (H_AMK = server proof)               │              │
│    │                                              │              │
│    │  [password never transmitted]                │              │
│    │  [MITM can't derive session key]             │              │
│    │                                              │              │
├──────────────────────────────────────────────────────────────────┤
│                 E2E ENCRYPTED CHAT (same socket)                 │
├──────────────────────────────────────────────────────────────────┤
│    │                                              │              │
│    │◄─────── {"type":"init","messages","users"} ─ │              │
│    │                                              │              │
│  ┌─┴─┐                                        ┌──┴──┐            │
│  │ C │─ {"type":"message","text":encrypted} ─►│  S  │            │
│  │ L │                                        │  E  │            │
│  │ I │◄── {"type":"message","data":{...}} ────│  R  │            │
│  │ E │                                        │  V  │            │
│  │ N │◄── {"type":"user_joined",...} ─────────│  E  │            │
│  │ T │                                        │  R  │            │
│  │   │◄── {"type":"user_left",...} ───────────│     │            │
│  └─┬─┘                                        └──┬──┘            │
│    │                                              │              │
│    │  [server stores ONLY ciphertext]             │              │
│    │  [server CANNOT read messages]               │              │
│    │  [all clients with same password             │              │
│    │   derive identical room_key]                 │              │
│    │                                              │              │
│    │  Transport:    TLS 1.2+ (RSA-2048)           │              │
│    │  Encryption:   Fernet (AES-128-CBC + HMAC)   │              │
│    │  Key derivation: HKDF-SHA256                 │              │
│    │  Protocol: newline-delimited JSON over TLS   │              │
│    │                                              │              │
│    │  [on disconnect: keys wiped from RAM]        │              │
│    │                                              │              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      KEY HIERARCHY                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TLS cert ──────────────────────────────► transport encryption   │
│                                                                  │
│  password ──┬──► SRP ──► session_key (per-user, auth only)       │
│             │                                                    │
│             └──► HKDF(password, room_salt) ──► room_key (shared) │
│                                                                  │
│  room_salt: generated once at server start                       │
│  room_key:  deterministic, same for all clients with same pwd    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**TLS** — encrypts and authenticates the transport layer. the server auto-generates a self-signed certificate on startup; provide your own cert/key pair for production.

**SRP (Secure Remote Password)** — password is never sent over the network. both sides prove they know it via zero-knowledge proof, then derive identical session keys.

## install

quick start scripts:

```bash
./start.sh serve 0.0.0.0 3000 --password mysecret
./start.sh connect SERVER_IP 3000 username mysecret --no-verify
```

windows:

```bat
start.bat serve 0.0.0.0 3000 --password mysecret
start.bat connect SERVER_IP 3000 username mysecret --no-verify
```

the scripts create `venv`, install `requirements.txt` when needed, then run the chat command you pass in.

manual setup:

```bash
git clone https://github.com/emilycodestar/cmd-chat.git
cd cmd-chat
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

windows:

```bash
python -m venv venv ; .\venv\Scripts\activate ; pip install -r requirements.txt
```

## usage

### server

```bash
./start.sh serve 0.0.0.0 3000 --password mysecret
```

the server auto-generates a self-signed TLS certificate and prints it to stdout. to use it for client verification, save it:

```bash
./start.sh serve 0.0.0.0 3000 --password mysecret > server.crt
```

to use your own certificate and key:

```bash
./start.sh serve 0.0.0.0 3000 --password mysecret --cert /path/to/cert.pem --key /path/to/key.pem
```

### client

connect and skip certificate verification (quick/local use — transport is still encrypted):

```bash
./start.sh connect SERVER_IP 3000 username mysecret --no-verify
```

connect and verify the server's certificate (recommended for untrusted networks):

```bash
./start.sh connect SERVER_IP 3000 username mysecret --ca-cert server.crt
```

### tls flags reference

| flag | side | description |
|---|---|---|
| `--cert CERT_PEM` | server | path to TLS certificate (PEM). auto-generated if omitted |
| `--key KEY_PEM` | server | path to TLS private key (PEM). required when `--cert` is given |
| `--ca-cert CA_PEM` | client | path to server's certificate for verification |
| `--no-verify` | client | skip certificate verification (transport remains encrypted) |

![Example](example.gif)

## features

- **tls transport** — TLS 1.2+ on every connection, auto-generated self-signed cert
- **ram only** — nothing touches disk
- **pure sockets** — no http, no websocket, just raw tcp over tls
- **srp auth** — password never sent over network
- **e2e encryption** — Fernet (AES-128-CBC + HMAC)
- **zero dependencies on web frameworks** — only asyncio

## license

MIT

