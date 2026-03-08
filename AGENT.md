# AGENT.md

## Product

AI Chess Tutor is a local-first chess review stack. The backend imports PGNs or Chess.com games, analyzes each move with Stockfish or a heuristic fallback, stores results in SQLite, and exposes a FastAPI surface for the UI. The frontend is a React review board. The browser extension is a local capture bridge for Chess.com pages.

## Folder Map

- `apps/web`: Vite + React review UI. Imports games, lists moves, renders the board, runs deep analysis, and sends grounded Q&A requests.
- `apps/extension`: Manifest V3 browser extension. Pulls PGN from Chess.com pages and posts it to the local API.
- `services/api/app`: FastAPI application code, engine integration, explanation logic, Chess.com import service, bot play, config, and persistence.
- `services/api/tests`: Minimal unit tests for move classification and explanation templating.
- `data`: Runtime SQLite database. Not source code.
- `artifacts`: Screenshots and visual checkpoints. Not runtime code.
- `.tools`: Vendored local binaries for Node and Stockfish used during development on this machine.
- `hello_test`: Currently empty and not part of the product.

## Request Flow

1. A game enters through `/imports/pgn`, `/imports/chesscom/archive`, or `/imports/extension/game`.
2. `AnalysisService` parses the PGN and evaluates each move.
3. `Database` stores the game summary plus per-ply JSON payloads in SQLite.
4. The web app fetches `/games`, `/games/{id}`, and `/games/{id}/moves/{ply}` to drive review.
5. Q&A uses deterministic move facts first, then optionally asks an Ollama-compatible local LLM to rewrite the answer more naturally.

## Runtime Dependencies

- Required for strong analysis: Stockfish via `STOCKFISH_PATH`.
- Optional for natural-language refinement: an Ollama-compatible local model via `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.
- No remote API key is required by the current codebase.

## API Key Policy

- Today: no paid API keys are needed. Chess.com import uses the public Chess.com API, Stockfish is local, and the LLM hook targets local Ollama.
- If you switch to a hosted LLM provider later, you will need your own provider key and a new adapter in `services/api/app/llm.py`. Nothing in the current repo talks to OpenAI, Anthropic, or Gemini yet.

## Main Gaps

- Analysis jobs are synchronous even though the API models them as jobs. There is no background worker or queue yet.
- The extension and current UX are built for post-game review, not live tutoring.
- Test coverage is thin and does not exercise full API flows, browser extension capture, or deployed frontend builds.
- Persistence has no migrations. SQLite plus JSON blobs is fine for a prototype but weak for multi-user production.
- The extension still assumes a local API endpoint.

## Shipping Notes

- Reinstall Node dependencies on the target OS before building the frontend. The current workspace contains platform-specific artifacts from local development.
- Use `apps/web/.env.example` and `services/api/.env.example` as the env templates.
- `services/api/requirements.txt` exists for platforms that prefer `requirements.txt`, but `services/api/pyproject.toml` remains the source of truth.

## Recommended Next Work

- Add background job execution for deep analysis.
- Replace the hardcoded extension API target with a configurable option.
- Add API integration tests and one end-to-end frontend smoke test.
- Split engine truth from explanation generation more cleanly if you plan to support multiple LLM providers.
