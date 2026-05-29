# Backend

FastAPI backend for AI PR Review Assistant.

The backend currently provides:

- `GET /health`
- `POST /api/analyze-pr` with GitHub PR metadata fetching, changed files fetching, Rule Engine risk scanning, pluggable AI Provider analysis, and the stable response schema

The analyze flow uses `MockProvider` by default when no DeepSeek key is configured. When `DEEPSEEK_API_KEY` is present and `AI_PROVIDER=auto`, it calls DeepSeek through the OpenAI-compatible chat completions API and then composes a stable response through `report_composer.py`.

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

## AI Provider Configuration

```env
AI_PROVIDER=auto
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
AI_TIMEOUT_SECONDS=30
```

Provider behavior:

```text
AI_PROVIDER=auto
- With DEEPSEEK_API_KEY: use DeepSeekProvider
- Without DEEPSEEK_API_KEY: use MockProvider
- DeepSeek timeout / API error / invalid JSON: fall back to MockProvider and return a warning

AI_PROVIDER=mock
- Always use MockProvider

AI_PROVIDER=deepseek
- Require DEEPSEEK_API_KEY
- Provider failures return HTTP 502 with detail.code=AI_PROVIDER_ERROR
```

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
