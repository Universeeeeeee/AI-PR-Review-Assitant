from time import perf_counter

from fastapi import FastAPI, HTTPException, status

from app.config import get_settings
from app.schemas import AnalyzePrRequest, AnalyzePrResponse
from app.services.github_client import (
    GitHubApiError,
    GitHubClient,
    GitHubClientConfig,
    GitHubNotFoundError,
    GitHubRateLimitedError,
    InvalidPrUrlError,
)
from app.services.mock_analyzer import build_mock_analysis_from_context

app = FastAPI(title="AI PR Review Assistant API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-pr-review-assistant-backend",
    }


@app.post("/api/analyze-pr", response_model=AnalyzePrResponse)
def analyze_pr(request: AnalyzePrRequest) -> AnalyzePrResponse:
    started = perf_counter()
    try:
        context = _get_github_client().fetch_pr_context(request.pr_url)
        duration_ms = int((perf_counter() - started) * 1000)
        return build_mock_analysis_from_context(context, duration_ms=duration_ms)
    except InvalidPrUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PR_URL",
                "message": "请输入有效的 GitHub Pull Request URL。",
            },
        ) from exc
    except GitHubNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GITHUB_NOT_FOUND",
                "message": "未找到对应的 GitHub Pull Request，请确认仓库和 PR 编号是否存在。",
            },
        ) from exc
    except GitHubRateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "GITHUB_RATE_LIMITED",
                "message": "GitHub API 访问频率受限，请稍后重试或配置 GITHUB_TOKEN。",
            },
        ) from exc
    except GitHubApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "GITHUB_API_ERROR",
                "message": "调用 GitHub API 失败，请稍后重试。",
            },
        ) from exc


def _get_github_client() -> GitHubClient:
    if hasattr(app.state, "github_client"):
        return app.state.github_client

    settings = get_settings()
    return GitHubClient(
        GitHubClientConfig(
            token=settings.github_token,
            max_files=settings.max_files,
            max_patch_chars=settings.max_patch_chars,
            timeout=settings.request_timeout,
        )
    )
