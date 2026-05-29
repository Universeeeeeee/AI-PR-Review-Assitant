# PR 1 Initialize Project Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the AI PR Review Assistant repository with a runnable project skeleton, configuration templates, and README draft for the first training-camp PR.

**Architecture:** This PR creates the repository foundation only. It defines the frontend/backend directory boundaries, documents the intended local workflow, and protects secrets through `.gitignore` and `backend/.env.example`; feature logic is intentionally left for later PRs.

**Tech Stack:** React + Vite + TypeScript frontend, FastAPI backend, GitHub REST API, pluggable AI Provider with DeepSeek and Mock modes.

---

## File Structure

- Create: `README.md` — project overview, Quick Start draft, architecture, current limits, PR roadmap.
- Create: `.gitignore` — secret, Python, Node, editor, build, and worktree ignores.
- Create: `backend/.env.example` — safe environment variable template for GitHub and DeepSeek configuration.
- Create: `backend/README.md` — backend skeleton responsibility and future run command.
- Create: `backend/app/__init__.py` — Python package marker.
- Create: `backend/app/main.py` — minimal FastAPI app placeholder with health endpoint for PR 1 smoke checks.
- Create: `backend/app/config.py` — basic settings loader for environment defaults.
- Create: `backend/requirements.txt` — minimal backend dependencies.
- Create: `backend/tests/test_health.py` — health endpoint regression test.
- Create: `frontend/README.md` — frontend skeleton responsibility and future run command.
- Create: `frontend/package.json` — minimal Vite React TypeScript scripts and dependencies.
- Create: `frontend/index.html` — Vite entry HTML.
- Create: `frontend/tsconfig.json` — TypeScript configuration for Vite.
- Create: `frontend/tsconfig.node.json` — TypeScript configuration for Vite config.
- Create: `frontend/vite.config.ts` — Vite React and Vitest configuration.
- Create: `frontend/src/App.test.tsx` — workbench placeholder behavior test.
- Create: `frontend/src/main.tsx` — React entrypoint.
- Create: `frontend/src/App.tsx` — placeholder workbench shell.
- Create: `frontend/src/styles.css` — basic non-marketing workbench styling.

## Task 1: Repository Metadata And Secret Safety

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `backend/.env.example`

- [ ] **Step 1: Create `.gitignore`**

Write ignores for local secrets, Python virtual environments, caches, Node dependencies, build outputs, logs, editor state, and local Superpowers worktrees.

- [ ] **Step 2: Create `backend/.env.example`**

Use safe empty placeholders:

```env
AI_PROVIDER=auto
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
GITHUB_TOKEN=
MAX_FILES=20
MAX_PATCH_CHARS=30000
REQUEST_TIMEOUT=60
AI_TIMEOUT_SECONDS=30
```

- [ ] **Step 3: Create README draft**

Cover project goal, core features, tech stack, architecture, Quick Start, Mock mode, current limits, deployment notes, and PR roadmap. State clearly that real `.env` files and API keys must not be committed.

## Task 2: Backend Skeleton

**Files:**
- Create: `backend/README.md`
- Create: `backend/requirements.txt`
- Create: `backend/tests/test_health.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Write the failing backend health test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_service_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-pr-review-assistant-backend",
    }
```

Run:

```powershell
cd backend
python -m pytest tests/test_health.py -q
```

Expected before implementation: FAIL because `app.main` does not exist.

- [ ] **Step 2: Add backend dependencies**

Use the minimal first-PR backend dependency set:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic-settings==2.7.1
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 3: Add backend settings**

Define defaults matching `.env.example`, without reading or storing real secrets in source.

- [ ] **Step 4: Add minimal FastAPI app**

Create `GET /health` returning:

```json
{
  "status": "ok",
  "service": "ai-pr-review-assistant-backend"
}
```

The real `/api/analyze-pr` endpoint is intentionally deferred to PR 2.

- [ ] **Step 5: Run the backend health test**

Run:

```powershell
cd backend
python -m pytest tests/test_health.py -q
```

Expected after implementation: PASS.

- [ ] **Step 6: Add backend README**

Document that this is the backend skeleton and list the future local run command:

```powershell
uvicorn app.main:app --reload
```

## Task 3: Frontend Skeleton

**Files:**
- Create: `frontend/README.md`
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Add Vite package metadata**

Use scripts:

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "test": "vitest run",
  "preview": "vite preview"
}
```

- [ ] **Step 2: Write the failing frontend workbench test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the initial PR review workbench shell", () => {
    render(<App />);

    expect(screen.getByText("AI PR Review Assistant")).toBeInTheDocument();
    expect(screen.getByText("Recent Analyses")).toBeInTheDocument();
    expect(screen.getByText("Analyze Pull Request")).toBeInTheDocument();
  });
});
```

Run:

```powershell
cd frontend
npm test -- --run
```

Expected before implementation: FAIL because `src/App.tsx` does not exist.

- [ ] **Step 3: Add React entrypoint**

Render `App` into `#root` and import `styles.css`.

- [ ] **Step 4: Add placeholder workbench shell**

Show a two-column shell with left "Recent Analyses" and right "Analyze Pull Request" sections, making clear that PR analysis arrives in later PRs.

- [ ] **Step 5: Run the frontend workbench test and build**

Run:

```powershell
cd frontend
npm test -- --run
npm run build
```

Expected after implementation: both commands exit with code 0.

- [ ] **Step 6: Add frontend README**

Document that this is the frontend skeleton and list the future local run command:

```powershell
npm install
npm run dev
```

## Task 4: Verification And Commit

**Files:**
- Verify all files created in Tasks 1-3.

- [ ] **Step 1: Check no secrets are staged**

Run:

```powershell
git status --short
Get-ChildItem -Recurse -Force -Filter ".env" | Select-Object FullName
```

Expected: no real `.env` file is listed; only `backend/.env.example` exists as a template.

- [ ] **Step 2: Verify backend import syntax if dependencies are unavailable**

Run:

```powershell
python -m py_compile backend/app/main.py backend/app/config.py
```

Expected: command exits with code 0.

- [ ] **Step 3: Verify frontend metadata is valid JSON**

Run:

```powershell
node -e "JSON.parse(require('fs').readFileSync('frontend/package.json','utf8')); console.log('package.json ok')"
```

Expected: `package.json ok`.

- [ ] **Step 4: Review diff**

Run:

```powershell
git diff --stat
git diff -- . ':!prompt.md'
```

Expected: PR 1 files only; `prompt.md` remains untracked and unstaged.

- [ ] **Step 5: Commit PR 1**

Run:

```powershell
git add README.md .gitignore backend frontend docs/superpowers/plans/2026-05-29-pr1-initialize-project.md
git status --short
git commit -m "chore: initialize project structure"
```

Expected: commit succeeds on branch `chore/init-project`, with no real `.env` or secret values staged.

## Self-Review

- Spec coverage: This plan covers only PR 1 from the approved design: project structure, README draft, `.gitignore`, `.env.example`, frontend skeleton, and backend skeleton. Later PRs implement Mock API, GitHub client, rule engine, AI providers, and full frontend behavior.
- Placeholder scan: The plan intentionally avoids implementation placeholders in committed code; README may describe future PRs, but source files should run as skeletons.
- Type consistency: Environment variable names match the approved design and `.env.example`.
