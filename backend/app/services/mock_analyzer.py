from datetime import UTC, datetime

from app.schemas import (
    AnalysisResult,
    AnalyzeMeta,
    AnalyzePrResponse,
    FileSummary,
    PrMetadata,
    RiskItem,
    WarningItem,
)
from app.services.github_client import GitHubPrContext, parse_github_pr_url


def build_mock_analysis(pr_url: str, duration_ms: int = 0) -> AnalyzePrResponse:
    parsed = parse_github_pr_url(pr_url)

    pr = PrMetadata(
        url=parsed.canonical_url,
        owner=parsed.owner,
        repo=parsed.repo,
        number=parsed.number,
        title=f"Mock analysis for {parsed.owner}/{parsed.repo}#{parsed.number}",
        author="mock-author",
        base_branch="main",
        head_branch="feature/mock-pr",
        changed_files=3,
        additions=128,
        deletions=24,
    )
    file_summaries = [
        FileSummary(
            file="backend/app/main.py",
            status="modified",
            additions=48,
            deletions=4,
            summary="新增 PR 分析接口入口，后续会接入 GitHub 数据和真实 AI Provider。",
        ),
        FileSummary(
            file="frontend/src/App.tsx",
            status="modified",
            additions=56,
            deletions=8,
            summary="调整工作台页面，为后续展示结构化 Review 结果预留区域。",
        ),
    ]
    risks = [
        RiskItem(
            id="mock-missing-tests-001",
            severity="medium",
            source="rule",
            rule_name="missing-tests",
            file="backend/app/main.py",
            title="建议确认核心流程测试覆盖",
            description="Mock 分析提示：接口或核心逻辑发生变化时，建议同步补充成功和失败场景测试。",
            suggestion="建议为 PR URL 校验、Mock 响应结构和错误返回增加自动化测试。",
        )
    ]
    suggestions = [
        "建议确认 PR 描述中包含功能描述、实现思路和测试方式。",
        "建议在接入真实 GitHub API 前保持 Mock 模式稳定可用，便于前端并行开发。",
    ]
    markdown_review = _build_markdown_review(pr, file_summaries, risks, suggestions)

    return AnalyzePrResponse(
        pr=pr,
        analysis=AnalysisResult(
            summary=f"这是针对 {parsed.owner}/{parsed.repo}#{parsed.number} 的 Mock PR Review 报告，用于验证 API 契约和前端集成流程。",
            risk_level="medium",
            truncated=False,
            file_summaries=file_summaries,
            risks=risks,
            suggestions=suggestions,
            markdown_review=markdown_review,
        ),
        meta=AnalyzeMeta(
            provider="mock",
            mock=True,
            analyzed_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=duration_ms,
            warnings=[
                WarningItem(
                    code="MOCK_MODE",
                    message="当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。",
                )
            ],
        ),
    )


def build_mock_analysis_from_context(
    context: GitHubPrContext,
    rule_risks: list[RiskItem] | None = None,
    duration_ms: int = 0,
) -> AnalyzePrResponse:
    file_summaries = [
        FileSummary(
            file=file.filename,
            status=file.status,
            additions=file.additions,
            deletions=file.deletions,
            summary=f"Mock 总结：`{file.filename}` 本次变更包含 {file.additions} 行新增和 {file.deletions} 行删除。",
        )
        for file in context.files
    ]
    if not file_summaries:
        file_summaries = [
            FileSummary(
                file="N/A",
                status="unknown",
                additions=0,
                deletions=0,
                summary="GitHub 未返回可分析的 patch 文件内容。",
            )
        ]

    risks = rule_risks if rule_risks is not None else []
    suggestions = [
        "建议确认 PR 描述中包含功能描述、实现思路和测试方式。",
    ]
    if risks:
        suggestions.append("建议优先人工确认规则引擎标记的可能风险，并结合真实 diff 判断是否需要修改。")
    else:
        suggestions.append("当前规则引擎未发现第一批确定性风险，仍建议人工 Review 核心变更路径。")

    markdown_review = _build_markdown_review(context.pr, file_summaries, risks, suggestions)
    warnings = [
        WarningItem(
            code="MOCK_MODE",
            message="当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。",
        )
    ]
    warnings.extend(context.warnings)

    return AnalyzePrResponse(
        pr=context.pr,
        analysis=AnalysisResult(
            summary=f"Mock 分析已基于 GitHub PR `{context.pr.title}` 获取真实元信息和 changed files。",
            risk_level=_overall_risk_level(risks),
            truncated=context.truncated,
            file_summaries=file_summaries,
            risks=risks,
            suggestions=suggestions,
            markdown_review=markdown_review,
        ),
        meta=AnalyzeMeta(
            provider="mock",
            mock=True,
            analyzed_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=duration_ms,
            warnings=warnings,
        ),
    )


def _build_markdown_review(
    pr: PrMetadata,
    file_summaries: list[FileSummary],
    risks: list[RiskItem],
    suggestions: list[str],
) -> str:
    file_lines = "\n".join(f"- `{item.file}`: {item.summary}" for item in file_summaries)
    risk_lines = "\n".join(
        f"- **{item.severity}** `{item.file}`: {item.title} - {item.suggestion}" for item in risks
    )
    suggestion_lines = "\n".join(f"- {suggestion}" for suggestion in suggestions)

    return (
        "## AI PR Review\n\n"
        "### Summary\n\n"
        f"Mock analysis for `{pr.owner}/{pr.repo}#{pr.number}`. "
        "This report validates the API contract before GitHub and DeepSeek integrations are added.\n\n"
        "### Risk Level\n\n"
        "medium\n\n"
        "### File Changes\n\n"
        f"{file_lines}\n\n"
        "### Possible Risks\n\n"
        f"{risk_lines}\n\n"
        "### Suggestions\n\n"
        f"{suggestion_lines}\n\n"
        "### Notes\n\n"
        "当前为 Mock 模式结果，需要人工 Review 结合真实 diff 确认。"
    )


def _overall_risk_level(risks: list[RiskItem]) -> str:
    if any(risk.severity == "high" for risk in risks):
        return "high"
    if any(risk.severity == "medium" for risk in risks):
        return "medium"
    return "low"
