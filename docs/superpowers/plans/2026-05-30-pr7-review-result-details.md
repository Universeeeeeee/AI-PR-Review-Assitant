# PR7 Review Result Details Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the frontend review result experience with detailed result sections, Markdown copy, and localStorage recent analyses.

**Architecture:** Keep backend unchanged. Add a small `history.ts` storage module that owns localStorage parsing, de-duplication, and max history length. Extend `App.tsx` to render full `AnalyzePrResponse` details, copy `analysis.markdownReview`, save successful analyses, restore history items without refetching, and clear history.

**Tech Stack:** React 19, Vite, TypeScript, Testing Library, Vitest.

---

### Task 1: LocalStorage History Module

**Files:**
- Create: `frontend/src/history.ts`
- Test: `frontend/src/history.test.ts`

- [x] **Step 1: Write failing tests**

Cover:
- Empty/missing storage returns `[]`.
- Saving an analysis creates an item with stable PR metadata and full result.
- Saving the same PR URL moves it to the top instead of duplicating.
- History is capped to 10 items.
- Invalid stored JSON is ignored.

- [x] **Step 2: Verify red**

Run:

```powershell
cd frontend
npm test -- --run src/history.test.ts
```

Expected: fails because `src/history.ts` does not exist.

- [x] **Step 3: Implement `history.ts`**

Export `AnalysisHistoryItem`, `loadAnalysisHistory`, `saveAnalysisHistoryItem`, and `clearAnalysisHistory`.

- [x] **Step 4: Verify green**

Run the history test file and confirm it passes.

### Task 2: Detailed Result Rendering and Markdown Copy

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [x] **Step 1: Write failing tests**

Cover:
- Successful analysis renders file summaries, possible risks, suggestions, and Markdown Review.
- Clicking `Copy Markdown` calls `navigator.clipboard.writeText(result.analysis.markdownReview)` and shows `Markdown copied.`

- [x] **Step 2: Verify red**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx
```

Expected: fails because detailed sections and copy button do not exist.

- [x] **Step 3: Implement detailed result UI**

Add compact sections inside the result panel:
- File summaries
- Possible risks
- Suggestions
- Markdown Review preview and copy button

- [x] **Step 4: Verify green**

Run the app test file.

### Task 3: Recent Analyses Sidebar

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [x] **Step 1: Write failing tests**

Cover:
- Successful analysis is saved to localStorage and displayed in the sidebar.
- Clicking a history item restores the saved result without calling the API again.
- Clicking `Clear` removes history and returns the sidebar to empty state.

- [x] **Step 2: Verify red**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx
```

- [x] **Step 3: Implement sidebar history**

Load history on initial render, update it after successful analysis, and support restore/clear.

- [x] **Step 4: Verify green**

Run app tests.

### Task 4: Documentation and Full Verification

**Files:**
- Modify: `README.md`
- Modify: `frontend/README.md`

- [x] **Step 1: Update docs**

Update current status and frontend feature notes to mention result details, Markdown copy, and localStorage history.

- [x] **Step 2: Run full verification**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm test -- --run
npm run build
```

- [x] **Step 3: Commit**

```powershell
git add README.md frontend docs/superpowers/plans/2026-05-30-pr7-review-result-details.md
git commit -m "feat: add review result details and history"
```
