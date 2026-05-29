# PR 2 Mock Analyze API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first usable FastAPI `/api/analyze-pr` endpoint with stable response schemas and deterministic Mock analysis.

**Architecture:** PR 2 keeps the backend self-contained and does not call GitHub or DeepSeek yet. It introduces shared Pydantic schemas, a Mock analyzer service, and endpoint error handling so the frontend can integrate against the final API shape in later PRs.

**Tech Stack:** FastAPI, Pydantic v2, pytest, TestClient.

---

## File Structure

- Create: `backend/app/schemas.py` — shared request, response, metadata, warning, file summary, risk, and analysis schemas.
- Create: `backend/app/services/__init__.py` — services package marker.
- Create: `backend/app/services/mock_analyzer.py` — deterministic Mock analysis service for valid public GitHub PR URLs.
- Create: `backend/tests/test_analyze_pr.py` — API tests for successful Mock response and invalid URL error response.
- Modify: `backend/app/main.py` — add `POST /api/analyze-pr` endpoint using the Mock analyzer.
- Modify: `backend/README.md` — document the current Mock API endpoint.
- Modify: `README.md` — update project status and API availability for PR 2.

## Task 1: Write API Contract Tests

**Files:**
- Create: `backend/tests/test_analyze_pr.py`

- [ ] **Step 1: Write failing success test**

Create a test that posts `{"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/1"}` to `/api/analyze-pr` and expects:

- HTTP 200.
- `pr.owner`, `pr.repo`, and `pr.number` parsed from the URL.
- camelCase fields such as `changedFiles`, `riskLevel`, `fileSummaries`, `markdownReview`, `analyzedAt`, and `durationMs`.
- `meta.provider == "mock"` and `meta.mock == true`.
- `meta.warnings` is an object array.

- [ ] **Step 2: Write failing invalid URL test**

Create a test that posts `{"prUrl": "https://example.com/not-a-pr"}` and expects:

```json
{
  "detail": {
    "code": "INVALID_PR_URL",
    "message": "请输入有效的 GitHub Pull Request URL。"
  }
}
```

with HTTP 400.

- [ ] **Step 3: Verify red**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_analyze_pr.py -q
```

Expected: FAIL because `/api/analyze-pr` and schemas do not exist yet.

## Task 2: Add Schemas And Mock Analyzer

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/mock_analyzer.py`

- [ ] **Step 1: Add Pydantic schemas**

Define the stable public API shape with snake_case Python fields and camelCase JSON aliases.

- [ ] **Step 2: Add Mock analyzer service**

Implement a deterministic analyzer that accepts only GitHub PR URLs in the shape:

```text
https://github.com/{owner}/{repo}/pull/{number}
```

It returns a realistic `AnalyzePrResponse` with Mock warning and Markdown Review text.

## Task 3: Add FastAPI Endpoint

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Wire endpoint**

Add `POST /api/analyze-pr` with `AnalyzePrRequest` input and `AnalyzePrResponse` output.

- [ ] **Step 2: Map invalid URL to API error contract**

Catch `InvalidPrUrlError` and return HTTP 400 with:

```json
{
  "detail": {
    "code": "INVALID_PR_URL",
    "message": "请输入有效的 GitHub Pull Request URL。"
  }
}
```

- [ ] **Step 3: Verify green**

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

- [ ] **Step 1: Update top-level README**

Note that PR 2 provides a Mock `/api/analyze-pr` endpoint and that GitHub fetching and DeepSeek integration come in later PRs.

- [ ] **Step 2: Update backend README**

Add a curl or PowerShell example for the Mock analyze endpoint.

## Task 5: Verification And Commit

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run backend tests**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all backend tests pass.

- [ ] **Step 2: Compile backend modules**

```powershell
cd backend
.\.venv\Scripts\python.exe -m py_compile app/main.py app/config.py app/schemas.py app/services/mock_analyzer.py
```

Expected: command exits with code 0.

- [ ] **Step 3: Run frontend checks to keep main runnable**

```powershell
cd frontend
npm test
npm run build
```

Expected: frontend test and build pass.

- [ ] **Step 4: Check secret safety and staged files**

```powershell
git status --short
Get-ChildItem -Recurse -Force -Filter ".env" | Select-Object FullName
git diff --check
```

Expected: no real `.env`; whitespace check passes.

- [ ] **Step 5: Commit PR 2**

```powershell
git add README.md backend docs/superpowers/plans/2026-05-29-pr2-mock-analyze-api.md
git commit -m "feat: add mock PR analysis API"
git push -u origin feat/mock-analyze-api
```

Expected: branch pushed for PR 2.

## Self-Review

- Spec coverage: This plan covers only PR 2: stable schema and Mock `/api/analyze-pr`. It intentionally does not implement GitHub API fetching, Rule Engine, DeepSeekProvider, or frontend API integration.
- Placeholder scan: No implementation placeholders are needed for PR 2; deterministic Mock output is enough for endpoint integration.
- Type consistency: Public JSON uses camelCase aliases, while Python uses snake_case fields.
