import { type FormEvent, useState } from "react";

import { AnalyzePrApiError, type AnalyzePrResponse, analyzePullRequest } from "./api";
import {
  type AnalysisHistoryItem,
  clearAnalysisHistory,
  loadAnalysisHistory,
  saveAnalysisHistoryItem,
} from "./history";

type ViewState = "idle" | "loading" | "success" | "error";

function App() {
  const [prUrl, setPrUrl] = useState("");
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [result, setResult] = useState<AnalyzePrResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState<AnalysisHistoryItem[]>(() => loadAnalysisHistory());
  const [copyStatus, setCopyStatus] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUrl = prUrl.trim();
    if (!trimmedUrl) {
      setErrorMessage("请输入 GitHub Pull Request URL。");
      setViewState("error");
      return;
    }

    setViewState("loading");
    setErrorMessage("");
    setCopyStatus("");
    try {
      const response = await analyzePullRequest(trimmedUrl);
      setResult(response);
      setHistory(saveAnalysisHistoryItem(trimmedUrl, response));
      setViewState("success");
    } catch (error) {
      setErrorMessage(error instanceof AnalyzePrApiError ? error.message : "分析请求失败，请稍后重试。");
      setViewState("error");
    }
  }

  function restoreHistoryItem(item: AnalysisHistoryItem) {
    setPrUrl(item.prUrl);
    setResult(item.result);
    setErrorMessage("");
    setCopyStatus("");
    setViewState("success");
  }

  function handleClearHistory() {
    clearAnalysisHistory();
    setHistory([]);
  }

  async function handleCopyMarkdown(markdownReview: string) {
    if (!navigator.clipboard) {
      setCopyStatus("当前浏览器不支持剪贴板复制。");
      return;
    }
    await navigator.clipboard.writeText(markdownReview);
    setCopyStatus("Markdown 已复制。");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">开发者 Review 工作台</p>
          <h1>AI PR Review Assistant</h1>
        </div>
      </header>

      <div className="workbench">
        <aside className="sidebar" aria-label="最近分析">
          <div className="panel-heading">
            <h2>最近分析</h2>
            <button type="button" className="ghost-button" onClick={handleClearHistory}>
              清空
            </button>
          </div>
          {history.length === 0 ? (
            <div className="empty-state">暂无分析记录。</div>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <button
                  type="button"
                  className="history-item"
                  key={`${item.prUrl}-${item.analyzedAt}`}
                  onClick={() => restoreHistoryItem(item)}
                  aria-label={`${item.repo} #${item.number} ${item.title} ${riskLabel(item.riskLevel)}`}
                >
                  <span className="history-repo">{item.repo} #{item.number}</span>
                  <span className="history-title">{item.title}</span>
                  <span className={`risk-badge risk-badge--${item.riskLevel}`}>{riskLabel(item.riskLevel)}</span>
                </button>
              ))}
            </div>
          )}
        </aside>

        <main className="main-panel">
          <section className="input-panel" aria-labelledby="analyze-heading">
            <h2 id="analyze-heading">分析 Pull Request</h2>
            <form className="pr-form" onSubmit={handleSubmit}>
              <label htmlFor="pr-url">GitHub PR URL</label>
              <div className="input-row">
                <input
                  id="pr-url"
                  name="prUrl"
                  type="url"
                  value={prUrl}
                  onChange={(event) => setPrUrl(event.target.value)}
                  placeholder="https://github.com/owner/repo/pull/123"
                  disabled={viewState === "loading"}
                />
                <button type="submit" disabled={viewState === "loading"}>
                  {viewState === "loading" ? "分析中" : "开始分析"}
                </button>
              </div>
            </form>
          </section>

          <section className="result-panel" aria-label="评审结果">
            {viewState === "idle" && (
              <div className="status-row">
                <span className="risk-badge">待分析</span>
                <span>等待输入 Pull Request URL。</span>
              </div>
            )}

            {viewState === "loading" && (
              <div className="status-row">
                <span className="risk-badge risk-badge--loading">分析中</span>
                <span>正在分析 Pull Request...</span>
              </div>
            )}

            {viewState === "error" && (
              <div className="error-box" role="alert">
                <div className="status-row">
                  <span className="risk-badge risk-badge--high">错误</span>
                  <span>分析请求失败。</span>
                </div>
                <p>{errorMessage}</p>
              </div>
            )}

            {viewState === "success" && result && (
              <ResultSummary result={result} copyStatus={copyStatus} onCopyMarkdown={handleCopyMarkdown} />
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

function ResultSummary({
  result,
  copyStatus,
  onCopyMarkdown,
}: {
  result: AnalyzePrResponse;
  copyStatus: string;
  onCopyMarkdown: (markdownReview: string) => void;
}) {
  return (
    <div className="result-summary">
      <div className="result-title-row">
        <div>
          <p className="eyebrow">{result.pr.owner}/{result.pr.repo} #{result.pr.number}</p>
          <h2>{result.pr.title}</h2>
        </div>
        <span className={`risk-badge risk-badge--${result.analysis.riskLevel}`}>
          {riskLabel(result.analysis.riskLevel)}
        </span>
      </div>

      <div className="meta-grid">
        <span>AI Provider：{result.meta.provider}</span>
        <span>{result.pr.changedFiles} 个文件</span>
        <span>+{result.pr.additions} / -{result.pr.deletions}</span>
        <span>{result.meta.durationMs} ms</span>
      </div>

      {result.meta.warnings.length > 0 && (
        <div className="warning-list" aria-label="分析警告">
          {result.meta.warnings.map((warning) => (
            <div className="warning-item" key={`${warning.code}-${warning.message}`}>
              <strong>{warningLabel(warning.code)}</strong>
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      )}

      <div className="summary-block">
        <h3>总结</h3>
        <p>{result.analysis.summary}</p>
      </div>

      <section className="detail-section" aria-labelledby="file-summaries-heading">
        <h3 id="file-summaries-heading">变更文件</h3>
        <div className="detail-list">
          {result.analysis.fileSummaries.map((file) => (
            <article className="detail-item" key={file.file}>
              <div className="detail-item-heading">
                <strong>{file.file}</strong>
                <span>{fileStatusLabel(file.status)} +{file.additions} / -{file.deletions}</span>
              </div>
              <p>{file.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="detail-section" aria-labelledby="risks-heading">
        <h3 id="risks-heading">可能风险</h3>
        {result.analysis.risks.length === 0 ? (
          <p className="muted-text">本次分析未返回可能风险。</p>
        ) : (
          <div className="detail-list">
            {result.analysis.risks.map((risk) => (
              <article className="detail-item" key={risk.id}>
                <div className="detail-item-heading">
                  <strong>{risk.title}</strong>
                  <span className={`risk-badge risk-badge--${risk.severity}`}>{riskLabel(risk.severity)}</span>
                </div>
                {risk.file && <p className="muted-text">{risk.file}</p>}
                <p>{risk.description}</p>
                <p>建议：{risk.suggestion}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="detail-section" aria-labelledby="suggestions-heading">
        <h3 id="suggestions-heading">评审建议</h3>
        {result.analysis.suggestions.length === 0 ? (
          <p className="muted-text">暂无额外建议。</p>
        ) : (
          <ul className="suggestion-list">
            {result.analysis.suggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="detail-section" aria-labelledby="markdown-heading">
        <div className="section-heading-row">
          <h3 id="markdown-heading">Markdown Review</h3>
          <button type="button" className="ghost-button" onClick={() => onCopyMarkdown(result.analysis.markdownReview)}>
            复制 Markdown
          </button>
        </div>
        {copyStatus && <p className="copy-status">{copyStatus}</p>}
        <pre className="markdown-preview">{result.analysis.markdownReview}</pre>
      </section>
    </div>
  );
}

function riskLabel(level: AnalyzePrResponse["analysis"]["riskLevel"]) {
  const labels: Record<AnalyzePrResponse["analysis"]["riskLevel"], string> = {
    low: "低风险",
    medium: "中风险",
    high: "高风险",
  };
  return labels[level];
}

function fileStatusLabel(status: string) {
  const labels: Record<string, string> = {
    added: "新增",
    modified: "修改",
    removed: "删除",
    renamed: "重命名",
    changed: "变更",
  };
  return labels[status] ?? status;
}

function warningLabel(code: string) {
  const labels: Record<string, string> = {
    MOCK_MODE: "Mock 模式",
    PATCH_TRUNCATED: "Diff 已截断",
    AI_TIMEOUT: "AI 超时",
    AI_PROVIDER_ERROR: "AI Provider 警告",
    AI_INVALID_JSON: "AI 响应警告",
  };
  return labels[code] ?? code;
}

export default App;
