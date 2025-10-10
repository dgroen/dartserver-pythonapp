#!/bin/bash

# Darts Game Application Startup Script

echo "🎯 Starting Darts Game Application"
echo "=================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -q -r requirements.txt
else
    pip3 install -q -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Start the application
echo "Starting application..."
echo "=================================="
python app.py
