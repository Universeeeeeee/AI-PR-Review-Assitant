from fastapi import FastAPI

app = FastAPI(title="AI PR Review Assistant API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-pr-review-assistant-backend",
    }
