---
title: HFS Code Platform
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# HFS Code Platform

A professional web-based code editor and execution environment. Write, run, and manage code in multiple languages through a clean, modern interface.

## Features

### 🎨 Modern UI/UX
- **Clean Design**: Consistent 8px spacing system, single-accent color palette
- **Mobile-First**: Fully responsive with slide-in sidebar navigation
- **Professional Feel**: Smooth animations, clear visual hierarchy

### 💻 Code Editor
- **Monaco Editor**: VS Code-powered editing experience
- **Multi-Language**: Python, JavaScript, HTML, CSS, JSON, Bash
- **Syntax Highlighting**: Full language support with IntelliSense

### 🤖 AI Assistant
- **Multiple Models**: GPT-3.5 Turbo, GPT-4, GPT-4o, or custom models
- **Code Generation**: Generate, review, and improve code with AI
- **Easy Integration**: Insert AI-generated code directly into editor

### 🔧 Development Tools
- **Terminal**: Execute shell commands with persistent directory
- **Python Executor**: Run Python code with full system access
- **JavaScript Runner**: Execute Node.js code
- **API Tester**: Test HTTP endpoints with formatted responses
- **File Manager**: Upload, save, and manage files

## Quick Start

### Hugging Face Spaces
1. Fork this repository
2. Create a new Space on Hugging Face
3. Select "Docker" as the SDK
4. Connect your GitHub repository
5. Deploy and access your platform!

### Local Development
```bash
# Clone the repository
git clone https://github.com/your-username/hfspac.git
cd hfspac

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 server.py
```

Access the interface at `http://localhost:7860`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/execute` | POST | Execute shell commands |
| `/api/eval` | POST | Execute Python code |
| `/api/run-javascript` | POST | Execute JavaScript code |
| `/api/run-file` | POST | Upload and run Python files |
| `/api/ai-chat` | POST | Chat with AI assistant |
| `/api/test-api` | POST | Test HTTP endpoints |
| `/api/save-file` | POST | Save files to server |
| `/health` | GET | Health check |

## Security

⚠️ This interface provides full system access. In production:
- Deploy behind a reverse proxy with HTTPS
- Implement proper authentication
- Use firewall rules to restrict access
- Monitor and log all command executions

## License

This project is licensed under the MIT License.