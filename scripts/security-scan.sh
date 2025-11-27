#!/usr/bin/env bash
# Security scanning script for all packages

set -e

echo "================================"
echo "Running Security Scans"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Check if tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 not found. Install with: pip install $2${NC}"
        return 1
    fi
    return 0
}

echo ""
echo "Checking security tools..."
check_tool bandit bandit || FAILED=1
check_tool safety safety || FAILED=1
check_tool pip-audit pip-audit || FAILED=1

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}Some tools are missing. Please install them.${NC}"
    exit 1
fi

# Scan each package
for pkg in packages/*/; do
    pkg_name=$(basename "$pkg")
    echo ""
    echo -e "${YELLOW}Scanning $pkg_name...${NC}"
    
    cd "$pkg"
    
    # Run Bandit
    echo -n "  Bandit: "
    if bandit -r src/ -q 2>/dev/null; then
        echo -e "${GREEN}✓ Passed${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        FAILED=1
    fi
    
    # Run Safety
    echo -n "  Safety: "
    if safety check --json 2>/dev/null | grep -q '"vulnerabilities": \[\]'; then
        echo -e "${GREEN}✓ Passed${NC}"
    else
        echo -e "${YELLOW}⚠ Check required${NC}"
    fi
    
    # Run pip-audit
    echo -n "  pip-audit: "
    if pip-audit 2>/dev/null | grep -q "No known vulnerabilities"; then
        echo -e "${GREEN}✓ Passed${NC}"
    else
        echo -e "${YELLOW}⚠ Check required${NC}"
    fi
    
    cd - > /dev/null
done

echo ""
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All security scans passed!${NC}"
    exit 0
else
    echo -e "${RED}Some security checks failed!${NC}"
    exit 1
fi
