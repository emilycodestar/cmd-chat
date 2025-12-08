# Contributing to CMD CHAT

Thank you for your interest in contributing to CMD CHAT! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:
1. Check if the issue already exists
2. Search through closed issues
3. Verify you're using the latest version

When creating an issue, please include:
- **Clear title**: Brief description of the issue
- **Description**: Detailed explanation of the problem
- **Steps to reproduce**: How to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, app version
- **Logs**: Relevant error messages or logs

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature already exists
2. Search through existing feature requests
3. Provide a clear description
4. Explain the use case and benefits
5. Consider implementation complexity

### Code Contributions

#### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/cmd-chat.git
   cd cmd-chat
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up pre-commit hooks** (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**:
   ```bash
   python test/run_all_tests.py
   # Or run individual tests
   python test/test_security.py
   ```

4. **Check code style**:
   ```bash
   # Format code (if using black)
   black cmd_chat/
   
   # Lint code (if using flake8)
   flake8 cmd_chat/
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: Brief description of changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

#### Pull Request Guidelines

- **Clear title**: Describe what the PR does
- **Detailed description**: Explain the changes and why
- **Reference issues**: Link to related issues
- **Tests**: Ensure all tests pass
- **Documentation**: Update docs if needed
- **Breaking changes**: Clearly mark any breaking changes

## 📋 Development Guidelines

### Code Style

We follow Python PEP 8 style guidelines:
- Use 4 spaces for indentation
- Maximum line length: 120 characters
- Use type hints where appropriate
- Write docstrings for functions and classes

### Project Structure

```
cmd_chat/
├── cmd_chat/
│   ├── client/          # Client-side code
│   │   ├── core/        # Core client functionality
│   │   └── config.py    # Client configuration
│   └── server/          # Server-side code
│       ├── auth.py      # Authentication
│       ├── models.py    # Data models
│       ├── server.py    # Server implementation
│       └── services.py  # Server services
├── test/                # Test files
├── .github/             # GitHub workflows and templates
└── docs/                # Documentation
```

### Architecture Principles

- **Clean Code**: Write readable, maintainable code
- **Error Handling**: Comprehensive error handling without exposing internals
- **Security First**: Security considerations in all code changes
- **Testing**: Unit and integration tests for new features
- **Documentation**: Update documentation with code changes

## 🧪 Testing

### Test Structure

```
test/
├── test_security.py         # Security tests
├── test_error_handling.py   # Error handling tests
├── test_heartbeat.py        # Heartbeat tests
├── test_json_parsing.py     # JSON parsing tests
├── test_rate_limiting.py    # Rate limiting tests
└── run_all_tests.py         # Test runner
```

### Writing Tests

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **Security tests**: Test security features
- **Coverage**: Aim for high test coverage

### Running Tests

```bash
# Run all tests
python test/run_all_tests.py

# Run specific test
python test/test_security.py
```

## 📚 Documentation

### Documentation Standards

- **Clear and concise**: Write clear, easy-to-understand documentation
- **Examples**: Include code examples
- **Up-to-date**: Keep documentation current
- **Comprehensive**: Cover all aspects of the project

### Types of Documentation

- **API Documentation**: Function and class documentation
- **User Guide**: End-user documentation
- **Developer Guide**: Developer documentation
- **README**: Project overview and quick start
- **CHANGELOG**: Version history and changes

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues**: Search for similar issues
2. **Update to latest version**: Ensure you're using the latest version
3. **Check documentation**: Review relevant documentation
4. **Test in clean environment**: Test in a fresh installation

### Bug Report Template

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Start server with '...'
2. Connect client with '....'
3. Send message '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Environment:**
- OS: [e.g. Windows 10, macOS 12, Ubuntu 20.04]
- Python Version: [e.g. 3.10.0]
- App Version: [e.g. 2.0.0]

**Logs**
Please include relevant log entries or error messages.
```

## ✨ Feature Requests

### Before Requesting

1. **Check existing features**: Ensure the feature doesn't already exist
2. **Search requests**: Look for similar feature requests
3. **Consider alternatives**: Think about workarounds
4. **Assess complexity**: Consider implementation complexity

### Feature Request Template

```markdown
**Feature Description**
A clear and concise description of the feature you'd like to see.

**Use Case**
Describe the use case and how this feature would be beneficial.

**Proposed Solution**
A clear and concise description of what you want to happen.

**Alternatives**
Describe any alternative solutions or features you've considered.
```

## 🔒 Security

### Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public issue
2. Email us at contact@voxhash.dev
3. Include detailed information about the vulnerability
4. Allow time for us to address the issue before disclosure

### Security Guidelines

- **Input validation**: Always validate user input
- **Authentication**: Implement proper authentication
- **Error handling**: Don't expose sensitive information in errors
- **Encryption**: Use proper encryption for sensitive data
- **Rate limiting**: Implement rate limiting to prevent abuse

## 📝 Commit Messages

### Commit Message Format

```
type(scope): brief description

Detailed description of changes

Closes #123
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Test changes
- **chore**: Maintenance tasks
- **security**: Security improvements

### Examples

```
feat(server): add heartbeat mechanism

Add heartbeat/ping-pong mechanism for connection stability.
Includes server-side ping sending and client-side pong handling.

Closes #45
```

```
fix(client): resolve reconnection issue

Fix issue where clients would fail to reconnect after connection loss.
Updated reconnection logic with exponential backoff.

Fixes #67
```

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers updated
- [ ] Release notes prepared
- [ ] Builds tested
- [ ] Release created

## 🤔 Questions?

If you have questions about contributing:

- **GitHub Discussions**: Use GitHub Discussions for general questions
- **Issues**: Create an issue for specific problems
- **Email**: Contact us at contact@voxhash.dev

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- **README**: Listed in the contributors section
- **Release Notes**: Mentioned in relevant releases
- **Changelog**: Credited for their contributions

Thank you for contributing to CMD CHAT! 🎉

