from __future__ import annotations

import json
import re
from typing import List, Optional

import httpx

from .analysis import AnalysisService
from .models import CoachingLayers, MoveAnalysis, QuestionAnswer


class LlmRouter:
    def __init__(
        self,
        summary_provider: Optional[str],
        summary_model: Optional[str],
        summary_api_key: Optional[str],
        move_provider: Optional[str],
        move_model: Optional[str],
        move_api_key: Optional[str],
        chat_provider: Optional[str],
        chat_model: Optional[str],
        chat_api_key: Optional[str],
        ollama_base_url: Optional[str],
    ) -> None:
        self.summary_provider = summary_provider or "deterministic"
        self.summary_model = summary_model
        self.summary_api_key = summary_api_key
        self.move_provider = move_provider or "deterministic"
        self.move_model = move_model
        self.move_api_key = move_api_key
        self.chat_provider = chat_provider or "deterministic"
        self.chat_model = chat_model
        self.chat_api_key = chat_api_key
        self.ollama_base_url = ollama_base_url

    async def generate_summary(self, prompt: str) -> Optional[str]:
        return await self._generate(self.summary_provider, self.summary_model, self.summary_api_key, prompt)

    async def generate_move(self, prompt: str) -> Optional[str]:
        return await self._generate(self.move_provider, self.move_model, self.move_api_key, prompt)

    async def generate_chat(self, prompt: str) -> Optional[str]:
        return await self._generate(self.chat_provider, self.chat_model, self.chat_api_key, prompt)

    async def _generate(self, provider: str, model: Optional[str], api_key: Optional[str], prompt: str) -> Optional[str]:
        if provider == "deterministic" or not model:
            return None
        if provider == "ollama":
            if not self.ollama_base_url:
                return None
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    response = await client.post(
                        "%s/api/generate" % self.ollama_base_url.rstrip("/"),
                        json={"model": model, "prompt": prompt, "stream": False},
                    )
                    response.raise_for_status()
                return response.json().get("response")
            except Exception:
                return None
        if provider in {"openrouter", "groq", "gemini"}:
            return await self._generate_openai_compatible(provider, model, api_key, prompt)
        return None

    async def _generate_openai_compatible(
        self,
        provider: str,
        model: str,
        api_key: Optional[str],
        prompt: str,
    ) -> Optional[str]:
        if not api_key:
            return None
        base_url = {
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        }.get(provider)
        if not base_url:
            return None
        headers = {"Authorization": "Bearer %s" % api_key, "Content-Type": "application/json"}
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://ai-chess-tutor.local"
            headers["X-Title"] = "AI Chess Tutor"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a chess coach. Stay grounded in supplied engine facts only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(base_url, headers=headers, json=payload)
                response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return None
            return choices[0].get("message", {}).get("content")
        except Exception:
            return None


