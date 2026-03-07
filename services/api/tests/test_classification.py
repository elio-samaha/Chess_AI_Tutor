from app.classification import classify_move, mover_win_probability_loss


def test_classify_book_move() -> None:
    assert classify_move(0, is_book=True) == "book"


def test_classify_blunder_threshold() -> None:
    assert classify_move(300) == "blunder"


def test_mover_loss_is_non_negative() -> None:
    assert mover_win_probability_loss(120, -50, "white") > 0
    assert mover_win_probability_loss(-120, 50, "black") > 0
