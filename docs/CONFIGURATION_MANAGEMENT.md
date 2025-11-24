# Configuration Management

This document describes the new configuration management system that separates sensitive configuration files into a dedicated secure repository.

## Overview

Configuration files for different environments (development, test, production) are now stored in a separate private GitHub repository called `dartserver-config`. This provides better security, organization, and version control for environment-specific configurations.

## Repository Structure

```
dartserver-config/
├── environments/
│   ├── development/     # Development environment configs
│   ├── test/           # Test environment configs
│   └── production/     # Production environment configs
│       ├── .env                    # Environment variables
│       ├── wso2is-config/
│       │   └── deployment.toml     # WSO2 Identity Server config
│       ├── ssl/                    # SSL certificates
│       │   ├── cert.pem
│       │   ├── key.pem
│       │   └── openssl.cnf
│       └── nginx/                  # Nginx configuration and certs
│           ├── nginx.conf
│           ├── cert.pem
│           └── key.pem
├── scripts/
│   ├── encrypt-configs.sh    # Setup git-crypt encryption
│   └── decrypt-configs.sh    # Decrypt files in CI/CD
├── .gitattributes           # Git-crypt encryption rules
└── README.md               # Repository documentation
```

## Security

### Encryption

Sensitive files are encrypted using `git-crypt`:
- SSL certificates (`*.pem`, `*.key`)
- Private keys and secrets
- Any file matching patterns in `.gitattributes`

### Access Control

- The config repository is **private**
- Access is controlled via GitHub repository permissions
- CI/CD uses a dedicated `CONFIG_REPO_TOKEN` secret
- GitHub environments provide additional approval gates

## Setup Instructions

### 1. Create Config Repository

1. Create a new **private** GitHub repository named `dartserver-config`
2. Copy the structure from the `dartserver-config/` directory in this repository
3. Initialize as a git repository and push to GitHub

### 2. Set Up Encryption

```bash
cd dartserver-config
chmod +x scripts/encrypt-configs.sh
./scripts/encrypt-configs.sh
```

This will:
- Initialize git-crypt
- Set up encryption for sensitive files
- Generate a symmetric key (store this securely)

### 3. Configure GitHub Secrets

Add these secrets to your main repository:

- `CONFIG_REPO_TOKEN`: Personal access token with access to the config repository
- `GIT_CRYPT_KEY`: Base64-encoded git-crypt symmetric key

### 4. Populate Configuration Files

For each environment, update the placeholder files with actual values:

1. **Environment Variables** (`.env`): Set actual database URLs, secrets, API keys
2. **WSO2 Config** (`deployment.toml`): Configure hostname, CORS origins, etc.
3. **SSL Certificates**: Replace placeholder files with actual certificates
4. **Nginx Config**: Update nginx.conf with environment-specific settings

### 5. Encrypt and Commit

```bash
git add .
git commit -m "Add initial configuration for all environments"
git push origin main
```

## CI/CD Integration

The GitHub Actions workflow automatically:

1. Checks out the config repository
2. Decrypts encrypted files using the `GIT_CRYPT_KEY`
3. Copies appropriate environment configs to the deployment directory
4. Proceeds with deployment

### Required Secrets

- `CONFIG_REPO_TOKEN`: Access token for config repository
- `GIT_CRYPT_KEY`: Symmetric key for git-crypt decryption

## Environment-Specific Configuration

### Development
- Uses localhost certificates
- Debug mode enabled
- Local database connections

### Test
- Staging certificates
- Production-like settings
- Test database connections

### Production
- Production SSL certificates
- Optimized settings
- Production database connections

## Maintenance

### Adding New Environments

1. Create new directory under `environments/`
2. Copy structure from existing environment
3. Update configurations appropriately
4. Encrypt and commit

### Updating Certificates

1. Replace certificate files in appropriate environment directory
2. Git-crypt will automatically encrypt them
3. Commit and push changes

### Rotating Encryption Keys

If you need to change the git-crypt key:

1. Export current key: `git-crypt export-key /tmp/old-key`
2. Reinitialize: `git-crypt init`
3. Re-encrypt: `git add . && git commit`
4. Update `GIT_CRYPT_KEY` secret with new key
5. Test deployment

## Troubleshooting

### Decryption Issues

If CI/CD fails to decrypt:
- Verify `GIT_CRYPT_KEY` secret is correct
- Check that `git-crypt` is installed in CI environment
- Ensure `.gitattributes` patterns match your files

### Permission Issues

If config repository access fails:
- Verify `CONFIG_REPO_TOKEN` has correct permissions
- Check repository visibility (must be private)
- Ensure token hasn't expired

### File Not Found Errors

If configuration files are missing:
- Check that all required files exist in config repository
- Verify environment directory structure
- Ensure files are committed and pushed

## Migration from Old System

The old system used base64-encoded secrets in GitHub. The new system:

- ✅ Provides better organization
- ✅ Enables proper version control of configs
- ✅ Supports encryption of sensitive files
- ✅ Allows environment-specific certificates
- ✅ Provides audit trail for config changes

To migrate:
1. Set up the config repository as described above
2. Decode existing secrets and populate config files
3. Test deployment with new system
4. Remove old secrets once migration is complete