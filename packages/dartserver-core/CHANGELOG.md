# Changelog - dartserver-core

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-27

### Added
- Initial release with core functionality extracted from monolith
- OAuth2/OIDC authentication with WSO2 Identity Server
- Configuration management with environment-aware settings
- SQLAlchemy ORM models for players, games, and scores
- Database service with session management
- Role-based access control (login_required, role_required, permission_required decorators)
- 17 public exports for all core functionality
- Comprehensive test suite (400+ LOC)
- Full documentation and API reference

### Features
- WSO2 IS integration with token refresh
- Multi-environment support (dev, staging, production)
- Secure session cookie configuration
- Database transaction management
- User role and permission system

### Security
- Session cookie HTTP-only flag enabled
- SameSite cookie policy set to 'Lax'
- Secure cookie flag for HTTPS
- Permission-based access control

## [Unreleased]

### Planned
- OIDC provider abstraction (support multiple providers)
- Token revocation mechanisms
- Enhanced audit logging
