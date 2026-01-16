# Documentation Index

Welcome to the Darts Game Web Application documentation. This folder contains comprehensive guides for users, developers, and system architects.

## 📚 Documentation Files

### 1. **[INSTALLATION.md](INSTALLATION.md)** - Getting Started
**For:** New users and system administrators  
**Topics:**
- Quick start with Docker
- Local development setup
- Production deployment
- Database configuration
- Environment variables
- Troubleshooting

**Start here if you need to:**
- Install the application
- Set up development environment
- Deploy to production
- Configure services (RabbitMQ, PostgreSQL)

---

### 2. **[USER_GUIDE.md](USER_GUIDE.md)** - Using the Application
**For:** Players, game masters, and end users  
**Topics:**
- How to access the application
- User roles and permissions
- Playing games (301, 401, 501, Cricket)
- Submitting scores (RabbitMQ, API, Web)
- Game rules
- Real-time features
- Mobile support
- Keyboard shortcuts
- FAQ and tips

**Start here if you want to:**
- Understand user roles
- Learn how to play a game
- Submit scores
- Use the control panel
- Get help with features

---

### 3. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Development Reference
**For:** Software developers and engineers  
**Topics:**
- Development environment setup
- Project structure and organization
- Code conventions and standards
- Testing framework and practices
- Database migrations and models
- Authentication system architecture
- API development
- Git workflow
- Deployment checklist
- Common development tasks

**Start here if you want to:**
- Set up your development environment
- Understand the codebase structure
- Write new features
- Run tests and linting
- Make API changes
- Deploy the application

---

### 4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System Design
**For:** Architects, senior developers, and system designers  
**Topics:**
- High-level system architecture
- Core component descriptions
- Request flow diagrams
- Authentication flow
- Game state machines
- Deployment architecture
- Technology stack
- Scaling strategies
- Security architecture
- Performance metrics
- Monitoring setup

**Start here if you want to:**
- Understand system design
- Review architecture decisions
- Plan scalability
- Design new features
- Understand data flow
- Review security measures
- Set up monitoring

---

## 🚀 Quick Navigation

### I want to...

**Set up the application**
→ Read [INSTALLATION.md](INSTALLATION.md)

**Play a game**
→ Read [USER_GUIDE.md](USER_GUIDE.md)

**Start development**
→ Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

**Understand the system**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Understand a specific role**
→ [USER_GUIDE.md - User Roles](USER_GUIDE.md#user-roles)

**Set up the development environment**
→ [DEVELOPER_GUIDE.md - Environment Setup](DEVELOPER_GUIDE.md#development-environment-setup)

**Deploy to production**
→ [INSTALLATION.md - Production Deployment](INSTALLATION.md#production-deployment)

**Understand authentication**
→ [ARCHITECTURE.md - Authentication Flow](ARCHITECTURE.md#authentication-flow)

**Scale the system**
→ [ARCHITECTURE.md - Scaling Considerations](ARCHITECTURE.md#scaling-considerations)

---

## 📋 Quick Reference

### System Requirements
- **Python**: 3.10, 3.11, or 3.12
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 2GB
- **OS**: Linux, macOS, or Windows (WSL2)

### Default Ports
- Flask Application: **5000**
- PostgreSQL: **5432**
- RabbitMQ: **5672** (AMQP), **15672** (Management UI)
- Nginx: **80** (HTTP), **443** (HTTPS)
- WSO2 Identity Server: **9443**

### Key Commands

```bash
# Development
python run.py                    # Start development server
pytest                          # Run tests
tox -e lint                     # Run linting
black .                         # Format code
ruff check . --fix              # Auto-fix issues

# Docker
docker-compose up -d            # Start services
docker-compose down             # Stop services
docker-compose logs -f web      # View logs

# Database
alembic upgrade head            # Apply migrations
alembic revision --autogenerate # Create migration
```

### Game Types
- **301**: Start with 301 points, reach exactly 0
- **401**: Start with 401 points, reach exactly 0
- **501**: Start with 501 points, reach exactly 0
- **Cricket**: Hit 15-20 and bull, scoring strategy

### User Roles
- **Player 🟢**: View board, submit scores
- **Game Master 🟡**: Create games, manage players, control flow
- **Admin 🔴**: Full system access

---

## 🔗 External Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- [pytest Testing Framework](https://docs.pytest.org/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Docs](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [WSO2 Identity Server](https://wso2.com/identity-and-access-management/)

---

## 📝 Documentation Standards

- All paths are relative to project root
- Code examples use bash/python unless specified
- Configuration samples use environment variables
- Mermaid diagrams for visual concepts
- Tables for quick reference
- Troubleshooting sections for common issues

---

## 🤝 Contributing

When updating documentation:
1. Keep it current with codebase changes
2. Use consistent formatting
3. Include examples for complex topics
4. Add diagrams for architecture concepts
5. Update this index if adding new files

---

## 📞 Support

For issues or questions:
1. Check FAQ sections in respective guides
2. Review troubleshooting sections
3. Check system logs
4. Contact system administrator

---

**Last Updated**: 2025-11-27  
**Documentation Version**: 1.0.0  
**Application Version**: 1.0.0
