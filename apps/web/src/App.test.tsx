import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CoachingLayers, GameDetail, GameSummary, MoveAnalysis } from "./types";

const apiMocks = vi.hoisted(() => ({
  askQuestion: vi.fn(),
  getCoachingLayers: vi.fn(),
  getGame: vi.fn(),
  getMove: vi.fn(),
  importChessComArchive: vi.fn(),
  importPgn: vi.fn(),
  listGames: vi.fn(),
  runAnalysis: vi.fn(),
}));

vi.mock("./lib/api", () => apiMocks);

import App from "./App";

interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
}

function createDeferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve;
    reject = nextReject;
  });

  return { promise, resolve, reject };
}

function makeGameSummary(id: string, title: string): GameSummary {
  return {
    id,
    source: "sample",
    title,
    white: `${title} White`,
    black: `${title} Black`,
    result: "1-0",
    move_count: 12,
    created_at: "2026-03-08T00:00:00Z",
  };
}

function makeGameDetail(id: string, title: string, plies: number[]): GameDetail {
  return {
    ...makeGameSummary(id, title),
    pgn: "1. e4 e5",
    site_game_id: null,
    source_url: null,
    analysis_mode: "quick",
    accuracy_white: 90,
    accuracy_black: 88,
    moves: plies.map((ply, index) => ({
      ply,
      fullmove_number: index + 1,
      color: index % 2 === 0 ? "white" : "black",
      san: `M${ply}`,
      classification: "good",
      cp_loss: 10,
    })),
  };
}

function makeMove(ply: number): MoveAnalysis {
  return {
    ply,
    fullmove_number: 1,
    color: "white",
    san: `M${ply}`,
    classification: "good",
    cp_loss: 10,
    fen_before: "8/8/8/8/8/8/8/8 w - - 0 1",
    fen_after: "8/8/8/8/8/8/8/8 w - - 0 1",
    eval_before: 0,
    eval_after: 20,
    win_prob_loss: 0.1,
    best_move: "e4",
    best_move_uci: "e2e4",
    played_rank: 1,
    pv: ["e4", "e5"],
    motifs: ["space"],
    explanation: {
      summary: `Summary ${ply}`,
      why_good_or_bad: "Why",
      what_changed: "Change",
      best_alternative: "Alternative",
      practical_lesson: "Lesson",
    },
  };
}

function makeCoaching(gameId: string, ply: number | undefined, label: string): CoachingLayers {
  return {
    game_id: gameId,
    ply: ply ?? null,
    high_level: `${label} high`,
    mid_level: `${label} mid`,
    move_level: `${label} move`,
    engine_line: ["e4", "e5"],
    grounding_note: `${label} grounding`,
  };
}

describe("App coaching requests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ignores stale coaching responses after switching games", async () => {
    const gameOne = makeGameDetail("game-1", "Game One", [1, 2]);
    const gameTwo = makeGameDetail("game-2", "Game Two", [9, 10]);
    const pendingGameTwoRequests: Array<{ ply: number | undefined; deferred: Deferred<CoachingLayers> }> = [];

    apiMocks.listGames.mockResolvedValue([
      makeGameSummary("game-1", "Game One"),
      makeGameSummary("game-2", "Game Two"),
    ]);
    apiMocks.getGame.mockImplementation(async (gameId: string) => {
      if (gameId === "game-1") {
        return gameOne;
      }

      return gameTwo;
    });
    apiMocks.getMove.mockImplementation(async (_gameId: string, ply: number) => makeMove(ply));
    apiMocks.getCoachingLayers.mockImplementation((gameId: string, ply?: number) => {
      if (gameId === "game-1") {
        return Promise.resolve(makeCoaching(gameId, ply, `coaching-${gameId}-${ply ?? "whole"}`));
      }

      const deferred = createDeferred<CoachingLayers>();
      pendingGameTwoRequests.push({ ply, deferred });
      return deferred.promise;
    });

    render(<App />);

    await screen.findByRole("heading", { name: "Game One" });
    await screen.findByText("coaching-game-1-1 move");

    fireEvent.click(screen.getByRole("button", { name: /Game Two/ }));

    await screen.findByRole("heading", { name: "Game Two" });
    await waitFor(() => expect(pendingGameTwoRequests.map((request) => request.ply).sort()).toEqual([1, 9]));

    const correctRequest = pendingGameTwoRequests.find((request) => request.ply === 9);
    const staleRequest = pendingGameTwoRequests.find((request) => request.ply === 1);

    expect(correctRequest).toBeDefined();
    expect(staleRequest).toBeDefined();

    correctRequest!.deferred.resolve(makeCoaching("game-2", 9, "coaching-game-2-9"));
    await screen.findByText("coaching-game-2-9 move");

    staleRequest!.deferred.resolve(makeCoaching("game-2", 1, "coaching-game-2-1"));

    await waitFor(() => {
      expect(screen.getByText("coaching-game-2-9 move")).toBeInTheDocument();
      expect(screen.queryByText("coaching-game-2-1 move")).not.toBeInTheDocument();
    });
  });
});
