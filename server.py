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

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that returns a simple HTML page"""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Telegram Server Manager Bot</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                }
                .status {
                    color: #28a745;
                    font-weight: bold;
                }
                .info {
                    background-color: #e7f3ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram Server Manager Bot</h1>
                <p class="status">✅ Bot is running!</p>
                <div class="info">
                    <h3>About this bot:</h3>
                    <p>This bot allows you to remotely manage your server using Telegram.</p>
                    <ul>
                        <li>Run commands via Telegram</li>
                        <li>Monitor server status</li>
                        <li>Check system resources</li>
                    </ul>
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
    uvicorn.run(app, host="0.0.0.0", port=port)
