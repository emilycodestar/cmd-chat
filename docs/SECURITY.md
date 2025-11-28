# CMD CHAT - Security Quick Guide

## Implemented Security Improvements

### Applied Fixes (v0.2)

#### 1. Strengthened Cryptography
- RSA upgraded from 512 to 2048 bits
- AES-256 via Fernet for symmetric traffic
- Per-client symmetric keys to avoid data leakage across users

#### 2. Token System
- UUID v4 tokens with configurable expiration
- Default time to live: 24 hours
- Manual revocation endpoint
- Automatic cleanup of expired tokens
- Optional IP validation

#### 3. SSL/TLS (WSS)
- Full support for secure WebSockets
- SSL certificate configuration flags on the server
- Automatic ws:// vs wss:// detection on the client
- Certificate verification on the client

#### 4. Anti-DoS Protections
- 10 KB limit per outbound message
- 1 MB limit for inbound payloads
- Payload size validation before processing
- Oversized messages are rejected

#### 5. Error Handling
- Targeted try/except blocks for crypto operations
- 10 second timeout for network calls
- Clear error messages without leaking internals
- Validation of empty or malformed responses

#### 6. JSON Parsing
- `ast.literal_eval` replaced by `json.loads` / `json.dumps`
- Eliminates code injection risk
- Faster and standardized serialization
- Universally supported format

---

## Using the New Features

### Generate Test SSL Certificates (self-signed)

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Run the Server with SSL

```bash
python cmd_chat.py serve 0.0.0.0 1000 \
  --password "MySecurePassword123!" \
  --ssl-cert cert.pem \
  --ssl-key key.pem
```

### Connect a Client with SSL and Token

```bash
# Step 1: generate a token
curl -X POST https://your-server.com:1000/generate_token \
  -d "admin_password=MySecurePassword123!" \
  -d "username=alice" \
  -d "ttl=3600"  # seconds

# Step 2: connect using the token
python cmd_chat.py connect your-server.com 1000 alice \
  --token "550e8400-e29b-41d4-a716-446655440000" \
  --ssl
```

### Health Check

```bash
curl https://your-server.com:1000/health
```

Expected response:

```json
{
  "status": "healthy",
  "active_users": 5,
  "messages_count": 142,
  "active_tokens": 8
}
```

---

## Version Comparison

| Aspect | Before (v0.1) | After (v0.2) |
| --- | --- | --- |
| RSA | 512 bits | 2048 bits |
| Symmetric key | Shared by all | One per client |
| Authentication | Password only | Password or token |
| Protocol | WS only | WS and WSS |
| Parsing | `ast.literal_eval` | `json.loads` |
| Anti-DoS | none | size limits |
| Errors | generic | scoped and safe |
| Tokens | not available | UUID with TTL |
| Health check | not available | `/health` endpoint |
| SSL client checks | not available | certificate verification |

---

## Recommended Next Steps

For production-grade security:

1. Add IP based rate limiting
2. Implement heartbeat or ping/pong
3. Produce audit logs for critical events (no sensitive payloads)
4. Configure CORS rules for the REST API
5. Enforce firewall rules per IP range
6. Use Let's Encrypt or another trusted CA for SSL

---

## Best Practices

### Do
- Use SSL/TLS in production (WSS)
- Generate tokens with short TTL (1 to 24 hours)
- Revoke unused or leaked tokens
- Require strong admin passwords (16+ chars)
- Monitor `/health` regularly
- Restrict network access via firewall rules

### Do Not
- Expose passwords or tokens in source control
- Use self-signed certificates in production
- Share tokens publicly
- Disable SSL verification (`verify=False`)
- Use RSA shorter than 2048 bits
- Log decrypted chat payloads

---

## Environment Variables

Copy `.env.example` to `.env` and set:

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=1000
ADMIN_PASSWORD=your_secure_password_here
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
TOKEN_TTL=86400
```

---

Full documentation: README.MD  
Roadmap: ROADMAP.md
