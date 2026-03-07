from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import io
import shutil
import uuid
from typing import List, Optional, Tuple

import chess
import chess.engine
import chess.pgn

from .classification import classify_move, mover_win_probability_loss
from .models import EngineSuggestion, Explanation, GameDetail, MoveAnalysis, MoveSummary


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass
class ParsedGame:
    game_id: str
    title: str
    white: str
    black: str
    result: str
    pgn: str
    source: str
    site_game_id: Optional[str] = None
    source_url: Optional[str] = None


def parse_pgn(pgn_text: str) -> chess.pgn.Game:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("PGN could not be parsed")
    return game


def sanitize_title(white: str, black: str, result: str, fallback: Optional[str] = None) -> str:
    if fallback:
        return fallback
    return "%s vs %s (%s)" % (white, black, result)


def build_game_detail(parsed: ParsedGame, moves: List[MoveAnalysis], mode: str) -> GameDetail:
    white_losses = [move.win_prob_loss for move in moves if move.color == "white"]
    black_losses = [move.win_prob_loss for move in moves if move.color == "black"]
    white_accuracy = max(0.0, round(100.0 - (sum(white_losses) / max(1, len(white_losses))), 2))
    black_accuracy = max(0.0, round(100.0 - (sum(black_losses) / max(1, len(black_losses))), 2))
    return GameDetail(
        id=parsed.game_id,
        source=parsed.source,
        title=parsed.title,
        white=parsed.white,
        black=parsed.black,
        result=parsed.result,
        move_count=len(moves),
        pgn=parsed.pgn,
        site_game_id=parsed.site_game_id,
        source_url=parsed.source_url,
        analysis_mode=mode,
        accuracy_white=white_accuracy,
        accuracy_black=black_accuracy,
        created_at=datetime.now(tz=timezone.utc),
        moves=[
            MoveSummary(
                ply=move.ply,
                fullmove_number=move.fullmove_number,
                color=move.color,
                san=move.san,
                classification=move.classification,
                cp_loss=move.cp_loss,
            )
            for move in moves
        ],
    )


class EngineProvider:
    def analyze(self, board: chess.Board, top_n: int, depth: int) -> List[EngineSuggestion]:
        raise NotImplementedError

    def evaluate_move(self, board: chess.Board, move: chess.Move, depth: int) -> EngineSuggestion:
        raise NotImplementedError


class HeuristicEngineProvider(EngineProvider):
    def analyze(self, board: chess.Board, top_n: int, depth: int) -> List[EngineSuggestion]:
        suggestions = [self.evaluate_move(board, move, depth) for move in board.legal_moves]
        suggestions.sort(key=lambda item: item.evaluation_cp, reverse=board.turn == chess.WHITE)
        return suggestions[:top_n]

    def evaluate_move(self, board: chess.Board, move: chess.Move, depth: int) -> EngineSuggestion:
        clone = board.copy()
        san = clone.san(move)
        clone.push(move)
        evaluation = material_score(clone) + activity_bonus(clone)
        return EngineSuggestion(move_uci=move.uci(), move_san=san, evaluation_cp=evaluation, pv=[san])


class StockfishEngineProvider(EngineProvider):
    def __init__(self, stockfish_path: str) -> None:
        self.stockfish_path = stockfish_path

    def analyze(self, board: chess.Board, top_n: int, depth: int) -> List[EngineSuggestion]:
        with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
            infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=top_n)
        suggestions = [self._info_to_suggestion(board, info) for info in infos if info.get("pv")]
        suggestions.sort(key=lambda item: item.evaluation_cp, reverse=board.turn == chess.WHITE)
        return suggestions

    def evaluate_move(self, board: chess.Board, move: chess.Move, depth: int) -> EngineSuggestion:
        clone = board.copy()
        san = clone.san(move)
        clone.push(move)
        with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
            info = engine.analyse(clone, chess.engine.Limit(depth=depth))
        score = info["score"].white()
        return EngineSuggestion(
            move_uci=move.uci(),
            move_san=san,
            evaluation_cp=score_to_cp(score),
            mate=score.mate(),
            pv=pv_to_san(clone, info.get("pv", [])),
        )

    def _info_to_suggestion(self, board: chess.Board, info: chess.engine.InfoDict) -> EngineSuggestion:
        clone = board.copy()
        move = info["pv"][0]
        san = clone.san(move)
        score = info["score"].white()
        return EngineSuggestion(
            move_uci=move.uci(),
            move_san=san,
            evaluation_cp=score_to_cp(score),
            mate=score.mate(),
            pv=pv_to_san(board, info.get("pv", [])),
        )


