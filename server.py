#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple FastAPI server for Hugging Face Spaces
This keeps the space alive and provides a basic web interface
"""

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import logging
import subprocess
import configparser
import tempfile
import traceback
import json
import sys
from io import StringIO

# Configure logging first
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. AI chat features will be disabled.")

try:
    import requests as req_lib
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests library not available. API testing features will be disabled.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for persistent shell session
shell_state = {
    "cwd": os.getcwd(),  # Current working directory
    "env": dict(os.environ)  # Environment variables
}

# Load config for authentication
def load_config():
    """Load configuration file"""
    config = configparser.ConfigParser()
    if os.path.exists("config"):
        config.read("config")
        return config
    return None

def verify_admin(chat_id: str):
    """Verify if the provided chat_id matches admin"""
    config = load_config()
    if config and "SecretConfig" in config:
        admin_cid = config["SecretConfig"].get("admincid", "")
        return str(chat_id) == str(admin_cid)
    # If no config, allow access for demo purposes in restricted environments
    # WARNING: This is insecure in production. Always use a config file with proper admin_id
    logger.warning("No config file found - running in insecure demo mode")
    return True

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that returns a professional web interface"""
    
    # Read and return the new UI template
    template_path = os.path.join(os.path.dirname(__file__), "ui_template.html")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to basic interface if template not found
        return f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Telegram Server Manager - Web Console</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .header {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                
                .header h1 {{
                    color: #333;
                    font-size: 2em;
                    margin-bottom: 10px;
                }}
                
                .status-badge {{
                    display: inline-block;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                
                .status-online {{
                    background: #d4edda;
                    color: #155724;
                }}
                
                .status-warning {{
                    background: #fff3cd;
                    color: #856404;
                }}
                
                .main-content {{
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 20px;
                }}
                
                @media (min-width: 768px) {{
                    .main-content {{
                        grid-template-columns: 1fr 1fr;
                    }}
                }}
                
                .card {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                
                .card h2 {{
                    color: #333;
                    margin-bottom: 15px;
                    font-size: 1.5em;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }}
                
                .form-group {{
                    margin-bottom: 15px;
                }}
                
                label {{
                    display: block;
                    margin-bottom: 5px;
                    color: #555;
                    font-weight: 600;
                }}
                
                input[type="text"],
                input[type="password"],
                textarea,
                select {{
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #e0e0e0;
                    border-radius: 5px;
                    font-size: 1em;
                    font-family: inherit;
                    transition: border-color 0.3s;
                }}
                
                input:focus,
                textarea:focus,
                select:focus {{
                    outline: none;
                    border-color: #667eea;
                }}
                
                textarea {{
                    min-height: 120px;
                    font-family: 'Courier New', monospace;
                    resize: vertical;
                }}
                
                button {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 5px;
                    font-size: 1em;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                
                button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                
                button:active {{
                    transform: translateY(0);
                }}
                
                button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}
                
                .output {{
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    max-height: 400px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    margin-top: 15px;
                }}
                
                .output.empty {{
                    color: #888;
                    font-style: italic;
                }}
                
                .loading {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255,255,255,.3);
                    border-radius: 50%;
                    border-top-color: white;
                    animation: spin 1s ease-in-out infinite;
                }}
                
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                
                .info-box {{
                    background: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                
                .warning-box {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                
                .success-box {{
                    background: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                
                .error-box {{
                    background: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}
                
                .file-upload {{
                    border: 2px dashed #667eea;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background 0.3s;
                }}
                
                .file-upload:hover {{
                    background: #f0f0f0;
                }}
                
                .tabs {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }}
                
                .tab {{
                    padding: 10px 20px;
                    cursor: pointer;
                    border: none;
                    background: none;
                    font-weight: 600;
                    color: #666;
                    border-bottom: 3px solid transparent;
                    transition: all 0.3s;
                }}
                
                .tab.active {{
                    color: #667eea;
                    border-bottom-color: #667eea;
                }}
                
                .tab-content {{
                    display: none;
                }}
                
                .tab-content.active {{
                    display: block;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Telegram Server Manager</h1>
                    <span class="status-badge {'status-online' if config_exists else 'status-warning'}">
                        {'✅ Web Console Active' if config_exists else '⚠️ Demo Mode'}
                    </span>
                    <p style="margin-top: 10px; color: #666;">Professional web interface for server management</p>
                </div>
                
                {'<div class="warning-box"><strong>⚠️ Demo Mode:</strong> Config file not found. Some features may be restricted. Create a <code>config</code> file to enable full functionality.</div>' if not config_exists else ''}
                
                <div class="main-content">
                    <!-- Command Execution Card -->
                    <div class="card">
                        <h2>💻 Command Executor</h2>
                        <div class="info-box">
                            <strong>💡 Tip:</strong> Run any shell command directly from the browser. Commands like <code>cd</code> persist across executions.
                        </div>
                        <div class="info-box" style="background: #f0f0f0; border-left-color: #666;">
                            <strong>📂 Current Directory:</strong> <span id="current-dir">Loading...</span>
                        </div>
                        
                        <div class="form-group">
                            <label for="cmd-input">Command:</label>
                            <input type="text" id="cmd-input" placeholder="ls -la" />
                        </div>
                        
                        <button onclick="runCommand()" id="cmd-btn">
                            Execute Command
                        </button>
                        
                        <div style="position: relative;">
                            <button onclick="copyOutput('cmd-output', this)" style="position: absolute; top: 10px; right: 10px; padding: 5px 10px; font-size: 0.8em;">
                                📋 Copy
                            </button>
                            <div class="output empty" id="cmd-output">
                                Output will appear here...
                            </div>
                        </div>
                    </div>
                    
                    <!-- Python Evaluator Card -->
                    <div class="card">
                        <h2>🐍 Python Evaluator</h2>
                        <div class="info-box">
                            <strong>💡 Tip:</strong> Execute Python code with full system access. Supports async/await!
                        </div>
                        
                        <div class="form-group">
                            <label for="py-input">Python Code:</label>
                            <textarea id="py-input" placeholder="print('Hello World')&#x0a;import os&#x0a;print(os.getcwd())"></textarea>
                        </div>
                        
                        <button onclick="runPython()" id="py-btn">
                            Execute Python
                        </button>
                        
                        <div style="position: relative;">
                            <button onclick="copyOutput('py-output', this)" style="position: absolute; top: 10px; right: 10px; padding: 5px 10px; font-size: 0.8em;">
                                📋 Copy
                            </button>
                            <div class="output empty" id="py-output">
                                Output will appear here...
                            </div>
                        </div>
                    </div>
                    
                    <!-- File Uploader Card -->
                    <div class="card">
                        <h2>📁 Python File Executor</h2>
                        <div class="info-box">
                            <strong>💡 Tip:</strong> Upload and run Python files
                        </div>
                        
                        <div class="form-group">
                            <label>Upload Python File (.py):</label>
                            <input type="file" id="file-input" accept=".py" style="margin-bottom: 10px;" />
                        </div>
                        
                        <button onclick="uploadAndRun()" id="file-btn">
                            Upload & Execute
                        </button>
                        
                        <div style="position: relative;">
                            <button onclick="copyOutput('file-output', this)" style="position: absolute; top: 10px; right: 10px; padding: 5px 10px; font-size: 0.8em;">
                                📋 Copy
                            </button>
                            <div class="output empty" id="file-output">
                                Output will appear here...
                            </div>
                        </div>
                    </div>
                    
                    <!-- System Info Card -->
                    <div class="card">
                        <h2>📊 Quick System Info</h2>
                        
                        <div class="tabs">
                            <button class="tab active" onclick="showTab('system')">System</button>
                            <button class="tab" onclick="showTab('disk')">Disk</button>
                            <button class="tab" onclick="showTab('network')">Network</button>
                        </div>
                        
                        <div id="system" class="tab-content active">
                            <button onclick="getSystemInfo('uname -a')" style="width: 100%; margin-bottom: 10px;">
                                System Information
                            </button>
                            <button onclick="getSystemInfo('df -h')" style="width: 100%; margin-bottom: 10px;">
                                Disk Usage
                            </button>
                            <button onclick="getSystemInfo('free -h')" style="width: 100%;">
                                Memory Usage
                            </button>
                        </div>
                        
                        <div id="disk" class="tab-content">
                            <button onclick="getSystemInfo('du -sh /* 2>/dev/null')" style="width: 100%; margin-bottom: 10px;">
                                Root Directories Size
                            </button>
                            <button onclick="getSystemInfo('lsblk')" style="width: 100%;">
                                Block Devices
                            </button>
                        </div>
                        
                        <div id="network" class="tab-content">
                            <button onclick="getSystemInfo('ip addr')" style="width: 100%; margin-bottom: 10px;">
                                IP Addresses
                            </button>
                            <button onclick="getSystemInfo('ping -c 4 8.8.8.8')" style="width: 100%;">
                                Network Test (ping)
                            </button>
                        </div>
                        
                        <div style="position: relative;">
                            <button onclick="copyOutput('sys-output', this)" style="position: absolute; top: 10px; right: 10px; padding: 5px 10px; font-size: 0.8em;">
                                📋 Copy
                            </button>
                            <div class="output empty" id="sys-output">
                                Click a button to see system info...
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="warning-box" style="margin-top: 20px;">
                    <h4>🔒 Security Notice:</h4>
                    <p><strong>⚠️ IMPORTANT:</strong> This web interface provides full system access and is designed for trusted environments only.</p>
                    <p>In production environments:</p>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li>Use strong authentication (configure admin chat ID in config file)</li>
                        <li>Deploy behind a reverse proxy with HTTPS</li>
                        <li>Implement rate limiting and input validation</li>
                        <li>Monitor and log all command executions</li>
                        <li>Restrict network access to trusted IPs only</li>
                    </ul>
                    <p style="margin-top: 10px;"><strong>Note:</strong> This tool intentionally allows shell command execution and Python eval - features equivalent to the Telegram bot. Use responsibly.</p>
                </div>
            </div>
            
            <script>
                // Load current directory on page load
                window.addEventListener('DOMContentLoaded', async () => {{
                    await updateCurrentDirectory();
                }});
                
                async function updateCurrentDirectory() {{
                    try {{
                        const response = await fetch('/api/pwd');
                        const data = await response.json();
                        if (data.success) {{
                            document.getElementById('current-dir').textContent = data.cwd;
                        }}
                    }} catch (error) {{
                        document.getElementById('current-dir').textContent = 'Unknown';
                    }}
                }}
                
                function copyOutput(elementId, btnElement) {{
                    const output = document.getElementById(elementId);
                    const text = output.textContent;
                    
                    navigator.clipboard.writeText(text).then(() => {{
                        // Show feedback
                        const originalText = btnElement.innerHTML;
                        btnElement.innerHTML = '✅ Copied!';
                        setTimeout(() => {{
                            btnElement.innerHTML = originalText;
                        }}, 2000);
                    }}).catch(err => {{
                        alert('Failed to copy: ' + err);
                    }});
                }}
                
                function showTab(tabName) {{
                    // Hide all tab contents
                    document.querySelectorAll('.tab-content').forEach(content => {{
                        content.classList.remove('active');
                    }});
                    
                    // Remove active class from all tabs
                    document.querySelectorAll('.tab').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    
                    // Show selected tab
                    document.getElementById(tabName).classList.add('active');
                    event.target.classList.add('active');
                }}
                
                async function runCommand() {{
                    const input = document.getElementById('cmd-input');
                    const output = document.getElementById('cmd-output');
                    const btn = document.getElementById('cmd-btn');
                    
                    const command = input.value.trim();
                    if (!command) {{
                        output.textContent = '❌ Please enter a command';
                        output.classList.remove('empty');
                        return;
                    }}
                    
                    btn.disabled = true;
                    btn.innerHTML = '<span class="loading"></span> Executing...';
                    output.textContent = 'Executing command...';
                    output.classList.remove('empty');
                    
                    try {{
                        const response = await fetch('/api/execute', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ command: command, admin_id: 'web-console' }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            output.textContent = '✅ Command executed successfully:\\n\\n' + data.output;
                            // Update current directory if command was successful
                            await updateCurrentDirectory();
                        }} else {{
                            output.textContent = '❌ Error:\\n\\n' + data.error;
                        }}
                    }} catch (error) {{
                        output.textContent = '❌ Network error: ' + error.message;
                    }} finally {{
                        btn.disabled = false;
                        btn.innerHTML = 'Execute Command';
                    }}
                }}
                
                async function runPython() {{
                    const input = document.getElementById('py-input');
                    const output = document.getElementById('py-output');
                    const btn = document.getElementById('py-btn');
                    
                    const code = input.value.trim();
                    if (!code) {{
                        output.textContent = '❌ Please enter Python code';
                        output.classList.remove('empty');
                        return;
                    }}
                    
                    btn.disabled = true;
                    btn.innerHTML = '<span class="loading"></span> Executing...';
                    output.textContent = 'Executing Python code...';
                    output.classList.remove('empty');
                    
                    try {{
                        const response = await fetch('/api/eval', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ code: code, admin_id: 'web-console' }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            output.textContent = '✅ Python executed successfully:\\n\\n' + data.output;
                        }} else {{
                            output.textContent = '❌ Error:\\n\\n' + data.error;
                        }}
                    }} catch (error) {{
                        output.textContent = '❌ Network error: ' + error.message;
                    }} finally {{
                        btn.disabled = false;
                        btn.innerHTML = 'Execute Python';
                    }}
                }}
                
                async function uploadAndRun() {{
                    const input = document.getElementById('file-input');
                    const output = document.getElementById('file-output');
                    const btn = document.getElementById('file-btn');
                    
                    if (!input.files || input.files.length === 0) {{
                        output.textContent = '❌ Please select a Python file';
                        output.classList.remove('empty');
                        return;
                    }}
                    
                    const file = input.files[0];
                    if (!file.name.endsWith('.py')) {{
                        output.textContent = '❌ Please select a .py file';
                        output.classList.remove('empty');
                        return;
                    }}
                    
                    btn.disabled = true;
                    btn.innerHTML = '<span class="loading"></span> Uploading & Executing...';
                    output.textContent = 'Uploading and executing file...';
                    output.classList.remove('empty');
                    
                    try {{
                        const formData = new FormData();
                        formData.append('file', file);
                        formData.append('admin_id', 'web-console');
                        
                        const response = await fetch('/api/run-file', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            output.textContent = '✅ File executed successfully:\\n\\n' + data.output;
                        }} else {{
                            output.textContent = '❌ Error:\\n\\n' + data.error;
                        }}
                    }} catch (error) {{
                        output.textContent = '❌ Network error: ' + error.message;
                    }} finally {{
                        btn.disabled = false;
                        btn.innerHTML = 'Upload & Execute';
                    }}
                }}
                
                async function getSystemInfo(command) {{
                    const output = document.getElementById('sys-output');
                    output.textContent = 'Loading...';
                    output.classList.remove('empty');
                    
                    try {{
                        const response = await fetch('/api/execute', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ command: command, admin_id: 'web-console' }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            output.textContent = data.output;
                        }} else {{
                            output.textContent = '❌ Error: ' + data.error;
                        }}
                    }} catch (error) {{
                        output.textContent = '❌ Network error: ' + error.message;
                    }}
                }}
                
                // Enable Enter key for command input
                document.getElementById('cmd-input').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        runCommand();
                    }}
                }});
            </script>
        </body>
    </html>
    """

@app.post("/api/execute")
async def execute_command(request: Request):
    """Execute a shell command with persistent working directory"""
    try:
        data = await request.json()
        command = data.get("command", "").strip()
        admin_id = data.get("admin_id", "")
        
        if not command:
            return JSONResponse({"success": False, "error": "No command provided"})
        
        # Verify admin (basic check)
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"Executing command: {command}")
        
        # Execute command with timeout
        try:
            # Check if command is 'cd' to update persistent state
            if command.startswith("cd ") or command == "cd":
                parts = command.split(maxsplit=1)
                if len(parts) == 1:
                    # cd without arguments goes to home
                    new_dir = os.path.expanduser("~")
                else:
                    new_dir = parts[1]
                    # Handle relative paths
                    if not os.path.isabs(new_dir):
                        new_dir = os.path.join(shell_state["cwd"], new_dir)
                    # Expand ~ and resolve path (realpath resolves symlinks and normalizes)
                    new_dir = os.path.expanduser(new_dir)
                    new_dir = os.path.realpath(new_dir)
                
                # Check if directory exists and is accessible
                # Note: This is an admin tool with full system access by design
                if os.path.isdir(new_dir) and os.access(new_dir, os.R_OK):
                    shell_state["cwd"] = new_dir
                    return JSONResponse({
                        "success": True,
                        "output": f"Changed directory to: {new_dir}",
                        "return_code": 0
                    })
                else:
                    return JSONResponse({
                        "success": False,
                        "error": f"Directory not found or not accessible: {new_dir}"
                    })
            
            # Execute command in the persistent working directory
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=shell_state["cwd"],
                env=shell_state["env"]
            )
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "Command executed successfully (no output)"
            
            return JSONResponse({
                "success": True,
                "output": output,
                "return_code": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            return JSONResponse({
                "success": False,
                "error": "Command timed out after 30 seconds"
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": f"Execution error: {str(e)}"
            })
            
    except Exception as e:
        logger.error(f"Error in execute_command: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.post("/api/eval")
async def evaluate_python(request: Request):
    """Execute Python code with support for async/await
    
    SECURITY NOTE: This endpoint intentionally allows arbitrary Python code execution.
    It is restricted to admin users only via verify_admin() check.
    This is designed for remote server management in trusted environments.
    Only authorized administrators should have access.
    """
    try:
        data = await request.json()
        code = data.get("code", "").strip()
        admin_id = data.get("admin_id", "")
        
        if not code:
            return JSONResponse({"success": False, "error": "No code provided"})
        
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"Executing Python code (length: {len(code)})")
        
        try:
            # Import necessary modules for async support
            import sys
            import asyncio
            from io import StringIO
            
            # Create a namespace for execution
            namespace = {
                '__builtins__': __builtins__,
                'os': os,
                'subprocess': subprocess,
                'asyncio': asyncio,
                'json': json,  # Add json module for better formatting
            }
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                # Check if code contains await (indicating async code)
                # Use AST parsing for more accurate detection
                try:
                    import ast
                    # Try to parse the code to detect async usage
                    tree = ast.parse(code)
                    has_await = any(isinstance(node, (ast.Await, ast.AsyncWith, ast.AsyncFor)) 
                                   for node in ast.walk(tree))
                    has_async_def = any(isinstance(node, ast.AsyncFunctionDef) 
                                       for node in ast.walk(tree))
                    is_async = has_await or has_async_def
                except SyntaxError:
                    # If parsing fails, fall back to simple string check
                    is_async = 'await ' in code or code.strip().startswith('async ')
                
                if is_async:
                    # Wrap code in async function and await it
                    import textwrap
                    indented_code = textwrap.indent(code, '    ')
                    async_code = f"""
