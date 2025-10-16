# 🚀 Backup Quick Reference

## 📦 Current Backup

**Location:** `./docker-backups/2025-10-14_18-02-07`  
**Size:** 851 MB  
**Date:** October 14, 2025

---

## ⚡ Quick Commands

### Create New Backup
```bash
./backup_docker_volumes.sh --yes
```

### View Backup Contents
```bash
ls -lh ./docker-backups/2025-10-14_18-02-07/
```

### View Restore Instructions
```bash
cat ./docker-backups/2025-10-14_18-02-07/BACKUP_MANIFEST.txt
```

---

## 🔄 Quick Restore Commands

### Restore PostgreSQL Database
```bash
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d postgres
gunzip -c ./docker-backups/2025-10-14_18-02-07/postgres_dump.sql.gz | \
  docker exec -i darts-postgres psql -U postgres dartsdb
docker-compose -f docker-compose.yml up -d
```

### Restore WSO2 IS Volume
```bash
docker-compose -f docker-compose-wso2.yml down
docker volume rm dartserver-pythonapp_wso2is_data
docker volume create dartserver-pythonapp_wso2is_data
docker run --rm \
  -v dartserver-pythonapp_wso2is_data:/data \
  -v $(pwd)/docker-backups/2025-10-14_18-02-07:/backup \
  alpine tar xzf /backup/wso2is_data.tar.gz -C /data
docker-compose -f docker-compose-wso2.yml up -d
```

---

## 📊 What's Backed Up

| Item | File | Size |
|------|------|------|
| PostgreSQL DB (dump) | `postgres_dump.sql.gz` | 8.0 KB |
| PostgreSQL Volume | `postgres_data.tar.gz` | 6.9 MB |
| RabbitMQ Volume | `rabbitmq_data.tar.gz` | 136 KB |
| WSO2 IS Volume | `wso2is_data.tar.gz` | 392 MB |
| WSO2 APIM Volume | `wso2apim_data.tar.gz` | 453 MB |
| Configuration Files | `config/` | Various |

---

## ✅ Ready for Upgrade

You can now safely proceed with the WSO2 IS 7.1.0 upgrade!

```bash
./upgrade_wso2_to_7.sh
```

See `WSO2_IS_UPGRADE_GUIDE.md` for detailed instructions.