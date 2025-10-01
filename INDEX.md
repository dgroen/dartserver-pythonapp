# 📚 Documentation Index

Welcome to the Darts Game Application documentation! This index will help you find what you need quickly.

---

## 🚀 Getting Started (Start Here!)

### New Users
1. **[GET_STARTED.md](GET_STARTED.md)** ⭐ START HERE
   - Installation options
   - Your first game
   - Common tasks
   - Troubleshooting

2. **[QUICKSTART.md](QUICKSTART.md)**
   - Quick reference
   - Installation steps
   - Testing guide
   - Example game flows

### Verification
- **[verify_installation.py](verify_installation.py)**
  - Run: `python verify_installation.py`
  - Checks: Python, packages, files, RabbitMQ

---

## 📖 Complete Documentation

### Main Documentation
- **[README.md](README.md)**
  - Complete feature documentation
  - Installation guide
  - Configuration
  - API reference
  - Troubleshooting

### Feature Overview
- **[SUMMARY.md](SUMMARY.md)**
  - Feature highlights
  - Project structure
  - Message formats
  - Customization guide

### System Architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)**
  - System design
  - Data flow diagrams
  - Component details
  - Deployment architecture
  - Scalability considerations

---

## 🧪 Testing & Examples

### Testing Tools
- **[test_rabbitmq.py](test_rabbitmq.py)**
  - RabbitMQ message testing
  - Send test scores
  - Continuous mode
  - Custom scores

### Code Examples
- **[examples/api_examples.py](examples/api_examples.py)**
  - REST API usage
  - Game management
  - Player management
  - Complete workflows

- **[examples/websocket_client.py](examples/websocket_client.py)**
  - WebSocket communication
  - Real-time events
  - Interactive mode
  - Game control

### Integration
- **[bridge_nodejs_to_rabbitmq.js](bridge_nodejs_to_rabbitmq.js)**
  - Bridge Node.js to RabbitMQ
  - Integration example
  - Message forwarding

---

## 🔧 Configuration & Setup

### Configuration Files
- **[.env.example](.env.example)**
  - Environment variables template
  - RabbitMQ settings
  - Flask settings

- **[requirements.txt](requirements.txt)**
  - Python dependencies
  - Package versions

### Deployment
- **[Dockerfile](Dockerfile)**
  - Container definition
  - Build instructions

- **[docker-compose.yml](docker-compose.yml)**
  - Multi-container setup
  - RabbitMQ + Application
  - Volume configuration

- **[run.sh](run.sh)**
  - Quick start script
  - Auto-setup
  - Virtual environment

---

## 💻 Source Code

### Core Application
- **[app.py](app.py)**
  - Main Flask application
  - REST API routes
  - WebSocket handlers
  - RabbitMQ consumer thread

- **[game_manager.py](game_manager.py)**
  - Game state management
  - Player management
  - Turn coordination
  - Event emission

- **[rabbitmq_consumer.py](rabbitmq_consumer.py)**
  - RabbitMQ connection
  - Message consumption
  - Error handling
  - Auto-reconnection

### Game Logic
- **[games/game_301.py](games/game_301.py)**
  - 301/401/501 implementation
  - Score calculation
  - Bust detection
  - Win detection

- **[games/game_cricket.py](games/game_cricket.py)**
  - Cricket implementation
  - Target tracking
  - Opening/closing logic
  - Scoring rules

### Web Interface
- **[templates/index.html](templates/index.html)**
  - Game board UI
  - Player display
  - Score display
  - Real-time updates

- **[templates/control.html](templates/control.html)**
  - Control panel UI
  - Game setup
  - Player management
  - Manual score entry

- **[static/css/style.css](static/css/style.css)**
  - Game board styling
  - Responsive design
  - Animations

- **[static/css/control.css](static/css/control.css)**
  - Control panel styling
  - Form styling

- **[static/js/main.js](static/js/main.js)**
  - Game board JavaScript
  - WebSocket client
  - UI updates

- **[static/js/control.js](static/js/control.js)**
  - Control panel JavaScript
  - Form handling
  - API calls

---

## 📋 Quick Reference

### By Task

**I want to...**

- **Get started quickly**
  → [GET_STARTED.md](GET_STARTED.md)

- **Install the application**
  → [QUICKSTART.md](QUICKSTART.md) → Installation section

- **Understand the architecture**
  → [ARCHITECTURE.md](ARCHITECTURE.md)

- **Test RabbitMQ integration**
  → [test_rabbitmq.py](test_rabbitmq.py)

- **Use the REST API**
  → [examples/api_examples.py](examples/api_examples.py)

- **Use WebSocket**
  → [examples/websocket_client.py](examples/websocket_client.py)

- **Integrate with Node.js**
  → [bridge_nodejs_to_rabbitmq.js](bridge_nodejs_to_rabbitmq.js)

- **Configure the application**
  → [.env.example](.env.example)

- **Deploy with Docker**
  → [docker-compose.yml](docker-compose.yml)

- **Add a new game mode**
  → [ARCHITECTURE.md](ARCHITECTURE.md) → Extension Points

- **Troubleshoot issues**
  → [GET_STARTED.md](GET_STARTED.md) → Troubleshooting

- **Verify installation**
  → [verify_installation.py](verify_installation.py)

---

