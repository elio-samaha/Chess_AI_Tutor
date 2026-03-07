# Project Journal

## Goal

- Build a local-first AI chess tutor that imports Chess.com games, explains every move, and supports grounded Q&A and bot training.

## Current Status

- Monorepo scaffold created for `apps/web`, `apps/extension`, and `services/api`.
- Backend API runs locally in a workspace virtualenv on Python 3.8 after a compatibility pass.
- Stockfish was downloaded into `.tools/stockfish` and verified through the API for real move analysis.
- Portable Node.js was downloaded into `.tools/node`, frontend dependencies were installed, and the web app builds successfully when run outside the sandbox.
- Local CORS/frontend request handling was fixed so the web app can call the API without forced preflights on simple GETs.
- A real user PGN was imported and analyzed locally.

## Architecture

- `services/api` owns the domain model, SQLite persistence, heuristic/Stockfish analysis adapters, explanation generation, and public API.
- `apps/web` renders game review and drives imports, analysis jobs, move navigation, and Q&A.
- `apps/extension` captures game metadata/PGN from Chess.com and posts it to `http://127.0.0.1:8000/imports/extension/game`.

## Key Decisions

- Use transparent move labels and accuracy heuristics rather than claiming parity with Chess.com’s proprietary review formula.
- Keep live engine help off Chess.com human games to respect fair-play constraints.
- Use deterministic explanation fallback whenever local LLM inference is not available.
- Support the current machine by keeping the backend Python-compatible with 3.8 instead of requiring a fresh Python install first.
- Let Stockfish own chess truth; use the LLM only to explain engine-grounded facts.

## Commands

- Backend venv: `services/api/.venv`
- Backend run: `services/api/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir services/api`
- Backend tests: `services/api/.venv/Scripts/python.exe -m pytest`
- Frontend install: `apps/web` with `.tools/node/node-v24.13.1-win-x64/npm.cmd install`
- Frontend build: `.tools/node/node-v24.13.1-win-x64/npm.cmd run build`
- Simple frontend serve: `C:\python\python.exe -m http.server 4173 --bind 127.0.0.1` from `apps/web/dist`
- Optional frontend dev server: `.tools/node/node-v24.13.1-win-x64/npm.cmd run dev`

## Known Issues

- The sample explanations are still template-driven unless an Ollama-compatible model is configured.
- The Chess.com DOM capture is intentionally conservative and may need hardening against page structure changes.
- Stockfish-backed analysis and Vite build steps need elevated execution in this environment because the sandbox blocks subprocess spawning.
- Headless screenshot capture of the live app is flaky in this environment even when the frontend itself builds and serves.

## Verification

- `pytest` passes in `services/api`.
- Sample game import, move fetch, Q&A, and bot endpoints were exercised through `fastapi.testclient`.
- Stockfish-backed deep analysis was verified on the sample game.
- A real user game (`king_collector_12 vs LISHENGA`, played on March 6, 2026) was analyzed with Stockfish.
- Frontend production build completes successfully when run outside the sandbox.

## User Game Notes

- White biggest issues in the quick full-game pass: `11.Bb3`, `27.Nxc6+`, `87.c4+`, `83.Kc4`, `55.g3`.
- Black biggest issues in the quick full-game pass: `10...Na5`, `48...Qa5`, `36...Ne7`, `66...Rb4`, `12...d5`.
- Quick-pass accuracy estimate: White `96.00`, Black `95.83`.

## Next Steps

- Add a local LLM runner path for stronger natural-language explanations.
- Improve move explanations by combining deep analysis only on critical plies with cached quick analysis elsewhere.
- Harden the frontend review workflow and extension capture against real Chess.com usage.
