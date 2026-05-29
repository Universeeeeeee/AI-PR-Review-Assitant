import re
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


class InvalidPrUrlError(ValueError):
    """Raised when the input is not a public GitHub Pull Request URL."""


PR_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?(?:[?#].*)?$"
)


def build_mock_analysis(pr_url: str, duration_ms: int = 0) -> AnalyzePrResponse:
    match = PR_URL_PATTERN.match(pr_url.strip())
    if not match:
        raise InvalidPrUrlError("Invalid GitHub Pull Request URL")

    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))
    canonical_url = f"https://github.com/{owner}/{repo}/pull/{number}"

    pr = PrMetadata(
        url=canonical_url,
        owner=owner,
        repo=repo,
        number=number,
        title=f"Mock analysis for {owner}/{repo}#{number}",
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
            summary=f"这是针对 {owner}/{repo}#{number} 的 Mock PR Review 报告，用于验证 API 契约和前端集成流程。",
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
