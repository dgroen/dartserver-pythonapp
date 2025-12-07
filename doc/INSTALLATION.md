# Installation Guide

## Quick Start with Docker

```bash
git clone <repository-url>
cd dartserver-pythonapp
cp .env.example .env
docker-compose -f docker-compose-wso2.yml up -d
```

Services: http://localhost:5000

## Local Development

1. **Python Environment**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **RabbitMQ**
   ```bash
   sudo systemctl start rabbitmq-server
   ```

3. **Configure**
   ```bash
   cp .env.example .env
   ```

4. **Run**
   ```bash
   python run.py
   ```

## Production

See DEVELOPER_GUIDE.md for production setup with Nginx and Systemd.
