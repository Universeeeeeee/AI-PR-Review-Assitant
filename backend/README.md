# Backend

FastAPI backend for AI PR Review Assistant.

The backend currently provides:

- `GET /health`
- `POST /api/analyze-pr` with GitHub PR metadata fetching, changed files fetching, Rule Engine risk scanning, deterministic Mock analysis, and the stable response schema

DeepSeekProvider and Report Composer will be added in later PRs.

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

Mock PR analysis:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/analyze-pr `
  -ContentType "application/json" `
  -Body '{"prUrl":"https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/1"}'
```

The analyze endpoint currently calls these GitHub REST API endpoints for public PRs:

```text
GET /repos/{owner}/{repo}/pulls/{pull_number}
GET /repos/{owner}/{repo}/pulls/{pull_number}/files
```

Set `GITHUB_TOKEN` in `backend/.env` to increase GitHub API rate limits. Do not commit `.env`.

Rule Engine currently scans changed files and patch diff for:

```text
hardcoded-secret
unsafe-html
unsafe-eval
sql-string-concat
removed-error-handling
removed-null-check
config-change
large-change
missing-tests
removed-tests
complex-condition
unclear-todo-fixme
```

Run tests:

```powershell
python -m pytest
```
