# AI Chess Tutor

Local-first chess review software that imports games, analyzes moves, and explains the game in plain language.

## What Is In This Repo

- `services/api`: FastAPI backend for PGN import, Chess.com archive import, move analysis, layered coaching, Q&A, and bot-game endpoints.
- `apps/web`: React + Vite review UI.
- `apps/extension`: unpacked Chrome/Edge extension that captures completed Chess.com games and posts them to the local API.
- `PROJECT_JOURNAL.md`: implementation notes and status log.

## What You Can Run

1. The full local app: backend + web UI.
2. The backend by itself, including Swagger docs at `http://127.0.0.1:8000/docs`.
3. The web app by itself, as long as the backend is already running.
4. The browser extension, which sends Chess.com games to the backend.
5. Backend-only bot-game endpoints. These exist today, but there is not a dedicated bot UI yet.
6. Backend tests, frontend tests, and a frontend production build.

## Prerequisites

- Python `3.8+`
- Node.js `20+`
- npm
- Stockfish if you want real engine-backed analysis
- Chromium/Chrome/Edge if you want to use the extension

Notes:

- The backend still runs without Stockfish, but it falls back to a heuristic evaluator.
- The backend still runs without LLM keys, but coaching/Q&A fall back to deterministic grounded text.
- Chess.com archive import needs internet access from the backend process.
- Run commands from the repository root unless a section says otherwise. That keeps the SQLite database at `data/chess_tutor.sqlite3`.
- The repo root is `/mnt/c/Users/User/Documents/Playground/Chess_AI_Tutor`.

### Path-Sensitive Setup Rule

The setup commands in this README assume your shell is at the repo root:

```bash
cd /mnt/c/Users/User/Documents/Playground/Chess_AI_Tutor
pwd
```

You should see:

```text
/mnt/c/Users/User/Documents/Playground/Chess_AI_Tutor
```

If your prompt ends in `/services/api`, do not run commands like `cp services/api/.env.example ...` or `python3 -m venv services/api/.venv` from there. Those are root-relative commands and will create the wrong paths.

### WSL Ubuntu Note

If you are running this repo from WSL Ubuntu:

- install `python3-venv` if `python3 -m venv` is missing
- install Linux Stockfish, not the Windows executable
- do not reuse a Windows-created `services/api/.venv`
- do not reuse a Windows-created `node_modules`

Recommended Ubuntu packages:

```bash
sudo apt update
sudo apt install -y python3-venv stockfish
```

If you previously ran this repo from Windows, remove the Windows-created environment artifacts and recreate them from WSL:

```bash
rm -rf services/api/.venv node_modules
```

If you accidentally ran the root-level venv command from inside `services/api`, you may also have created a nested path like `services/api/services/api/.venv`. Remove that accidental tree too before recreating the backend venv:

```bash
rm -rf services/api/services
```

## Fresh Setup From Scratch

### 1. Install backend dependencies

#### Bash

```bash
python3 -m venv services/api/.venv
source services/api/.venv/bin/activate
python -m pip install --upgrade pip
pip install -e './services/api[dev]'
```

#### PowerShell

```powershell
py -3 -m venv services/api/.venv
.\services\api\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e '.\services\api[dev]'
```

### 2. Install frontend dependencies

From the repo root:

```bash
npm install
```

This repo uses npm workspaces. Installing from the root is the intended path.

### 3. Create environment files

Create the backend env file:

#### Bash

```bash
cp services/api/.env.example services/api/.env
```

#### PowerShell

```powershell
Copy-Item services/api/.env.example services/api/.env
```

Create the frontend env file:

#### Bash

```bash
cp apps/web/.env.example apps/web/.env
```

#### PowerShell

```powershell
Copy-Item apps/web/.env.example apps/web/.env
```

Optional: if you prefer keeping only AI provider keys in a separate root file, you can also copy `AI.env.example` to `AI.env` and source it before starting the API.

### 4. Edit `services/api/.env`

At minimum, set:

```env
STOCKFISH_PATH=C:\path\to\stockfish.exe
```

Or on Ubuntu/WSL:

```env
STOCKFISH_PATH=/usr/games/stockfish
```

You can leave the LLM variables empty if you only want deterministic explanations.

The frontend env file can stay as:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Quick Start

Start the backend in one terminal and the web app in another.

### Terminal 1: backend

#### Bash

```bash
source services/api/.venv/bin/activate
python -m uvicorn --env-file services/api/.env app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir services/api
```

#### PowerShell

```powershell
.\services\api\.venv\Scripts\Activate.ps1
python -m uvicorn --env-file services/api/.env app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir services/api
```

### Terminal 2: web app

```bash
npm run dev:web
```

Then open:

- Web UI: `http://127.0.0.1:5173`
- API docs: `http://127.0.0.1:8000/docs`

On first backend startup the app creates `data/chess_tutor.sqlite3` and seeds a sample game, so the web app should have something to display immediately.

## Different Ways To Run The Project

### 1. Full app

Use the quick-start flow above.

This is the main polished path today:

- import PGN
- import Chess.com archives
- browse a game move by move
- run deep analysis on a selected game
- generate layered coaching
- ask grounded questions about the current game/move

