import { afterEach, describe, expect, it } from "vitest";

import type { AnalyzePrResponse } from "./api";
import {
  ANALYSIS_HISTORY_KEY,
  clearAnalysisHistory,
  loadAnalysisHistory,
  saveAnalysisHistoryItem,
} from "./history";

describe("analysis history storage", () => {
  afterEach(() => {
    localStorage.clear();
  });

  it("returns an empty list when storage is missing or invalid", () => {
    expect(loadAnalysisHistory()).toEqual([]);

    localStorage.setItem(ANALYSIS_HISTORY_KEY, "not-json");

    expect(loadAnalysisHistory()).toEqual([]);
  });

  it("ignores malformed stored history items", () => {
    localStorage.setItem(
      ANALYSIS_HISTORY_KEY,
      JSON.stringify([
        {
          id: "owner/repo#1",
          prUrl: "https://github.com/owner/repo/pull/1",
          repo: "owner/repo",
          number: 1,
          title: "PR 1",
          summary: "Summary 1",
          analyzedAt: "2026-05-30T00:00:01Z",
          result: makeResult(1),
        },
      ]),
    );

    expect(loadAnalysisHistory()).toEqual([]);
  });

  it("saves an analysis with PR metadata and full result", () => {
    const result = makeResult(1);

    const history = saveAnalysisHistoryItem("https://github.com/owner/repo/pull/1", result);

    expect(history).toHaveLength(1);
    expect(history[0]).toMatchObject({
      id: "owner/repo#1",
      prUrl: "https://github.com/owner/repo/pull/1",
      repo: "owner/repo",
      number: 1,
      title: "PR 1",
      riskLevel: "medium",
      summary: "Summary 1",
      analyzedAt: "2026-05-30T00:00:01Z",
      result,
    });
    expect(loadAnalysisHistory()[0].result.analysis.markdownReview).toBe("## Review 1");
  });

  it("moves duplicate PR URLs to the top instead of duplicating", () => {
    saveAnalysisHistoryItem("https://github.com/owner/repo/pull/1", makeResult(1));
    saveAnalysisHistoryItem("https://github.com/owner/repo/pull/2", makeResult(2));

    const history = saveAnalysisHistoryItem("https://github.com/owner/repo/pull/1", {
      ...makeResult(1),
      analysis: {
        ...makeResult(1).analysis,
        summary: "Updated summary",
      },
    });

    expect(history).toHaveLength(2);
    expect(history[0].prUrl).toBe("https://github.com/owner/repo/pull/1");
    expect(history[0].summary).toBe("Updated summary");
    expect(history[1].prUrl).toBe("https://github.com/owner/repo/pull/2");
  });

  it("keeps only the latest ten analyses", () => {
    for (let index = 1; index <= 12; index += 1) {
      saveAnalysisHistoryItem(`https://github.com/owner/repo/pull/${index}`, makeResult(index));
    }

    const history = loadAnalysisHistory();

    expect(history).toHaveLength(10);
    expect(history[0].number).toBe(12);
    expect(history[9].number).toBe(3);
  });

  it("clears analysis history", () => {
    saveAnalysisHistoryItem("https://github.com/owner/repo/pull/1", makeResult(1));

    clearAnalysisHistory();

    expect(loadAnalysisHistory()).toEqual([]);
  });
});

function makeResult(number: number): AnalyzePrResponse {
  return {
    pr: {
      url: `https://github.com/owner/repo/pull/${number}`,
      owner: "owner",
      repo: "repo",
      number,
      title: `PR ${number}`,
      author: "alice",
      baseBranch: "main",
      headBranch: "feature",
      changedFiles: 2,
      additions: 10,
      deletions: 2,
    },
    analysis: {
      summary: `Summary ${number}`,
      riskLevel: "medium",
      truncated: false,
      fileSummaries: [],
      risks: [],
      suggestions: [],
      markdownReview: `## Review ${number}`,
    },
    meta: {
      provider: "mock",
      mock: true,
      analyzedAt: `2026-05-30T00:00:${String(number).padStart(2, "0")}Z`,
      durationMs: 100,
      warnings: [],
    },
  };
}
