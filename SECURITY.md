# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it via one of the following methods:

### Email
Send an email to **contact@voxhash.dev** with:
- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)

### Response Time
- We will acknowledge receipt of your report within **48 hours**
- We will provide a detailed response within **7 days**
- We will keep you informed of the progress toward a fix

### Disclosure Policy
- We will work with you to understand and resolve the issue quickly
- We will credit you for the discovery (if desired)
- We will not disclose the vulnerability publicly until a fix is available

## Security Best Practices

### For Users
- Keep your application updated to the latest version
- Use strong, unique passwords for server authentication
- Never share your authentication tokens
- Use SSL/TLS (WSS) in production environments
- Regularly review connection logs
- Use rate limiting to prevent abuse

### For Developers
- Never commit sensitive data (passwords, tokens, keys)
- Use environment variables for configuration
- Keep dependencies updated
- Review code changes for security implications
- Follow secure coding practices
- Don't expose stack traces to clients

## Security Considerations

This application handles sensitive data including:
- Authentication credentials (passwords, tokens)
- Encrypted message content
- RSA key pairs (generated client-side)
- Symmetric encryption keys

All data is stored in memory only and is wiped when the session ends. We recommend:
- Using strong passwords (minimum 16 characters)
- Rotating authentication tokens regularly
- Using SSL/TLS for production deployments
- Implementing proper firewall rules
- Monitoring for suspicious activity

## Security Features

### Encryption
- **RSA 2048-bit**: Used for secure key exchange
- **Fernet (AES-128)**: Used for message encryption
- **End-to-End**: Messages are encrypted before transmission

### Authentication
- **Token-based**: Secure token authentication with expiration
- **Password-based**: Password authentication (backward compatibility)
- **IP Binding**: Optional IP address binding for tokens

### Rate Limiting
- **Message Rate**: 10 messages per 60 seconds per user
- **Payload Size**: Maximum 10KB per message, 1MB per payload
- **Connection Limits**: Prevents resource exhaustion

### Error Handling
- **Clean Errors**: No stack traces or sensitive information exposed
- **Secure Logging**: No passwords or tokens in logs
- **Graceful Failures**: Secure error handling throughout

## Known Security Considerations

### Memory-Only Storage
- All data is stored in RAM only
- Data is wiped when server shuts down
- No persistent storage of messages or keys

### Key Exchange
- RSA public keys are sent to the server
- Symmetric keys are encrypted with RSA before transmission
- Keys are generated fresh for each session

### WebSocket Security
- Supports both WS (unencrypted) and WSS (encrypted)
- Use WSS in production environments
- Heartbeat mechanism prevents connection hijacking

## Security Updates

Security updates are released as soon as possible after a vulnerability is discovered and fixed. We recommend:
- Monitoring the repository for security updates
- Updating to the latest version promptly
- Reviewing CHANGELOG.md for security-related changes

## Contact

For security-related inquiries, contact: **contact@voxhash.dev**

