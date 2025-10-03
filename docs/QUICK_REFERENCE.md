# Build Structure - Quick Reference

## 📁 New Directory Locations

| Type | Location |
|------|----------|
| **Documentation** | `docs/` |
| **Coverage Reports** | `build/coverage/` |
| **Test Reports** | `build/reports/` |
| **Build Artifacts** | `build/lib/`, `build/bdist.*/` |

## 🔧 Common Commands

```bash
# Run tests with coverage
make test-cov

# Generate coverage report
make coverage

# View HTML coverage report
open build/coverage/html/index.html

# Build documentation
make docs

# Clean all build artifacts
make clean

# Run all quality checks
make check-all
```

## 📊 Output Files

### Coverage Files
- `build/coverage/html/` - HTML coverage report
- `build/coverage/coverage.xml` - XML format (for CI/CD)
- `build/coverage/coverage.json` - JSON format
- `build/coverage/.coverage` - Coverage data file

### Test Reports
- `build/reports/junit.xml` - JUnit test results

### Documentation
- `docs/build/html/` - Generated HTML documentation

## 🧹 Cleanup

The `make clean` command now:
- ✅ Removes all coverage files
- ✅ Removes all test reports
- ✅ Removes build artifacts
- ✅ Preserves directory structure (.gitkeep files)
- ✅ Cleans cache directories

## 🔄 Migration

If you have an existing checkout with old files:

```bash
./migrate_build_structure.sh
```

## 📝 Notes

- All `.gitkeep` files are preserved during cleanup
- Directory structure is maintained in git
- All build artifacts are gitignored
- Old scattered files have been removed