def get_engine_provider(stockfish_path: Optional[str]) -> EngineProvider:
    if stockfish_path and shutil.which(stockfish_path):
        return StockfishEngineProvider(stockfish_path)
    return HeuristicEngineProvider()


def score_to_cp(score: chess.engine.Score) -> int:
    cp = score.score(mate_score=100000)
    return 0 if cp is None else int(cp)


def material_score(board: chess.Board) -> int:
    total = 0
    for piece_type, value in PIECE_VALUES.items():
        total += len(board.pieces(piece_type, chess.WHITE)) * value
        total -= len(board.pieces(piece_type, chess.BLACK)) * value
    return total


def activity_bonus(board: chess.Board) -> int:
    mobility = len(list(board.legal_moves))
    bonus = mobility * 2
    return bonus if board.turn == chess.WHITE else -bonus


def pv_to_san(board: chess.Board, pv: List[chess.Move]) -> List[str]:
    clone = board.copy()
    output = []
    for move in pv:
        output.append(clone.san(move))
        clone.push(move)
    return output


def detect_motifs(board: chess.Board, move: chess.Move, best: EngineSuggestion, cp_loss: int) -> List[str]:
    motifs = []
    if board.is_capture(move):
        motifs.append("capture")
    if board.gives_check(move):
        motifs.append("check")
    if board.is_castling(move):
        motifs.append("castling")
    if cp_loss > 110:
        motifs.append("tactical oversight")
    from_square = chess.square_name(move.from_square)
    to_square = chess.square_name(move.to_square)
    if from_square[1] == "2" and to_square[1] == "4":
        motifs.append("space gain")
    if move.promotion:
        motifs.append("promotion")
    if best.move_san in {"O-O", "O-O-O"} and not board.is_castling(move):
        motifs.append("missed king safety")
    return motifs or ["quiet move"]


def explanation_from_facts(
    san: str,
    classification: str,
    cp_loss: int,
    best_move: str,
    eval_before: int,
    eval_after: int,
    motifs: List[str],
) -> Explanation:
    direction = "improved" if eval_after >= eval_before else "worsened"
    motif_text = ", ".join(motifs[:3])
    return Explanation(
        summary="%s is classified as %s." % (san, classification),
        why_good_or_bad=(
            "It changed the position by %s centipawns relative to the best move. The main themes are %s."
            % (cp_loss, motif_text)
        ),
        what_changed=(
            "The evaluation %s from %.2f to %.2f. That reflects the new balance of material, safety, and activity."
            % (direction, eval_before / 100.0, eval_after / 100.0)
        ),
        best_alternative="The engine preferred %s in this position." % best_move,
        practical_lesson=(
            "Before playing, compare forcing moves, king safety, and loose pieces. "
            "That usually explains the largest swings."
        ),
    )


