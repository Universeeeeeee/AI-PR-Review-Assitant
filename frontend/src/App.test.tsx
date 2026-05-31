import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import * as api from "./api";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    cleanup();
  });

  it("renders the initial PR review workbench shell", () => {
    render(<App />);

    expect(screen.getByText("AI PR Review Assistant")).toBeInTheDocument();
    expect(screen.getByText("最近分析")).toBeInTheDocument();
    expect(screen.getByText("分析 Pull Request")).toBeInTheDocument();
  });

  it("submits a PR URL and renders basic analysis result state", async () => {
    vi.spyOn(api, "analyzePullRequest").mockResolvedValue(successPayload);
    render(<App />);

    fireEvent.change(screen.getByLabelText("GitHub PR URL"), {
      target: { value: "https://github.com/owner/repo/pull/1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始分析" }));

    expect(screen.getByText("正在分析 Pull Request...")).toBeInTheDocument();

    expect(await screen.findByRole("heading", { name: "Add API integration" })).toBeInTheDocument();
    const resultRegion = screen.getByRole("region", { name: "评审结果" });
    expect(within(resultRegion).getByText("owner/repo #1")).toBeInTheDocument();
    expect(within(resultRegion).getAllByText("中风险").length).toBeGreaterThan(0);
    expect(within(resultRegion).getByText("AI Provider：mock")).toBeInTheDocument();
    expect(screen.getByText("Mock 模式")).toBeInTheDocument();
    expect(screen.getByText("Diff 已截断")).toBeInTheDocument();
    expect(screen.getByText("AI 总结：本 PR 接入前端 API 调用。")).toBeInTheDocument();
    expect(api.analyzePullRequest).toHaveBeenCalledWith("https://github.com/owner/repo/pull/1");
  });

  it("renders detailed result sections and copies markdown review", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    vi.spyOn(api, "analyzePullRequest").mockResolvedValue(successPayload);
    render(<App />);

    fireEvent.change(screen.getByLabelText("GitHub PR URL"), {
      target: { value: "https://github.com/owner/repo/pull/1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始分析" }));

    expect(await screen.findByRole("heading", { name: "变更文件" })).toBeInTheDocument();
    const changedFilesSection = screen.getByRole("heading", { name: "变更文件" }).closest("section")!;
    expect(within(changedFilesSection).getByText("frontend/src/App.tsx")).toBeInTheDocument();
    expect(within(changedFilesSection).getByText("修改 +32 / -4")).toBeInTheDocument();
    expect(within(changedFilesSection).getByText("渲染分析结果详情。")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "可能风险" })).toBeInTheDocument();
    expect(screen.getByText("建议确认测试覆盖")).toBeInTheDocument();
    const suggestionsSection = screen.getByRole("heading", { name: "评审建议" }).closest("section")!;
    expect(within(suggestionsSection).getByText("建议补充前端交互测试。")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Markdown Review" })).toBeInTheDocument();
    const markdownSection = screen.getByRole("heading", { name: "Markdown Review" }).closest("section")!;
    expect(within(markdownSection).getByText(/## AI PR Review/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "复制 Markdown" }));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith("## AI PR Review\n\nSummary"));
    expect(screen.getByText("Markdown 已复制。")).toBeInTheDocument();
  });

  it("renders backend error message and keeps the URL editable", async () => {
    vi.spyOn(api, "analyzePullRequest").mockRejectedValue(
      new api.AnalyzePrApiError("INVALID_PR_URL", "请输入有效的 GitHub Pull Request URL。"),
    );
    render(<App />);

    const input = screen.getByLabelText("GitHub PR URL");
    fireEvent.change(input, { target: { value: "https://example.com/not-a-pr" } });
    fireEvent.click(screen.getByRole("button", { name: "开始分析" }));

    expect(await screen.findByText("请输入有效的 GitHub Pull Request URL。")).toBeInTheDocument();
    expect(input).toHaveValue("https://example.com/not-a-pr");
    await waitFor(() => expect(screen.getByRole("button", { name: "开始分析" })).not.toBeDisabled());
  });

  it("saves successful analyses to history, restores them without refetching, and clears history", async () => {
    const analyzeSpy = vi.spyOn(api, "analyzePullRequest").mockResolvedValue(successPayload);
    render(<App />);

    fireEvent.change(screen.getByLabelText("GitHub PR URL"), {
      target: { value: "https://github.com/owner/repo/pull/1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始分析" }));

    expect(await screen.findByRole("button", { name: "owner/repo #1 Add API integration 中风险" })).toBeInTheDocument();
    expect(localStorage.getItem("ai-pr-review-history")).toContain("Add API integration");

    analyzeSpy.mockClear();
    fireEvent.change(screen.getByLabelText("GitHub PR URL"), {
      target: { value: "https://github.com/another/repo/pull/2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "owner/repo #1 Add API integration 中风险" }));

    expect(screen.getByLabelText("GitHub PR URL")).toHaveValue("https://github.com/owner/repo/pull/1");
    expect(screen.getByText("AI 总结：本 PR 接入前端 API 调用。")).toBeInTheDocument();
    expect(analyzeSpy).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "清空" }));

    expect(screen.getByText("暂无分析记录。")).toBeInTheDocument();
    expect(localStorage.getItem("ai-pr-review-history")).toBeNull();
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
    fileSummaries: [
      {
        file: "frontend/src/App.tsx",
        status: "modified",
        additions: 32,
        deletions: 4,
        summary: "渲染分析结果详情。",
      },
    ],
    risks: [
      {
        id: "rule-missing-tests-abc123",
        severity: "medium",
        source: "rule",
        ruleName: "missing-tests",
        file: "frontend/src/App.tsx",
        title: "建议确认测试覆盖",
        description: "核心 UI 行为变化，建议确认是否补充测试。",
        suggestion: "建议补充前端交互测试。",
      },
    ],
    suggestions: ["建议补充前端交互测试。"],
    markdownReview: "## AI PR Review\n\nSummary",
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
