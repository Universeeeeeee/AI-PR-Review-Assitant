# PR 3 GitHub PR Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add GitHub PR URL parsing and GitHub REST API fetching for PR metadata, changed files, and patch diff.

**Architecture:** PR 3 introduces `github_client.py` as the only module that knows GitHub REST endpoints and rate-limit/error translation. `/api/analyze-pr` will fetch real PR metadata/files first, then pass that context to the existing Mock analyzer so the API returns real PR shape without implementing Rule Engine or DeepSeek yet.

**Tech Stack:** FastAPI, Pydantic v2, httpx, pytest, FastAPI TestClient.

---

## File Structure

- Create: `backend/app/services/github_client.py` — URL parsing, GitHub REST client, truncation limits, and GitHub error types.
- Create: `backend/tests/test_github_client.py` — parser, client response mapping, truncation, and error tests using a fake transport.
- Modify: `backend/app/services/mock_analyzer.py` — accept fetched `GitHubPrContext` and generate summaries from real PR metadata/files.
- Modify: `backend/app/main.py` — call GitHub client before Mock analyzer, map GitHub errors to API error contract.
- Modify: `backend/tests/test_analyze_pr.py` — mock GitHub client dependency through app state and assert real metadata flows into response.
- Modify: `README.md` and `backend/README.md` — document PR 3 GitHub fetching behavior and optional `GITHUB_TOKEN`.

## Task 1: GitHub URL Parser And Client Tests

**Files:**
- Create: `backend/tests/test_github_client.py`

- [ ] **Step 1: Write failing URL parser tests**

Test valid URL:

```python
from app.services.github_client import parse_github_pr_url


def test_parse_github_pr_url_returns_owner_repo_and_number():
    parsed = parse_github_pr_url("https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2")

    assert parsed.owner == "Universeeeeeee"
    assert parsed.repo == "AI-PR-Review-Assitant"
    assert parsed.number == 2
    assert parsed.canonical_url == "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"
```

Test invalid URL raises `InvalidPrUrlError`.

- [ ] **Step 2: Write failing client mapping test**

Use `httpx.MockTransport` to return PR metadata and file payloads, then assert:

- title, author, base/head branch, changedFiles, additions, deletions are mapped.
- files include filename, status, additions, deletions, patch.
- API URLs include `/repos/{owner}/{repo}/pulls/{number}` and `/files`.

- [ ] **Step 3: Write failing truncation test**

Configure `max_files=1` and small `max_patch_chars`. Assert:

- only one file remains.
- patch is truncated.
- warnings contain `PATCH_TRUNCATED`.
- context `truncated` is true.

- [ ] **Step 4: Write failing GitHub error mapping tests**

Use fake responses:

- 404 -> `GitHubNotFoundError`
- 403 with rate-limit header `X-RateLimit-Remaining: 0` -> `GitHubRateLimitedError`
- 500 -> `GitHubApiError`

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_github_client.py -q
```

Expected: FAIL because `github_client.py` does not exist.

## Task 2: Implement GitHub Client

**Files:**
- Create: `backend/app/services/github_client.py`

- [ ] **Step 1: Add context dataclasses in `github_client.py`**

Create:

- `ParsedPullRequestUrl`
- `ChangedFile`
- `GitHubPrContext`

- [ ] **Step 2: Implement parser**

Accept only:

```text
https://github.com/{owner}/{repo}/pull/{number}
```

and allow trailing slash, query string, or fragment.

- [ ] **Step 3: Implement `GitHubClient.fetch_pr_context()`**

Use GitHub REST API:

```text
GET https://api.github.com/repos/{owner}/{repo}/pulls/{number}
GET https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files
```

Add headers:

```text
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Authorization: Bearer <GITHUB_TOKEN>   # only when configured
```

- [ ] **Step 4: Implement limits**

Apply `max_files` and `max_patch_chars`. Return `PATCH_TRUNCATED` warning when files or patch content are truncated.

- [ ] **Step 5: Verify client tests pass**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_github_client.py -q
```

Expected: PASS.

## Task 3: Wire Analyze Endpoint

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/mock_analyzer.py`
- Modify: `backend/tests/test_analyze_pr.py`

- [ ] **Step 1: Update endpoint tests to inject fake GitHub client**

Use `app.state.github_client` or dependency helper to inject fake context into `POST /api/analyze-pr`.

- [ ] **Step 2: Update Mock analyzer**

Add `build_mock_analysis_from_context(context, duration_ms)` and keep `build_mock_analysis(pr_url, duration_ms)` only if needed by tests.

- [ ] **Step 3: Map API errors**

Endpoint mappings:

```text
InvalidPrUrlError      -> 400 INVALID_PR_URL
GitHubNotFoundError    -> 404 GITHUB_NOT_FOUND
GitHubRateLimitedError -> 429 GITHUB_RATE_LIMITED
GitHubApiError         -> 502 GITHUB_API_ERROR
```

- [ ] **Step 4: Verify endpoint tests pass**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_analyze_pr.py tests/test_health.py -q
```

Expected: PASS.

## Task 4: Update Docs

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] **Step 1: Update README status**

Note PR 3 now fetches public GitHub PR metadata and changed files before returning Mock analysis.

- [ ] **Step 2: Update backend README**

Document optional `GITHUB_TOKEN` and the two GitHub REST endpoints used.

## Task 5: Verification And Commit

**Files:**
- Verify all changed files.

- [ ] **Step 1: Backend tests**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all backend tests pass.

- [ ] **Step 2: Backend compile**

```powershell
cd backend
.\.venv\Scripts\python.exe -m py_compile app/main.py app/config.py app/schemas.py app/services/mock_analyzer.py app/services/github_client.py
```

Expected: exit code 0.

- [ ] **Step 3: Frontend remains runnable**

```powershell
cd frontend
npm test
npm run build
```

Expected: frontend test and build pass.

- [ ] **Step 4: Secret and whitespace checks**

```powershell
git status --short
Get-ChildItem -Recurse -Force -Filter ".env" | Select-Object FullName
git diff --check
```

Expected: no real `.env`, no whitespace errors.

- [ ] **Step 5: Commit and push**

```powershell
git add README.md backend docs/superpowers/plans/2026-05-29-pr3-github-pr-client.md
git commit -m "feat: fetch GitHub PR metadata"
git push -u origin feat/github-pr-client
```

Expected: PR 3 branch pushed.

## Self-Review

- Spec coverage: This plan covers PR 3 only: GitHub PR URL parsing, PR metadata fetching, changed files/patch fetching, limit warnings, and endpoint error mapping.
- Deferred work: Rule Engine, DeepSeekProvider, AI Provider switching, frontend API integration, and localStorage remain later PRs.
- Type consistency: `PrMetadata`, `FileSummary`, `WarningItem`, and public JSON camelCase remain compatible with PR 2 response shape.