async def __async_exec():
{indented_code}
"""
                    # Compile and execute the async function definition
                    exec(async_code, namespace)
                    # Now await the async function
                    result = await namespace['__async_exec']()
                    if result is not None:
                        print(result)
                else:
                    # Try to evaluate as expression first
                    try:
                        result = eval(code, namespace)
                        if result is not None:
                            # If result is dict or list, auto-format as JSON
                            if isinstance(result, (dict, list)):
                                print(json.dumps(result, indent=2, ensure_ascii=False))
                            else:
                                print(result)
                    except SyntaxError:
                        # If it fails, execute as statement
                        exec(code, namespace)
                
                output = sys.stdout.getvalue()
                if not output:
                    output = "Code executed successfully (no output)"
                
                # Try to detect and format JSON output
                try:
                    # Check if output looks like JSON (starts with { or [)
                    stripped = output.strip()
                    if (stripped.startswith('{') or stripped.startswith('[')) and (stripped.endswith('}') or stripped.endswith(']')):
                        # Try to parse and reformat as JSON
                        json_obj = json.loads(stripped)
                        output = json.dumps(json_obj, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, ValueError):
                    # Not valid JSON, keep original output
                    pass
                
                return JSONResponse({
                    "success": True,
                    "output": output
                })
                
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}\\n{traceback.format_exc()}"
            })
            
    except Exception as e:
        logger.error(f"Error in evaluate_python: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.post("/api/run-file")
async def run_python_file(file: UploadFile = File(...), admin_id: str = Form(...)):
    """Upload and execute a Python file"""
    try:
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        # Verify file type
        if not file.filename.endswith('.py'):
            return JSONResponse({
                "success": False,
                "error": "Only .py files are allowed"
            })
        
        logger.info(f"Executing uploaded file: {file.filename}")
        
        # Save file to temp location
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            content = await file.read()
            tmp.write(content.decode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Execute the file
            result = subprocess.run(
                ['python3', tmp_path],  # Use python3 from PATH instead of hardcoded path
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "File executed successfully (no output)"
            
            return JSONResponse({
                "success": True,
                "output": output,
                "return_code": result.returncode,
                "filename": file.filename
            })
            
        except subprocess.TimeoutExpired:
            return JSONResponse({
                "success": False,
                "error": "Execution timed out after 30 seconds"
            })
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not delete temp file {tmp_path}: {e}")
                
    except Exception as e:
        logger.error(f"Error in run_python_file: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "running"}

@app.get("/api/pwd")
async def get_pwd():
    """Get current working directory"""
    return {
        "success": True,
        "cwd": shell_state["cwd"]
    }

@app.get("/api/status")
async def status():
    """Status endpoint"""
    return {
        "status": "online",
        "service": "Telegram Server Manager Bot",
        "port": 7860,
        "web_console": "enabled"
    }

@app.post("/api/run-javascript")
async def run_javascript(request: Request):
    """Execute JavaScript code using Node.js"""
    try:
        data = await request.json()
        code = data.get("code", "").strip()
        admin_id = data.get("admin_id", "")
        
        if not code:
            return JSONResponse({"success": False, "error": "No code provided"})
        
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"Executing JavaScript code (length: {len(code)})")
        
        # Save code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            # Execute with Node.js
            result = subprocess.run(
                ['node', tmp_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=shell_state["cwd"],
                env=shell_state["env"]
            )
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "Code executed successfully (no output)"
            
            return JSONResponse({
                "success": True,
                "output": output,
                "return_code": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            return JSONResponse({
                "success": False,
                "error": "Execution timed out after 30 seconds"
            })
        except FileNotFoundError:
            return JSONResponse({
                "success": False,
                "error": "Node.js not found. Please install Node.js to execute JavaScript code."
            })
        finally:
            try:
                os.unlink(tmp_path)
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not delete temp file {tmp_path}: {e}")
                
    except Exception as e:
        logger.error(f"Error in run_javascript: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.post("/api/ai-chat")
async def ai_chat(request: Request):
    """Chat with OpenAI GPT for code assistance
    
    SECURITY NOTE: API keys are sent from client to server for OpenAI requests.
    In production, consider storing API keys server-side in environment variables
    or a secure key management system.
    """
    try:
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            return JSONResponse({
                "success": False,
                "error": "OpenAI library is not installed. Please install it with: pip install openai"
            })
        
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        api_key = data.get("api_key", "").strip()
        admin_id = data.get("admin_id", "")
        model = data.get("model", "gpt-4")  # Allow model selection, default to gpt-4
        
        if not prompt:
            return JSONResponse({"success": False, "error": "No prompt provided"})
        
        if not api_key:
            return JSONResponse({"success": False, "error": "No API key provided"})
        
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"AI Chat request (prompt length: {len(prompt)}, model: {model})")
        
        try:
            # Create OpenAI client
            client = openai.OpenAI(api_key=api_key)
            
            # List of models to try in order of preference
            models_to_try = [model, "gpt-3.5-turbo", "gpt-4o-mini"]
            
            last_error = None
            for model_name in models_to_try:
                try:
                    # Make API call
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are a professional coding assistant. Help users write, debug, and improve code. Provide clear, concise, and accurate responses. When providing code, use markdown code blocks with the appropriate language."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2000,
                        temperature=0.7
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    return JSONResponse({
                        "success": True,
                        "response": ai_response,
                        "model_used": model_name
                    })
                except Exception as model_error:
                    last_error = model_error
                    # If model not found, try next one
                    if "model" in str(model_error).lower() and "not found" in str(model_error).lower():
                        logger.warning(f"Model {model_name} not available, trying next...")
                        continue
                    else:
                        # For other errors, don't try other models
                        raise
            
            # If we get here, all models failed
            raise last_error if last_error else Exception("No models available")
            
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                error_msg = "Invalid API key. Please check your OpenAI API key."
            elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                error_msg = "Rate limit or quota exceeded. Please try again later or check your OpenAI account."
            return JSONResponse({
                "success": False,
                "error": f"OpenAI API error: {error_msg}"
            })
            
    except Exception as e:
        logger.error(f"Error in ai_chat: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.post("/api/save-file")
async def save_file(request: Request):
    """Save code to a file on the server"""
    try:
        data = await request.json()
        filename = data.get("filename", "").strip()
        content = data.get("content", "")
        admin_id = data.get("admin_id", "")
        
        if not filename:
            return JSONResponse({"success": False, "error": "No filename provided"})
        
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"Saving file: {filename}")
        
        # Security: prevent path traversal
        filename = os.path.basename(filename)
        
        # Save to current working directory
        file_path = os.path.join(shell_state["cwd"], filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return JSONResponse({
                "success": True,
                "path": file_path,
                "message": f"File saved successfully: {filename}"
            })
            
        except PermissionError:
            return JSONResponse({
                "success": False,
                "error": "Permission denied. Cannot write to this directory."
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": f"File save error: {str(e)}"
            })
            
    except Exception as e:
        logger.error(f"Error in save_file: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

@app.post("/api/test-api")
async def test_api(request: Request):
    """Test API endpoints with custom requests"""
    try:
        # Check if requests library is available
        if not REQUESTS_AVAILABLE:
            return JSONResponse({
                "success": False,
                "error": "Requests library is not installed. Please install it with: pip install requests"
            })
        
        data = await request.json()
        method = data.get("method", "GET").upper()
        url = data.get("url", "").strip()
        headers_text = data.get("headers", "{}")
        body_text = data.get("body", "{}")
        admin_id = data.get("admin_id", "")
        
        if not url:
            return JSONResponse({"success": False, "error": "No URL provided"})
        
        # Verify admin
        if not verify_admin(admin_id):
            return JSONResponse({"success": False, "error": "Unauthorized"})
        
        logger.info(f"API Test: {method} {url}")
        
        try:
            # Parse headers
            headers = {}
            if headers_text.strip():
                headers = json.loads(headers_text)
            
            # Parse body
            body = None
            if body_text.strip() and method in ['POST', 'PUT', 'PATCH']:
                body = json.loads(body_text)
            
            # Make request
            if method == 'GET':
                response = req_lib.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = req_lib.post(url, headers=headers, json=body, timeout=30)
            elif method == 'PUT':
                response = req_lib.put(url, headers=headers, json=body, timeout=30)
            elif method == 'DELETE':
                response = req_lib.delete(url, headers=headers, timeout=30)
            else:
                return JSONResponse({
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                })
            
            # Try to format response as JSON
            try:
                response_json = response.json()
                response_text = json.dumps(response_json, indent=2)
            except:
                response_text = response.text
            
            return JSONResponse({
                "success": True,
                "response": response_text,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            })
            
        except json.JSONDecodeError as e:
            return JSONResponse({
                "success": False,
                "error": f"Invalid JSON: {str(e)}"
            })
        except req_lib.exceptions.Timeout:
            return JSONResponse({
                "success": False,
                "error": "Request timed out after 30 seconds"
            })
        except req_lib.exceptions.RequestException as e:
            return JSONResponse({
                "success": False,
                "error": f"Request error: {str(e)}"
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": f"API test error: {str(e)}"
            })
            
    except Exception as e:
        logger.error(f"Error in test_api: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        })

if __name__ == "__main__":
    # Run on port 7860 for Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Starting web server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
