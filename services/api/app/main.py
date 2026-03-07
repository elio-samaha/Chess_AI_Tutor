from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis import AnalysisService
from .bots import BotService
from .chesscom import ChessComService
from .config import get_settings
from .llm import ExplanationService
from .models import (
    AnalysisJob,
    AnalysisRequest,
    ArchiveImportRequest,
    BotGameCreateRequest,
    BotGameMoveRequest,
    BotGameState,
    ExtensionImportRequest,
    GameDetail,
    GameSummary,
    ImportPgnRequest,
    MoveAnalysis,
    QuestionAnswer,
    QuestionRequest,
)
from .sample_data import ensure_sample_game
from .storage import Database


settings = get_settings()
database = Database(settings.database_path)
analysis_service = AnalysisService(settings.stockfish_path)
bot_service = BotService(analysis_service)
chesscom_service = ChessComService()
explanation_service = ExplanationService(
    analysis_service,
    base_url=settings.ollama_base_url,
    model=settings.ollama_model,
)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    database.initialize()
    ensure_sample_game(database, analysis_service)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/games", response_model=List[GameSummary])
def list_games() -> List[GameSummary]:
    return database.list_games()


@app.get("/games/{game_id}", response_model=GameDetail)
def get_game(game_id: str) -> GameDetail:
    game = database.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.get("/games/{game_id}/moves/{ply}", response_model=MoveAnalysis)
def get_move(game_id: str, ply: int) -> MoveAnalysis:
    move = database.get_move_analysis(game_id, ply)
    if move is None:
        raise HTTPException(status_code=404, detail="Move not found")
    return move


@app.post("/imports/pgn", response_model=GameDetail)
def import_pgn(request: ImportPgnRequest) -> GameDetail:
    parsed = analysis_service.parse_import(request.pgn, source="pgn", title=request.title)
    detail, analyses = analysis_service.analyze_pgn(parsed, mode="quick")
    database.save_game(detail)
    database.save_move_analyses(detail.id, analyses)
    stored = database.get_game(detail.id)
    if stored is None:
        raise HTTPException(status_code=500, detail="Failed to persist imported game")
    return stored


@app.post("/imports/chesscom/archive", response_model=List[GameSummary])
async def import_archives(request: ArchiveImportRequest) -> List[GameSummary]:
    try:
        archive_games = await chesscom_service.fetch_archives(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Chess.com import failed: %s" % exc)
    imported_ids = []
    for item in archive_games:
        pgn = item.get("pgn")
        if not pgn:
            continue
        parsed = analysis_service.parse_import(
            pgn,
            source="chesscom",
            title=item.get("url"),
            site_game_id=item.get("url"),
            source_url=item.get("url"),
        )
        detail, analyses = analysis_service.analyze_pgn(parsed, mode="quick")
        database.save_game(detail)
        database.save_move_analyses(detail.id, analyses)
        imported_ids.append(detail.id)
    return [game for game in database.list_games() if game.id in imported_ids]


@app.post("/imports/extension/game", response_model=GameDetail)
def import_extension_game(request: ExtensionImportRequest) -> GameDetail:
    parsed = analysis_service.parse_import(
        request.pgn,
        source="extension",
        title="Chess.com %s" % request.mode,
        site_game_id=request.site_game_id,
        source_url=request.source_url,
    )
    detail, analyses = analysis_service.analyze_pgn(parsed, mode="quick")
    detail.result = request.result
    database.save_game(detail)
    database.save_move_analyses(detail.id, analyses)
    stored = database.get_game(detail.id)
    if stored is None:
        raise HTTPException(status_code=500, detail="Failed to persist imported extension game")
    return stored


@app.post("/analyses", response_model=AnalysisJob)
def analyze_game(request: AnalysisRequest) -> AnalysisJob:
    game = database.get_game(request.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        game_id=request.game_id,
        mode=request.mode,
        status="running",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        message="Analyzing game",
    )
    database.save_job(job)
    parsed = analysis_service.parse_import(
        game.pgn,
        source=game.source,
        title=game.title,
        site_game_id=game.site_game_id,
        source_url=game.source_url,
    )
    parsed.game_id = game.id
    detail, analyses = analysis_service.analyze_pgn(parsed, mode=request.mode)
    detail.id = game.id
    detail.created_at = game.created_at
    database.save_game(detail)
    database.save_move_analyses(game.id, analyses)
    completed = job.model_copy(
        update={
            "status": "completed",
            "updated_at": datetime.now(tz=timezone.utc),
            "message": "%s analysis completed" % request.mode.title(),
        }
    )
    database.save_job(completed)
    return completed


@app.get("/analyses/{job_id}", response_model=AnalysisJob)
def get_analysis_job(job_id: str) -> AnalysisJob:
    job = database.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


@app.post("/games/{game_id}/questions", response_model=QuestionAnswer)
async def ask_question(game_id: str, request: QuestionRequest) -> QuestionAnswer:
    game = database.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    analyses = database.list_move_analyses(game_id)
    answer = await explanation_service.answer_question(
        game_id,
        request.question,
        analyses,
        ply=request.ply,
        candidate_move=request.candidate_move,
        mode=game.analysis_mode,
    )
    database.save_answer(answer)
    return answer


@app.post("/bot-games", response_model=BotGameState)
def create_bot_game(request: BotGameCreateRequest) -> BotGameState:
    game = bot_service.create_game(request.bot_elo, request.player_color)
    database.save_bot_game(game)
    return game


@app.post("/bot-games/{game_id}/moves", response_model=BotGameState)
def play_bot_move(game_id: str, request: BotGameMoveRequest) -> BotGameState:
    game = database.get_bot_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Bot game not found")
    updated = bot_service.apply_player_move(game, request.san)
    database.save_bot_game(updated)
    return updated
