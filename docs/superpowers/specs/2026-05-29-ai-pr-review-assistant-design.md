# AI PR Review Assistant 第一版设计文档

日期：2026-05-29

## 1. 产品定位

AI PR Review Assistant 是一个面向开发者的 Web 工具。用户输入 GitHub Pull Request 链接后，系统自动获取 PR 基本信息、changed files 和 patch diff，通过规则引擎与 AI Provider 混合分析，生成结构化 Review 报告，帮助开发者更快理解变更、识别可能风险，并获得可复制的 Markdown Review 建议。

第一版重点不是替代人工 Review，而是辅助人工 Review。所有风险措辞都使用“可能风险”“建议确认”“建议补充测试”“需要人工 Review 关注”等表达，避免把模型或规则扫描结果包装成绝对结论。

第一版优先保证本地运行演示稳定，同时提供在线部署方案。有 DeepSeek API Key 时使用真实模型分析；未配置 API Key 时自动进入 Mock 模式，仍然可以完整体验 PR 获取、规则分析、报告展示、Markdown 复制和最近分析记录。

## 2. 第一版范围

第一版包含：

- React + Vite + TypeScript 前端工作台。
- FastAPI 后端。
- GitHub REST API 获取公开 PR 基本信息、changed files 和 patch diff。
- 可选 GitHub Token，用于提高公开 API 限额。
- 基于 file path + patch diff 的轻量规则引擎。
- 可插拔 AI Provider：DeepSeekProvider 与 MockProvider。
- 统一结构化 ReviewResult 响应。
- PR 总结、文件摘要、风险分级、Review 建议。
- 可复制 Markdown Review。
- 浏览器 localStorage 最近分析记录。
- Mock Mode、Truncated、Warning、Error 状态展示。
- README、Quick Start、环境变量说明、Mock 模式说明、当前限制、部署说明、依赖说明和未来规划。

第一版不包含：

- 私有仓库完整权限流程。
- 获取完整仓库内容或完整文件内容。
- AST 级语义分析。
- 跨文件调用链分析。
- 异步任务队列。
- 后端数据库。
- GitHub PR 行级评论发布。
- 误报标记闭环。

这些能力作为未来规划写入 README。

## 3. 总体架构

项目采用前后端分离结构：

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
  -> 获取 PR 基本信息
  -> 获取 changed files + patch diff
  -> 按 MAX_FILES / MAX_PATCH_CHARS 做截断保护
  -> Rule Engine 生成结构化风险项
  -> AI Provider 生成总结、文件摘要和建议草稿
  -> Report Composer 校验、合并、去重、降级
  -> 生成统一 JSON + Markdown Review
  -> 返回前端
