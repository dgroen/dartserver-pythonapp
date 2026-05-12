# Changelog - dartserver-games

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-27

### Added
- Initial release with game implementations extracted from monolith
- BaseGame abstract class providing consistent game interface
- 5 game types: 301, 401, 501, Cricket, Round the Clock, Bull Practice
- Configurable game rules (double-out, reset-on-miss, etc)
- Game state serialization for display and replay
- GameFactory for dynamic game creation
- Comprehensive game tests (900+ LOC)
- Full documentation and game rules

### Games
- **301/401/501**: Count-down games with configurable finish rules
- **Cricket**: Target-based game with marking system
- **Round the Clock**: Sequential number targeting (1-20, bull)
- **Bull Practice**: Bull-focused training game

### Features
- Per-round score tracking
- Multi-player support (2+ players)
- Dynamic player management
- Game state broadcast capability
- Rule engine with configurable options

## [Unreleased]

### Planned
- Throw-level statistics tracking
- Advanced scoring rules
- Tournament mode
- Game replay/analysis tools
