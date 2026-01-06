#!/bin/bash

echo "🚀 Starting Telegram Server Manager Bot..."
echo "🔄 Cleaning old session files..."

# Delete old session files
find . -name "*.session" -type f -delete

echo "🌐 Starting web server..."
# Start the FastAPI server in the background
python3 server.py &

echo "🤖 Starting Telegram bot..."
# Start the Telegram bot
python3 bot.py