```

第一版不做异步任务队列。通过限制文件数量、patch 长度和请求超时时间控制响应速度，并在大型 PR 场景返回截断提示。

默认限制：

```env
MAX_FILES=20
MAX_PATCH_CHARS=30000
REQUEST_TIMEOUT=60
AI_TIMEOUT_SECONDS=30
```

如果 PR 较大，后端优先截断 diff 并继续分析，返回 `analysis.truncated=true` 与 `meta.warnings`。只有截断后仍无法构造有效输入时，才返回 `PR_TOO_LARGE`。

## 4. API 契约

第一版只提供一个核心接口：

```http
POST /api/analyze-pr
Content-Type: application/json
```

请求体：

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

前端 JSON 使用 `prUrl`，后端 Python 内部使用 `pr_url`，通过 Pydantic alias 保持对外 camelCase、对内 snake_case。

成功响应分为三层：`pr`、`analysis`、`meta`。

```json
{
  "pr": {
    "url": "https://github.com/owner/repo/pull/123",
    "owner": "owner",
    "repo": "repo",
    "number": 123,
    "title": "Fix login error handling",
    "author": "alice",
    "baseBranch": "main",
    "headBranch": "fix-login",
    "changedFiles": 3,
    "additions": 42,
    "deletions": 10
  },
  "analysis": {
    "summary": "本 PR 主要调整登录接口请求和错误处理逻辑。",
    "riskLevel": "medium",
    "truncated": false,
    "fileSummaries": [
      {
        "file": "src/api/user.ts",
        "status": "modified",
        "additions": 20,
        "deletions": 5,
        "summary": "调整登录请求参数和错误处理。"
      }
    ],
    "risks": [
      {
        "id": "rule-hardcoded-secret-a8f31c",
        "severity": "high",
        "source": "rule",
        "ruleName": "hardcoded-secret",
        "file": "backend/config.py",
        "title": "疑似硬编码密钥",
        "description": "变更中出现类似 token、secret、password 的敏感配置，可能需要人工确认。",
        "suggestion": "建议改为从环境变量读取，并确认密钥未提交到仓库。"
      }
    ],
    "suggestions": [
      "建议补充核心流程的失败场景测试。"
    ],
    "markdownReview": "## AI PR Review\n\n..."
  },
  "meta": {
    "provider": "deepseek",
    "mock": false,
    "analyzedAt": "2026-05-29T12:00:00Z",
    "durationMs": 4200,
    "warnings": [
      {
        "code": "PATCH_TRUNCATED",
        "message": "当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。"
      }
    ]
  }
}
```

失败响应：

```json
{
  "detail": {
    "code": "INVALID_PR_URL",
    "message": "请输入有效的 GitHub Pull Request URL。"
  }
}
```

错误码与 HTTP 状态码：

```text
INVALID_PR_URL        400
GITHUB_NOT_FOUND      404
GITHUB_RATE_LIMITED   429
GITHUB_API_ERROR      502
AI_PROVIDER_ERROR     502
PR_TOO_LARGE          413
INTERNAL_ERROR        500
```

## 5. GitHub Client

`github_client.py` 负责：

- 解析 GitHub PR URL。
- 校验 URL 是否符合 `https://github.com/{owner}/{repo}/pull/{number}`。
- 调用 GitHub REST API 获取 PR 基本信息。
- 调用 GitHub REST API 获取 changed files。
- 提取每个文件的 `filename`、`status`、`additions`、`deletions`、`patch`。
- 应用 `MAX_FILES` 与 `MAX_PATCH_CHARS` 截断策略。
- 生成 `PATCH_TRUNCATED` warning。

GitHub Token 只从后端 `.env` 读取，前端不接触 Token。未配置 Token 时仍支持公开 PR，但可能遇到 GitHub API rate limit。配置 Token 后只用于提高公开 API 限额，第一版不做私有仓库权限流程。

## 6. Rule Engine

`rule_engine.py` 采用基于 `file path + patch diff` 的轻量规则扫描，不做 AST、不做跨文件调用链。规则输出结构化 `RiskItem`，作为确定性风险提示传给 AI Provider 和 Report Composer。

Patch 解析要区分新增行和删除行：

```text
+ 新增行：用于发现新增风险。
- 删除行：用于发现被移除的保护逻辑。
```

第一版核心规则：

```text
high
- hardcoded-secret：新增 token / password / secret / api_key 等敏感字段。
- unsafe-html：新增 dangerouslySetInnerHTML。
- unsafe-eval：新增 eval / Function 构造执行。
- sql-string-concat：新增 SQL 字符串拼接迹象。
- removed-tests：删除测试文件或大量删除测试代码。

medium
- removed-error-handling：删除 try / catch / except / error handler。
- removed-null-check：删除 null / undefined / None / optional 判空逻辑。
- config-change：修改 .env.example / yaml / json / toml / config 文件。
- large-change：单文件 patch 超过 300 行或 12000 字符。
- missing-tests：存在核心代码变更，但没有测试文件变更。

low
- complex-condition：新增过长 if 条件或多重逻辑判断。
- unclear-todo-fixme：新增 TODO / FIXME / temporary / hack。
```