## 📊 By User Type

### End Users
1. [GET_STARTED.md](GET_STARTED.md) - Setup and play
2. [QUICKSTART.md](QUICKSTART.md) - Quick reference
3. Web UI - http://localhost:5000

### Developers
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [examples/](examples/) - Code examples
3. Source code - [app.py](app.py), [game_manager.py](game_manager.py)

### System Integrators
1. [README.md](README.md) - API documentation
2. [examples/api_examples.py](examples/api_examples.py) - API usage
3. [bridge_nodejs_to_rabbitmq.js](bridge_nodejs_to_rabbitmq.js) - Integration

### DevOps
1. [docker-compose.yml](docker-compose.yml) - Deployment
2. [Dockerfile](Dockerfile) - Container build
3. [.env.example](.env.example) - Configuration

---

## 🎯 By Topic

### Installation & Setup
- [GET_STARTED.md](GET_STARTED.md)
- [QUICKSTART.md](QUICKSTART.md)
- [verify_installation.py](verify_installation.py)
- [run.sh](run.sh)

### Game Rules & Logic
- [SUMMARY.md](SUMMARY.md) → Game Rules
- [games/game_301.py](games/game_301.py)
- [games/game_cricket.py](games/game_cricket.py)

### API & Integration
- [README.md](README.md) → API Reference
- [examples/api_examples.py](examples/api_examples.py)
- [examples/websocket_client.py](examples/websocket_client.py)
- [bridge_nodejs_to_rabbitmq.js](bridge_nodejs_to_rabbitmq.js)

### RabbitMQ
- [rabbitmq_consumer.py](rabbitmq_consumer.py)
- [test_rabbitmq.py](test_rabbitmq.py)
- [ARCHITECTURE.md](ARCHITECTURE.md) → RabbitMQ section

### Deployment
- [docker-compose.yml](docker-compose.yml)
- [Dockerfile](Dockerfile)
- [.env.example](.env.example)

### Customization
- [SUMMARY.md](SUMMARY.md) → Customization
- [ARCHITECTURE.md](ARCHITECTURE.md) → Extension Points

---

## 📏 Document Sizes

| Document | Size | Reading Time |
|----------|------|--------------|
| GET_STARTED.md | 7.2 KB | 10 min |
| QUICKSTART.md | 4.5 KB | 5 min |
| README.md | 6.0 KB | 8 min |
| SUMMARY.md | 7.8 KB | 10 min |
| ARCHITECTURE.md | 14.7 KB | 20 min |

**Total Documentation:** ~40 KB, ~50 minutes reading time

---

## 🎓 Learning Path

### Beginner Path
1. ✅ Read [GET_STARTED.md](GET_STARTED.md) (10 min)
2. ✅ Run `python verify_installation.py` (1 min)
3. ✅ Start application: `docker-compose up` (2 min)
4. ✅ Open http://localhost:5000 and play (5 min)
5. ✅ Try [test_rabbitmq.py](test_rabbitmq.py) (5 min)

**Total:** ~25 minutes to first game

### Intermediate Path
1. ✅ Complete Beginner Path
2. ✅ Read [QUICKSTART.md](QUICKSTART.md) (5 min)
3. ✅ Try [examples/api_examples.py](examples/api_examples.py) (10 min)
4. ✅ Try [examples/websocket_client.py](examples/websocket_client.py) (10 min)
5. ✅ Read [SUMMARY.md](SUMMARY.md) (10 min)

**Total:** ~60 minutes to full understanding

### Advanced Path
1. ✅ Complete Intermediate Path
2. ✅ Read [ARCHITECTURE.md](ARCHITECTURE.md) (20 min)
3. ✅ Study source code (30 min)
4. ✅ Implement custom game mode (60 min)
5. ✅ Deploy to production (30 min)

**Total:** ~3 hours to mastery

---

## 🔍 Search Tips

### Find by Keyword

**Installation:**
- GET_STARTED.md
- QUICKSTART.md
- verify_installation.py

**Configuration:**
- .env.example
- docker-compose.yml
- README.md

**API:**
- README.md → API Reference
- examples/api_examples.py

**RabbitMQ:**
- rabbitmq_consumer.py
- test_rabbitmq.py
- ARCHITECTURE.md

**Game Logic:**
- games/game_301.py
- games/game_cricket.py
- SUMMARY.md

**Troubleshooting:**
- GET_STARTED.md → Troubleshooting
- verify_installation.py

---

## 📞 Quick Help

**Can't find what you need?**

1. Check this index
2. Use your editor's search (Ctrl+F)
3. Run `grep -r "keyword" *.md`
4. Check the examples/ directory
5. Review the source code comments

---

## 🎯 Most Important Files

### Must Read (Start Here)
1. ⭐ **[GET_STARTED.md](GET_STARTED.md)** - Your first stop
2. ⭐ **[QUICKSTART.md](QUICKSTART.md)** - Quick reference

### Core Documentation
3. **[README.md](README.md)** - Complete guide
4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design

### Essential Tools
5. **[verify_installation.py](verify_installation.py)** - Check setup
6. **[test_rabbitmq.py](test_rabbitmq.py)** - Test messaging

---

**Happy Reading! 📚**

*Start with [GET_STARTED.md](GET_STARTED.md) and you'll be playing darts in minutes!*