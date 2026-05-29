from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AnalyzePrRequest(ApiModel):
    pr_url: str = Field(min_length=1)


class PrMetadata(ApiModel):
    url: str
    owner: str
    repo: str
    number: int
    title: str
    author: str
    base_branch: str
    head_branch: str
    changed_files: int
    additions: int
    deletions: int


class FileSummary(ApiModel):
    file: str
    status: str
    additions: int
    deletions: int
    summary: str


class RiskItem(ApiModel):
    id: str
    severity: Literal["low", "medium", "high"]
    source: Literal["rule", "ai", "mixed"]
    rule_name: str | None = None
    file: str | None = None
    title: str
    description: str
    suggestion: str


class AnalysisResult(ApiModel):
    summary: str
    risk_level: Literal["low", "medium", "high"]
    truncated: bool
    file_summaries: list[FileSummary]
    risks: list[RiskItem]
    suggestions: list[str]
    markdown_review: str


class WarningItem(ApiModel):
    code: str
    message: str


class AnalyzeMeta(ApiModel):
    provider: str
    mock: bool
    analyzed_at: str
    duration_ms: int
    warnings: list[WarningItem]


class AnalyzePrResponse(ApiModel):
    pr: PrMetadata
    analysis: AnalysisResult
    meta: AnalyzeMeta