规则细节：

- `missing-tests` 是 PR 级规则，在所有文件扫描结束后统一判断，避免重复风险项。
- `config-change` 默认 medium；如果配置变更中同时出现 secret / token / password，则升级为 high。
- `large-change` 对 `package-lock.json`、`pnpm-lock.yaml`、`yarn.lock` 等锁文件降级或忽略。
- 风险 ID 使用 `ruleName + file + index/hash` 稳定生成，例如 `rule-hardcoded-secret-a8f31c`。
- 所有描述使用提示性措辞，不写成绝对漏洞判定。

轻量语言增强：

```text
React
- useEffect 依赖数组变更。
- fetch / axios 新增调用但没有明显 catch / try。

Python / FastAPI
- 新增 @app / router 路由但没有明显鉴权依赖。
- 删除 try/except。
- 新增 os.environ 默认值中包含敏感字段。
```

`duplicated-change-pattern` 暂不作为第一批核心规则实现，可作为后续增强。

## 7. AI Provider

`ai_provider.py` 定义统一 Provider 接口。第一版支持 `DeepSeekProvider` 和 `MockProvider`。

环境变量：

```env
AI_PROVIDER=auto
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
AI_TIMEOUT_SECONDS=30
```

Provider 选择策略：

```text
AI_PROVIDER=auto
- 有 DEEPSEEK_API_KEY：使用 DeepSeekProvider。
- 没有 DEEPSEEK_API_KEY：使用 MockProvider。

AI_PROVIDER=mock
- 强制使用 MockProvider。

AI_PROVIDER=deepseek
- 强制使用 DeepSeekProvider。
- 如果缺少 DEEPSEEK_API_KEY，返回 AI_PROVIDER_ERROR。
```

AI 输入包含：

- PR 元信息。
- 文件列表与 patch diff 摘要。
- Rule Engine 生成的结构化风险项。
- `truncated` 标记与 warnings。

AI 不接收完整仓库、不接收完整文件内容，避免上下文过大。

AI 输出只是 `AIAnalysisDraft`，不是最终结果。最终 `ReviewResult` 只能由 `report_composer.py` 生成。

```text
DeepSeekProvider / MockProvider
  -> AIAnalysisDraft

Rule Engine
  -> List[RiskItem]

Report Composer
  -> ReviewResult
```

`AIAnalysisDraft` 结构：

```json
{
  "summary": "本 PR 主要调整登录流程和接口错误处理。",
  "fileSummaries": [
    {
      "file": "src/api/user.ts",
      "summary": "调整用户登录请求参数和失败处理。"
    }
  ],
  "risks": [
    {
      "severity": "medium",
      "source": "ai",
      "file": "src/api/user.ts",
      "title": "建议确认错误提示兼容性",
      "description": "登录失败处理发生变化，可能影响旧页面的错误展示。",
      "suggestion": "建议补充登录失败和接口异常场景测试。"
    }
  ],
  "suggestions": [
    "建议补充核心流程的失败场景测试。"
  ]
}
```

降级策略：

```text
auto 模式
- 缺少 API Key：MockProvider。
- DeepSeek 超时：规则结果 + Mock 总结 + warning: AI_TIMEOUT。
- DeepSeek API 错误：规则结果 + Mock 总结 + warning: AI_PROVIDER_ERROR。
- 模型返回非 JSON：尝试提取 JSON；失败后规则结果 + Mock 总结 + warning: AI_INVALID_JSON。

deepseek 模式
- 缺少 API Key：返回 AI_PROVIDER_ERROR。
- 请求超时：返回 AI_PROVIDER_ERROR。
- API 错误：返回 AI_PROVIDER_ERROR。
- 非 JSON：可降级为规则报告，但 meta.warnings 必须标明 AI_INVALID_JSON。
```

