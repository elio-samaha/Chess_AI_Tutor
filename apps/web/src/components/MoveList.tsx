import type { FC } from "react";

import type { MoveSummary } from "../types";

interface MoveListProps {
  moves: MoveSummary[];
  selectedPly: number | null;
  onSelect: (ply: number) => void;
}

function badgeClass(classification: string): string {
  return `badge badge-${classification}`;
}

const MoveList: FC<MoveListProps> = ({ moves, selectedPly, onSelect }) => {
  return (
    <div className="move-list">
      {moves.map((move) => (
        <button
          key={move.ply}
          type="button"
          className={move.ply === selectedPly ? "move-row move-row-active" : "move-row"}
          onClick={() => onSelect(move.ply)}
        >
          <span className="move-san">
            {move.fullmove_number}.{move.color === "black" ? ".." : ""} {move.san}
          </span>
          <span className={badgeClass(move.classification)}>{move.classification}</span>
          <span className="move-loss">-{move.cp_loss} cp</span>
        </button>
      ))}
    </div>
  );
};

export default MoveList;
