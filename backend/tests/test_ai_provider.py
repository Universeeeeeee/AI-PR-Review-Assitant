import json

import httpx
import pytest

from app.config import Settings
from app.schemas import PrMetadata, RiskItem
from app.services.ai_provider import (
    AIProviderError,
    DeepSeekProvider,
    MockProvider,
    build_ai_provider,
)
from app.services.github_client import ChangedFile, GitHubPrContext


def test_auto_provider_without_deepseek_key_uses_mock():
    provider = build_ai_provider(_settings(ai_provider="auto", deepseek_api_key=""))

    assert isinstance(provider, MockProvider)
    assert provider.name == "mock"
    assert provider.mock is True


def test_auto_provider_with_deepseek_key_uses_deepseek():
    provider = build_ai_provider(_settings(ai_provider="auto", deepseek_api_key="test-key"))

    assert isinstance(provider, DeepSeekProvider)
    assert provider.name == "deepseek"
    assert provider.mock is False


def test_mock_provider_setting_forces_mock_even_with_key():
    provider = build_ai_provider(_settings(ai_provider="mock", deepseek_api_key="test-key"))

    assert isinstance(provider, MockProvider)


def test_mock_provider_generates_contextual_review_from_real_pr_data():
    provider = MockProvider()
    context = GitHubPrContext(
        pr=PrMetadata(
            url="https://github.com/owner/repo/pull/42",
            owner="owner",
            repo="repo",
            number=42,
            title="Improve auth flow",
            author="alice",
            base_branch="main",
            head_branch="feat/auth",
            changed_files=3,
            additions=86,
            deletions=14,
        ),
        files=[
            ChangedFile(
                filename="backend/app/main.py",
                status="modified",
                additions=40,
                deletions=6,
                patch='@@ -1 +1 @@\n-old\n+ API_TOKEN = "secret-value"\n',
            ),
            ChangedFile(
                filename="frontend/src/App.tsx",
                status="modified",
                additions=30,
                deletions=8,
                patch="@@ -1 +1 @@\n-old\n+ fetch('/api/analyze-pr')\n",
            ),
            ChangedFile(
                filename="README.md",
                status="modified",
                additions=16,
                deletions=0,
                patch="@@ -1 +1 @@\n-old\n+ docs\n",
            ),
        ],
        truncated=True,
        warnings=[],
    )

    draft = provider.analyze(
        context,
        [
            RiskItem(
                id="rule-hardcoded-secret-abc123",
                severity="high",
                source="rule",
                rule_name="hardcoded-secret",
                file="backend/app/main.py",
                title="疑似硬编码密钥",
                description="新增内容中出现疑似敏感配置。",
                suggestion="建议改为从环境变量读取。",
            )
        ],
    )

    assert "owner/repo#42" in draft.summary
    assert "3 个文件" in draft.summary
    assert "+86/-14" in draft.summary
    assert "最高风险 high" in draft.summary
    assert "后端逻辑" in draft.file_summaries["backend/app/main.py"]
    assert "疑似硬编码密钥" in draft.file_summaries["backend/app/main.py"]
    assert "前端界面" in draft.file_summaries["frontend/src/App.tsx"]
    assert "文档" in draft.file_summaries["README.md"]
    assert any("高风险" in suggestion and "疑似硬编码密钥" in suggestion for suggestion in draft.suggestions)
    assert any("截断" in suggestion for suggestion in draft.suggestions)


def test_deepseek_provider_without_key_raises_provider_error():
    with pytest.raises(AIProviderError) as exc_info:
        build_ai_provider(_settings(ai_provider="deepseek", deepseek_api_key=""))

    assert exc_info.value.code == "AI_PROVIDER_ERROR"


def test_deepseek_provider_sends_json_mode_request_and_returns_draft():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content)
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.url == "https://api.deepseek.test/chat/completions"
        assert payload["model"] == "deepseek-v4-flash"
        assert payload["response_format"] == {"type": "json_object"}
        assert "json" in payload["messages"][0]["content"].lower()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "AI 总结：本 PR 调整了分析流程。",
                                    "fileSummaries": [
                                        {
                                            "file": "backend/app/main.py",
                                            "summary": "接入 AI Provider。",
                                        }
                                    ],
                                    "suggestions": ["建议补充 Provider 降级测试。"],
                                }
                            )
                        }
                    }
                ]
            },
        )

    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.test",
        model="deepseek-v4-flash",
        timeout=5,
        transport=httpx.MockTransport(handler),
    )

    draft = provider.analyze(_context(), _rule_risks())

    assert len(requests) == 1
    assert draft.summary == "AI 总结：本 PR 调整了分析流程。"
    assert draft.file_summaries["backend/app/main.py"] == "接入 AI Provider。"
    assert draft.suggestions == ["建议补充 Provider 降级测试。"]


def test_deepseek_provider_extracts_json_from_markdown_fence():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '```json\n{"summary":"fenced","fileSummaries":[],"suggestions":[]}\n```'
                        }
                    }
                ]
            },
        )

    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.test",
        model="deepseek-v4-flash",
        timeout=5,
        transport=httpx.MockTransport(handler),
    )

    assert provider.analyze(_context(), []).summary == "fenced"


def test_deepseek_provider_invalid_json_raises_invalid_json_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    provider = DeepSeekProvider(
        api_key="test-key",
        base_url="https://api.deepseek.test",
        model="deepseek-v4-flash",
        timeout=5,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIProviderError) as exc_info:
        provider.analyze(_context(), [])

    assert exc_info.value.code == "AI_INVALID_JSON"


def _settings(ai_provider: str, deepseek_api_key: str) -> Settings:
    return Settings(
        AI_PROVIDER=ai_provider,
        DEEPSEEK_API_KEY=deepseek_api_key,
        DEEPSEEK_BASE_URL="https://api.deepseek.test",
        DEEPSEEK_MODEL="deepseek-v4-flash",
        AI_TIMEOUT_SECONDS=5,
    )


def _context() -> GitHubPrContext:
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
        truncated=False,
        warnings=[],
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
