import type { AnalyzePrResponse, RiskLevel } from "./api";

export const ANALYSIS_HISTORY_KEY = "ai-pr-review-history";
const MAX_HISTORY_ITEMS = 10;

export type AnalysisHistoryItem = {
  id: string;
  prUrl: string;
  repo: string;
  number: number;
  title: string;
  riskLevel: RiskLevel;
  summary: string;
  analyzedAt: string;
  result: AnalyzePrResponse;
};

export function loadAnalysisHistory(): AnalysisHistoryItem[] {
  const raw = localStorage.getItem(ANALYSIS_HISTORY_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isAnalysisHistoryItem);
  } catch {
    return [];
  }
}

export function saveAnalysisHistoryItem(prUrl: string, result: AnalyzePrResponse): AnalysisHistoryItem[] {
  const item = buildHistoryItem(prUrl, result);
  const previous = loadAnalysisHistory().filter((historyItem) => historyItem.prUrl !== prUrl);
  const next = [item, ...previous].slice(0, MAX_HISTORY_ITEMS);
  localStorage.setItem(ANALYSIS_HISTORY_KEY, JSON.stringify(next));
  return next;
}

export function clearAnalysisHistory(): void {
  localStorage.removeItem(ANALYSIS_HISTORY_KEY);
}

function buildHistoryItem(prUrl: string, result: AnalyzePrResponse): AnalysisHistoryItem {
  const repo = `${result.pr.owner}/${result.pr.repo}`;
  return {
    id: `${repo}#${result.pr.number}`,
    prUrl,
    repo,
    number: result.pr.number,
    title: result.pr.title,
    riskLevel: result.analysis.riskLevel,
    summary: result.analysis.summary,
    analyzedAt: result.meta.analyzedAt,
    result,
  };
}

function isAnalysisHistoryItem(value: unknown): value is AnalysisHistoryItem {
  if (!value || typeof value !== "object") {
    return false;
  }
  const item = value as Partial<AnalysisHistoryItem>;
  return (
    typeof item.id === "string" &&
    typeof item.prUrl === "string" &&
    typeof item.repo === "string" &&
    typeof item.number === "number" &&
    typeof item.title === "string" &&
    isRiskLevel(item.riskLevel) &&
    typeof item.summary === "string" &&
    typeof item.analyzedAt === "string" &&
    Boolean(item.result)
  );
}

function isRiskLevel(value: unknown): value is RiskLevel {
  return value === "low" || value === "medium" || value === "high";
}
