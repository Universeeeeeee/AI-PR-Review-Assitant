from fastapi.testclient import TestClient

from app.main import app


def test_analyze_pr_returns_mock_review_contract():
    client = TestClient(app)

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["pr"]["url"] == "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/1"
    assert body["pr"]["owner"] == "Universeeeeeee"
    assert body["pr"]["repo"] == "AI-PR-Review-Assitant"
    assert body["pr"]["number"] == 1
    assert body["pr"]["changedFiles"] >= 1

    assert body["analysis"]["riskLevel"] == "medium"
    assert body["analysis"]["truncated"] is False
    assert body["analysis"]["summary"]
    assert body["analysis"]["fileSummaries"]
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
        }
    ]


def test_analyze_pr_rejects_invalid_github_pr_url():
    client = TestClient(app)

    response = client.post("/api/analyze-pr", json={"prUrl": "https://example.com/not-a-pr"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "code": "INVALID_PR_URL",
            "message": "请输入有效的 GitHub Pull Request URL。",
        }
    }
