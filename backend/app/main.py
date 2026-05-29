from time import perf_counter

from fastapi import FastAPI, HTTPException, status

from app.schemas import AnalyzePrRequest, AnalyzePrResponse
from app.services.mock_analyzer import InvalidPrUrlError, build_mock_analysis

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
        duration_ms = int((perf_counter() - started) * 1000)
        return build_mock_analysis(request.pr_url, duration_ms=duration_ms)
    except InvalidPrUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PR_URL",
                "message": "请输入有效的 GitHub Pull Request URL。",
            },
        ) from exc
