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
      setCopyStatus("Clipboard unavailable.");
      return;
    }
    await navigator.clipboard.writeText(markdownReview);
    setCopyStatus("Markdown copied.");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Developer Review Workbench</p>
          <h1>AI PR Review Assistant</h1>
        </div>
      </header>

      <div className="workbench">
        <aside className="sidebar" aria-label="Recent analyses">
          <div className="panel-heading">
            <h2>Recent Analyses</h2>
            <button type="button" className="ghost-button" onClick={handleClearHistory}>
              Clear
            </button>
          </div>
          {history.length === 0 ? (
            <div className="empty-state">No analyses yet.</div>
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
            <h2 id="analyze-heading">Analyze Pull Request</h2>
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
                  {viewState === "loading" ? "Analyzing" : "Analyze"}
                </button>
              </div>
            </form>
          </section>

          <section className="result-panel" aria-label="Review result">
            {viewState === "idle" && (
              <div className="status-row">
                <span className="risk-badge">Pending</span>
                <span>Waiting for a Pull Request URL.</span>
              </div>
            )}

            {viewState === "loading" && (
              <div className="status-row">
                <span className="risk-badge risk-badge--loading">Running</span>
                <span>Analyzing Pull Request...</span>
              </div>
            )}

            {viewState === "error" && (
              <div className="error-box" role="alert">
                <div className="status-row">
                  <span className="risk-badge risk-badge--high">Error</span>
                  <span>Review request failed.</span>
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
        <span>Provider: {result.meta.provider}</span>
        <span>{result.pr.changedFiles} files</span>
        <span>+{result.pr.additions} / -{result.pr.deletions}</span>
        <span>{result.meta.durationMs} ms</span>
      </div>

      {result.meta.warnings.length > 0 && (
        <div className="warning-list" aria-label="Analysis warnings">
          {result.meta.warnings.map((warning) => (
            <div className="warning-item" key={`${warning.code}-${warning.message}`}>
              <strong>{warningLabel(warning.code)}</strong>
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      )}

      <div className="summary-block">
        <h3>Summary</h3>
        <p>{result.analysis.summary}</p>
      </div>

      <section className="detail-section" aria-labelledby="file-summaries-heading">
        <h3 id="file-summaries-heading">Changed Files</h3>
        <div className="detail-list">
          {result.analysis.fileSummaries.map((file) => (
            <article className="detail-item" key={file.file}>
              <div className="detail-item-heading">
                <strong>{file.file}</strong>
                <span>{file.status} +{file.additions} / -{file.deletions}</span>
              </div>
              <p>{file.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="detail-section" aria-labelledby="risks-heading">
        <h3 id="risks-heading">Possible Risks</h3>
        {result.analysis.risks.length === 0 ? (
          <p className="muted-text">No possible risks were returned for this analysis.</p>
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
                <p>Suggestion: {risk.suggestion}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="detail-section" aria-labelledby="suggestions-heading">
        <h3 id="suggestions-heading">Review Suggestions</h3>
        {result.analysis.suggestions.length === 0 ? (
          <p className="muted-text">No additional suggestions were returned.</p>
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
            Copy Markdown
          </button>
        </div>
        {copyStatus && <p className="copy-status">{copyStatus}</p>}
        <pre className="markdown-preview">{result.analysis.markdownReview}</pre>
      </section>
    </div>
  );
}

function riskLabel(level: AnalyzePrResponse["analysis"]["riskLevel"]) {
  return `${level[0].toUpperCase()}${level.slice(1)} risk`;
}

function warningLabel(code: string) {
  const labels: Record<string, string> = {
    MOCK_MODE: "Mock mode",
    PATCH_TRUNCATED: "Diff truncated",
    AI_TIMEOUT: "AI timeout",
    AI_PROVIDER_ERROR: "AI provider warning",
    AI_INVALID_JSON: "AI response warning",
  };
  return labels[code] ?? code;
}

export default App;
