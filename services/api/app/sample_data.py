from __future__ import annotations

from .analysis import AnalysisService
from .storage import Database


SAMPLE_PGN = """
[Event "Sample Training Game"]
[Site "Local"]
[Date "2026.03.06"]
[Round "-"]
[White "Student"]
[Black "CoachBot"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+ 7. Nc3 Nxe4
8. O-O Bxc3 9. bxc3 d5 10. Ba3 dxc4 11. Re1 f5 12. Nd2 Kf7 13. Nxe4 fxe4
14. Rxe4 Re8 15. Qh5+ Kg8 16. Rxe8+ Qxe8 17. Qxe8#
"""


def ensure_sample_game(db: Database, analysis_service: AnalysisService) -> None:
    if db.list_games():
        return
    parsed = analysis_service.parse_import(SAMPLE_PGN.strip(), source="sample", title="Sample Training Game")
    detail, analyses = analysis_service.analyze_pgn(parsed, mode="quick")
    db.save_game(detail)
    db.save_move_analyses(detail.id, analyses)
