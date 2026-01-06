---
title: Remote Command Runner Web Console
emoji: 🌐
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
---

# Remote Command Runner - Web Console

A powerful web-based interface for remote server management. Execute commands, run Python code, and manage your server through a modern, professional web interface.

## Hugging Face Spaces Deployment

This application is designed for Hugging Face Spaces and provides instant 24/7 web access!

### Features:
- ✅ Modern web interface on port 7860
- ✅ Execute shell commands remotely
- ✅ Run Python code with full system access
- ✅ Upload and execute Python files
- ✅ System information dashboard
- ✅ No configuration required - works out of the box!
- ✅ FastAPI-powered REST API
- ✅ Automatic session cleanup

### Deploy to Hugging Face Spaces:
1. Fork this repository
2. Create a new Space on Hugging Face
3. Select "Docker" as the SDK
4. Connect your GitHub repository
5. Deploy and access your web console!

## Features

### Web Console
- **Command Executor**: Run any shell command directly from the browser
- **Python Evaluator**: Execute Python code with full system access
- **File Executor**: Upload and run Python files
- **System Dashboard**: View system information, disk usage, memory, and network status
- **Professional UI**: Modern, responsive interface with real-time output

### Security
The web interface provides full system access. In production:
- Deploy behind a reverse proxy with HTTPS
- Implement proper authentication
- Use firewall rules to restrict access
- Monitor and log all command executions

## Prerequisites

* Python 3.x installed on your system
* FastAPI and Uvicorn for the web server

## Installation

1. Clone this repository to your server.

2. Install the required dependencies by running `pip install -r requirements.txt` in the terminal.

3. (Optional) For authentication, create a `config` file based on `config.example` with your admin chat ID.

4. Run the server by running `./start.sh` or `python3 server.py` in the terminal.

5. Access the web interface at `http://localhost:7860`

## Usage

Simply open your web browser and navigate to the server's address (typically `http://localhost:7860` for local, or your Hugging Face Space URL).

The web interface provides:
- **Command Executor**: Run shell commands
- **Python Evaluator**: Execute Python code snippets
- **File Uploader**: Upload and run Python scripts
- **System Info**: Quick access to system metrics

## API Endpoints

- `GET /` - Web interface
- `POST /api/execute` - Execute shell commands
- `POST /api/eval` - Execute Python code
- `POST /api/run-file` - Upload and run Python files
- `GET /health` - Health check
- `GET /api/status` - Service status

## Optional: Telegram Bot

The repository includes a legacy Telegram bot (`bot.py`) that can be enabled if needed. To use it:
1. Create a `config` file with your Telegram bot token and admin chat ID
2. Modify `start.sh` to include bot startup
3. The bot provides remote command execution via Telegram

## Contributions

Contributions to this project are welcome! If you have ideas for new features or improvements, feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License.