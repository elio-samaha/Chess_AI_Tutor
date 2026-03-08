import asyncio

from app.analysis import AnalysisService
from app.llm import ExplanationService, LlmRouter


PGN = """[Event \"Rated Blitz game\"]
[Site \"https://chess.com/game/live/1\"]
[Date \"2024.01.01\"]
[Round \"-\"]
[White \"Alice\"]
[Black \"Bob\"]
[Result \"1-0\"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""


def test_coaching_layers_grounding_and_move_payload() -> None:
    analysis = AnalysisService(stockfish_path=None)
    parsed = analysis.parse_import(PGN, source="pgn")
    _, moves = analysis.analyze_pgn(parsed, mode="quick")
    service = ExplanationService(
        analysis,
        LlmRouter(None, None, None, None, None, None, None, None, None, None),
    )

    layered = asyncio.run(service.build_coaching_layers(parsed.game_id, moves, ply=2))

    assert layered.ply == 2
    assert "fen_before" not in layered.move_level
    assert layered.grounding_note.startswith("Move-level explanation")
    assert len(layered.engine_line) >= 1
