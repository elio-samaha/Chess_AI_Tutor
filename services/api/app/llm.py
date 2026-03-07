from __future__ import annotations

import re
from typing import List, Optional

import httpx

from .analysis import AnalysisService
from .models import MoveAnalysis, QuestionAnswer


class ExplanationService:
    def __init__(self, analysis_service: AnalysisService, base_url: Optional[str], model: Optional[str]) -> None:
        self.analysis_service = analysis_service
        self.base_url = base_url
        self.model = model

    async def answer_question(
        self,
        game_id: str,
        question: str,
        analyses: List[MoveAnalysis],
        ply: Optional[int] = None,
        candidate_move: Optional[str] = None,
        mode: str = "deep",
    ) -> QuestionAnswer:
        target = self._select_move(question, analyses, ply)
        citations = []
        suggested_lines = []
        answer_parts = []
        if target is not None:
            citations.append(target.ply)
            suggested_lines.extend(target.pv[:4])
            answer_parts.append(
                "Move %s (%s) was classified as %s with %s centipawns of loss."
                % (target.ply, target.san, target.classification, target.cp_loss)
            )
            answer_parts.append(target.explanation.why_good_or_bad)
            answer_parts.append(target.explanation.what_changed)
        if candidate_move and target is not None:
            try:
                what_if = self.analysis_service.analyze_candidate_move(target.fen_before, candidate_move, mode)
                answer_parts.append(
                    "If you played %s instead, it would be %s with %s centipawns of loss."
                    % (candidate_move, what_if.classification, what_if.cp_loss)
                )
                suggested_lines.extend(what_if.pv[:4])
            except Exception:
                answer_parts.append("I could not validate the counterfactual move %s from that position." % candidate_move)
        if not answer_parts:
            answer_parts.append(
                "I need a selected move or a clearer reference to answer precisely. Try asking from a highlighted move in the review pane."
            )
        draft = " ".join(answer_parts)
        if self.base_url and self.model:
            refined = await self._refine_with_ollama(question, draft, suggested_lines)
            if refined:
                draft = refined
        return QuestionAnswer(
            game_id=game_id,
            question=question,
            answer=draft,
            citations=citations,
            suggested_lines=suggested_lines[:5],
        )

    def _select_move(self, question: str, analyses: List[MoveAnalysis], explicit_ply: Optional[int]) -> Optional[MoveAnalysis]:
        if explicit_ply is not None:
            for item in analyses:
                if item.ply == explicit_ply:
                    return item
            return None
        match = re.search(r"\b(\d+)\b", question)
        if match:
            fullmove = int(match.group(1))
            for item in analyses:
                if item.fullmove_number == fullmove:
                    return item
        return analyses[-1] if analyses else None

    async def _refine_with_ollama(self, question: str, draft: str, suggested_lines: List[str]) -> Optional[str]:
        prompt = (
            "Rewrite the answer as a grounded chess tutor. Do not invent engine lines or tactical claims.\n\n"
            "Question: %s\nDraft answer: %s\nKnown line: %s\n"
            % (question, draft, " ".join(suggested_lines[:4]))
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "%s/api/generate" % self.base_url.rstrip("/"),
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
        except Exception:
            return None
        data = response.json()
        return data.get("response")
