# Changelog

All notable changes to the CMD CHAT project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.1] - 2025-12-08

### Fixed
- **Room-Based Encryption**: Fixed critical issue where users in the same room couldn't read each other's messages
- **Key Sharing**: Changed from per-client keys to room-based keys - all clients in the same room now share the same encryption key
- **Room Key Refresh**: Clients now automatically request new room key when switching rooms
- **Decryption Errors**: Added graceful error handling to skip messages that can't be decrypted (e.g., from old sessions)

### Changed
- **Key Exchange**: Server now sends room keys instead of per-client keys during key exchange
- **Key Request**: Client now passes room_id in both URL query string and POST data for reliability

### Technical
- **Server**: Modified `/get_key` endpoint to return room key instead of per-client key
- **Client**: Updated key request to include room_id parameter
- **Renderers**: Added try-except blocks to gracefully handle decryption failures

## [3.2.0] - 2025-12-08

### Added
- **Server Connection Info**: Server now displays IP address and connection instructions on startup
- **Room-Based User Filtering**: Users list now filtered by room to show only users in the same room
- **Enhanced Translations**: Updated all 13 language files with missing keys (welcome_message, welcome_instructions, current_room, rooms_list, no_rooms_available)
- **Improved Command Help**: All languages now include /rooms command in help text

### Changed
- **Server Startup**: Enhanced server startup message with connection details
- **Message Routing**: Improved room-based message filtering to ensure users only see messages from their room
- **Translation Files**: All translation files synchronized with English template

### Fixed
- **Windows Shutdown**: Fixed BrokenPipeError during server shutdown on Windows
- **Server Shutdown**: Added graceful shutdown with 'q' command and improved Ctrl+C handling
- **Message Routing**: Fixed user list to show only users in the same room
- **Message Decryption**: Fixed AttributeError when decrypting messages (extract text from dict before decrypting)
- **Welcome Message**: Welcome message now persists until /clear command is used

### Technical
- **Server**: Added connection info display with local IP detection
- **Services**: Enhanced message payload generation to filter users by room
- **Error Handling**: Improved Windows-specific error handling for graceful shutdown

## [3.1.0] - 2025-12-07

### Added
- **Internationalization (i18n)**: Complete translation system with 13 supported languages
  - English (en), French (fr), Spanish (es), Chinese (zh), Japanese (ja)
  - German (de), Russian (ru), Estonian (et), Portuguese (pt), Korean (ko)
  - Catalan (ca), Basque (eu), Galician (gl)
- **Language Selection**: CLI option `--language` to select interface language
- **Environment Variable Support**: `CMD_CHAT_LANGUAGE` environment variable for language selection
- **Translation Manager**: Centralized translation system with fallback to English
- **Comprehensive Translations**: All UI strings translated across all languages

### Changed
- **Client UI**: All user-facing strings now use translation system
- **CLI**: Added `--language` / `-l` option for language selection
- **Configuration**: Updated .env.example with language configuration

### Technical
- **Translation Files**: JSON-based translation files in `cmd_chat/client/i18n/locales/`
- **Translation Manager**: Automatic fallback to English for missing translations
- **Key Validation**: All languages have identical translation keys

## [3.0.0] - 2025-12-07

### Added
- **Per-Client Symmetric Keys**: Each client now gets a unique symmetric encryption key instead of a shared global key
- **Multiple Rooms Support**: Full room/channel support with room_id parameter for isolated chat spaces
- **Chat Commands**: Command system with `/nick`, `/clear`, `/help`, `/quit`, and `/room` commands
- **Message Timestamps**: All messages now include timestamps for chronological ordering
- **Sequence Numbers**: Messages include sequence numbers for reliable delta updates
- **Delta Updates**: Only new messages are sent to clients (not full history) for better performance
- **Local Encrypted History**: Optional local message history storage (encrypted, configurable)
- **Customizable Renderers**: Three renderer modes - rich (default), minimal, and json (for automation)
- **Quiet Reconnection Status**: Subtle reconnection indicators that don't clutter the UI
- **Configurable Message Buffer**: Adjustable message buffer length via environment variables
- **Force SSL/TLS**: Option to enforce WSS (TLS) connections in production environments
- **Room-Based Key Management**: Each room has its own encryption key for better security isolation

