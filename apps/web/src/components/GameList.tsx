import type { FC } from "react";

import type { GameSummary } from "../types";

interface GameListProps {
  games: GameSummary[];
  selectedGameId: string | null;
  onSelect: (gameId: string) => void;
}

const GameList: FC<GameListProps> = ({ games, selectedGameId, onSelect }) => {
  if (games.length === 0) {
    return <p className="empty-state">No games loaded yet.</p>;
  }

  return (
    <div className="game-list">
      {games.map((game) => (
        <button
          key={game.id}
          className={game.id === selectedGameId ? "game-card game-card-active" : "game-card"}
          onClick={() => onSelect(game.id)}
          type="button"
        >
          <strong>{game.title}</strong>
          <span>{game.white} vs {game.black}</span>
          <span>
            {game.result} · {game.move_count} plies
          </span>
        </button>
      ))}
    </div>
  );
};

export default GameList;
