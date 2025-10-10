#!/bin/bash
# Migration script to clean up old build artifacts and set up new structure

set -e

echo "=========================================="
echo "Build Structure Migration Script"
echo "=========================================="
echo ""

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Step 1: Cleaning up old build artifacts...${NC}"

# Remove old coverage files
if [ -d "htmlcov" ] || [ -d "htmlcov-py310" ] || [ -d "htmlcov-py311" ] || [ -d "htmlcov-py312" ]; then
    echo "  Removing old htmlcov directories..."
    rm -rf htmlcov htmlcov-py310 htmlcov-py311 htmlcov-py312
fi

if [ -d "coverage" ]; then
    echo "  Removing old coverage directory..."
    rm -rf coverage
fi

# Remove old coverage files in root
if ls coverage*.xml 1> /dev/null 2>&1 || ls coverage*.json 1> /dev/null 2>&1; then
    echo "  Removing old coverage XML/JSON files..."
    rm -f coverage*.xml coverage*.json
fi

# Remove old junit files
if ls junit*.xml 1> /dev/null 2>&1; then
    echo "  Removing old junit XML files..."
    rm -f junit*.xml
fi

# Remove old .coverage files
if ls .coverage* 1> /dev/null 2>&1; then
    echo "  Removing old .coverage files..."
    rm -f .coverage*
fi

echo -e "${GREEN}✓ Old artifacts cleaned${NC}"
echo ""

echo -e "${BLUE}Step 2: Creating new directory structure...${NC}"

# Create new directories
mkdir -p docs/source
mkdir -p docs/build
mkdir -p build/coverage
mkdir -p build/reports

# Create .gitkeep files
touch build/coverage/.gitkeep
touch build/reports/.gitkeep
touch docs/source/.gitkeep

echo -e "${GREEN}✓ New directories created${NC}"
echo ""

echo -e "${BLUE}Step 3: Verifying structure...${NC}"

# Verify directories exist
if [ -d "docs/source" ] && [ -d "build/coverage" ] && [ -d "build/reports" ]; then
    echo -e "${GREEN}✓ All directories verified${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Some directories may not have been created${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Migration Complete!${NC}"
echo "=========================================="
echo ""
echo "New structure:"
echo "  docs/           - All documentation"
echo "  build/coverage/ - All coverage reports"
echo "  build/reports/  - All test reports"
echo ""
echo "You can now run:"
echo "  make test-cov   - Run tests with coverage"
echo "  make coverage   - Generate coverage report"
echo "  make clean      - Clean build artifacts"
echo ""
