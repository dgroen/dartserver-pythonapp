#!/bin/bash

# Verification script for Python app migration
# This script verifies that the migration was successful

echo "🔍 Verifying Python Application Migration..."
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Not in dartserver-pythonapp directory"
    exit 1
fi

echo "✅ In correct directory: $(pwd)"
echo ""

# Check core files
echo "📂 Checking core files..."
files=(
    "app.py"
    "game_manager.py"
    "rabbitmq_consumer.py"
    "requirements.txt"
    "docker-compose.yml"
    "Dockerfile"
    ".env.example"
    ".gitignore"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
    fi
done
echo ""

# Check directories
echo "📁 Checking directories..."
dirs=(
    "games"
    "templates"
    "static"
    "examples"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ Missing: $dir/"
    fi
done
echo ""

# Check documentation
echo "📚 Checking documentation..."
docs=(
    "README.md"
    "README_REPO.md"
    "GET_STARTED.md"
    "QUICKSTART.md"
    "SUMMARY.md"
    "ARCHITECTURE.md"
    "INDEX.md"
    "MIGRATION_COMPLETE.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✅ $doc"
    else
        echo "  ❌ Missing: $doc"
    fi
done
echo ""

# Check git repository
echo "🔧 Checking git repository..."
if [ -d ".git" ]; then
    echo "  ✅ Git repository initialized"
    echo "  📝 Latest commit: $(git log --oneline -1)"
else
    echo "  ❌ Git repository not found"
fi
echo ""

# Check Python files
echo "🐍 Checking Python files..."
py_count=$(find . -type f -name "*.py" | wc -l)
echo "  ✅ Found $py_count Python files"
echo ""

# Check if paths are updated in documentation
echo "📝 Checking for old path references..."
old_refs=$(grep -r "cd python_app" *.md 2>/dev/null | wc -l)
if [ "$old_refs" -eq 0 ]; then
    echo "  ✅ No old path references found in documentation"
else
    echo "  ⚠️  Warning: Found $old_refs references to 'cd python_app'"
    echo "     Run: grep -r 'cd python_app' *.md"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Migration Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Repository: $(pwd)"
echo "Python files: $py_count"
echo "Git status: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'Not a git repo')"
echo ""
echo "✅ Migration verification complete!"
echo ""
echo "🚀 Next steps:"
echo "   1. Start the application: docker-compose up"
echo "   2. Access game board: http://localhost:5000"
echo "   3. Access control panel: http://localhost:5000/control"
echo "   4. Read documentation: cat GET_STARTED.md"
echo ""
