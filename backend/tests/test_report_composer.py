from app.schemas import PrMetadata, RiskItem, WarningItem
from app.services.ai_provider import AIAnalysisDraft
from app.services.github_client import ChangedFile, GitHubPrContext
from app.services.report_composer import compose_review_response


def test_compose_review_response_preserves_rule_risks_and_ai_text():
    context = _context()
    rule_risks = _rule_risks()
    draft = AIAnalysisDraft(
        summary="AI 总结：本 PR 接入了可插拔 Provider。",
        file_summaries={"backend/app/main.py": "AI 文件摘要：路由调用 Provider。"},
        suggestions=["建议补充 DeepSeek 错误降级测试。"],
    )

    response = compose_review_response(
        context=context,
        rule_risks=rule_risks,
        ai_draft=draft,
        provider_name="deepseek",
        mock=False,
        duration_ms=42,
    )

    assert response.analysis.summary == "AI 总结：本 PR 接入了可插拔 Provider。"
    assert response.analysis.risk_level == "medium"
    assert response.analysis.file_summaries[0].summary == "AI 文件摘要：路由调用 Provider。"
    assert response.analysis.risks == rule_risks
    assert response.analysis.suggestions == ["建议补充 DeepSeek 错误降级测试。"]
    assert "## AI PR Review" in response.analysis.markdown_review
    assert "AI 总结：本 PR 接入了可插拔 Provider。" in response.analysis.markdown_review
    assert response.meta.provider == "deepseek"
    assert response.meta.mock is False
    assert response.meta.duration_ms == 42


def test_compose_review_response_keeps_truncation_and_extra_warnings():
    context = _context(
        truncated=True,
        warnings=[
            WarningItem(
                code="PATCH_TRUNCATED",
                message="当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
            )
        ],
    )

    response = compose_review_response(
        context=context,
        rule_risks=[],
        ai_draft=AIAnalysisDraft(summary="", file_summaries={}, suggestions=[]),
        provider_name="mock",
        mock=True,
        duration_ms=7,
        extra_warnings=[
            WarningItem(
                code="AI_PROVIDER_ERROR",
                message="AI Provider 调用失败，系统已使用 Mock 模式生成报告。",
            )
        ],
    )

    assert response.analysis.truncated is True
    assert response.analysis.summary.startswith("Mock 分析已基于 GitHub PR")
    assert response.analysis.file_summaries[0].file == "backend/app/main.py"
    assert response.analysis.suggestions
    assert [warning.code for warning in response.meta.warnings] == [
        "MOCK_MODE",
        "PATCH_TRUNCATED",
        "AI_PROVIDER_ERROR",
    ]


def _context(
    truncated: bool = False,
    warnings: list[WarningItem] | None = None,
) -> GitHubPrContext:
    return GitHubPrContext(
        pr=PrMetadata(
            url="https://github.com/owner/repo/pull/1",
            owner="owner",
            repo="repo",
            number=1,
            title="Test PR",
            author="alice",
            base_branch="main",
            head_branch="feature",
            changed_files=1,
            additions=10,
            deletions=2,
        ),
        files=[
            ChangedFile(
                filename="backend/app/main.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="@@ -1 +1 @@\n-old\n+new\n",
            )
        ],
        truncated=truncated,
        warnings=warnings or [],
    )


def _rule_risks() -> list[RiskItem]:
    return [
        RiskItem(
            id="rule-missing-tests-abc123",
            severity="medium",
            source="rule",
            rule_name="missing-tests",
            file=None,
            title="建议确认测试覆盖",
            description="核心代码变化但未看到测试文件变化。",
            suggestion="建议补充关键路径测试。",
        )
    ]
