# PR 4 Rule Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic Rule Engine that scans GitHub changed files and patch diff for first-version PR review risks.

**Architecture:** PR 4 introduces `rule_engine.py` as the only module that converts `GitHubPrContext` into structured `RiskItem` objects. `/api/analyze-pr` will run the Rule Engine after GitHub fetching and pass those risks into the existing Mock report path; DeepSeek and frontend rendering remain later PRs.

**Tech Stack:** FastAPI, Pydantic v2, pytest.

---

## File Structure

- Create: `backend/app/services/rule_engine.py` — patch parsing, file/path classification, risk rule scanning, stable risk IDs.
- Create: `backend/tests/test_rule_engine.py` — deterministic unit tests for security, stability, test, maintainability, and PR-level rules.
- Modify: `backend/app/main.py` — call Rule Engine before Mock analyzer.
- Modify: `backend/app/services/mock_analyzer.py` — accept rule risks and render them in JSON/Markdown.
- Modify: `backend/tests/test_analyze_pr.py` — assert endpoint includes rule-generated risks.
- Modify: `README.md` and `backend/README.md` — document PR 4 Rule Engine behavior and first-version limits.

## Task 1: Rule Engine Tests

**Files:**
- Create: `backend/tests/test_rule_engine.py`

- [ ] **Step 1: Write failing security rule tests**

Create a `GitHubPrContext` with added lines containing:

```text
+ API_TOKEN = "secret-value"
+ dangerouslySetInnerHTML={{ __html: content }}
+ eval(userInput)
+ query = "SELECT * FROM users WHERE id=" + user_id
```

Assert returned rules include:

- `hardcoded-secret` with severity `high`
- `unsafe-html` with severity `high`
- `unsafe-eval` with severity `high`
- `sql-string-concat` with severity `high`

- [ ] **Step 2: Write failing removed-protection tests**

Create a patch with deleted lines:

```text
- try:
- if user is None:
```

Assert returned rules include:

- `removed-error-handling` severity `medium`
- `removed-null-check` severity `medium`

- [ ] **Step 3: Write failing PR-level test coverage tests**

Create one context with core code changes and no test files. Assert `missing-tests` appears once. Create another context with a `tests/test_login.py` file. Assert `missing-tests` does not appear.

- [ ] **Step 4: Write failing config/large/todo tests**

Assert:

- config file changes produce `config-change`
- long patches produce `large-change`
- added TODO/FIXME/hack lines produce `unclear-todo-fixme`

- [ ] **Step 5: Verify red**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_rule_engine.py -q
```

Expected: FAIL because `rule_engine.py` does not exist.

## Task 2: Implement Rule Engine

**Files:**
- Create: `backend/app/services/rule_engine.py`

- [ ] **Step 1: Implement patch parsing**

Extract added and deleted lines while ignoring diff metadata lines such as `+++`, `---`, and `@@`.

- [ ] **Step 2: Implement file-level rules**

Implement first batch:

```text
high:
- hardcoded-secret
- unsafe-html
- unsafe-eval
- sql-string-concat
- removed-tests

medium:
- removed-error-handling
- removed-null-check
- config-change
- large-change

low:
- complex-condition
- unclear-todo-fixme
```

- [ ] **Step 3: Implement PR-level `missing-tests`**

Emit one `missing-tests` risk when core code changed and no test-like file changed.

- [ ] **Step 4: Implement stable risk IDs**

Use `ruleName + file + evidence` hash, e.g. `rule-hardcoded-secret-a8f31c`.

- [ ] **Step 5: Verify Rule Engine tests pass**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_rule_engine.py -q
```

Expected: PASS.

## Task 3: Wire Rule Engine Into Analyze API

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/mock_analyzer.py`
- Modify: `backend/tests/test_analyze_pr.py`

- [ ] **Step 1: Add endpoint test expectation**

Update fake GitHub context patch to include a real rule trigger and assert `/api/analyze-pr` returns that rule risk.

- [ ] **Step 2: Call Rule Engine in endpoint**

After GitHub context is fetched:

```text
rule_risks = analyze_rules(context)
return build_mock_analysis_from_context(context, rule_risks, duration_ms)
```

- [ ] **Step 3: Update Mock analyzer**

Use provided rule risks in `analysis.risks`; if none are present, return an empty risk list with `riskLevel="low"` and suggestion text that no deterministic first-pass risks were found.

- [ ] **Step 4: Verify endpoint tests pass**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_analyze_pr.py tests/test_health.py -q
```

Expected: PASS.

## Task 4: Docs

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] **Step 1: Update README status**

Add PR 4 status and list the first batch of Rule Engine categories.

- [ ] **Step 2: Update backend README**

Document that `/api/analyze-pr` now returns rule-generated `analysis.risks` before DeepSeek integration.

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
.\.venv\Scripts\python.exe -m py_compile app/main.py app/config.py app/schemas.py app/services/mock_analyzer.py app/services/github_client.py app/services/rule_engine.py
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
git add README.md backend docs/superpowers/plans/2026-05-29-pr4-rule-engine.md
git commit -m "feat: add rule-based risk scanning"
git push -u origin feat/rule-engine
```

Expected: PR 4 branch pushed.

## Self-Review

- Spec coverage: This plan covers PR 4 only: deterministic rule risk scanning and endpoint integration.
- Deferred work: DeepSeekProvider, AI Provider switching, Report Composer, frontend API integration, localStorage, and line-level comments remain later PRs.
- Type consistency: Rule Engine returns existing `RiskItem` schema from PR 2, so frontend response shape remains stable.
