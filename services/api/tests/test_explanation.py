from app.analysis import explanation_from_facts


def test_explanation_contains_best_alternative() -> None:
    explanation = explanation_from_facts(
        san="Nf3",
        classification="good",
        cp_loss=42,
        best_move="d4",
        eval_before=10,
        eval_after=32,
        motifs=["development", "space gain"],
    )
    assert "d4" in explanation.best_alternative
    assert "good" in explanation.summary
