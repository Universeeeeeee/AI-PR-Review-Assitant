import { describe, expect, it, vi } from "vitest";

import { AnalyzePrApiError, analyzePullRequest } from "./api";

describe("analyzePullRequest", () => {
  it("posts the PR URL to the analyze endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(successPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await analyzePullRequest("https://github.com/owner/repo/pull/1", fetchMock);

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/analyze-pr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prUrl: "https://github.com/owner/repo/pull/1" }),
    });
    expect(result.pr.title).toBe("Add API integration");
    expect(result.analysis.riskLevel).toBe("medium");
    expect(result.meta.warnings[0].code).toBe("MOCK_MODE");
  });

  it("throws a structured API error when backend returns detail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            code: "INVALID_PR_URL",
            message: "请输入有效的 GitHub Pull Request URL。",
          },
        }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    let error: unknown;
    try {
      await analyzePullRequest("bad-url", fetchMock);
    } catch (caught) {
      error = caught;
    }

    expect(error).toBeInstanceOf(AnalyzePrApiError);
    expect(error).toMatchObject({
      code: "INVALID_PR_URL",
      message: "请输入有效的 GitHub Pull Request URL。",
    });
  });
});

const successPayload = {
  pr: {
    url: "https://github.com/owner/repo/pull/1",
    owner: "owner",
    repo: "repo",
    number: 1,
    title: "Add API integration",
    author: "alice",
    baseBranch: "main",
    headBranch: "feature",
    changedFiles: 2,
    additions: 42,
    deletions: 8,
  },
  analysis: {
    summary: "AI 总结：本 PR 接入前端 API 调用。",
    riskLevel: "medium",
    truncated: false,
    fileSummaries: [],
    risks: [],
    suggestions: [],
    markdownReview: "## AI PR Review",
  },
  meta: {
    provider: "mock",
    mock: true,
    analyzedAt: "2026-05-30T00:00:00Z",
    durationMs: 120,
    warnings: [
      {
        code: "MOCK_MODE",
        message: "当前未配置 DeepSeek API Key，系统使用 Mock 模式生成报告。",
      },
    ],
  },
};
