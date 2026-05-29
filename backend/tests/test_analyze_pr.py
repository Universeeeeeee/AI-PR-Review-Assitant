import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.schemas import AnalyzePrResponse, PrMetadata, WarningItem
from app.services.github_client import (
    ChangedFile,
    GitHubApiError,
    GitHubNotFoundError,
    GitHubPrContext,
    GitHubRateLimitedError,
)


def test_analyze_pr_returns_mock_review_contract():
    app.state.github_client = FakeGitHubClient()
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"},
    )
    del app.state.github_client

    assert response.status_code == 200
    body = response.json()

    assert body["pr"]["url"] == "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"
    assert body["pr"]["owner"] == "Universeeeeeee"
    assert body["pr"]["repo"] == "AI-PR-Review-Assitant"
    assert body["pr"]["number"] == 2
    assert body["pr"]["title"] == "feat: add mock PR analysis API"
    assert body["pr"]["author"] == "Universeeeeeee"
    assert body["pr"]["changedFiles"] == 2

    assert body["analysis"]["riskLevel"] == "high"
    assert body["analysis"]["truncated"] is True
    assert "feat: add mock PR analysis API" in body["analysis"]["summary"]
    assert body["analysis"]["fileSummaries"][0]["file"] == "backend/app/main.py"
    assert body["analysis"]["risks"]
    assert body["analysis"]["suggestions"]
    assert "## AI PR Review" in body["analysis"]["markdownReview"]

    assert body["meta"]["provider"] == "mock"
    assert body["meta"]["mock"] is True
    assert body["meta"]["analyzedAt"]
    assert isinstance(body["meta"]["durationMs"], int)
    assert body["meta"]["warnings"] == [
        {
            "code": "MOCK_MODE",
            "message": "当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。",
        },
        {
            "code": "PATCH_TRUNCATED",
            "message": "当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
        }
    ]


def test_analyze_pr_rejects_invalid_github_pr_url():
    app.state.github_client = FakeGitHubClient()
    client = TestClient(app)

    response = client.post("/api/analyze-pr", json={"prUrl": "https://example.com/not-a-pr"})
    del app.state.github_client

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "code": "INVALID_PR_URL",
            "message": "请输入有效的 GitHub Pull Request URL。",
        }
    }


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (GitHubNotFoundError("not found"), 404, "GITHUB_NOT_FOUND"),
        (GitHubRateLimitedError("rate limited"), 429, "GITHUB_RATE_LIMITED"),
        (GitHubApiError("api error"), 502, "GITHUB_API_ERROR"),
    ],
)
def test_analyze_pr_maps_github_client_errors(error: Exception, status_code: int, code: str):
    app.state.github_client = ErrorGitHubClient(error)
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"},
    )
    del app.state.github_client

    assert response.status_code == status_code
    assert response.json()["detail"]["code"] == code


def test_analyze_pr_returns_rule_engine_risks_from_github_patch():
    app.state.github_client = FakeGitHubClient()
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"},
    )
    del app.state.github_client

    assert response.status_code == 200
    risks = response.json()["analysis"]["risks"]
    rule_names = {risk["ruleName"] for risk in risks}
    assert "hardcoded-secret" in rule_names
    assert "mock-review-focus" not in rule_names


def test_analyze_pr_duration_includes_report_generation_time(monkeypatch):
    app.state.github_client = FakeGitHubClient()
    original_builder = main_module.build_mock_analysis_from_context

    def slow_builder(*args, **kwargs) -> AnalyzePrResponse:
        import time

        time.sleep(0.03)
        return original_builder(*args, **kwargs)

    monkeypatch.setattr(main_module, "build_mock_analysis_from_context", slow_builder)
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"},
    )
    del app.state.github_client

    assert response.status_code == 200
    assert response.json()["meta"]["durationMs"] >= 30


def test_analyze_pr_response_uses_camel_case_keys():
    app.state.github_client = FakeGitHubClient()
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"},
    )
    del app.state.github_client

    assert response.status_code == 200
    body = response.json()
    assert "changedFiles" in body["pr"]
    assert "changed_files" not in body["pr"]
    assert "riskLevel" in body["analysis"]
    assert "risk_level" not in body["analysis"]
    assert "fileSummaries" in body["analysis"]
    assert "file_summaries" not in body["analysis"]
    assert "markdownReview" in body["analysis"]
    assert "markdown_review" not in body["analysis"]
    assert "analyzedAt" in body["meta"]
    assert "analyzed_at" not in body["meta"]
    assert "durationMs" in body["meta"]
    assert "duration_ms" not in body["meta"]


class FakeGitHubClient:
    def fetch_pr_context(self, pr_url: str) -> GitHubPrContext:
        if not pr_url.startswith("https://github.com/"):
            from app.services.github_client import InvalidPrUrlError

            raise InvalidPrUrlError("invalid")
        return GitHubPrContext(
            pr=PrMetadata(
                url="https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2",
                owner="Universeeeeeee",
                repo="AI-PR-Review-Assitant",
                number=2,
                title="feat: add mock PR analysis API",
                author="Universeeeeeee",
                base_branch="main",
                head_branch="feat/mock-analyze-api",
                changed_files=2,
                additions=120,
                deletions=8,
            ),
            files=[
                ChangedFile(
                    filename="backend/app/main.py",
                    status="modified",
                    additions=30,
                    deletions=2,
                    patch='@@ -1 +1 @@\n-old\n+ API_TOKEN = "secret-value"\n',
                )
            ],
            truncated=True,
            warnings=[
                WarningItem(
                    code="PATCH_TRUNCATED",
                    message="当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
                )
            ],
        )


class ErrorGitHubClient:
    def __init__(self, error: Exception):
        self._error = error

    def fetch_pr_context(self, pr_url: str) -> GitHubPrContext:
        raise self._error
