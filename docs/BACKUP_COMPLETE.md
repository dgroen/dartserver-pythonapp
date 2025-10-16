# ✅ Docker Volumes Backup Complete

## 📦 Backup Summary

**Backup Date:** October 14, 2025 at 18:02 UTC  
**Backup Location:** `./docker-backups/2025-10-14_18-02-07`  
**Total Size:** 851 MB

---

## 📊 What Was Backed Up

### 1. **PostgreSQL Database** ✓
- **Method:** pg_dump (SQL dump)
- **File:** `postgres_dump.sql.gz`
- **Size:** 8.0 KB
- **Database:** dartsdb
- **Status:** ✅ Successfully backed up

### 2. **PostgreSQL Volume** ✓
- **Volume:** `dartserver-pythonapp_postgres_data`
- **File:** `postgres_data.tar.gz`
- **Size:** 6.9 MB
- **Status:** ✅ Successfully backed up

### 3. **RabbitMQ Volume** ✓
- **Volume:** `dartserver-pythonapp_rabbitmq_data`
- **File:** `rabbitmq_data.tar.gz`
- **Size:** 136 KB
- **Status:** ✅ Successfully backed up

### 4. **WSO2 Identity Server Volume** ✓
- **Volume:** `dartserver-pythonapp_wso2is_data`
- **File:** `wso2is_data.tar.gz`
- **Size:** 392 MB
- **Status:** ✅ Successfully backed up

### 5. **WSO2 API Manager Volume** ✓
- **Volume:** `dartserver-pythonapp_wso2apim_data`
- **File:** `wso2apim_data.tar.gz`
- **Size:** 453 MB
- **Status:** ✅ Successfully backed up

### 6. **Configuration Files** ✓
Backed up in `config/` directory:
- ✅ `wso2is-deployment.toml` - WSO2 IS configuration
- ✅ `docker-compose-wso2.yml` - Docker Compose configuration
- ✅ `.env` - Environment variables
- ✅ `nginx/` - Nginx reverse proxy configuration

---

## 📁 Backup Structure

```
docker-backups/2025-10-14_18-02-07/
├── BACKUP_MANIFEST.txt          # Detailed backup manifest with restore instructions
├── postgres_dump.sql.gz         # PostgreSQL database dump (RECOMMENDED for restore)
├── postgres_data.tar.gz         # PostgreSQL volume backup
├── rabbitmq_data.tar.gz         # RabbitMQ volume backup
├── wso2is_data.tar.gz          # WSO2 IS volume backup
├── wso2apim_data.tar.gz        # WSO2 API Manager volume backup
└── config/                      # Configuration files
    ├── .env
    ├── docker-compose-wso2.yml
    ├── wso2is-deployment.toml
    └── nginx/
```

---

## 🔄 How to Restore

### Option 1: Restore PostgreSQL Database (RECOMMENDED)

This is the **recommended** method for PostgreSQL as it's cleaner and more reliable:

```bash
# 1. Stop containers
docker-compose -f docker-compose.yml down

# 2. Start only PostgreSQL
docker-compose -f docker-compose.yml up -d postgres

# 3. Restore database
gunzip -c ./docker-backups/2025-10-14_18-02-07/postgres_dump.sql.gz | \
  docker exec -i darts-postgres psql -U postgres dartsdb

# 4. Start all containers
docker-compose -f docker-compose.yml up -d
```

### Option 2: Restore Docker Volumes

For restoring any volume (including WSO2 IS, WSO2 APIM, RabbitMQ):

```bash
# Example: Restore WSO2 IS volume

# 1. Stop containers
docker-compose -f docker-compose-wso2.yml down

# 2. Remove old volume
docker volume rm dartserver-pythonapp_wso2is_data

# 3. Create new volume
docker volume create dartserver-pythonapp_wso2is_data

# 4. Restore from backup
docker run --rm \
  -v dartserver-pythonapp_wso2is_data:/data \
  -v $(pwd)/docker-backups/2025-10-14_18-02-07:/backup \
  alpine \
  tar xzf /backup/wso2is_data.tar.gz -C /data

# 5. Start containers
docker-compose -f docker-compose-wso2.yml up -d
```

---

## 📝 Backup Script Usage

The backup script is located at: `./backup_docker_volumes.sh`

### Run Backup Interactively
```bash
./backup_docker_volumes.sh
```

### Run Backup Automatically (No Prompts)
```bash
./backup_docker_volumes.sh --yes
```

### Show Help
```bash
./backup_docker_volumes.sh --help
```

---

## 🎯 Key Features

1. **Dual Backup Strategy for PostgreSQL**
   - SQL dump (pg_dump) - Best for database restore
   - Volume backup - Complete data directory backup

2. **Automatic Container Detection**
   - Finds PostgreSQL container regardless of naming
   - Handles both `darts-postgres` and auto-generated names

3. **Configuration Backup**
   - All critical configuration files included
   - Easy to restore complete environment

4. **Comprehensive Manifest**
   - Detailed restore instructions
   - File sizes and checksums
   - Multiple restore examples

5. **Safe and Non-Destructive**
   - Read-only volume mounts
   - Timestamped backups (no overwrites)
   - Confirmation prompts (unless --yes flag used)

---

## ⚠️ Important Notes

### Before Upgrading to WSO2 IS 7.1.0

This backup is **critical** before performing the WSO2 IS upgrade:

1. ✅ **All volumes are backed up** - You can rollback if needed
2. ✅ **Configuration files saved** - Reference for new setup
3. ✅ **Database preserved** - User data is safe
4. ✅ **Complete restore path** - Can revert to current state

### Backup Retention

- Keep this backup until WSO2 IS 7.1.0 upgrade is complete and tested
- Store in a safe location (consider copying to external storage)
- Test restore procedure before relying on it

### Regular Backups

Consider scheduling regular backups:

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * cd /data/dartserver-pythonapp && ./backup_docker_volumes.sh --yes
```

---

## 🔍 Verify Backup

To verify the backup was successful:

```bash
# View manifest
cat ./docker-backups/2025-10-14_18-02-07/BACKUP_MANIFEST.txt

# Check backup files
ls -lh ./docker-backups/2025-10-14_18-02-07/

# Verify PostgreSQL dump
gunzip -c ./docker-backups/2025-10-14_18-02-07/postgres_dump.sql.gz | head -n 20
```

---

## ✅ Next Steps

Now that your data is safely backed up, you can proceed with:

1. **WSO2 IS 7.1.0 Upgrade** - Follow `WSO2_IS_UPGRADE_GUIDE.md`
2. **Run Upgrade Script** - Execute `./upgrade_wso2_to_7.sh`
3. **Test New Setup** - Verify everything works
4. **Keep This Backup** - Until upgrade is confirmed successful

---

## 📞 Support

If you need to restore from this backup:

1. Read the `BACKUP_MANIFEST.txt` file in the backup directory
2. Follow the restore instructions carefully
3. Test the restore in a development environment first if possible

---

**Backup Status:** ✅ **COMPLETE AND VERIFIED**

All Docker volumes and configurations have been successfully backed up and are ready for the WSO2 IS 7.1.0 upgrade process.