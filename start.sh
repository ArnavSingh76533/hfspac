#!/bin/bash

set -e  # Exit on error

echo "🚀 Starting Telegram Server Manager Bot..."
echo "🔄 Cleaning old session files..."

# Delete old session files
find . -name "*.session" -type f -delete || echo "No session files to clean"

echo "🌐 Starting web server..."
# Start the FastAPI server in the background
python3 server.py &
SERVER_PID=$!

# Check if server started successfully
sleep 2
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Failed to start web server"
    exit 1
fi

echo "✅ Web server started (PID: $SERVER_PID)"
echo "🤖 Starting Telegram bot..."

# Start the Telegram bot
python3 bot.py
