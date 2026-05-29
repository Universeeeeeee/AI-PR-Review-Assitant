import httpx
import pytest

from app.schemas import WarningItem
from app.services.github_client import (
    GitHubApiError,
    GitHubClient,
    GitHubClientConfig,
    GitHubNotFoundError,
    GitHubRateLimitedError,
    InvalidPrUrlError,
    parse_github_pr_url,
)


def test_parse_github_pr_url_returns_owner_repo_and_number():
    parsed = parse_github_pr_url("https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2")

    assert parsed.owner == "Universeeeeeee"
    assert parsed.repo == "AI-PR-Review-Assitant"
    assert parsed.number == 2
    assert parsed.canonical_url == "https://github.com/Universeeeeeee/AI-PR-Review-Assitant/pull/2"


@pytest.mark.parametrize(
    "pr_url",
    [
        "https://example.com/owner/repo/pull/1",
        "https://github.com/owner/repo/issues/1",
        "not-a-url",
    ],
)
def test_parse_github_pr_url_rejects_invalid_urls(pr_url: str):
    with pytest.raises(InvalidPrUrlError):
        parse_github_pr_url(pr_url)


def test_fetch_pr_context_maps_metadata_and_changed_files():
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.path == "/repos/owner/repo/pulls/7":
            return httpx.Response(
                200,
                json={
                    "html_url": "https://github.com/owner/repo/pull/7",
                    "title": "Improve login handling",
                    "user": {"login": "alice"},
                    "base": {"ref": "main"},
                    "head": {"ref": "feature/login"},
                    "changed_files": 2,
                    "additions": 42,
                    "deletions": 8,
                },
            )
        if request.url.path == "/repos/owner/repo/pulls/7/files":
            return httpx.Response(
                200,
                json=[
                    {
                        "filename": "src/login.ts",
                        "status": "modified",
                        "additions": 30,
                        "deletions": 4,
                        "patch": "@@ -1 +1 @@\n-old\n+new",
                    },
                    {
                        "filename": "tests/login.test.ts",
                        "status": "added",
                        "additions": 12,
                        "deletions": 0,
                        "patch": "@@ -0,0 +1 @@\n+test",
                    },
                ],
            )
        return httpx.Response(404)

    client = GitHubClient(
        config=GitHubClientConfig(token="token-123", max_files=20, max_patch_chars=30000, timeout=10),
        transport=httpx.MockTransport(handler),
    )

    context = client.fetch_pr_context("https://github.com/owner/repo/pull/7")

    assert requested_urls == [
        "https://api.github.com/repos/owner/repo/pulls/7",
        "https://api.github.com/repos/owner/repo/pulls/7/files",
    ]
    assert context.pr.title == "Improve login handling"
    assert context.pr.author == "alice"
    assert context.pr.base_branch == "main"
    assert context.pr.head_branch == "feature/login"
    assert context.pr.changed_files == 2
    assert context.pr.additions == 42
    assert context.pr.deletions == 8
    assert [file.filename for file in context.files] == ["src/login.ts", "tests/login.test.ts"]
    assert context.files[0].patch == "@@ -1 +1 @@\n-old\n+new"
    assert context.truncated is False
    assert context.warnings == []


def test_fetch_pr_context_applies_file_and_patch_limits():
    long_patch = "+abcdef\n" * 10

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/files"):
            return httpx.Response(
                200,
                json=[
                    {
                        "filename": "src/large.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 1,
                        "patch": long_patch,
                    },
                    {
                        "filename": "src/ignored.py",
                        "status": "modified",
                        "additions": 1,
                        "deletions": 1,
                        "patch": "+ignored",
                    },
                ],
            )
        return httpx.Response(
            200,
            json={
                "html_url": "https://github.com/owner/repo/pull/9",
                "title": "Large change",
                "user": {"login": "bob"},
                "base": {"ref": "main"},
                "head": {"ref": "large"},
                "changed_files": 2,
                "additions": 11,
                "deletions": 2,
            },
        )

    client = GitHubClient(
        config=GitHubClientConfig(max_files=1, max_patch_chars=12, timeout=10),
        transport=httpx.MockTransport(handler),
    )

    context = client.fetch_pr_context("https://github.com/owner/repo/pull/9")

    assert len(context.files) == 1
    assert context.files[0].patch == long_patch[:12]
    assert context.truncated is True
    assert context.warnings == [
        WarningItem(
            code="PATCH_TRUNCATED",
            message="当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
        )
    ]


@pytest.mark.parametrize(
    ("status_code", "headers", "expected_error"),
    [
        (404, {}, GitHubNotFoundError),
        (403, {"X-RateLimit-Remaining": "0"}, GitHubRateLimitedError),
        (500, {}, GitHubApiError),
    ],
)
def test_fetch_pr_context_maps_github_errors(status_code: int, headers: dict[str, str], expected_error: type[Exception]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, headers=headers, json={"message": "error"})

    client = GitHubClient(
        config=GitHubClientConfig(timeout=10),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(expected_error):
        client.fetch_pr_context("https://github.com/owner/repo/pull/7")
