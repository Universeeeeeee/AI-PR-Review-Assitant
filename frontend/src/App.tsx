function App() {
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
            <form className="pr-form">
              <label htmlFor="pr-url">GitHub PR URL</label>
              <div className="input-row">
                <input
                  id="pr-url"
                  name="prUrl"
                  type="url"
                  placeholder="https://github.com/owner/repo/pull/123"
                />
                <button type="submit">Analyze</button>
              </div>
            </form>
          </section>

          <section className="result-panel" aria-label="Review result">
            <div className="status-row">
              <span className="risk-badge">Pending</span>
              <span>Waiting for a Pull Request URL.</span>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
