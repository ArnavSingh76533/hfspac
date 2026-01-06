#!/bin/bash

set -e  # Exit on error

echo "🚀 Starting Telegram Server Manager Web Console..."
echo "🔄 Cleaning old session files..."

# Delete old session files
find . -name "*.session" -type f -delete || echo "No session files to clean"

echo "🌐 Starting web server..."
# Start the FastAPI server (no Telegram bot)
python3 server.py
