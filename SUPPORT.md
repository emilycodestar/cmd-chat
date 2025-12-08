# Support

## Getting Help

We're here to help! Here are the best ways to get support for CMD CHAT.

## 📚 Documentation

Before asking for help, please check our documentation:
- [README.md](README.md) - Quick start and overview
- [ROADMAP.md](ROADMAP.md) - Planned features and improvements
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## 🐛 Reporting Issues

Found a bug or have a feature request?

1. **Search existing issues** to avoid duplicates
2. **Use the appropriate template**:
   - [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
   - [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
   - [Documentation Improvement](.github/ISSUE_TEMPLATE/docs_improvement.md)

3. **Provide detailed information**:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, app version)
   - Relevant logs or error messages

## 💬 Community Support

- **GitHub Discussions**: [Join the discussion](https://github.com/VoxHash/cmd-chat/discussions)
- **GitHub Issues**: [Report issues](https://github.com/VoxHash/cmd-chat/issues)

## 📧 Direct Contact

For direct support or security-related issues:
- **Email**: contact@voxhash.dev
- **Response Time**: We aim to respond within 48 hours

## 🤝 Contributing

Want to contribute? Check out our [Contributing Guide](CONTRIBUTING.md)!

## ⚠️ Important Notes

- **Security Issues**: Please report security vulnerabilities via email (contact@voxhash.dev) rather than public issues
- **Connection Issues**: For connection problems, check firewall settings and network configuration
- **Rate Limiting**: Be aware of rate limiting (10 messages per 60 seconds) when testing
- **Encryption**: All messages are encrypted end-to-end using RSA 2048-bit + Fernet

## 📋 Support Checklist

Before requesting support, please:
- [ ] Checked the documentation
- [ ] Searched existing issues
- [ ] Read the README
- [ ] Checked ROADMAP for planned features
- [ ] Provided all required information
- [ ] Included relevant logs or error messages
- [ ] Tested with latest version

## 🆘 Emergency Support

For critical issues affecting production use:
- Email: contact@voxhash.dev
- Subject: [URGENT] - Brief description
- Include: Full error logs, environment details, steps to reproduce

## 🔧 Common Issues

### Connection Problems

- **Check server is running**: Ensure the server is started before connecting clients
- **Verify port availability**: Make sure the port isn't blocked by firewall
- **Check authentication**: Verify password or token is correct
- **Network issues**: Check network connectivity between client and server

### Encryption Issues

- **Key exchange**: Ensure key exchange completes successfully
- **Message decryption**: Check that messages are being encrypted/decrypted correctly
- **RSA keys**: Verify RSA key generation is working

### Rate Limiting

- **Message limit**: Remember the limit is 10 messages per 60 seconds per user
- **Wait period**: Wait for the rate limit window to reset
- **Multiple users**: Each user has their own rate limit

## 📖 Quick Start Troubleshooting

1. **Server won't start**:
   - Check if port is already in use
   - Verify Python version (3.10+)
   - Check all dependencies are installed

2. **Client can't connect**:
   - Verify server IP and port
   - Check password/token is correct
   - Ensure firewall allows connection

3. **Messages not appearing**:
   - Check encryption is working
   - Verify WebSocket connection is active
   - Check rate limiting hasn't been exceeded

---

**Made with ❤️ by [VoxHash Technologies](https://voxhash.dev)**

