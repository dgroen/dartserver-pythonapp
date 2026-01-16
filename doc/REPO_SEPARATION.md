# Repository Separation Guide

## Overview

This document describes how to separate the monorepo into individual repositories while maintaining continuity and version management.

## Current Structure (Monorepo)

```
dartserver-pythonapp/
├── packages/
│   ├── dartserver-core/
│   ├── dartserver-games/
│   ├── dartserver-services/
│   └── dartserver-app/
├── .github/workflows/
├── doc/
└── scripts/
```

## Target Structure (Separate Repos)

### Individual Package Repositories

```
dartserver-core/
├── src/dartserver_core/
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .github/workflows/
└── doc/

dartserver-games/
├── src/dartserver_games/
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .github/workflows/
└── doc/

dartserver-services/
├── src/dartserver_services/
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .github/workflows/
└── doc/

dartserver-app/
├── src/dartserver_app/
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .github/workflows/
└── doc/

dartserver-pythonapp/ (Main repo - remains as coordinator)
├── packages/          # Git submodules reference other repos
├── doc/              # Central documentation
├── scripts/          # Common scripts
├── .github/          # Main org workflows
└── README.md         # Main entry point
```

## Separation Steps

### Phase 1: Preparation

1. **Create organization** on GitHub (if not exists)
   - github.com/letsplaydarts

2. **Create repositories** for each package
   - dartserver-core
   - dartserver-games
   - dartserver-services
   - dartserver-app

3. **Prepare Git history**
   ```bash
   # Create subtree splits for each package
   git subtree split -P packages/dartserver-core -b dartserver-core-history
   git subtree split -P packages/dartserver-games -b dartserver-games-history
   git subtree split -P packages/dartserver-services -b dartserver-services-history
   git subtree split -P packages/dartserver-app -b dartserver-app-history
   ```

### Phase 2: Create Individual Repositories

1. **For each package** (using dartserver-core as example):

```bash
# Clone the split history
git init dartserver-core
cd dartserver-core
git fetch --depth=1 <original-repo-url> dartserver-core-history
git merge -X ours FETCH_HEAD --allow-unrelated-histories

# Clean up
rm -rf packages/dartserver-games
rm -rf packages/dartserver-services
rm -rf packages/dartserver-app
mv packages/dartserver-core/* .
rmdir packages

# Update documentation
git remote add origin https://github.com/letsplaydarts/dartserver-core.git
git branch -M main
git push -u origin main
```

2. **Setup GitHub repository**
   - Add collaborators
   - Enable branch protection
   - Setup automated workflows
   - Enable publishing to PyPI

### Phase 3: Update Main Repository

1. **Convert to monorepo with submodules**:

```bash
cd dartserver-pythonapp

# Remove package directories
rm -rf packages/dartserver-core
rm -rf packages/dartserver-games
rm -rf packages/dartserver-services
rm -rf packages/dartserver-app

# Add as submodules
git submodule add https://github.com/letsplaydarts/dartserver-core.git packages/dartserver-core
git submodule add https://github.com/letsplaydarts/dartserver-games.git packages/dartserver-games
git submodule add https://github.com/letsplaydarts/dartserver-services.git packages/dartserver-services
git submodule add https://github.com/letsplaydarts/dartserver-app.git packages/dartserver-app

git commit -m "Convert to monorepo with Git submodules"
```

2. **Update cloning instructions**:

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/letsplaydarts/dartserver-pythonapp.git

# Or initialize existing clone
git submodule update --init --recursive
```

### Phase 4: Update CI/CD

1. **Individual package repositories**:
   - Copy workflows from .github/workflows/
   - Each repo tests itself independently
   - Publish to PyPI on release

2. **Main repository workflows**:
   - Run integration tests across all submodules
   - Coordinate releases
   - Update root documentation

3. **Update workflow files**:

```yaml
# In each package repo .github/workflows/ci-cd.yml
on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  # Test package
  test:
    runs-on: ubuntu-latest
    steps:
      # ... standard test steps ...

  # Publish to PyPI
  publish:
    needs: test
    if: github.event_name == 'release'
    # ... publish steps ...
```

## Version Management

### Before Separation (Current)
- Single version: 1.0.0 (all packages)
- Updated together
- Git tags: v1.0.0

### After Separation
- Independent versions per package
- Each package has its own release cycle
- Git tags: dartserver-core-v1.0.0

### Version Pinning Strategy

```toml
# dartserver-games/pyproject.toml
dependencies = [
    "dartserver-core>=1.0.0,<2.0.0",
]

# dartserver-services/pyproject.toml
dependencies = [
    "dartserver-core>=1.0.0,<2.0.0",
]

# dartserver-app/pyproject.toml
dependencies = [
    "dartserver-core>=1.0.0,<2.0.0",
    "dartserver-games>=1.0.0,<2.0.0",
    "dartserver-services>=1.0.0,<2.0.0",
]
```

## Dependency Management

### Publishing Order

1. **dartserver-core** (no dependencies)
   - Publish first
   - Needed by all others

2. **dartserver-games** (depends on core)
   - Publish second
   - Update dependency versions

3. **dartserver-services** (depends on core)
   - Publish third
   - Update dependency versions

4. **dartserver-app** (depends on all)
   - Publish last
   - Update all dependency versions

### PyPI Publishing Workflow

```bash
# For each package in order:

# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit and tag
git tag -a dartserver-core-v1.1.0 -m "Release 1.1.0"
git push origin dartserver-core-v1.1.0

# 4. GitHub Actions automatically publishes to PyPI
# 5. Verify: pip install dartserver-core==1.1.0
```

## Rollback Plan

If separation causes issues:

1. **Short-term**: Keep monorepo active alongside
2. **Medium-term**: Use git history to revert
3. **Documentation**: Maintain clear version mapping

Example mapping:
```
Monorepo v1.0.0 == dartserver-core v1.0.0
                  dartserver-games v1.0.0
                  dartserver-services v1.0.0
                  dartserver-app v1.0.0
```

## Communication Plan

1. **Before separation**:
   - Announce in README
   - Update documentation
   - Plan transition period

2. **During separation**:
   - Maintain both repos briefly
   - Clear migration guide
   - Active support channel

3. **After separation**:
   - Archive monorepo
   - Update all links
   - Consolidate documentation

## Long-term Benefits

✅ **Independence**: Packages evolve independently
✅ **Clarity**: Clear responsibility areas
✅ **Collaboration**: External contributors easier
✅ **Releases**: Decoupled release cycles
✅ **Maintenance**: Smaller, focused repositories
