# PR8 Final README Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the first-version delivery documentation with reviewer-friendly run instructions, deployment notes, design notes, and demo screenshots.

**Architecture:** Keep application code unchanged unless screenshot generation exposes a documentation-blocking issue. Add documentation under `README.md` and `docs/`, and add static image assets under `docs/assets/` so reviewers can inspect the project without running it first.

**Tech Stack:** Markdown documentation, Mermaid diagrams, React/Vite local app for screenshots, FastAPI local backend for screenshot data.

---

### Task 1: Finalize Reviewer README

**Files:**
- Modify: `README.md`

- [x] **Step 1: Add reviewer path**

Add a concise section that tells reviewers the recommended path:

```md
## Recommended Review Path

1. Follow Quick Start to run the backend and frontend locally.
2. Keep `AI_PROVIDER=auto` and leave `DEEPSEEK_API_KEY` empty for Mock mode, or configure DeepSeek for real model output.
3. Open `http://localhost:5173`.
4. Analyze a public GitHub PR URL such as `https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/7`.
5. Review the summary, possible risks, warnings, and Markdown Review output.
```

- [x] **Step 2: Add API contract summary**

Add a compact contract section for `POST /api/analyze-pr` with request shape, successful response layers, and error shape.

- [x] **Step 3: Expand deployment notes**

Add frontend and backend deployment guidance without requiring an already-live demo URL:

```md
Frontend: Vercel / Netlify with `frontend` as the app root.
Backend: Render / Railway / Fly.io with `backend` as the service root.
```

Include required environment variables for online deployment and CORS.

- [x] **Step 4: Add verification commands**

Add commands for backend tests, frontend tests, and frontend build so reviewers can reproduce the validation.

### Task 2: Add Design Notes

**Files:**
- Create: `docs/design.md`
- Modify: `README.md`

- [x] **Step 1: Create design document**

Write `docs/design.md` with:

- Product positioning.
- System architecture.
- Backend flow.
- Rule Engine strategy.
- AI Provider strategy.
- Frontend workbench strategy.
- Data and persistence boundary.
- Failure and fallback behavior.
- Current limits and future work.

- [x] **Step 2: Link design document from README**

Add a README link to `docs/design.md`.

### Task 3: Add Demo Screenshot Asset

**Files:**
- Create: `docs/assets/`
- Create: `docs/assets/workbench-demo.png`
- Modify: `README.md`

- [x] **Step 1: Start local backend and frontend**

Run backend on `http://127.0.0.1:8000` and frontend on `http://127.0.0.1:5173`.

- [x] **Step 2: Generate demo screenshot**

Use a local browser automation path to capture the workbench after loading a sample analysis. If browser automation is not available, capture the initial workbench state and document that the live result appears after analyzing a PR URL.

- [x] **Step 3: Reference screenshot**

Add the screenshot to README:

```md
![AI PR Review Assistant workbench](docs/assets/workbench-demo.png)
```

### Task 4: Verification and Git

**Files:**
- Modified docs and assets from Tasks 1-3.

- [x] **Step 1: Run full verification**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm test -- --run
npm run build
```

- [x] **Step 2: Run repository checks**

```powershell
git diff --check
git status --short --ignored
```

Confirm no real `.env`, API key, token, cache directory, `dist`, or `node_modules` is staged.

- [x] **Step 3: Commit and push**

```powershell
git add README.md docs
git commit -m "docs: polish final review documentation"
git push -u origin docs/final-readme-polish
```
