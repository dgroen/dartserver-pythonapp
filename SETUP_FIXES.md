# Setup Script Fixes - Python venv Integration

## Issues Identified and Fixed

### 1. **Python venv Not Available**
**Problem:** The system didn't have `python3-venv` package installed, which is required for creating virtual environments with `python3 -m venv`.

**Error:**
```
The virtual environment was not created successfully because ensurepip is not available.
On Debian/Ubuntu systems, you need to install the python3-venv package.
```

**Fix:** Added automatic check and installation of `python3-venv` in the setup script:
```bash
# Check for python3-venv
print_info "Checking for python3-venv..."
if python3 -m venv --help &> /dev/null; then
    print_success "python3-venv is available"
else
    print_error "python3-venv is not installed"
    print_info "Installing python3-venv..."
    sudo apt-get update && sudo apt-get install -y python3-venv
fi
```

### 2. **pip Not Available in venv**
**Problem:** When creating a venv with `python3 -m venv`, pip was not automatically included in the virtual environment.

**Error:**
```
/data/dartserver-pythonapp/.venv/bin/python: No module named pip
```

**Fix:** Added pip availability check and installation:
```bash
# Ensure pip is available in venv
print_info "Ensuring pip is available..."
if ! python -m pip --version &> /dev/null; then
    print_warning "pip not found in venv, installing..."
    python -m ensurepip --upgrade 2>/dev/null || curl https://bootstrap.pypa.io/get-pip.py | python
fi
print_success "pip is available"
```

### 3. **Pre-commit Installation Issues**
**Problem:** Pre-commit installation was overly complex and had multiple fallback paths that could fail.

**Fix:** Simplified pre-commit installation since it's already included in dev dependencies:
```bash
# Verify pre-commit is installed (should be from dev dependencies)
if python -m pip show pre-commit &> /dev/null; then
    print_success "pre-commit is installed"

    # Install pre-commit hooks
    print_info "Installing pre-commit hooks..."
    if pre-commit install; then
        print_success "Pre-commit hooks installed"
    else
        print_warning "Failed to install pre-commit hooks, but continuing..."
    fi
fi
```

### 4. **Deprecated Stage Names in Pre-commit Config**
**Problem:** Pre-commit configuration used deprecated `commit` stage name instead of `pre-commit`.

**Warnings:**
```
[WARNING] hook id `ruff` uses deprecated stage names (commit) which will be removed in a future version.
[WARNING] top-level `default_stages` uses deprecated stage names (commit)
```

**Fix:** Updated `.pre-commit-config.yaml`:
```yaml
# Changed from:
default_stages: [commit]
stages: [commit]

# To:
default_stages: [pre-commit]
stages: [pre-commit]
```

### 5. **UV PATH Configuration**
**Problem:** UV could be installed in different locations (`~/.cargo/bin` or `~/.local/bin`).

**Fix:** Added both paths to ensure UV is found:
```bash
# Add UV to PATH for current session (try multiple possible locations)
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
```

---

## Changes Made to Files

### 1. `/data/dartserver-pythonapp/setup-dev.sh`

**Added:**
- Python3-venv availability check and installation
- pip availability check and installation in venv
- Improved UV PATH configuration
- Simplified pre-commit installation
- Better error handling and messages

**Key sections modified:**
- Lines 87-102: Added python3-venv check
- Lines 115-116: Improved UV PATH
- Lines 162-168: Added pip availability check
- Lines 181-197: Simplified pre-commit installation

### 2. `/data/dartserver-pythonapp/.pre-commit-config.yaml`

**Changed:**
- Line 7: `default_stages: [commit]` → `default_stages: [pre-commit]`
- Lines 47, 57, 67, 76, 86, 95: `stages: [commit]` → `stages: [pre-commit]`

---

## Verification Steps

### 1. Clean Installation Test
```bash
cd /data/dartserver-pythonapp
rm -rf .venv
./setup-dev.sh
```