### Changed
- **Key Exchange**: Now generates per-client keys instead of shared room keys
- **Message Model**: Enhanced with timestamp, sequence, room_id, and username fields
- **Update Payload**: Supports delta updates with last_sequence parameter
- **Client Architecture**: Refactored to support multiple renderer modes and room switching
- **Server Endpoints**: Enhanced to support room_id and sequence-based updates

### Fixed
- **Security**: Per-client keys prevent cross-client message decryption
- **Performance**: Delta updates reduce bandwidth and improve responsiveness
- **User Experience**: Better command handling and room management

### Technical
- **Server**: Room management, per-client key generation, command processing
- **Client**: Renderer abstraction, local history, delta update tracking
- **CLI**: Added --room, --renderer, and --force-ssl options

## [2.0.0] - 2025-12-07

### Added
- **Heartbeat/Ping-Pong Mechanism**: Automatic connection health monitoring with 30s interval and 60s timeout
- **Rate Limiting**: Built-in anti-spam protection (10 messages per 60 seconds per user)
- **Clean Error Handling**: No stack traces exposed to clients, secure error messages
- **Token-Based Authentication**: Secure token authentication system with expiration
- **Comprehensive Test Suite**: Tests for security, rate limiting, error handling, heartbeat, and JSON parsing
- **CI/CD Workflows**: GitHub Actions for multi-platform testing and automated releases
- **Documentation**: Complete README.md with usage examples and configuration
- **Configuration Files**: .env.example with all configuration options
- **Message Size Limits**: 10KB per message, 1MB payload limit

### Changed
- **JSON Message Parsing**: All messages now use JSON (replacing any ast.literal_eval usage)
- **RSA Key Size**: Using RSA 2048-bit encryption (upgraded from 512-bit)
- **Error Messages**: Clean, user-friendly error messages without exposing internal details
- **Dependencies**: Updated all dependencies with version constraints
- **Project Metadata**: Updated setup.py with VoxHash Technologies information

### Fixed
- **Security**: Cleaned error handling to prevent information leakage
- **Connection Stability**: Improved reconnection handling with heartbeat mechanism
- **Rate Limiting**: Implemented proper message rate limiting to prevent abuse
- **Documentation**: Comprehensive documentation and examples

### Technical
- **Server**: Enhanced WebSocket endpoints with heartbeat support
- **Client**: Added heartbeat response handling and reconnection logic
- **Testing**: Comprehensive test coverage for all new features
- **CI/CD**: Automated testing across Ubuntu, Windows, and macOS with Python 3.10-3.12

## [1.0.0] - Initial Release

### Added
- **Initial Release**: First stable release of CMD CHAT
- **End-to-End Encryption**: RSA + Fernet symmetric encryption
- **Memory-Only Storage**: All data stored in RAM, wiped on exit
- **WebSocket Communication**: Real-time chat via WebSocket connections
- **Multi-Client Support**: Support for multiple concurrent clients
- **Token Authentication**: Token-based authentication system
- **SSL/TLS Support**: Optional SSL/TLS encryption for secure connections
- **Health Check Endpoint**: Server health monitoring endpoint

### Technical Details
- **Language**: Python 3.10+
- **Server Framework**: Sanic
- **Encryption**: RSA 2048-bit + Fernet
- **Communication**: WebSocket (ws:// and wss://)
- **Architecture**: Client-server with in-memory message storage

---

## Contributing to the Changelog

When adding new entries to this changelog:

1. **Follow the format**: Use the established format for consistency
2. **Be descriptive**: Provide clear descriptions of changes
3. **Categorize properly**: Use the correct categories (Added, Changed, Fixed, Removed, Security)
4. **Include details**: Add relevant technical details
5. **Link issues**: Reference related issues and pull requests
6. **Version correctly**: Use semantic versioning
7. **Date entries**: Include release dates
8. **Group changes**: Group related changes together
9. **Be concise**: Keep entries concise but informative
10. **Review carefully**: Review entries for accuracy and completeness

## Changelog Maintenance

This changelog is maintained by the development team and community contributors. It should be updated with every release to provide users with a clear understanding of what has changed.

For questions about the changelog or to suggest improvements, please open an issue or pull request on the GitHub repository.

