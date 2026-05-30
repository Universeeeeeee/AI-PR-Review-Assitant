from time import perf_counter

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.config import get_settings
from app.config import parse_cors_origins
from app.schemas import AnalyzePrRequest, AnalyzePrResponse, WarningItem
from app.services.ai_provider import AIProvider, AIProviderError, MockProvider, build_ai_provider
from app.services.github_client import (
    GitHubApiError,
    GitHubClient,
    GitHubClientConfig,
    GitHubNotFoundError,
    GitHubRateLimitedError,
    InvalidPrUrlError,
)
from app.services.report_composer import compose_review_response
from app.services.rule_engine import analyze_rules

app = FastAPI(title="AI PR Review Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(get_settings().cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-pr-review-assistant-backend",
    }


@app.post("/api/analyze-pr", response_model=AnalyzePrResponse, response_model_by_alias=True)
def analyze_pr(request: AnalyzePrRequest) -> AnalyzePrResponse:
    started = perf_counter()
    try:
        settings = _get_settings()
        context = _get_github_client(settings).fetch_pr_context(request.pr_url)
        rule_risks = analyze_rules(context)
        provider = _get_ai_provider(settings)
        extra_warnings: list[WarningItem] = []

        try:
            ai_draft = provider.analyze(context, rule_risks)
            provider_name = provider.name
            mock = provider.mock
        except AIProviderError as exc:
            if settings.ai_provider.strip().lower() != "auto":
                raise
            fallback_provider = MockProvider()
            ai_draft = fallback_provider.analyze(context, rule_risks)
            provider_name = fallback_provider.name
            mock = fallback_provider.mock
            extra_warnings.append(_fallback_warning(exc))

        response = compose_review_response(
            context=context,
            rule_risks=rule_risks,
            ai_draft=ai_draft,
            provider_name=provider_name,
            mock=mock,
            duration_ms=0,
            extra_warnings=extra_warnings,
        )
        response.meta.duration_ms = int((perf_counter() - started) * 1000)
        return response
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
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": exc.message,
            },
        ) from exc


def _get_settings() -> Settings:
    if hasattr(app.state, "settings"):
        return app.state.settings
    return get_settings()


def _get_github_client(settings: Settings) -> GitHubClient:
    if hasattr(app.state, "github_client"):
        return app.state.github_client

    return GitHubClient(
        GitHubClientConfig(
            token=settings.github_token,
            max_files=settings.max_files,
            max_patch_chars=settings.max_patch_chars,
            timeout=settings.request_timeout,
        )
    )


def _get_ai_provider(settings: Settings) -> AIProvider:
    if hasattr(app.state, "ai_provider"):
        return app.state.ai_provider
    return build_ai_provider(settings)


def _fallback_warning(exc: AIProviderError) -> WarningItem:
    messages = {
        "AI_TIMEOUT": "DeepSeek 分析请求超时，系统已使用 Mock 模式生成报告。",
        "AI_INVALID_JSON": "DeepSeek 返回内容格式异常，系统已使用 Mock 模式生成报告。",
        "AI_PROVIDER_ERROR": "AI Provider 调用失败，系统已使用 Mock 模式生成报告。",
    }
    return WarningItem(
        code=exc.code,
        message=messages.get(exc.code, "AI Provider 调用失败，系统已使用 Mock 模式生成报告。"),
    )