MockProvider 不是固定假数据，而是基于真实 PR 元信息、文件变更和规则风险生成可解释报告，确保未配置 Key 时仍能稳定演示完整流程。

## 8. Report Composer

`report_composer.py` 负责把 GitHub 数据、规则结果和 AI 草稿合并为最终 `ReviewResult`。

职责：

- 校验 AI JSON。
- AI 输出失败时降级为规则报告或 Mock 总结。
- 合并 rule risks 与 ai risks。
- 对相似风险做轻量去重。
- 根据最高风险级别和风险数量生成总体 `riskLevel`。
- 补齐文件摘要。
- 生成可复制 `markdownReview`。
- 保证前端永远消费稳定结构。

风险来源：

```text
rule：规则引擎发现。
ai：AI 补充判断。
mixed：规则和 AI 都认为需要关注。
```

Markdown Review 内容结构：

```md
## AI PR Review

### Summary

### Risk Level

### File Changes

### Possible Risks

### Suggestions

### Notes
```

Markdown 中同样使用“可能风险”“建议确认”“建议补充测试”等辅助性措辞。

## 9. 前端工作台

第一版前端采用方案 B：工作台布局，而不是单列工具页。

```text
┌────────────────────────────────────────────┐
│ Header: AI PR Review Assistant             │
├───────────────┬────────────────────────────┤
│ 左侧           │ 右侧                        │
│ 最近分析       │ PR 链接输入区                │
│ - repo #123   │ 分析按钮 / 状态提示           │
│ - repo #118   │                            │
│               │ 分析结果详情                 │
│               │ - PR 概览                   │
│               │ - 总体风险级别               │
│               │ - PR 总结                   │
│               │ - 文件摘要                   │
│               │ - 可能风险列表               │
│               │ - Review 建议               │
│               │ - Markdown Review 复制       │
└───────────────┴────────────────────────────┘
```

交互流程：

```text
用户输入 GitHub PR URL
  -> 点击 Analyze
  -> 前端调用 POST /api/analyze-pr
  -> 展示 analyzing 状态
  -> 成功后渲染结构化结果
  -> 保存最近分析到 localStorage
  -> 用户可复制 markdownReview
```

最近分析：

- 保存最近 5 到 10 条。
- 内容包括 `prUrl`、`repo`、`number`、`title`、`riskLevel`、`summary`、`analyzedAt`、`result`。
- 点击历史项直接恢复结果，不重新请求后端。
- 提供清空历史按钮。

必须展示的状态：

```text
Mock Mode
当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。

Truncated
当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。

Warning
展示 meta.warnings 中的 code 和 message。

Error
展示后端返回的 detail.message，保留输入内容，允许修改 URL 后重试。
```

视觉风格：

- 偏开发工具工作台，信息密度适中。
- 不做营销首页。
- 使用清晰的 high / medium / low 风险色彩。
- 风险文案保持辅助性，不做绝对判断。

## 10. 配置与密钥安全

DeepSeek API Key 和 GitHub Token 都只放后端 `.env`，前端不接触密钥。

`.env.example`：

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

`.gitignore` 必须包含：

```text
.env
.env.*
!.env.example
node_modules/
dist/
.venv/
__pycache__/
```

README 只说明如何配置，不写真实 API Key。需要真实 DeepSeek API Key 时，由用户本地提供并写入未追踪的 `.env` 文件。

## 11. README 内容

README 第一版至少包含：

- 项目简介。
- 核心功能。
- 技术栈。
- 系统架构。
- Quick Start。
- 本地运行方式。
- 环境变量说明。
- Mock 模式说明。
- 示例 PR 链接。
- API 说明。
- 模型选择说明。
- 上下文获取方式。
- 误报/漏报控制策略。
- 响应速度与大型 PR 截断策略。
- 当前限制。
- 在线部署方案。
- 未来规划。
- 原创说明与第三方依赖说明。

Quick Start 示例：

