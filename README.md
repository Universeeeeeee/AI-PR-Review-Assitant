# AI PR Review Assistant

<p align="right">
语言 / Language: <a href="#中文">中文</a> | <a href="#english">English</a>
</p>

<a id="中文"></a>

## 中文

AI PR Review Assistant 是一个面向开发者的 Web 工具。用户输入 GitHub Pull Request 链接后，系统会获取 PR 基本信息、changed files 和 patch diff，并通过规则引擎与 AI Provider 混合分析，生成 PR 总结、可能风险、Review 建议和可复制的 Markdown Review。

第一版定位是辅助人工 Review，而不是替代人工结论。页面和报告会使用“可能风险”“建议确认”“建议补充测试”等措辞，帮助评审者更快聚焦需要关注的变更。

### 评委快速版

视频演示链接：https://pan.baidu.com/s/1IIdBLdoHiY6rSbEbyEBanw?pwd=1234  提取码: 1234

本项目不需要 AI API Key 也能完整运行。默认保持 `AI_PROVIDER=auto` 且不填写 `DEEPSEEK_API_KEY` 时，系统会使用高质量 Mock 模式生成报告。

Windows PowerShell:

```powershell
git clone https://github.com/Universeeeeeee/AI-PR-Review-Assitant.git
cd AI-PR-Review-Assitant
.\scripts\start-dev.ps1
```

macOS / Linux:

```bash
git clone https://github.com/Universeeeeeee/AI-PR-Review-Assitant.git
cd AI-PR-Review-Assitant
chmod +x scripts/start-dev.sh scripts/stop-dev.sh
./scripts/start-dev.sh
```

打开：

```text
http://localhost:5173
```

示例 PR：

```text
https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/7
```

![AI PR Review Assistant workbench](docs/assets/workbench-demo.png)

详细架构与设计说明见：[docs/design.md](docs/design.md)。

### 核心功能

- 输入公开 GitHub PR 链接并分析变更。
- 基于 diff 和文件路径执行规则风险扫描。
- 展示 PR 概览、总体风险级别、PR 总结、文件摘要、可能风险和 Review 建议。
- 支持一键复制 Markdown Review。
- 支持 DeepSeek 真实模型分析。
- 未配置 DeepSeek API Key 时自动进入 Mock 模式，保证本地演示稳定。
- 支持可选 GitHub Token，提高公开 GitHub API 访问限额。
- 最近分析记录保存在浏览器 localStorage。

### 技术栈

```text
frontend: React + Vite + TypeScript
backend:  FastAPI
api:      GitHub REST API
ai:       DeepSeekProvider / MockProvider
storage:  browser localStorage
```

### 架构

```text
frontend/
  React + Vite + TypeScript
  - PR 链接输入
  - 分析结果展示
  - 风险级别展示
  - Markdown Review 复制
  - 最近分析 localStorage

backend/
  FastAPI
  - /api/analyze-pr

  app/
    main.py
    config.py
    schemas.py
    services/
      github_client.py
      rule_engine.py
      ai_provider.py
      report_composer.py
```

后端主流程：

```text
POST /api/analyze-pr
  -> 解析 GitHub PR URL
  -> 获取 PR 元信息
  -> 获取 changed files 和 patch diff
  -> 截断超大 diff
  -> 执行 Rule Engine
  -> 执行 AI Provider
  -> 生成稳定的 ReviewResult JSON 和 Markdown
  -> 返回前端
```

### 当前状态

```text
PR 1: 初始化项目结构、README 草案、前端外壳和后端健康检查。
PR 2: 实现 Mock /api/analyze-pr 接口和共享响应结构。
PR 3: 在 Mock 分析前获取 GitHub PR 元信息和 changed files。
PR 4: Rule Engine 基于 changed files 和 patch diff 生成确定性风险提示。
PR 5: 增加可插拔 AI Provider，支持 Mock / DeepSeek 切换和降级。
PR 6: 前端工作台提交 PR 链接并展示基础状态、警告和错误。
PR 7: 前端展示详细结果，支持 Markdown Review 复制和 localStorage 最近分析。
PR 8: 完善 README、部署说明、设计说明和截图。
PR 9: 优化评委快速启动路径，补充跨平台启动脚本和停止服务脚本。
```

### 推荐评审路径

