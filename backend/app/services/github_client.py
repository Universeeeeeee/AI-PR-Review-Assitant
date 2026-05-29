import re
from dataclasses import dataclass

import httpx

from app.schemas import PrMetadata, WarningItem


class InvalidPrUrlError(ValueError):
    """Raised when the input is not a public GitHub Pull Request URL."""


class GitHubApiError(RuntimeError):
    """Raised when GitHub returns an unexpected API error."""


class GitHubNotFoundError(GitHubApiError):
    """Raised when the requested PR or repository cannot be found."""


class GitHubRateLimitedError(GitHubApiError):
    """Raised when GitHub API rate limits are exhausted."""


@dataclass(frozen=True)
class ParsedPullRequestUrl:
    owner: str
    repo: str
    number: int
    canonical_url: str


@dataclass(frozen=True)
class ChangedFile:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str


@dataclass(frozen=True)
class GitHubPrContext:
    pr: PrMetadata
    files: list[ChangedFile]
    truncated: bool
    warnings: list[WarningItem]


@dataclass(frozen=True)
class GitHubClientConfig:
    token: str = ""
    max_files: int = 20
    max_patch_chars: int = 30000
    timeout: int = 60
    base_url: str = "https://api.github.com"


PR_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?(?:[?#].*)?$"
)

TRUNCATED_WARNING = WarningItem(
    code="PATCH_TRUNCATED",
    message="当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
)


def parse_github_pr_url(pr_url: str) -> ParsedPullRequestUrl:
    match = PR_URL_PATTERN.match(pr_url.strip())
    if not match:
        raise InvalidPrUrlError("Invalid GitHub Pull Request URL")

    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))

    return ParsedPullRequestUrl(
        owner=owner,
        repo=repo,
        number=number,
        canonical_url=f"https://github.com/{owner}/{repo}/pull/{number}",
    )


class GitHubClient:
    def __init__(self, config: GitHubClientConfig, transport: httpx.BaseTransport | None = None):
        self._config = config
        self._transport = transport

    def fetch_pr_context(self, pr_url: str) -> GitHubPrContext:
        parsed = parse_github_pr_url(pr_url)
        with httpx.Client(
            base_url=self._config.base_url,
            headers=self._headers(),
            timeout=self._config.timeout,
            transport=self._transport,
        ) as client:
            pr_payload = self._get_json(client, f"/repos/{parsed.owner}/{parsed.repo}/pulls/{parsed.number}")
            files_payload = self._get_json(
                client, f"/repos/{parsed.owner}/{parsed.repo}/pulls/{parsed.number}/files"
            )

        return self._build_context(parsed, pr_payload, files_payload)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-pr-review-assistant",
        }
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"
        return headers

    def _get_json(self, client: httpx.Client, path: str) -> object:
        response = client.get(path)
        if response.status_code == 404:
            raise GitHubNotFoundError("GitHub Pull Request not found")
        if response.status_code in {403, 429} and response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubRateLimitedError("GitHub API rate limit exceeded")
        if response.status_code >= 400:
            raise GitHubApiError(f"GitHub API error: {response.status_code}")
        return response.json()

    def _build_context(
        self,
        parsed: ParsedPullRequestUrl,
        pr_payload: object,
        files_payload: object,
    ) -> GitHubPrContext:
        if not isinstance(pr_payload, dict) or not isinstance(files_payload, list):
            raise GitHubApiError("Unexpected GitHub API response shape")

        pr = PrMetadata(
            url=str(pr_payload.get("html_url") or parsed.canonical_url),
            owner=parsed.owner,
            repo=parsed.repo,
            number=parsed.number,
            title=str(pr_payload.get("title") or ""),
            author=str(_nested_get(pr_payload, "user", "login") or "unknown"),
            base_branch=str(_nested_get(pr_payload, "base", "ref") or ""),
            head_branch=str(_nested_get(pr_payload, "head", "ref") or ""),
            changed_files=int(pr_payload.get("changed_files") or 0),
            additions=int(pr_payload.get("additions") or 0),
            deletions=int(pr_payload.get("deletions") or 0),
        )

        truncated = len(files_payload) > self._config.max_files
        files: list[ChangedFile] = []
        for item in files_payload[: self._config.max_files]:
            if not isinstance(item, dict):
                continue
            patch = str(item.get("patch") or "")
            if len(patch) > self._config.max_patch_chars:
                patch = patch[: self._config.max_patch_chars]
                truncated = True
            files.append(
                ChangedFile(
                    filename=str(item.get("filename") or ""),
                    status=str(item.get("status") or ""),
                    additions=int(item.get("additions") or 0),
                    deletions=int(item.get("deletions") or 0),
                    patch=patch,
                )
            )

        return GitHubPrContext(
            pr=pr,
            files=files,
            truncated=truncated,
            warnings=[TRUNCATED_WARNING] if truncated else [],
        )


def _nested_get(payload: dict[str, object], *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