````md
## Quick Start

### 1. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 打开页面

访问：

```text
http://localhost:5173
```
````

Windows README 中要补充 PowerShell 写法：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

当前限制：

```md
## 当前限制

- 当前版本主要支持公开 GitHub PR；
- 不支持私有仓库 PR 的完整权限流程；
- 不抓取完整仓库内容，仅分析 PR changed files 和 patch diff；
- 不做 AST 级语义分析；
- 不做异步任务队列；
- 不使用数据库，最近分析仅保存在浏览器 localStorage；
- 大型 PR 会进行 diff 截断分析。
```

在线部署方案：

- 前端可部署到 Vercel 或 Netlify。
- 后端可部署到 Render、Railway 或 Fly.io。
- 有条件再提供真实 Demo 地址。
- 本地运行演示是第一优先级，在线部署是第二优先级。

## 12. PR 与提交计划

按小粒度 PR 持续交付，保证主分支每次合并后可运行。

```text
PR 1：初始化项目结构、README 草案、.gitignore、.env.example
PR 2：FastAPI Mock 分析接口和统一 schema
PR 3：GitHub PR URL 解析和 PR files 获取
PR 4：Rule Engine 基础风险扫描
PR 5：DeepSeekProvider + MockProvider 切换与降级
PR 6：React 工作台基础页面和 API 调用
PR 7：结果展示、Markdown 复制、localStorage 最近分析
PR 8：README 完善、部署说明、设计说明、示例截图
```

每个 PR 描述固定包含：

```md
## 功能描述

## 实现思路

## 测试方式
```

每个 PR 至少说明：

- 本 PR 做了什么。
- 为什么这样设计。
- 如何本地验证。
- 是否影响环境变量或 README。

## 13. 测试策略

后端：

- PR URL 解析单元测试。
- GitHub Client 对 API 响应的解析测试，使用 mock 响应。
- Rule Engine 规则测试，覆盖新增行、删除行、PR 级规则和锁文件例外。
- AI Provider 选择策略测试，覆盖 auto、mock、deepseek。
- Report Composer 合并、去重、降级和 Markdown 生成测试。
- `/api/analyze-pr` Mock 模式集成测试。

前端：

- API client 请求和错误解析测试。
- localStorage 最近分析读写测试。
- Mock Mode / Truncated / Warning / Error 状态渲染测试。
- Markdown 复制按钮交互测试。

手动验证：

- 未配置 DeepSeek API Key 时，Mock 模式完整可用。
- 配置 DeepSeek API Key 时，真实模型调用可用。
- 输入无效 PR URL 时展示后端错误。
- 输入大型 PR 时展示截断提示。
- 刷新页面后最近分析仍可恢复。

## 14. 未来规划

后续版本可以扩展：

- 异步任务模型与分析进度。
- 深度分析模式，获取完整文件与周边上下文。
- SQLite 或后端数据库保存历史分析。
- 误报标记与规则优化闭环。
- GitHub App / GitHub Action，自动在 PR 中评论。
- 私有仓库 OAuth 权限流程。
- JS/TS/Python AST 级分析。
- 行级 Review 建议定位。
- 团队共享分析记录。

## 15. 验收标准

第一版完成后应满足：

- 本地按 README 可启动后端和前端。
- 未配置 DeepSeek API Key 时可以进入 Mock 模式并完整分析示例公开 PR。
- 配置 DeepSeek API Key 后可以走真实 DeepSeekProvider。
- 输入公开 GitHub PR URL 后能展示 PR 概览、风险级别、总结、文件摘要、可能风险和建议。
- 可以复制 Markdown Review。
- localStorage 保存最近分析，并能点击恢复。
- Mock、Truncated、Warning、Error 状态可见且文案清晰。
- `.env` 不进入 Git，`.env.example` 提供完整配置模板。
- README 说明依赖、原创功能、运行方式、限制和未来规划。
