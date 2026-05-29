import json
import re
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import Settings
from app.schemas import RiskItem
from app.services.github_client import GitHubPrContext


class AIProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class AIAnalysisDraft:
    summary: str
    file_summaries: dict[str, str] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


class AIProvider(Protocol):
    name: str
    mock: bool

    def analyze(self, context: GitHubPrContext, rule_risks: list[RiskItem]) -> AIAnalysisDraft:
        ...


class MockProvider:
    name = "mock"
    mock = True

    def analyze(self, context: GitHubPrContext, rule_risks: list[RiskItem]) -> AIAnalysisDraft:
        suggestions = ["建议确认 PR 描述中包含功能描述、实现思路和测试方式。"]
        if rule_risks:
            suggestions.append("建议优先人工确认规则引擎标记的可能风险，并结合真实 diff 判断是否需要修改。")
        else:
            suggestions.append("当前规则引擎未发现第一批确定性风险，仍建议人工 Review 核心变更路径。")

        return AIAnalysisDraft(
            summary=f"Mock 分析已基于 GitHub PR `{context.pr.title}` 获取真实元信息和 changed files。",
            file_summaries={
                file.filename: (
                    f"Mock 总结：`{file.filename}` 本次变更包含 {file.additions} 行新增和 "
                    f"{file.deletions} 行删除。"
                )
                for file in context.files
            },
            suggestions=suggestions,
        )


class DeepSeekProvider:
    name = "deepseek"
    mock = False

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._transport = transport

    def analyze(self, context: GitHubPrContext, rule_risks: list[RiskItem]) -> AIAnalysisDraft:
        try:
            with httpx.Client(
                base_url=self._base_url,
                headers=self._headers(),
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = client.post("/chat/completions", json=self._payload(context, rule_risks))
        except httpx.TimeoutException as exc:
            raise AIProviderError("AI_TIMEOUT", "DeepSeek 分析请求超时。") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError("AI_PROVIDER_ERROR", "调用 DeepSeek API 失败。") from exc

        if response.status_code >= 400:
            raise AIProviderError("AI_PROVIDER_ERROR", f"DeepSeek API 返回错误状态码：{response.status_code}。")

        content = _extract_message_content(response)
        return _parse_ai_draft(content)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, context: GitHubPrContext, rule_risks: list[RiskItem]) -> dict[str, object]:
        return {
            "model": self._model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI PR review assistant. Return only a valid json object. "
                        "Use cautious wording such as possible risk, recommend confirming, and "
                        "avoid claiming a definite vulnerability or bug. The json object must "
                        "contain summary, fileSummaries, and suggestions."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_prompt(context, rule_risks),
                },
            ],
        }


def build_ai_provider(
    settings: Settings,
    transport: httpx.BaseTransport | None = None,
) -> AIProvider:
    mode = settings.ai_provider.strip().lower()
    has_key = bool(settings.deepseek_api_key.strip())

    if mode == "mock":
        return MockProvider()
    if mode == "auto" and not has_key:
        return MockProvider()
    if mode == "deepseek" and not has_key:
        raise AIProviderError("AI_PROVIDER_ERROR", "AI_PROVIDER=deepseek 时必须配置 DEEPSEEK_API_KEY。")
    if mode in {"auto", "deepseek"}:
        return DeepSeekProvider(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout=settings.ai_timeout_seconds,
            transport=transport,
        )

    raise AIProviderError("AI_PROVIDER_ERROR", "AI_PROVIDER 只支持 auto、mock 或 deepseek。")


def _build_prompt(context: GitHubPrContext, rule_risks: list[RiskItem]) -> str:
    files = "\n\n".join(
        (
            f"File: {file.filename}\n"
            f"Status: {file.status}\n"
            f"Additions: {file.additions}, Deletions: {file.deletions}\n"
            f"Patch:\n{file.patch[:4000]}"
        )
        for file in context.files
    )
    risks = json.dumps(
        [risk.model_dump(mode="json", by_alias=True) for risk in rule_risks],
        ensure_ascii=False,
    )
    return (
        f"PR: {context.pr.owner}/{context.pr.repo}#{context.pr.number}\n"
        f"Title: {context.pr.title}\n"
        f"Author: {context.pr.author}\n"
        f"Base: {context.pr.base_branch}, Head: {context.pr.head_branch}\n\n"
        f"Rule risks JSON:\n{risks}\n\n"
        f"Changed files and patches:\n{files}\n\n"
        "Return this JSON shape exactly:\n"
        '{"summary":"...","fileSummaries":[{"file":"path","summary":"..."}],"suggestions":["..."]}'
    )


def _extract_message_content(response: httpx.Response) -> str:
    try:
        payload = response.json()
        choices = payload["choices"]
        return str(choices[0]["message"]["content"])
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("AI_PROVIDER_ERROR", "DeepSeek API 返回结构不符合预期。") from exc


def _parse_ai_draft(content: str) -> AIAnalysisDraft:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIProviderError("AI_INVALID_JSON", "DeepSeek 返回的内容不是有效 JSON。") from exc

    if not isinstance(payload, dict):
        raise AIProviderError("AI_INVALID_JSON", "DeepSeek 返回的 JSON 顶层必须是对象。")

    return AIAnalysisDraft(
        summary=str(payload.get("summary") or ""),
        file_summaries=_parse_file_summaries(payload),
        suggestions=_parse_suggestions(payload),
    )


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1)

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return stripped[first_brace : last_brace + 1]
    return stripped


def _parse_file_summaries(payload: dict[str, object]) -> dict[str, str]:
    raw = payload.get("fileSummaries") or payload.get("file_summaries") or []
    if isinstance(raw, dict):
        return {str(key): str(value) for key, value in raw.items()}
    if not isinstance(raw, list):
        return {}

    summaries: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        file = item.get("file")
        summary = item.get("summary")
        if file and summary:
            summaries[str(file)] = str(summary)
    return summaries


def _parse_suggestions(payload: dict[str, object]) -> list[str]:
    raw = payload.get("suggestions") or []
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if item]
