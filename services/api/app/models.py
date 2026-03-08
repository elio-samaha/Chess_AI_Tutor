from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


MoveClassification = Literal[
    "book",
    "forced",
    "best",
    "excellent",
    "good",
    "inaccuracy",
    "mistake",
    "blunder",
]

AnalysisMode = Literal["quick", "deep"]
SourceType = Literal["sample", "pgn", "chesscom", "extension", "bot"]


class Explanation(BaseModel):
    summary: str
    why_good_or_bad: str
    what_changed: str
    best_alternative: str
    practical_lesson: str


class EngineSuggestion(BaseModel):
    move_uci: str
    move_san: str
    evaluation_cp: int
    mate: Optional[int] = None
    pv: List[str] = Field(default_factory=list)


class MoveSummary(BaseModel):
    ply: int
    fullmove_number: int
    color: Literal["white", "black"]
    san: str
    classification: MoveClassification
    cp_loss: int


class MoveAnalysis(BaseModel):
    ply: int
    fullmove_number: int
    color: Literal["white", "black"]
    san: str
    fen_before: str
    fen_after: str
    classification: MoveClassification
    eval_before: int
    eval_after: int
    cp_loss: int
    win_prob_loss: float
    best_move: str
    best_move_uci: str
    played_rank: int
    pv: List[str]
    motifs: List[str]
    explanation: Explanation


class GameSummary(BaseModel):
    id: str
    source: SourceType
    title: str
    white: str
    black: str
    result: str
    move_count: int
    created_at: datetime


class GameDetail(GameSummary):
    pgn: str
    site_game_id: Optional[str] = None
    source_url: Optional[str] = None
    analysis_mode: AnalysisMode = "quick"
    accuracy_white: float = 0.0
    accuracy_black: float = 0.0
    moves: List[MoveSummary] = Field(default_factory=list)


class AnalysisJob(BaseModel):
    id: str
    game_id: str
    mode: AnalysisMode
    status: Literal["queued", "running", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    message: str = ""


class ImportPgnRequest(BaseModel):
    pgn: str
    title: Optional[str] = None


class ArchiveImportRequest(BaseModel):
    username: str
    from_month: str
    to_month: str


class ExtensionImportRequest(BaseModel):
    source_url: str
    site_game_id: str
    pgn: str
    result: str
    mode: str
    captured_at: datetime


class AnalysisRequest(BaseModel):
    game_id: str
    mode: AnalysisMode = "quick"


class QuestionRequest(BaseModel):
    question: str
    ply: Optional[int] = None
    candidate_move: Optional[str] = None


class QuestionAnswer(BaseModel):
    game_id: str
    question: str
    answer: str
    citations: List[int] = Field(default_factory=list)
    suggested_lines: List[str] = Field(default_factory=list)


class CoachingLayers(BaseModel):
    game_id: str
    ply: Optional[int] = None
    high_level: str
    mid_level: str
    move_level: str
    engine_line: List[str] = Field(default_factory=list)
    grounding_note: str


class BotGameCreateRequest(BaseModel):
    bot_elo: int = Field(ge=800, le=2200)
    player_color: Literal["white", "black"] = "white"


class BotGameMoveRequest(BaseModel):
    san: str


class BotGameState(BaseModel):
    id: str
    bot_elo: int
    player_color: Literal["white", "black"]
    fen: str
    moves: List[str] = Field(default_factory=list)
    status: Literal["active", "completed"] = "active"
    commentary: List[str] = Field(default_factory=list)
