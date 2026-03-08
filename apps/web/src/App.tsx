import { useEffect, useMemo, useState } from "react";

import Board from "./components/Board";
import ExplanationPanel from "./components/ExplanationPanel";
import CoachingPanel from "./components/CoachingPanel";
import GameList from "./components/GameList";
import MoveList from "./components/MoveList";
import QaPanel from "./components/QaPanel";
import { askQuestion, getCoachingLayers, getGame, getMove, importChessComArchive, importPgn, listGames, runAnalysis } from "./lib/api";
import type { CoachingLayers, GameDetail, GameSummary, MoveAnalysis, QuestionAnswer } from "./types";

const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

function clampEval(evalCp: number): number {
  return Math.max(0, Math.min(100, 50 + evalCp / 20));
}

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

export default function App() {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [selectedGame, setSelectedGame] = useState<GameDetail | null>(null);
  const [selectedPly, setSelectedPly] = useState<number | null>(null);
  const [selectedMove, setSelectedMove] = useState<MoveAnalysis | null>(null);
  const [status, setStatus] = useState("Loading games...");
  const [importTitle, setImportTitle] = useState("");
  const [importPgnText, setImportPgnText] = useState("");
  const [username, setUsername] = useState("");
  const [fromMonth, setFromMonth] = useState(currentMonth());
  const [toMonth, setToMonth] = useState(currentMonth());
  const [question, setQuestion] = useState("");
  const [candidateMove, setCandidateMove] = useState("");
  const [answer, setAnswer] = useState<QuestionAnswer | null>(null);
  const [asking, setAsking] = useState(false);
  const [coaching, setCoaching] = useState<CoachingLayers | null>(null);
  const [coachingLoading, setCoachingLoading] = useState(false);

  async function refreshGames(nextSelectedId?: string): Promise<void> {
    try {
      const nextGames = await listGames();
      setGames(nextGames);
      const selected = nextSelectedId ?? nextGames[0]?.id ?? null;
      setSelectedGameId(selected);
      setStatus(nextGames.length ? "Ready" : "No games yet.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load games.");
    }
  }

  useEffect(() => {
    void refreshGames();
  }, []);

  useEffect(() => {
    if (!selectedGameId) {
      setSelectedGame(null);
      setSelectedMove(null);
      setSelectedPly(null);
      return;
    }

    void (async () => {
      try {
        const game = await getGame(selectedGameId);
        setSelectedGame(game);
        setSelectedPly(game.moves[0]?.ply ?? null);
        setAnswer(null);
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to load game.");
      }
    })();
  }, [selectedGameId]);

  useEffect(() => {
    if (!selectedGameId || !selectedPly) {
      setSelectedMove(null);
      return;
    }

    void (async () => {
      try {
        const move = await getMove(selectedGameId, selectedPly);
        setSelectedMove(move);
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to load move.");
      }
    })();
  }, [selectedGameId, selectedPly]);

  useEffect(() => {
    if (!selectedGameId) {
      setCoaching(null);
      return;
    }
    setCoachingLoading(true);
    void (async () => {
      try {
        const layered = await getCoachingLayers(selectedGameId, selectedPly ?? undefined);
        setCoaching(layered);
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to generate coaching layers.");
      } finally {
        setCoachingLoading(false);
      }
    })();
  }, [selectedGameId, selectedPly]);

  const evalPercent = useMemo(() => clampEval(selectedMove?.eval_after ?? 0), [selectedMove]);

  async function handlePgnImport(): Promise<void> {
    if (!importPgnText.trim()) {
      return;
    }
    try {
      setStatus("Importing PGN...");
      const game = await importPgn({ pgn: importPgnText, title: importTitle || undefined });
      setImportPgnText("");
      setImportTitle("");
      await refreshGames(game.id);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "PGN import failed.");
    }
  }

  async function handleArchiveImport(): Promise<void> {
    if (!username.trim()) {
      return;
    }
    try {
      setStatus("Importing Chess.com archives...");
      const imported = await importChessComArchive({ username, from_month: fromMonth, to_month: toMonth });
      await refreshGames(imported[0]?.id);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Archive import failed.");
    }
  }

  async function handleDeepAnalysis(): Promise<void> {
    if (!selectedGameId) {
      return;
    }
    try {
      setStatus("Running deep analysis...");
      await runAnalysis({ game_id: selectedGameId, mode: "deep" });
      const game = await getGame(selectedGameId);
      setSelectedGame(game);
      const nextPly = selectedPly ?? game.moves[0]?.ply ?? null;
      setSelectedPly(nextPly);
      if (nextPly) {
        setSelectedMove(await getMove(selectedGameId, nextPly));
      }
      setStatus("Deep analysis complete.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Deep analysis failed.");
    }
  }

  async function handleQuestion(): Promise<void> {
    if (!selectedGameId || !question.trim()) {
      return;
    }
    setAsking(true);
    try {
      const reply = await askQuestion(selectedGameId, {
        question,
        ply: selectedPly ?? undefined,
        candidate_move: candidateMove || undefined,
      });
      setAnswer(reply);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Question failed.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-section">
          <p className="eyebrow">Imports</p>
          <label>
            Game title
            <input value={importTitle} onChange={(event) => setImportTitle(event.target.value)} />
          </label>
          <label>
            Paste PGN
            <textarea value={importPgnText} onChange={(event) => setImportPgnText(event.target.value)} />
          </label>
          <button type="button" className="primary-button" onClick={() => void handlePgnImport()}>
            Import PGN
          </button>
          <div className="divider" />
          <label>
            Chess.com username
            <input value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>
            From month
            <input type="month" value={fromMonth} onChange={(event) => setFromMonth(event.target.value)} />
          </label>
          <label>
            To month
            <input type="month" value={toMonth} onChange={(event) => setToMonth(event.target.value)} />
          </label>
          <button type="button" className="secondary-button" onClick={() => void handleArchiveImport()}>
            Import Chess.com archives
          </button>
        </div>
        <div className="sidebar-section">
          <p className="eyebrow">Games</p>
          <GameList games={games} selectedGameId={selectedGameId} onSelect={(gameId) => setSelectedGameId(gameId)} />
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Review board</p>
            <h1>{selectedGame?.title ?? "Select a game"}</h1>
            <p className="workspace-meta">
              {selectedGame ? `${selectedGame.white} vs ${selectedGame.black} · ${selectedGame.result}` : status}
            </p>
          </div>
          <button type="button" className="primary-button" onClick={() => void handleDeepAnalysis()} disabled={!selectedGameId}>
            Run deep analysis
          </button>
        </header>

        <section className="review-grid">
          <div className="board-column">
            <div className="board-panel">
              <div className="eval-bar">
                <div className="eval-white" style={{ height: `${evalPercent}%` }} />
              </div>
              <Board fen={selectedMove?.fen_after ?? START_FEN} />
            </div>
            <div className="stats-row">
              <div className="stat-card">
                <span>White accuracy</span>
                <strong>{selectedGame?.accuracy_white.toFixed(1) ?? "0.0"}%</strong>
              </div>
              <div className="stat-card">
                <span>Black accuracy</span>
                <strong>{selectedGame?.accuracy_black.toFixed(1) ?? "0.0"}%</strong>
              </div>
              <div className="stat-card">
                <span>Engine line</span>
                <strong>{selectedMove?.pv.join(" ") ?? "-"}</strong>
              </div>
            </div>
          </div>

          <div className="analysis-column">
            <div className="panel-block">
              <div className="section-header">
                <h2>Move review</h2>
                <span>{selectedMove ? `${selectedMove.san} · ${selectedMove.classification}` : "No move selected"}</span>
              </div>
              <MoveList moves={selectedGame?.moves ?? []} selectedPly={selectedPly} onSelect={(ply) => setSelectedPly(ply)} />
            </div>
            <ExplanationPanel move={selectedMove} />
            <CoachingPanel coaching={coaching} loading={coachingLoading} />
          </div>

          <div className="qa-column">
            <QaPanel
              question={question}
              candidateMove={candidateMove}
              answer={answer}
              loading={asking}
              onQuestionChange={setQuestion}
              onCandidateMoveChange={setCandidateMove}
              onSubmit={handleQuestion}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