### 2. Backend only

Run only the API if you want to drive it with Swagger, curl, Postman, or your own client:

#### Bash

```bash
source services/api/.venv/bin/activate
python -m uvicorn --env-file services/api/.env app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir services/api
```

#### PowerShell

```powershell
.\services\api\.venv\Scripts\Activate.ps1
python -m uvicorn --env-file services/api/.env app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir services/api
```

Useful endpoints:

- `GET /health`
- `GET /games`
- `GET /games/{game_id}`
- `GET /games/{game_id}/moves/{ply}`
- `POST /imports/pgn`
- `POST /imports/chesscom/archive`
- `POST /analyses`
- `POST /games/{game_id}/coaching`
- `POST /games/{game_id}/questions`
- `POST /bot-games`
- `POST /bot-games/{game_id}/moves`

### 3. Web app only

The frontend is not standalone. It requires the API to already be running.

Development server:

```bash
npm run dev:web
```

Production build:

```bash
npm run build:web
```

Preview the production build:

```bash
npm run preview:web -- --host 127.0.0.1 --port 4173
```

### 4. Browser extension

The extension is in `apps/extension`.

Important:

- It posts to `http://127.0.0.1:8000` and that URL is hardcoded.
- The backend must therefore be running on `127.0.0.1:8000`, not some other port.
- There is no separate build step for the extension right now.

How to use it:

1. Start the backend.
2. Open `chrome://extensions` or `edge://extensions`.
3. Enable Developer Mode.
4. Click `Load unpacked`.
5. Select `apps/extension`.
6. Open a completed Chess.com game or analysis page.
7. Click the extension action button.

If the backend is offline, the extension queues payloads in `chrome.storage.local` and retries later.

### 5. Bot-game API

Bot play exists at the API layer even though the main web UI is focused on post-game review.

Create a bot game:

```bash
curl -X POST http://127.0.0.1:8000/bot-games \
  -H "Content-Type: application/json" \
  -d '{"bot_elo":1200,"player_color":"white"}'
```

Play a move in SAN:

```bash
curl -X POST http://127.0.0.1:8000/bot-games/<game_id>/moves \
  -H "Content-Type: application/json" \
  -d '{"san":"e4"}'
```

The backend stores bot game state in SQLite just like the rest of the app.

### 6. Tests

Backend tests:

#### Bash

```bash
source services/api/.venv/bin/activate
python -m pytest services/api/tests
```

#### PowerShell

```powershell
.\services\api\.venv\Scripts\Activate.ps1
python -m pytest services/api/tests
```

Frontend tests:

```bash
npm --workspace apps/web run test
```

## Useful Root Commands

These are the shortcuts currently defined in the root `package.json`:

- `npm run dev:web`
- `npm run build:web`
- `npm run build`
- `npm run dev:api`
- `npm run test:api`
- `npm run test:web`
- `npm run preview:web`

Important note about `npm run dev:api` and `npm run test:api`:

- they assume your Python environment is already activated
- they do not automatically load `services/api/.env`

So the safest backend command is still the explicit `python -m uvicorn --env-file ...` command shown above.

## Environment Variables

### Backend

Recommended file: `services/api/.env`

Key variables:

- `STOCKFISH_PATH`: path to the Stockfish binary
- `API_HOST`: default API host in config
- `API_PORT`: default API port in config
- `CORS_ALLOW_ORIGINS`: comma-separated frontend origins
- `DATA_DIR`: folder for app data
- `DATABASE_PATH`: SQLite path
- `OLLAMA_BASE_URL`: optional local model endpoint
- `LLM_SUMMARY_PROVIDER`, `LLM_SUMMARY_MODEL`, `LLM_SUMMARY_API_KEY`
- `LLM_MOVE_PROVIDER`, `LLM_MOVE_MODEL`, `LLM_MOVE_API_KEY`
- `LLM_CHAT_PROVIDER`, `LLM_CHAT_MODEL`, `LLM_CHAT_API_KEY`

The backend does not load `.env` files automatically on import. Use `uvicorn --env-file services/api/.env ...` or export the variables in your shell before starting the API.

### Frontend

Recommended file: `apps/web/.env`

Key variable:

- `VITE_API_BASE_URL=http://127.0.0.1:8000`

## Troubleshooting

### The web app loads but requests fail

- Make sure the API is running at `http://127.0.0.1:8000`.
- Make sure `apps/web/.env` points to the same API URL.

### The extension does not import anything

- Make sure the API is on `127.0.0.1:8000`.
- Make sure you are on a completed Chess.com game or analysis page.
- If the extension badge shows queued state, bring the backend up and click again.

### Analysis looks weak or obviously non-engine

- `STOCKFISH_PATH` is missing or invalid.
- Without Stockfish, the backend falls back to a heuristic engine provider.

### Coaching/Q&A sounds template-driven

- LLM provider variables are missing, empty, or the provider is unavailable.
- The backend is designed to keep working with deterministic grounded text instead of failing hard.

### The database was created in the wrong place

- Start the backend from the repo root as documented.
- The default `data/` path is relative to the current working directory.
