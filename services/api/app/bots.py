from __future__ import annotations

import random
import uuid
from typing import Tuple

import chess

from .analysis import AnalysisService
from .models import BotGameState


class BotService:
    def __init__(self, analysis_service: AnalysisService) -> None:
        self.analysis_service = analysis_service

    def create_game(self, bot_elo: int, player_color: str) -> BotGameState:
        board = chess.Board()
        state = BotGameState(
            id=str(uuid.uuid4()),
            bot_elo=bot_elo,
            player_color=player_color,
            fen=board.fen(),
            moves=[],
            commentary=["Bot game created."],
        )
        if player_color == "black":
            move, comment = self._pick_bot_move(board, bot_elo)
            san = board.san(move)
            board.push(move)
            state.fen = board.fen()
            state.moves.append(san)
            state.commentary.append(comment)
        return state

    def apply_player_move(self, state: BotGameState, san: str) -> BotGameState:
        board = chess.Board(state.fen)
        player_move = board.parse_san(san)
        board.push(player_move)
        state.moves.append(san)
        state.commentary.append("You played %s. Review compares it to the engine line after the move." % san)
        if board.is_game_over():
            state.fen = board.fen()
            state.status = "completed"
            return state
        move, comment = self._pick_bot_move(board, state.bot_elo)
        bot_san = board.san(move)
        board.push(move)
        state.moves.append(bot_san)
        state.commentary.append(comment)
        state.fen = board.fen()
        state.status = "completed" if board.is_game_over() else "active"
        return state

    def _pick_bot_move(self, board: chess.Board, bot_elo: int) -> Tuple[chess.Move, str]:
        depth = 8 if bot_elo < 1400 else 10 if bot_elo < 1800 else 12
        suggestions = self.analysis_service.engine.analyze(board, 3, depth)
        if not suggestions:
            move = next(iter(board.legal_moves))
            return move, "The bot had only one legal move available."
        variance = 0 if bot_elo >= 2000 else 1 if bot_elo >= 1400 else 2
        index = min(len(suggestions) - 1, random.randint(0, variance))
        chosen = suggestions[index]
        comment = "Bot selected %s at target strength %s. The top line started with %s." % (
            chosen.move_san,
            bot_elo,
            " ".join(chosen.pv[:3]),
        )
        return chess.Move.from_uci(chosen.move_uci), comment
