# Chess AI Tutor

## Cursor Cloud specific instructions

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| **API** (FastAPI) | `STOCKFISH_PATH=/usr/games/stockfish uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir services/api` | 8000 | Uses Python venv at `services/api/.venv`; activate it first |
| **Web** (Vite + React) | `npm run dev:web` | 5173 | Requires `apps/web/.env` with `VITE_API_BASE_URL=http://127.0.0.1:8000` |

### Key caveats

- **Stockfish** is installed at `/usr/games/stockfish`. The `STOCKFISH_PATH` env var must be set when starting the API, otherwise analysis falls back to heuristics only.
- **Ollama is optional.** The LLM-based explanation refinement requires `OLLAMA_BASE_URL` and `OLLAMA_MODEL` env vars. Without them, the API uses deterministic template-based explanations (fully functional).
- **SQLite database** is created automatically at `data/chess_tutor.sqlite3` on first API startup. A sample game is seeded automatically.
- **Python venv** lives at `services/api/.venv`. Activate with `source services/api/.venv/bin/activate` before running pytest or uvicorn directly.
- The root `package.json` uses npm workspaces. Run `npm install` from the repo root to install frontend dependencies.
- The browser extension (`apps/extension/`) is a Manifest V3 Chrome extension loaded unpacked; it is not runnable in a headless cloud environment.

### Commands reference

See `README.md` for full setup. Key shortcuts:
- **Tests:** `source services/api/.venv/bin/activate && STOCKFISH_PATH=/usr/games/stockfish pytest services/api/tests -v`
- **Frontend tests:** `npm run test:web`
- **Build frontend:** `npm run build:web`
- **Dev servers:** start API and web in separate terminals (see table above)
- **Lint (TypeScript):** `npx --workspace apps/web tsc --noEmit`

### Gotchas

- The backend does **not** auto-load `.env` files. Either pass `--env-file services/api/.env` to uvicorn or export `STOCKFISH_PATH` directly in the shell.
- Deep analysis (`POST /analyses` with `mode: deep`) takes ~10 s per game because Stockfish evaluates every position at depth 20. Tests mock this, so they are fast.
- `npm run dev:api` and `npm run test:api` from `package.json` assume the venv is already activated in the current shell.
