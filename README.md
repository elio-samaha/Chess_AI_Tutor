# AI Chess Tutor

Local-first chess review software that imports Chess.com games, analyzes every move, and explains what changed in plain language.

## Monorepo Layout

- `apps/web`: React + TypeScript review interface.
- `apps/extension`: Chrome/Edge extension for Chess.com capture.
- `services/api`: FastAPI service for PGN import, analysis, Q&A, and bot play.
- `PROJECT_JOURNAL.md`: concise running status and architecture notes.

## Current Scope

The repository now contains the v1 scaffold:

- PGN import and seeded sample game support.
- Chess.com archive and extension import endpoints.
- Move analysis pipeline with transparent classification thresholds.
- Grounded explanation and Q&A fallback logic.
- Chess.com-style review UI scaffold.
- Browser extension scaffold that captures completed games and posts them to `localhost`.

## Local Setup

### Backend

1. Install Python 3.11+ and Stockfish.
2. Create a virtual environment.
3. Install dependencies:

```powershell
cd services/api
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

4. Configure environment variables:

```powershell
$env:STOCKFISH_PATH="C:\path\to\stockfish.exe"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen2.5:7b-instruct"
```

5. Run the API:

```powershell
uvicorn app.main:app --reload --app-dir services/api
```

### Web App

1. Install Node.js 20+.
2. Install dependencies and start Vite:

```powershell
cd apps/web
npm install
npm run dev
```

The UI expects the backend at `http://127.0.0.1:8000`.

### Browser Extension

1. Open `chrome://extensions`.
2. Enable Developer Mode.
3. Load unpacked extension from `apps/extension`.
4. With the API running locally, click the extension action on a completed Chess.com game page.

## Notes

- Live tutoring on Chess.com human games is intentionally out of scope.
- Bot play is implemented through API endpoints and service scaffolding, but the first polished UX is still the post-game review flow.
- If Ollama is not available, the backend falls back to deterministic explanations so the app remains usable.
