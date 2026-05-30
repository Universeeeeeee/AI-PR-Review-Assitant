import { type FormEvent, useState } from "react";

import { AnalyzePrApiError, type AnalyzePrResponse, analyzePullRequest } from "./api";

type ViewState = "idle" | "loading" | "success" | "error";

function App() {
  const [prUrl, setPrUrl] = useState("");
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [result, setResult] = useState<AnalyzePrResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

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
    try {
      const response = await analyzePullRequest(trimmedUrl);
      setResult(response);
      setViewState("success");
    } catch (error) {
      setErrorMessage(error instanceof AnalyzePrApiError ? error.message : "分析请求失败，请稍后重试。");
      setViewState("error");
    }
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
            <button type="button" className="ghost-button">
              Clear
            </button>
          </div>
          <div className="empty-state">No analyses yet.</div>
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

            {viewState === "success" && result && <ResultSummary result={result} />}
          </section>
        </main>
      </div>
    </div>
  );
}

function ResultSummary({ result }: { result: AnalyzePrResponse }) {
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