class AnalysisService:
    def __init__(self, stockfish_path: Optional[str] = None) -> None:
        self.engine = get_engine_provider(stockfish_path)

    def parse_import(
        self,
        pgn: str,
        source: str,
        title: Optional[str] = None,
        site_game_id: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> ParsedGame:
        game = parse_pgn(pgn)
        white = game.headers.get("White", "White")
        black = game.headers.get("Black", "Black")
        result = game.headers.get("Result", "*")
        return ParsedGame(
            game_id=str(uuid.uuid4()),
            title=sanitize_title(white, black, result, title),
            white=white,
            black=black,
            result=result,
            pgn=pgn,
            source=source,
            site_game_id=site_game_id,
            source_url=source_url,
        )

    def analyze_pgn(self, parsed: ParsedGame, mode: str) -> Tuple[GameDetail, List[MoveAnalysis]]:
        game = parse_pgn(parsed.pgn)
        board = game.board()
        analyses = []
        depth = 10 if mode == "quick" else 14
        for ply, move in enumerate(game.mainline_moves(), start=1):
            fen_before = board.fen()
            color = "white" if board.turn == chess.WHITE else "black"
            fullmove_number = board.fullmove_number
            san = board.san(move)
            top = self.engine.analyze(board, 3, depth)
            played = next((item for item in top if item.move_uci == move.uci()), None)
            if played is None:
                played = self.engine.evaluate_move(board, move, depth)
                top.append(played)
            top.sort(key=lambda item: item.evaluation_cp, reverse=board.turn == chess.WHITE)
            best = top[0]
            orientation = 1 if color == "white" else -1
            cp_loss = max(0, int((best.evaluation_cp - played.evaluation_cp) * orientation))
            motifs = detect_motifs(board, move, best, cp_loss)
            classification = classify_move(
                cp_loss,
                is_book=ply <= 8 and cp_loss <= 15,
                is_forced=board.legal_moves.count() == 1,
                mate_swing=best.mate is not None and played.mate is None,
            )
            eval_before = analyses[-1].eval_after if analyses else 0
            board.push(move)
            fen_after = board.fen()
            eval_after = played.evaluation_cp
            win_prob_loss = mover_win_probability_loss(best.evaluation_cp, played.evaluation_cp, color)
            analyses.append(
                MoveAnalysis(
                    ply=ply,
                    fullmove_number=fullmove_number,
                    color=color,
                    san=san,
                    fen_before=fen_before,
                    fen_after=fen_after,
                    classification=classification,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    cp_loss=cp_loss,
                    win_prob_loss=win_prob_loss,
                    best_move=best.move_san,
                    best_move_uci=best.move_uci,
                    played_rank=rank_of_move(top, move.uci()),
                    pv=best.pv or [best.move_san],
                    motifs=motifs,
                    explanation=explanation_from_facts(
                        san,
                        classification,
                        cp_loss,
                        best.move_san,
                        eval_before,
                        eval_after,
                        motifs,
                    ),
                )
            )
        detail = build_game_detail(parsed, analyses, mode)
        return detail, analyses

    def analyze_candidate_move(self, fen: str, san: str, mode: str) -> MoveAnalysis:
        board = chess.Board(fen)
        move = board.parse_san(san)
        color = "white" if board.turn == chess.WHITE else "black"
        fullmove_number = board.fullmove_number
        depth = 10 if mode == "quick" else 14
        top = self.engine.analyze(board, 3, depth)
        played = next((item for item in top if item.move_uci == move.uci()), None)
        if played is None:
            played = self.engine.evaluate_move(board, move, depth)
            top.append(played)
        top.sort(key=lambda item: item.evaluation_cp, reverse=board.turn == chess.WHITE)
        best = top[0]
        orientation = 1 if color == "white" else -1
        cp_loss = max(0, int((best.evaluation_cp - played.evaluation_cp) * orientation))
        motifs = detect_motifs(board, move, best, cp_loss)
        eval_before = 0
        board.push(move)
        classification = classify_move(cp_loss)
        return MoveAnalysis(
            ply=1,
            fullmove_number=fullmove_number,
            color=color,
            san=san,
            fen_before=fen,
            fen_after=board.fen(),
            classification=classification,
            eval_before=eval_before,
            eval_after=played.evaluation_cp,
            cp_loss=cp_loss,
            win_prob_loss=mover_win_probability_loss(best.evaluation_cp, played.evaluation_cp, color),
            best_move=best.move_san,
            best_move_uci=best.move_uci,
            played_rank=rank_of_move(top, move.uci()),
            pv=best.pv or [best.move_san],
            motifs=motifs,
            explanation=explanation_from_facts(
                san,
                classification,
                cp_loss,
                best.move_san,
                eval_before,
                played.evaluation_cp,
                motifs,
            ),
        )


def rank_of_move(top: List[EngineSuggestion], move_uci: str) -> int:
    for index, item in enumerate(top, start=1):
        if item.move_uci == move_uci:
            return index
    return len(top) + 1
