# Frontend

React + Vite + TypeScript frontend for AI PR Review Assistant.

The current frontend includes the workbench shell, PR URL submission, backend API integration, loading state, result summary, changed-file details, possible risk sections, review suggestions, Markdown Review copy, warning display, backend error display, and localStorage recent analyses.

Recent analyses are stored in the browser only. Clearing browser storage or using another browser will reset this history.

## Local Development

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

By default the app calls:

```text
http://localhost:8000/api/analyze-pr
```

Set `VITE_API_BASE_URL` in `frontend/.env` if the backend runs elsewhere:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Run tests:

```powershell
npm test
```

Build:

```powershell
npm run build
```