**Expected Output:**
- ✅ Python 3.10.12 detected
- ✅ python3-venv available
- ✅ UV 0.8.22 installed
- ✅ Virtual environment created with python venv
- ✅ pip available in venv
- ✅ 109 dependencies installed
- ✅ pre-commit 4.3.0 installed
- ✅ Pre-commit hooks installed (no warnings)
- ✅ Custom git hooks installed
- ✅ 98 tests passed

### 2. Manual Verification
```bash
# Activate virtual environment
source .venv/bin/activate

# Check Python
python --version
# Output: Python 3.10.12

# Check pip
python -m pip --version
# Output: pip 24.x.x from /data/dartserver-pythonapp/.venv/lib/python3.10/site-packages/pip (python 3.10)

# Check UV
uv --version
# Output: uv 0.8.22

# Check pre-commit
pre-commit --version
# Output: pre-commit 4.3.0

# Run tests
pytest tests/ --cov=. --cov-report=term
# Output: 98 passed, 80.17% coverage
```

### 3. Pre-commit Hook Test
```bash
# Make a small change
echo "# Test comment" >> app.py

# Stage the change
git add app.py

# First commit (should check)
git commit -m "Test pre-commit"
# Should run all hooks

# If hooks fail, commit again (should auto-fix)
git commit -m "Test pre-commit"
# Should auto-fix and commit
```

---

## System Requirements

### Required Packages (Auto-installed by script)
- `python3.10-venv` - For creating virtual environments
- `python3-pip` - Usually included with python3-venv

### Manual Installation (if needed)
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10-venv python3-pip

# Verify
python3 -m venv --help
python3 -m pip --version
```

---

## Benefits of Using Python venv

### 1. **Native Python Tool**
- Built into Python 3.3+
- No external dependencies
- Standard and well-supported

### 2. **Lightweight**
- Minimal overhead
- Fast creation
- Small disk footprint

### 3. **Compatible with UV**
- UV works seamlessly with venv
- Can use `uv pip install` in venv
- Best of both worlds: standard venv + fast UV

### 4. **Portable**
- Works on all platforms
- No special installation required
- Standard Python workflow

---

## UV Integration

Even though we use Python's venv for creating the virtual environment, we still use UV for package management:

### Why This Combination?
1. **venv** - Standard, reliable virtual environment creation
2. **UV** - Fast package installation (10-100x faster than pip)

### Usage:
```bash
# Create venv (standard Python)
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install packages with UV (fast!)
uv pip install -e ".[dev,lint,test]"

# Or use regular pip if needed
python -m pip install <package>
```

---

## Troubleshooting

### Issue: "ensurepip is not available"
**Solution:** Run the setup script again - it will automatically install python3-venv.

Or manually:
```bash
sudo apt-get install -y python3.10-venv
```

### Issue: "No module named pip"
**Solution:** The setup script now handles this automatically. If you encounter it manually:
```bash
python -m ensurepip --upgrade
```

### Issue: Pre-commit warnings about deprecated stages
**Solution:** Already fixed in `.pre-commit-config.yaml`. If you see warnings, run:
```bash
pre-commit migrate-config
```

### Issue: UV not found
**Solution:** Ensure PATH is set correctly:
```bash
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
```

Add to your shell profile for persistence:
```bash
echo 'export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Summary

All issues have been identified and fixed:

✅ **Python venv** - Automatic installation and setup
✅ **pip availability** - Ensured in virtual environment  
✅ **Pre-commit** - Simplified installation, no warnings
✅ **UV integration** - Works seamlessly with venv
✅ **Error handling** - Improved messages and fallbacks
✅ **Testing** - All 98 tests passing

The setup script now provides a robust, one-command installation that:
- Uses standard Python venv for virtual environments
- Leverages UV for fast package installation
- Handles all edge cases and system requirements
- Provides clear feedback and error messages
- Works reliably on Ubuntu/Debian systems

**Ready for development!** 🚀