1. 按快速开始本地启动后端和前端。
2. 保持 `AI_PROVIDER=auto`，并留空 `DEEPSEEK_API_KEY` 使用 Mock 模式；也可以配置 DeepSeek API Key 获取真实模型输出。
3. 打开 `http://localhost:5173`。
4. 输入公开 GitHub PR 链接，例如：

```text
https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/7
```

5. 查看 PR 元信息、总结、可能风险、警告提示、Review 建议和 Markdown Review。
6. 点击 `Copy Markdown` 复制生成的 Review 文案。

### 快速开始

环境要求：

- Python 3.11+
- Node.js 20+
- npm

推荐方式：一键启动本地开发环境。

Windows PowerShell:

```powershell
.\scripts\start-dev.ps1
```

如果 PowerShell 执行策略拦截脚本，可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

macOS / Linux:

```bash
chmod +x scripts/start-dev.sh scripts/stop-dev.sh
./scripts/start-dev.sh
```

启动后访问：

```text
http://localhost:5173
```

未配置 DeepSeek API Key 时，系统会自动使用 Mock 模式，仍可体验完整分析流程。

停止本地服务：

Windows PowerShell:

```powershell
.\scripts\stop-dev.ps1
```

macOS / Linux:

```bash
./scripts/stop-dev.sh
```

#### 手动启动

后端：

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### 环境变量

复制 `backend/.env.example` 为 `backend/.env`：

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
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

前端可以通过 `frontend/.env` 配置后端地址：

```env
VITE_API_BASE_URL=http://localhost:8000
```

不要提交真实 `.env` 文件、API Key 或 GitHub Token。`.gitignore` 已配置为忽略本地密钥文件，同时保留 `.env.example` 模板。

