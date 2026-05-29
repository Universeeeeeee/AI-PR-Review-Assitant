# PR5 AI Provider Switching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pluggable AI Provider layer so `/api/analyze-pr` can use Mock mode by default and DeepSeek when configured.

**Architecture:** Keep GitHub fetching and rule scanning unchanged. Add `ai_provider.py` for provider selection and DeepSeek API interaction, and `report_composer.py` for converting provider drafts plus rule risks into the stable `AnalyzePrResponse` contract. The route remains synchronous and owns HTTP error mapping.

**Tech Stack:** FastAPI, Pydantic v2, httpx, pytest.

---

### Task 1: AI Provider Selection

**Files:**
- Create: `backend/app/services/ai_provider.py`
- Test: `backend/tests/test_ai_provider.py`

- [ ] **Step 1: Write failing tests**

Create tests that prove:
- `AI_PROVIDER=auto` with no key returns `MockProvider`.
- `AI_PROVIDER=auto` with a key returns `DeepSeekProvider`.
- `AI_PROVIDER=mock` always returns `MockProvider`.
- `AI_PROVIDER=deepseek` without a key raises `AIProviderError`.

- [ ] **Step 2: Verify red**

Run:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_ai_provider.py -q
```

Expected: fails because `app.services.ai_provider` does not exist.

- [ ] **Step 3: Implement provider selection**

Create `AIAnalysisDraft`, `AIProviderError`, `MockProvider`, `DeepSeekProvider`, and `build_ai_provider(settings)`.

- [ ] **Step 4: Verify green**

Run the same test file and confirm the provider selection tests pass.

### Task 2: DeepSeek JSON Draft Parsing

**Files:**
- Modify: `backend/app/services/ai_provider.py`
- Test: `backend/tests/test_ai_provider.py`

- [ ] **Step 1: Write failing tests**

Add tests using `httpx.MockTransport` that prove:
- DeepSeek sends `response_format={"type": "json_object"}`.
- A valid JSON response becomes an `AIAnalysisDraft`.
- JSON wrapped in Markdown fences is extracted.
- Invalid JSON raises `AIProviderError` with code `AI_INVALID_JSON`.

- [ ] **Step 2: Verify red**

Run:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_ai_provider.py -q
```

- [ ] **Step 3: Implement DeepSeekProvider.analyze**

Use `POST /chat/completions` with `Authorization: Bearer <key>`, the configured model, and a compact diff prompt built from PR metadata, changed files, patches, and rule risks.

- [ ] **Step 4: Verify green**

Run the provider tests again.

### Task 3: Stable Report Composition

**Files:**
- Create: `backend/app/services/report_composer.py`
- Modify: `backend/app/services/mock_analyzer.py`
- Test: `backend/tests/test_report_composer.py`

- [ ] **Step 1: Write failing tests**

Prove composer behavior:
- Rule risks are preserved.
- AI summary and suggestions are used when present.
- Provider metadata is set to `mock` or `deepseek`.
- Existing truncation warnings remain in `meta.warnings`.

- [ ] **Step 2: Verify red**

Run:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_report_composer.py -q
```

- [ ] **Step 3: Implement composer**

Move shared response-building logic into `compose_review_response(context, rule_risks, ai_draft, provider_name, mock, duration_ms, extra_warnings)`.

- [ ] **Step 4: Verify green**

Run composer tests.

### Task 4: Route Integration and Fallbacks

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_analyze_pr.py`

- [ ] **Step 1: Write failing tests**

Add route tests that prove:
- `app.state.ai_provider` is used when provided.
- DeepSeek-style provider success returns `meta.provider="deepseek"` and `mock=false`.
- Provider error in auto mode falls back to Mock and adds warning code `AI_PROVIDER_ERROR`.
- Provider error in forced deepseek mode returns 502 with `AI_PROVIDER_ERROR`.

- [ ] **Step 2: Verify red**

Run:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_analyze_pr.py -q
```

- [ ] **Step 3: Implement route wiring**

After GitHub context and rule risks, call the selected provider, compose the final response, and map forced-provider failures to the existing API error contract.

- [ ] **Step 4: Verify green**

Run route tests.

### Task 5: Documentation and Full Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `README.md`

- [ ] **Step 1: Update docs**

Document `AI_PROVIDER=auto|mock|deepseek`, fallback behavior, DeepSeek env vars, and Mock mode.

- [ ] **Step 2: Run full verification**

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm test -- --run
npm run build
```

- [ ] **Step 3: Commit**

```bash
git add backend docs README.md
git commit -m "feat: add pluggable AI provider"
```
