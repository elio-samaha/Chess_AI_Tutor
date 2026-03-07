from __future__ import annotations

from math import exp
from typing import List, Tuple

from .models import MoveClassification


CLASSIFICATION_THRESHOLDS: List[Tuple[MoveClassification, int]] = [
    ("best", 15),
    ("excellent", 30),
    ("good", 60),
    ("inaccuracy", 110),
    ("mistake", 250),
]


def classify_move(
    cp_loss: int,
    is_book: bool = False,
    is_forced: bool = False,
    mate_swing: bool = False,
) -> MoveClassification:
    if is_book:
        return "book"
    if is_forced:
        return "forced"
    if mate_swing or cp_loss > 250:
        return "blunder"
    for label, threshold in CLASSIFICATION_THRESHOLDS:
        if cp_loss <= threshold:
            return label
    return "blunder"


def win_probability_from_cp(cp: int) -> float:
    return 100.0 / (1.0 + exp(-cp / 180.0))


def mover_win_probability_loss(best_eval: int, played_eval: int, color: str) -> float:
    best_white = win_probability_from_cp(best_eval)
    played_white = win_probability_from_cp(played_eval)
    if color == "white":
        return max(0.0, round(best_white - played_white, 2))
    return max(0.0, round((100.0 - best_white) - (100.0 - played_white), 2))
