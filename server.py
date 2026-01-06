#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple FastAPI server for Hugging Face Spaces
This keeps the space alive and provides a basic web interface
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that returns a simple HTML page"""
    
    # Check if config file exists
    config_exists = os.path.exists("config")
    
    status_html = ""
    if config_exists:
        status_html = """
        <p class="status">🟡 Web server is running</p>
        <p class="info-text">The Telegram bot is attempting to connect. Check the container logs for status.</p>
        """
    else:
        status_html = """
        <p class="status-warning">⚠️ Configuration needed</p>
        <p class="info-text">Create a <code>config</code> file with your Telegram bot token and admin chat ID to enable the bot.</p>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Telegram Server Manager Bot</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                }}
                .status {{
                    color: #28a745;
                    font-weight: bold;
                    font-size: 1.2em;
                }}
                .status-warning {{
                    color: #ffc107;
                    font-weight: bold;
                    font-size: 1.2em;
                }}
                .info {{
                    background-color: #e7f3ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .info-text {{
                    color: #666;
                    margin: 10px 0;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }}
                .warning-box {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram Server Manager Bot</h1>
                {status_html}
                <div class="info">
                    <h3>About this bot:</h3>
                    <p>This bot allows you to remotely manage your server using Telegram.</p>
                    <ul>
                        <li>Run commands via Telegram</li>
                        <li>Monitor server status</li>
                        <li>Check system resources</li>
                        <li>Execute Python code with /eval command</li>
                    </ul>
                </div>
                <div class="warning-box">
                    <h4>⚠️ Note for Hugging Face Spaces:</h4>
                    <p>Hugging Face Spaces may have network restrictions that prevent the bot from connecting to Telegram's API. 
                    If you see connection errors in the logs, this is expected behavior when running in a restricted environment.</p>
                    <p>To use this bot with full functionality, deploy it on a server with unrestricted internet access.</p>
                </div>
                <div class="info">
                    <h3>Configuration:</h3>
                    <p>To enable the bot, create a <code>config</code> file with:</p>
                    <pre><code>[SecretConfig]
token = YOUR_TELEGRAM_BOT_TOKEN
admincid = YOUR_TELEGRAM_CHAT_ID</code></pre>
                    <p><strong>Start a chat with your bot on Telegram to use it!</strong></p>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "running"}

@app.get("/api/status")
async def status():
    """Status endpoint"""
    return {
        "status": "online",
        "service": "Telegram Server Manager Bot",
        "port": 7860
    }

if __name__ == "__main__":
    # Run on port 7860 for Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Starting web server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
