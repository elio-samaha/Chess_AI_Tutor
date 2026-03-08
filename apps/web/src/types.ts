export type MoveClassification =
  | "book"
  | "forced"
  | "best"
  | "excellent"
  | "good"
  | "inaccuracy"
  | "mistake"
  | "blunder";

export interface Explanation {
  summary: string;
  why_good_or_bad: string;
  what_changed: string;
  best_alternative: string;
  practical_lesson: string;
}

export interface MoveSummary {
  ply: number;
  fullmove_number: number;
  color: "white" | "black";
  san: string;
  classification: MoveClassification;
  cp_loss: number;
}

export interface MoveAnalysis extends MoveSummary {
  fen_before: string;
  fen_after: string;
  eval_before: number;
  eval_after: number;
  win_prob_loss: number;
  best_move: string;
  best_move_uci: string;
  played_rank: number;
  pv: string[];
  motifs: string[];
  explanation: Explanation;
}

export interface GameSummary {
  id: string;
  source: "sample" | "pgn" | "chesscom" | "extension" | "bot";
  title: string;
  white: string;
  black: string;
  result: string;
  move_count: number;
  created_at: string;
}

export interface GameDetail extends GameSummary {
  pgn: string;
  site_game_id?: string | null;
  source_url?: string | null;
  analysis_mode: "quick" | "deep";
  accuracy_white: number;
  accuracy_black: number;
  moves: MoveSummary[];
}

export interface AnalysisJob {
  id: string;
  game_id: string;
  mode: "quick" | "deep";
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  message: string;
}

export interface QuestionAnswer {
  game_id: string;
  question: string;
  answer: string;
  citations: number[];
  suggested_lines: string[];
}


export interface CoachingLayers {
  game_id: string;
  ply?: number | null;
  high_level: string;
  mid_level: string;
  move_level: string;
  engine_line: string[];
  grounding_note: string;
}
