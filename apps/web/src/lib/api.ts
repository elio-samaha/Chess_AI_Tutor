import type { AnalysisJob, GameDetail, GameSummary, MoveAnalysis, QuestionAnswer } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listGames(): Promise<GameSummary[]> {
  return request<GameSummary[]>("/games");
}

export function getGame(gameId: string): Promise<GameDetail> {
  return request<GameDetail>(`/games/${gameId}`);
}

export function getMove(gameId: string, ply: number): Promise<MoveAnalysis> {
  return request<MoveAnalysis>(`/games/${gameId}/moves/${ply}`);
}

export function importPgn(payload: { pgn: string; title?: string }): Promise<GameDetail> {
  return request<GameDetail>("/imports/pgn", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function importChessComArchive(payload: {
  username: string;
  from_month: string;
  to_month: string;
}): Promise<GameSummary[]> {
  return request<GameSummary[]>("/imports/chesscom/archive", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runAnalysis(payload: { game_id: string; mode: "quick" | "deep" }): Promise<AnalysisJob> {
  return request<AnalysisJob>("/analyses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function askQuestion(
  gameId: string,
  payload: { question: string; ply?: number; candidate_move?: string },
): Promise<QuestionAnswer> {
  return request<QuestionAnswer>(`/games/${gameId}/questions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
