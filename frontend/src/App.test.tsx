import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import * as api from "./api";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  it("renders the initial PR review workbench shell", () => {
    render(<App />);

    expect(screen.getByText("AI PR Review Assistant")).toBeInTheDocument();
    expect(screen.getByText("Recent Analyses")).toBeInTheDocument();
    expect(screen.getByText("Analyze Pull Request")).toBeInTheDocument();
  });

  it("submits a PR URL and renders basic analysis result state", async () => {
    vi.spyOn(api, "analyzePullRequest").mockResolvedValue(successPayload);
    render(<App />);

    fireEvent.change(screen.getByLabelText("GitHub PR URL"), {
      target: { value: "https://github.com/owner/repo/pull/1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));

    expect(screen.getByText("Analyzing Pull Request...")).toBeInTheDocument();

    expect(await screen.findByText("Add API integration")).toBeInTheDocument();
    expect(screen.getByText("owner/repo #1")).toBeInTheDocument();
    expect(screen.getByText("Medium risk")).toBeInTheDocument();
    expect(screen.getByText("Provider: mock")).toBeInTheDocument();
    expect(screen.getByText("Mock mode")).toBeInTheDocument();
    expect(screen.getByText("Diff truncated")).toBeInTheDocument();
    expect(screen.getByText("AI 总结：本 PR 接入前端 API 调用。")).toBeInTheDocument();
    expect(api.analyzePullRequest).toHaveBeenCalledWith("https://github.com/owner/repo/pull/1");
  });

  it("renders backend error message and keeps the URL editable", async () => {
    vi.spyOn(api, "analyzePullRequest").mockRejectedValue(
      new api.AnalyzePrApiError("INVALID_PR_URL", "请输入有效的 GitHub Pull Request URL。"),
    );
    render(<App />);

    const input = screen.getByLabelText("GitHub PR URL");
    fireEvent.change(input, { target: { value: "https://example.com/not-a-pr" } });
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));

    expect(await screen.findByText("请输入有效的 GitHub Pull Request URL。")).toBeInTheDocument();
    expect(input).toHaveValue("https://example.com/not-a-pr");
    await waitFor(() => expect(screen.getByRole("button", { name: "Analyze" })).not.toBeDisabled());
  });
});

const successPayload: api.AnalyzePrResponse = {
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
    truncated: true,
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
      {
        code: "PATCH_TRUNCATED",
        message: "当前 PR 变更较大，系统已截断部分 diff 内容进行快速分析。",
      },
    ],
  },
};
