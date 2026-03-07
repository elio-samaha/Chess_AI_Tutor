from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import sqlite3
from typing import Iterator, List, Optional

from .models import AnalysisJob, BotGameState, GameDetail, GameSummary, MoveAnalysis, MoveSummary, QuestionAnswer


class Database:
    def __init__(self, path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    white_player TEXT NOT NULL,
                    black_player TEXT NOT NULL,
                    result TEXT NOT NULL,
                    move_count INTEGER NOT NULL,
                    pgn TEXT NOT NULL,
                    site_game_id TEXT,
                    source_url TEXT,
                    analysis_mode TEXT NOT NULL,
                    accuracy_white REAL NOT NULL,
                    accuracy_black REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS move_analyses (
                    game_id TEXT NOT NULL,
                    ply INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (game_id, ply)
                );
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS qa_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bot_games (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                """
            )

    def save_game(self, game: GameDetail) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO games (
                    id, source, title, white_player, black_player, result, move_count,
                    pgn, site_game_id, source_url, analysis_mode, accuracy_white,
                    accuracy_black, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game.id,
                    game.source,
                    game.title,
                    game.white,
                    game.black,
                    game.result,
                    game.move_count,
                    game.pgn,
                    game.site_game_id,
                    game.source_url,
                    game.analysis_mode,
                    game.accuracy_white,
                    game.accuracy_black,
                    game.created_at.isoformat(),
                ),
            )

    def save_move_analyses(self, game_id: str, analyses: List[MoveAnalysis]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM move_analyses WHERE game_id = ?", (game_id,))
            connection.executemany(
                "INSERT INTO move_analyses (game_id, ply, payload) VALUES (?, ?, ?)",
                [(game_id, item.ply, item.model_dump_json()) for item in analyses],
            )

    def get_move_analysis(self, game_id: str, ply: int) -> Optional[MoveAnalysis]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM move_analyses WHERE game_id = ? AND ply = ?",
                (game_id, ply),
            ).fetchone()
        if row is None:
            return None
        return MoveAnalysis.model_validate_json(row["payload"])

    def list_move_analyses(self, game_id: str) -> List[MoveAnalysis]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM move_analyses WHERE game_id = ? ORDER BY ply ASC",
                (game_id,),
            ).fetchall()
        return [MoveAnalysis.model_validate_json(row["payload"]) for row in rows]

    def list_games(self) -> List[GameSummary]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, source, title, white_player, black_player, result, move_count, created_at
                FROM games
                ORDER BY datetime(created_at) DESC
                """
            ).fetchall()
        return [
            GameSummary(
                id=row["id"],
                source=row["source"],
                title=row["title"],
                white=row["white_player"],
                black=row["black_player"],
                result=row["result"],
                move_count=row["move_count"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def get_game(self, game_id: str) -> Optional[GameDetail]:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if row is None:
            return None
        analyses = self.list_move_analyses(game_id)
        return GameDetail(
            id=row["id"],
            source=row["source"],
            title=row["title"],
            white=row["white_player"],
            black=row["black_player"],
            result=row["result"],
            move_count=row["move_count"],
            pgn=row["pgn"],
            site_game_id=row["site_game_id"],
            source_url=row["source_url"],
            analysis_mode=row["analysis_mode"],
            accuracy_white=row["accuracy_white"],
            accuracy_black=row["accuracy_black"],
            created_at=datetime.fromisoformat(row["created_at"]),
            moves=[
                MoveSummary(
                    ply=item.ply,
                    fullmove_number=item.fullmove_number,
                    color=item.color,
                    san=item.san,
                    classification=item.classification,
                    cp_loss=item.cp_loss,
                )
                for item in analyses
            ],
        )

    def save_job(self, job: AnalysisJob) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analysis_jobs
                (id, game_id, mode, status, created_at, updated_at, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.game_id,
                    job.mode,
                    job.status,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.message,
                ),
            )

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM analysis_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return AnalysisJob(
            id=row["id"],
            game_id=row["game_id"],
            mode=row["mode"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            message=row["message"],
        )

    def save_answer(self, answer: QuestionAnswer) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO qa_history (game_id, question, answer_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    answer.game_id,
                    answer.question,
                    answer.model_dump_json(),
                    datetime.now(tz=timezone.utc).isoformat(),
                ),
            )

    def save_bot_game(self, game: BotGameState) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO bot_games (id, payload) VALUES (?, ?)",
                (game.id, game.model_dump_json()),
            )

    def get_bot_game(self, game_id: str) -> Optional[BotGameState]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM bot_games WHERE id = ?",
                (game_id,),
            ).fetchone()
        if row is None:
            return None
        return BotGameState.model_validate_json(row["payload"])
