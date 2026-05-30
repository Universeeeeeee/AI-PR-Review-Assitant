# PR6 Frontend Workbench API Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the React workbench submit a GitHub PR URL to the FastAPI backend and render basic loading, success, warning, and error states.

**Architecture:** Keep PR6 focused on API integration and first-level result visibility. Add a frontend API client with typed response/error handling, wire it into `App.tsx`, and add backend CORS support so the Vite app can call `http://localhost:8000` during local demos. Full result sections, Markdown copy, and localStorage history remain PR7.

**Tech Stack:** React 19, Vite, TypeScript, Testing Library, Vitest, FastAPI.

---

### Task 1: Frontend API Client Contract

**Files:**
- Create: `frontend/src/api.ts`
- Test: `frontend/src/api.test.ts`

- [ ] **Step 1: Write failing tests**

Cover:
- `analyzePullRequest("https://github.com/owner/repo/pull/1")` sends `POST /api/analyze-pr` with `{ prUrl }`.
- Successful JSON returns the parsed `AnalyzePrResponse`.
- Backend error JSON `{ detail: { code, message } }` throws an `AnalyzePrApiError` with `code` and `message`.

- [ ] **Step 2: Verify red**

Run:

```powershell
cd frontend
npm test -- --run src/api.test.ts
```

Expected: fail because `src/api.ts` does not exist.

- [ ] **Step 3: Implement `api.ts`**

Define TypeScript types for the response shape used by the UI and implement `analyzePullRequest(prUrl, fetchImpl = fetch)`.

- [ ] **Step 4: Verify green**

Run the same test file and confirm it passes.

### Task 2: Workbench Submit and Result States

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing tests**

Cover:
- User enters a PR URL and submits; the workbench calls the API client and shows loading text.
- Successful response renders PR title, risk level, summary, provider label, and warning messages.
- Error response renders backend `detail.message` and keeps the input editable for retry.

- [ ] **Step 2: Verify red**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx
```

Expected: fail because the form is not wired to state or API calls.

- [ ] **Step 3: Implement component behavior**

Use `useState`, `onSubmit`, and the API client. Keep result display intentionally compact: PR overview, status badges, summary, and warning list only.

- [ ] **Step 4: Verify green**

Run the app tests again.

### Task 3: Backend CORS for Local Vite

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Write failing test**

Add a CORS preflight test with `Origin: http://localhost:5173` and `Access-Control-Request-Method: POST`.

- [ ] **Step 2: Verify red**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_health.py -q
```

Expected: fail because CORS middleware is not configured.

- [ ] **Step 3: Implement CORS**

Add `cors_origins` setting with default `http://localhost:5173,http://127.0.0.1:5173` and configure `CORSMiddleware`.

- [ ] **Step 4: Verify green**

Run the backend health/CORS test.

### Task 4: Documentation and Full Verification

**Files:**
- Modify: `frontend/README.md`
- Modify: `README.md`

- [ ] **Step 1: Update docs**

Document `VITE_API_BASE_URL` and local backend URL expectations. Update current status to include PR6.

- [ ] **Step 2: Run full verification**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm test -- --run
npm run build
```

- [ ] **Step 3: Commit**

```powershell
git add README.md backend frontend docs/superpowers/plans/2026-05-30-pr6-frontend-workbench-api.md
git commit -m "feat: connect frontend workbench to analyze API"
```
