export type RiskLevel = "low" | "medium" | "high";

export type WarningItem = {
  code: string;
  message: string;
};

export type PullRequestMetadata = {
  url: string;
  owner: string;
  repo: string;
  number: number;
  title: string;
  author: string;
  baseBranch: string;
  headBranch: string;
  changedFiles: number;
  additions: number;
  deletions: number;
};

export type FileSummary = {
  file: string;
  status: string;
  additions: number;
  deletions: number;
  summary: string;
};

export type RiskItem = {
  id: string;
  severity: RiskLevel;
  source: "rule" | "ai" | "mixed";
  ruleName?: string | null;
  file?: string | null;
  title: string;
  description: string;
  suggestion: string;
};

export type AnalysisResult = {
  summary: string;
  riskLevel: RiskLevel;
  truncated: boolean;
  fileSummaries: FileSummary[];
  risks: RiskItem[];
  suggestions: string[];
  markdownReview: string;
};

export type AnalyzeMeta = {
  provider: string;
  mock: boolean;
  analyzedAt: string;
  durationMs: number;
  warnings: WarningItem[];
};

export type AnalyzePrResponse = {
  pr: PullRequestMetadata;
  analysis: AnalysisResult;
  meta: AnalyzeMeta;
};

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export class AnalyzePrApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "AnalyzePrApiError";
    this.code = code;
  }
}

export async function analyzePullRequest(
  prUrl: string,
  fetchImpl: FetchLike = fetch,
): Promise<AnalyzePrResponse> {
  const response = await fetchImpl(`${apiBaseUrl()}/api/analyze-pr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prUrl }),
  });

  const payload: unknown = await response.json();
  if (!response.ok) {
    throw parseApiError(payload);
  }
  return payload as AnalyzePrResponse;
}

function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return DEFAULT_API_BASE_URL;
}

function parseApiError(payload: unknown): AnalyzePrApiError {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    payload.detail &&
    typeof payload.detail === "object" &&
    "message" in payload.detail
  ) {
    const detail = payload.detail as { code?: unknown; message?: unknown };
    return new AnalyzePrApiError(
      typeof detail.code === "string" ? detail.code : "API_ERROR",
      typeof detail.message === "string" ? detail.message : "分析请求失败，请稍后重试。",
    );
  }
  return new AnalyzePrApiError("API_ERROR", "分析请求失败，请稍后重试。");
}
