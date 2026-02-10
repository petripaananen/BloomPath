---
description: How to start BloomPath middleware and ngrok for local development
---

# Start BloomPath Locally

## Prerequisites
- Python 3.12+ with dependencies installed (`python -m pip install -r requirements.txt`)
- `.env` file configured (copy from `.env.template`)
- ngrok installed and authenticated

## Steps

// turbo
1. Verify environment:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
python verify_env.py
```

// turbo
2. Start ngrok in the background:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
powershell -File start_ngrok.ps1
```

// turbo
3. Start the middleware:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
$env:PYTHONIOENCODING = 'utf-8'
$env:DEFAULT_PROVIDER = 'linear'
$env:PORT = '5005'
$env:DEBUG = 'true'
python -m middleware.app
```

4. Verify health:
```powershell
Invoke-RestMethod -Uri http://localhost:5005/health
```

## Troubleshooting
- **Port in use**: Change `$env:PORT` or kill the existing process
- **ngrok not found**: Install from https://ngrok.com and run `ngrok config add-authtoken <token>`
- **Module errors**: Run `python -m pip install -r requirements.txt`
