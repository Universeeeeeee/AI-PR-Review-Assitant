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
from app.services.ai_provider import AIAnalysisDraft
from app.services.github_client import GitHubPrContext


MOCK_MODE_WARNING = WarningItem(
    code="MOCK_MODE",
    message="当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。",
)

MOCK_FALLBACK_WARNING = WarningItem(
    code="MOCK_MODE",
    message="当前 AI Provider 不可用，系统使用 Mock 模式生成报告。",
)


def compose_review_response(
    context: GitHubPrContext,
    rule_risks: list[RiskItem],
    ai_draft: AIAnalysisDraft,
    provider_name: str,
    mock: bool,
    duration_ms: int,
    extra_warnings: list[WarningItem] | None = None,
) -> AnalyzePrResponse:
    risks = rule_risks
    file_summaries = _build_file_summaries(context, ai_draft)
    suggestions = ai_draft.suggestions or _default_suggestions(risks)
    summary = ai_draft.summary or f"Mock 分析已基于 GitHub PR `{context.pr.title}` 获取真实元信息和 changed files。"
    risk_level = _overall_risk_level(risks)
    markdown_review = _build_markdown_review(
        pr=context.pr,
        summary=summary,
        risk_level=risk_level,
        file_summaries=file_summaries,
        risks=risks,
        suggestions=suggestions,
    )

    return AnalyzePrResponse(
        pr=context.pr,
        analysis=AnalysisResult(
            summary=summary,
            risk_level=risk_level,
            truncated=context.truncated,
            file_summaries=file_summaries,
            risks=risks,
            suggestions=suggestions,
            markdown_review=markdown_review,
        ),
        meta=AnalyzeMeta(
            provider=provider_name,
            mock=mock,
            analyzed_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=duration_ms,
            warnings=_build_warnings(mock, context.warnings, extra_warnings or []),
        ),
    )


def _build_file_summaries(context: GitHubPrContext, ai_draft: AIAnalysisDraft) -> list[FileSummary]:
    file_summaries = [
        FileSummary(
            file=file.filename,
            status=file.status,
            additions=file.additions,
            deletions=file.deletions,
            summary=ai_draft.file_summaries.get(
                file.filename,
                f"Mock 总结：`{file.filename}` 本次变更包含 {file.additions} 行新增和 {file.deletions} 行删除。",
            ),
        )
        for file in context.files
    ]
    if file_summaries:
        return file_summaries

    return [
        FileSummary(
            file="N/A",
            status="unknown",
            additions=0,
            deletions=0,
            summary="GitHub 未返回可分析的 patch 文件内容。",
        )
    ]


def _default_suggestions(risks: list[RiskItem]) -> list[str]:
    suggestions = ["建议确认 PR 描述中包含功能描述、实现思路和测试方式。"]
    if risks:
        suggestions.append("建议优先人工确认规则引擎标记的可能风险，并结合真实 diff 判断是否需要修改。")
    else:
        suggestions.append("当前规则引擎未发现第一批确定性风险，仍建议人工 Review 核心变更路径。")
    return suggestions


def _build_warnings(
    mock: bool,
    context_warnings: list[WarningItem],
    extra_warnings: list[WarningItem],
) -> list[WarningItem]:
    warnings = [_mock_mode_warning(extra_warnings)] if mock else []
    warnings.extend(context_warnings)
    warnings.extend(extra_warnings)
    return warnings


def _mock_mode_warning(extra_warnings: list[WarningItem]) -> WarningItem:
    fallback_codes = {"AI_TIMEOUT", "AI_PROVIDER_ERROR", "AI_INVALID_JSON"}
    if any(warning.code in fallback_codes for warning in extra_warnings):
        return MOCK_FALLBACK_WARNING
    return MOCK_MODE_WARNING


def _build_markdown_review(
    pr: PrMetadata,
    summary: str,
    risk_level: str,
    file_summaries: list[FileSummary],
    risks: list[RiskItem],
    suggestions: list[str],
) -> str:
    file_lines = "\n".join(f"- `{item.file}`: {item.summary}" for item in file_summaries)
    risk_lines = "\n".join(
        f"- **{item.severity}** `{item.file or 'PR'}`: {item.title} - {item.suggestion}" for item in risks
    )
    if not risk_lines:
        risk_lines = "- 当前规则引擎未发现第一批确定性风险，仍建议人工 Review 核心变更路径。"
    suggestion_lines = "\n".join(f"- {suggestion}" for suggestion in suggestions)

    return (
        "## AI PR Review\n\n"
        "### Summary\n\n"
        f"{summary}\n\n"
        "### Risk Level\n\n"
        f"{risk_level}\n\n"
        "### File Changes\n\n"
        f"{file_lines}\n\n"
        "### Possible Risks\n\n"
        f"{risk_lines}\n\n"
        "### Suggestions\n\n"
        f"{suggestion_lines}\n\n"
        "### Notes\n\n"
        f"本报告用于辅助 Review `{pr.owner}/{pr.repo}#{pr.number}`，需要人工结合完整上下文确认。"
    )


def _overall_risk_level(risks: list[RiskItem]) -> str:
    if any(risk.severity == "high" for risk in risks):
        return "high"
    if any(risk.severity == "medium" for risk in risks):
        return "medium"
    return "low"
