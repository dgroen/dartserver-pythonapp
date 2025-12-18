# Changelog - dartserver-services

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-27

### Added
- Initial release with services extracted from monolith
- RabbitMQ message consumer with auto-reconnection
- Text-to-Speech service with dual engines (pyttsx3, gTTS)
- Dartboard GPIO mapping and score calculation service
- Mobile API management with key rotation
- Event-based callback pattern for circular dependency resolution
- 5 public exports with clean service APIs
- Comprehensive service tests (380+ LOC)
- Full documentation and configuration guides

### Services
- **RabbitMQConsumer**: Asynchronous score ingestion with heartbeat
- **TTSService**: Multi-language speech synthesis with audio streaming
- **DartboardService**: GPIO pin mapping and zone validation
- **MobileService**: Device registration and hotspot management

### Features
- Auto-reconnection with exponential backoff
- 12+ language support for TTS
- Bulk dartboard mapping import
- API key management with expiration
- Device configuration persistence

## [Unreleased]

### Planned
- MQTT protocol support (alternative to RabbitMQ)
- Advanced TTS voice selection
- Dartboard calibration tools
- Mobile analytics collection