DeepSeek API 兼容性可参考官方文档：[Your First API Call](https://api-docs.deepseek.com/) 和 [Models](https://api-docs.deepseek.com/api/list-models)。

### API 契约

`POST /api/analyze-pr`

请求：

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

成功响应分三层：

```text
pr        GitHub PR metadata
analysis  summary, riskLevel, truncated, fileSummaries, risks, suggestions, markdownReview
meta      provider, mock, analyzedAt, durationMs, warnings
```

错误响应：

```json
{
  "detail": {
    "code": "INVALID_PR_URL",
    "message": "请输入有效的 GitHub Pull Request URL。"
  }
}
```

错误码：

```text
INVALID_PR_URL        400
GITHUB_NOT_FOUND      404
GITHUB_RATE_LIMITED   429
GITHUB_API_ERROR      502
AI_PROVIDER_ERROR     502
```

### Mock 模式

默认模式：

```text
AI_PROVIDER=auto
```

行为：

- `AI_PROVIDER=auto` 且没有 `DEEPSEEK_API_KEY`：使用 `MockProvider`。
- `AI_PROVIDER=auto` 且配置了 `DEEPSEEK_API_KEY`：使用 `DeepSeekProvider`。
- `AI_PROVIDER=mock`：强制使用 `MockProvider`。
- `AI_PROVIDER=deepseek`：强制使用 `DeepSeekProvider`，缺少 Key 或调用失败时返回 `AI_PROVIDER_ERROR`。
- auto 模式下 DeepSeek 超时、API 错误或返回非 JSON 时，会降级到 Mock 模式并返回警告提示。
- Mock 与 DeepSeek 都会保留 Rule Engine 的确定性风险结果。
- Mock 模式不是静态占位数据。它会基于真实 GitHub PR 元信息、changed files、patch diff、规则风险、测试变更和截断状态生成确定性的总结、文件摘要和 Review 建议，保证评委没有 API Key 时也能体验完整流程。

### 规则引擎

当前 Rule Engine 基于 changed file path 和 patch diff 行扫描，不做 AST 或跨文件语义分析。

第一批规则：

```text
security: hardcoded-secret, unsafe-html, unsafe-eval, sql-string-concat
stability: removed-error-handling, removed-null-check, config-change, large-change
tests: missing-tests, removed-tests
maintainability: complex-condition, unclear-todo-fixme
```

规则结果是 Review 提示，不是绝对漏洞判定。报告措辞应保持“可能风险”“建议确认”。

前端会展示：

```text
当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。
```

auto 降级时也会展示 `AI_TIMEOUT`、`AI_PROVIDER_ERROR` 或 `AI_INVALID_JSON` 等警告提示。

### 验证

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

前端：

```powershell
cd frontend
npm test -- --run
npm run build
```

### 当前限制

- 当前版本主要支持公开 GitHub PR。
- 不支持私有仓库 PR 的完整权限流程。
- 不抓取完整仓库内容，仅分析 PR changed files 和 patch diff。
- 不做 AST 级语义分析。
- 不做跨文件调用链分析。
- 不做异步任务队列。
- 不使用数据库，最近分析仅保存在浏览器 localStorage。
- 大型 PR 会进行 diff 截断分析。

### 交付计划

开发按小 PR 拆分，每个 PR 保持 `main` 可运行，并提供清晰的 PR 描述、实现思路和测试方式。

```text
PR 1: 初始化项目结构、README 草案、.gitignore 和 .env.example
PR 2: FastAPI Mock 分析接口和共享 schema
PR 3: GitHub PR URL 解析和 changed files 获取
PR 4: Rule Engine 基础风险扫描
PR 5: DeepSeekProvider + MockProvider 切换与降级
PR 6: React 工作台基础页面和 API 集成
PR 7: 结果展示、Markdown 复制和 localStorage 最近分析
PR 8: README 完善、部署说明、设计说明和截图
PR 9: 评委快速启动、macOS / Linux 脚本和停止服务脚本
```

PR 描述模板：

```md
## 功能描述

## 实现思路

## 测试方式
```

### 部署方案

本地运行是第一优先级。在线部署可沿用前后端分离方案。

Docker 不作为默认快速开始路径。它可以作为后续统一部署方案补充，但本项目第一版优先保证评审能用本地脚本快速复现。

前端部署：

- 使用 Vercel 或 Netlify。
- 项目根目录设置为 `frontend`。
- 构建命令：`npm run build`。
- 发布目录：`dist`。
- 配置 `VITE_API_BASE_URL` 指向后端地址。

后端部署：

- 使用 Render、Railway 或 Fly.io。
- 服务根目录设置为 `backend`。
- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
- 配置 `AI_PROVIDER`、`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、`GITHUB_TOKEN`、`MAX_FILES`、`MAX_PATCH_CHARS`、`REQUEST_TIMEOUT`、`AI_TIMEOUT_SECONDS` 和 `CORS_ORIGINS`。
- `CORS_ORIGINS` 应设置为线上前端域名。

如果没有线上 Demo，评审仍可按快速开始本地复现完整流程。

### 原创工作与依赖

本项目为训练营 AI PR Review Assistant 题目开发。第三方依赖列在 `backend/requirements.txt` 和 `frontend/package.json` 中；项目功能代码位于 `backend/app` 和 `frontend/src`。

---

<a id="english"></a>

## English

AI PR Review Assistant is a developer-facing web tool. After a user enters a GitHub Pull Request URL, the system fetches PR metadata, changed files, and patch diff, then combines deterministic rule scanning with a pluggable AI Provider to generate a PR summary, possible risks, review suggestions, and a copyable Markdown Review.

The first version is designed to assist human reviewers, not replace their judgment. The UI and report use cautious wording such as “possible risks” and “suggested confirmation”.

### For Reviewers

This project can run end-to-end without an AI API key. By default, when `AI_PROVIDER=auto` and `DEEPSEEK_API_KEY` is empty, the system uses high-quality Mock mode to generate the report.

Windows PowerShell:

```powershell
git clone https://github.com/Universeeeeeee/AI-PR-Review-Assitant.git
cd AI-PR-Review-Assitant
.\scripts\start-dev.ps1
```

macOS / Linux:

```bash
git clone https://github.com/Universeeeeeee/AI-PR-Review-Assitant.git
cd AI-PR-Review-Assitant
chmod +x scripts/start-dev.sh scripts/stop-dev.sh
./scripts/start-dev.sh
```

Open:

```text
http://localhost:5173
```

Try this PR:

```text
https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/7
```

![AI PR Review Assistant workbench](docs/assets/workbench-demo.png)

Detailed architecture and design notes are available in [docs/design.md](docs/design.md).

### Core Features

- Analyze a public GitHub PR URL.
- Run deterministic risk scanning based on diff content and file paths.
- Display PR metadata, overall risk level, summary, file summaries, possible risks, and review suggestions.
- Copy the generated Markdown Review.
- Support real DeepSeek model analysis.
- Fall back to Mock mode when no DeepSeek API key is configured, keeping local demos stable.
- Support an optional GitHub Token to increase public GitHub API rate limits.
- Store recent analyses in browser localStorage.

### Tech Stack

```text
frontend: React + Vite + TypeScript
backend:  FastAPI
api:      GitHub REST API
ai:       DeepSeekProvider / MockProvider
storage:  browser localStorage
```

### Architecture

```text
frontend/
  React + Vite + TypeScript
  - PR URL input
  - result display
  - risk level display
  - Markdown Review copy
  - recent analyses in localStorage

backend/
  FastAPI
  - /api/analyze-pr

  app/
    main.py
    config.py
    schemas.py
    services/
      github_client.py
      rule_engine.py
      ai_provider.py
      report_composer.py
```

Backend flow:

```text
POST /api/analyze-pr
  -> parse GitHub PR URL
  -> fetch PR metadata
  -> fetch changed files + patch diff
  -> truncate oversized diffs
  -> run Rule Engine
  -> run AI Provider
  -> compose stable ReviewResult JSON + Markdown
  -> return to frontend
```

### Current Status

```text
PR 1: project skeleton, README draft, frontend shell, backend health check.
PR 2: Mock /api/analyze-pr endpoint and shared response schemas.
PR 3: GitHub PR metadata and changed files fetching before Mock analysis.
PR 4: Rule Engine scans changed files and patch diff for deterministic risks.
PR 5: pluggable AI Provider layer with Mock / DeepSeek switching and fallback.
PR 6: frontend workbench submits PR URLs to the backend and renders basic status, warning, and error states.
PR 7: frontend renders detailed results, supports Markdown Review copy, and stores recent analyses in localStorage.
PR 8: final README polish, deployment notes, design notes, and screenshots.
PR 9: reviewer quick start polish with cross-platform startup and stop scripts.
```

### Recommended Review Path

1. Follow Quick Start to run the backend and frontend locally.
2. Keep `AI_PROVIDER=auto` and leave `DEEPSEEK_API_KEY` empty for Mock mode, or configure a DeepSeek API key for real model output.
3. Open `http://localhost:5173`.
4. Analyze a public GitHub PR URL, for example:

```text
https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/7
```

5. Review PR metadata, summary, possible risks, warnings, suggestions, and Markdown Review output.
6. Use `Copy Markdown` to copy the generated review text.

### Quick Start

Prerequisites:

- Python 3.11+
- Node.js 20+
- npm

Recommended path: start the local development environment with one command.

Windows PowerShell:

```powershell
.\scripts\start-dev.ps1
```

If PowerShell execution policy blocks the script, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

macOS / Linux:

```bash
chmod +x scripts/start-dev.sh scripts/stop-dev.sh
./scripts/start-dev.sh
```

Then open:

```text
http://localhost:5173
```

When no DeepSeek API key is configured, the app automatically uses Mock mode and still supports the full demo flow.

Stop local services:

Windows PowerShell:

```powershell
.\scripts\stop-dev.ps1
```

macOS / Linux:

```bash
./scripts/stop-dev.sh
```

#### Manual Startup

Backend:

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env`:

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
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The frontend can optionally configure the backend base URL in `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Do not commit real `.env` files, API keys, or GitHub tokens. `.gitignore` keeps local secret files out of Git while allowing `.env.example` templates.

DeepSeek API compatibility is documented in the official DeepSeek docs: [Your First API Call](https://api-docs.deepseek.com/) and [Models](https://api-docs.deepseek.com/api/list-models).

### API Contract

`POST /api/analyze-pr`

Request:

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

Successful response:

```text
pr        GitHub PR metadata
analysis  summary, riskLevel, truncated, fileSummaries, risks, suggestions, markdownReview
meta      provider, mock, analyzedAt, durationMs, warnings
```

Error response:

```json
{
  "detail": {
    "code": "INVALID_PR_URL",
    "message": "请输入有效的 GitHub Pull Request URL。"
  }
}
```

Error code mapping:

```text
INVALID_PR_URL        400
GITHUB_NOT_FOUND      404
GITHUB_RATE_LIMITED   429
GITHUB_API_ERROR      502
AI_PROVIDER_ERROR     502
```

### Mock Mode

Default mode:

```text
AI_PROVIDER=auto
```

Behavior:

- `AI_PROVIDER=auto` without `DEEPSEEK_API_KEY` uses `MockProvider`.
- `AI_PROVIDER=auto` with `DEEPSEEK_API_KEY` uses `DeepSeekProvider`.
- `AI_PROVIDER=mock` always uses `MockProvider`.
- `AI_PROVIDER=deepseek` requires `DEEPSEEK_API_KEY`; missing key or provider failures return `AI_PROVIDER_ERROR`.
- In auto mode, DeepSeek timeout, API errors, or invalid JSON falls back to Mock mode and adds a warning.
- Mock and DeepSeek modes both preserve deterministic Rule Engine risks.
- Mock mode is not static placeholder data. It uses real GitHub PR metadata, changed files, patch diff, rule risks, test changes, and truncation status to generate deterministic summaries, file notes, and review suggestions, so reviewers can evaluate the full flow without an API key.

### Rule Engine

The current Rule Engine scans changed file paths and patch diff lines. It does not perform AST or cross-file semantic analysis.

First batch rules:

```text
security: hardcoded-secret, unsafe-html, unsafe-eval, sql-string-concat
stability: removed-error-handling, removed-null-check, config-change, large-change
tests: missing-tests, removed-tests
maintainability: complex-condition, unclear-todo-fixme
```

Rule results are review hints, not absolute bug claims. Reports should use wording such as “possible risk” and “suggested confirmation”.

The frontend displays:

```text
当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。
```

When auto fallback happens, the frontend also shows warning codes such as `AI_TIMEOUT`, `AI_PROVIDER_ERROR`, or `AI_INVALID_JSON`.

### Verification

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend:

```powershell
cd frontend
npm test -- --run
npm run build
```

### Current Limits

- The current version primarily supports public GitHub PRs.
- Private repository auth and full permission flows are not implemented.
- The system does not fetch full repository contents; it analyzes PR changed files and patch diff only.
- No AST-level semantic analysis.
- No cross-file call graph analysis.
- No asynchronous task queue.
- No database; recent analyses are stored only in browser localStorage.
- Large PRs are analyzed with diff truncation.

### Delivery Plan

Development is split into small PRs. Each PR should keep `main` runnable and include a clear PR description with feature description, implementation notes, and test steps.

```text
PR 1: initialize project structure, README draft, .gitignore, .env.example
PR 2: FastAPI mock analyze endpoint and shared schemas
PR 3: GitHub PR URL parsing and changed files fetching
PR 4: Rule Engine basic risk scanning
PR 5: DeepSeekProvider + MockProvider switching and fallback
PR 6: React workbench base page and API integration
PR 7: result display, Markdown copy, localStorage recent analyses
PR 8: README polish, deployment notes, design notes, screenshots
PR 9: reviewer quick start, macOS / Linux scripts, and stop scripts
```

PR template:

```md
## 功能描述

## 实现思路

## 测试方式
```

### Deployment Plan

Local run is the first priority for evaluation. Optional online deployment can use the same frontend/backend split.

Docker is not the default Quick Start path. It can be added later as a deployment convenience, but the first version prioritizes a fast local script that reviewers can run with minimal setup.

Frontend deployment:

- Use Vercel or Netlify.
- Set the project root to `frontend`.
- Build command: `npm run build`.
- Publish directory: `dist`.
- Configure `VITE_API_BASE_URL` to the deployed backend URL.

Backend deployment:

- Use Render, Railway, or Fly.io.
- Set the service root to `backend`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Configure `AI_PROVIDER`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `GITHUB_TOKEN`, `MAX_FILES`, `MAX_PATCH_CHARS`, `REQUEST_TIMEOUT`, `AI_TIMEOUT_SECONDS`, and `CORS_ORIGINS`.
- Set `CORS_ORIGINS` to the deployed frontend origin.

If an online demo is not available, reviewers can still reproduce the project locally through Quick Start.

### Original Work And Dependencies

This project is built for the training-camp AI PR Review Assistant topic. Third-party dependencies are listed in `backend/requirements.txt` and `frontend/package.json`. Original project functionality is implemented in `backend/app` and `frontend/src`.
