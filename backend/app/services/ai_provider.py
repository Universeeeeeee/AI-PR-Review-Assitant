import json
import re
from dataclasses import dataclass, field
from collections.abc import Iterable
from typing import Protocol

import httpx

from app.config import Settings
from app.schemas import RiskItem
from app.services.github_client import ChangedFile, GitHubPrContext


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
        return AIAnalysisDraft(
            summary=_build_mock_summary(context, rule_risks),
            file_summaries={
                file.filename: _build_mock_file_summary(file, _risks_for_file(rule_risks, file.filename))
                for file in context.files
            },
            suggestions=_build_mock_suggestions(context, rule_risks),
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


def _build_mock_summary(context: GitHubPrContext, rule_risks: list[RiskItem]) -> str:
    changed_files = len(context.files) or context.pr.changed_files
    areas = "、".join(_changed_areas(context.files)) or "通用代码"
    if rule_risks:
        risk_text = f"规则引擎标记 {len(rule_risks)} 条可能风险，最高风险 {_highest_risk(rule_risks)}。"
    else:
        risk_text = "规则引擎未发现第一批确定性风险。"

    truncated_text = "当前 diff 已截断，结论应结合完整 PR 人工确认。" if context.truncated else "当前 diff 未触发截断。"
    return (
        f"Mock 分析基于 GitHub PR `{context.pr.owner}/{context.pr.repo}#{context.pr.number}`"
        f"（{context.pr.title}），覆盖 {changed_files} 个文件，变更规模 +{context.pr.additions}/-{context.pr.deletions}。"
        f"本次变更主要涉及{areas}。{risk_text}{truncated_text}"
    )


def _build_mock_file_summary(file: ChangedFile, file_risks: list[RiskItem]) -> str:
    area = _file_area(file.filename)
    cues = _patch_cues(file.filename, file.patch)
    risk_text = _file_risk_text(file_risks)
    return (
        f"{area}文件 `{file.filename}` {file.status}，新增 {file.additions} 行、删除 {file.deletions} 行。"
        f"{cues}{risk_text}"
    )


def _build_mock_suggestions(context: GitHubPrContext, rule_risks: list[RiskItem]) -> list[str]:
    suggestions = ["建议确认 PR 描述中包含功能描述、实现思路和测试方式，并说明本次变更的主要验证路径。"]
    high_risks = [risk for risk in rule_risks if risk.severity == "high"]
    medium_risks = [risk for risk in rule_risks if risk.severity == "medium"]

    if high_risks:
        titles = "、".join(_unique(risk.title for risk in high_risks[:3]))
        suggestions.append(f"建议优先人工确认高风险项：{titles}。")
    elif medium_risks:
        titles = "、".join(_unique(risk.title for risk in medium_risks[:3]))
        suggestions.append(f"建议重点确认中风险项：{titles}。")
    else:
        suggestions.append("当前规则引擎未发现第一批确定性风险，仍建议人工 Review 核心变更路径。")

    if _has_core_change(context.files) and not _has_test_change(context.files):
        suggestions.append("本 PR 涉及核心代码但未看到测试文件变化，建议确认是否需要补充自动化测试。")
    elif _has_test_change(context.files):
        suggestions.append("本 PR 包含测试变更，建议确认新增或更新的测试覆盖了主要风险路径。")

    if context.truncated:
        suggestions.append("当前 PR diff 已截断，建议结合 GitHub 完整 diff 人工确认未展示部分。")

    return suggestions


def _changed_areas(files: list[ChangedFile]) -> list[str]:
    return _unique(_file_area(file.filename) for file in files)


def _file_area(filename: str) -> str:
    normalized = filename.replace("\\", "/").lower()
    basename = normalized.rsplit("/", 1)[-1]
    if _is_test_file(normalized):
        return "测试"
    if normalized.startswith("backend/") or normalized.startswith("app/") or basename.endswith(".py"):
        return "后端逻辑"
    if normalized.startswith("frontend/") or normalized.startswith("src/") or basename.endswith((".tsx", ".jsx")):
        return "前端界面"
    if _is_config_file(normalized):
        return "配置"
    if normalized.startswith("docs/") or basename.endswith((".md", ".mdx", ".rst")):
        return "文档"
    if basename.endswith((".json", ".yaml", ".yml", ".toml")):
        return "配置"
    return "通用代码"


def _patch_cues(filename: str, patch: str) -> str:
    normalized = filename.replace("\\", "/").lower()
    patch_lower = patch.lower()
    cues: list[str] = []
    if "fetch(" in patch_lower or "axios" in patch_lower or "/api/" in patch_lower:
        cues.append("涉及接口请求或 API 调用路径")
    if "route" in patch_lower or "fastapi" in patch_lower or "@app." in patch_lower:
        cues.append("涉及后端路由或服务入口")
    if "localstorage" in patch_lower:
        cues.append("涉及浏览器本地历史记录")
    if "deepseek" in patch_lower or "ai_provider" in normalized:
        cues.append("涉及 AI Provider 配置或调用")
    if "test" in normalized or "expect(" in patch_lower or "pytest" in patch_lower:
        cues.append("涉及自动化测试")
    if not cues:
        return ""
    return f"变更线索：{'；'.join(_unique(cues))}。"


def _file_risk_text(file_risks: list[RiskItem]) -> str:
    if not file_risks:
        return "未在该文件上标记确定性风险。"
    risk_parts = [f"{risk.title}（{risk.severity}）" for risk in file_risks[:3]]
    return f"规则引擎提示：{'；'.join(risk_parts)}。"


def _risks_for_file(rule_risks: list[RiskItem], filename: str) -> list[RiskItem]:
    return [risk for risk in rule_risks if risk.file == filename]


def _highest_risk(rule_risks: list[RiskItem]) -> str:
    order = {"high": 3, "medium": 2, "low": 1}
    return max((risk.severity for risk in rule_risks), key=lambda severity: order[severity])


def _is_config_file(filename: str) -> bool:
    basename = filename.rsplit("/", 1)[-1]
    return (
        basename == ".env.example"
        or "config" in filename
        or basename.endswith((".env", ".yaml", ".yml", ".json", ".toml"))
    )


def _is_test_file(filename: str) -> bool:
    basename = filename.rsplit("/", 1)[-1]
    return (
        "/test/" in filename
        or "/tests/" in filename
        or "__tests__" in filename
        or basename.startswith("test_")
        or basename.endswith("_test.py")
        or ".test." in basename
        or ".spec." in basename
    )


def _has_core_change(files: list[ChangedFile]) -> bool:
    return any(_file_area(file.filename) in {"后端逻辑", "前端界面", "通用代码"} for file in files)


def _has_test_change(files: list[ChangedFile]) -> bool:
    return any(_is_test_file(file.filename.replace("\\", "/").lower()) for file in files)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


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
