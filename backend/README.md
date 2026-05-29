# Backend

FastAPI backend for AI PR Review Assistant.

PR 1 includes only the project skeleton and `GET /health`. The main PR analysis endpoint, GitHub client, rule engine, AI Provider, and report composer will be added in later PRs.

## Local Development

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Health check:

```text
http://localhost:8000/health
```

Run tests:

```powershell
python -m pytest
```