class ExplanationService:
    def __init__(self, analysis_service: AnalysisService, llm_router: LlmRouter) -> None:
        self.analysis_service = analysis_service
        self.llm_router = llm_router

    async def build_coaching_layers(self, game_id: str, analyses: List[MoveAnalysis], ply: Optional[int] = None) -> CoachingLayers:
        target = self._select_move("", analyses, ply)
        high_prompt = self._high_level_prompt(analyses)
        mid_prompt = self._mid_level_prompt(analyses)
        move_prompt = self._move_level_prompt(target)

        high_level = await self.llm_router.generate_summary(high_prompt) or self._fallback_high_level(analyses)
        mid_level = await self.llm_router.generate_summary(mid_prompt) or self._fallback_mid_level(analyses)
        move_level = await self.llm_router.generate_move(move_prompt) or self._fallback_move_level(target)

        return CoachingLayers(
            game_id=game_id,
            ply=target.ply if target else None,
            high_level=high_level.strip(),
            mid_level=mid_level.strip(),
            move_level=move_level.strip(),
            engine_line=(target.pv[:5] if target else []),
            grounding_note="Move-level explanation is generated from fen_before, san move, fen_after, cp loss, eval shift, best move and PV only.",
        )

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
        refined = await self.llm_router.generate_chat(
            "Question: %s\nGrounded draft: %s\nKnown line: %s" % (question, draft, " ".join(suggested_lines[:4]))
        )
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

    def _high_level_prompt(self, analyses: List[MoveAnalysis]) -> str:
        snapshot = [
            {
                "ply": m.ply,
                "san": m.san,
                "classification": m.classification,
                "cp_loss": m.cp_loss,
                "eval_after": m.eval_after,
            }
            for m in analyses
        ]
        return (
            "Provide a concise whole-game coaching summary with opening/middlegame/endgame themes and biggest lessons. "
            "Use only this engine-derived JSON.\n%s" % json.dumps(snapshot)
        )

    def _mid_level_prompt(self, analyses: List[MoveAnalysis]) -> str:
        sorted_moves = sorted(analyses, key=lambda item: item.cp_loss, reverse=True)[:5]
        snapshot = [
            {
                "ply": m.ply,
                "san": m.san,
                "cp_loss": m.cp_loss,
                "best_move": m.best_move,
                "classification": m.classification,
                "what_changed": m.explanation.what_changed,
            }
            for m in sorted_moves
        ]
        return "Explain the 3-5 most impactful moves and how they changed the game. Ground strictly in this JSON.\n%s" % json.dumps(snapshot)

    def _move_level_prompt(self, move: Optional[MoveAnalysis]) -> str:
        if move is None:
            return "No move selected."
        payload = {
            "fen_before": move.fen_before,
            "played_move": move.san,
            "fen_after": move.fen_after,
            "classification": move.classification,
            "cp_loss": move.cp_loss,
            "eval_before": move.eval_before,
            "eval_after": move.eval_after,
            "best_move": move.best_move,
            "pv": move.pv[:5],
        }
        return (
            "Explain this move in concrete terms and explain why the engine line is preferred. "
            "Do not use external context. Use only the payload below.\n%s" % json.dumps(payload)
        )

    def _fallback_high_level(self, analyses: List[MoveAnalysis]) -> str:
        if not analyses:
            return "No analyzed moves yet."
        opening = analyses[:12]
        middle = analyses[12:40]
        endgame = analyses[40:]
        def avg_cp(items: List[MoveAnalysis]) -> int:
            if not items:
                return 0
            return int(sum(item.cp_loss for item in items) / len(items))
        return (
            "Opening average centipawn loss: %s. Middlegame average: %s. Endgame average: %s. "
            "Your biggest losses came on plies %s."
            % (
                avg_cp(opening),
                avg_cp(middle),
                avg_cp(endgame),
                ", ".join(str(item.ply) for item in sorted(analyses, key=lambda m: m.cp_loss, reverse=True)[:3]),
            )
        )

    def _fallback_mid_level(self, analyses: List[MoveAnalysis]) -> str:
        swings = sorted(analyses, key=lambda item: item.cp_loss, reverse=True)[:4]
        if not swings:
            return "No move swings found yet."
        return " ".join(
            "Ply %s %s lost %scp vs best %s. %s"
            % (item.ply, item.san, item.cp_loss, item.best_move, item.explanation.what_changed)
            for item in swings
        )

    def _fallback_move_level(self, move: Optional[MoveAnalysis]) -> str:
        if move is None:
            return "Select a move to get concrete explanation."
        return (
            "At ply %s you played %s. Engine preferred %s. Evaluation moved from %.2f to %.2f and cp loss was %s. "
            "Principal variation: %s"
            % (
                move.ply,
                move.san,
                move.best_move,
                move.eval_before / 100.0,
                move.eval_after / 100.0,
                move.cp_loss,
                " ".join(move.pv[:5]),
            )
        )
