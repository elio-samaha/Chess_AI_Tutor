import type { FC } from "react";

const PIECES: Record<string, string> = {
  p: "♟",
  r: "♜",
  n: "♞",
  b: "♝",
  q: "♛",
  k: "♚",
  P: "♙",
  R: "♖",
  N: "♘",
  B: "♗",
  Q: "♕",
  K: "♔",
};

function parseFenBoard(fen: string): string[][] {
  const [placement] = fen.split(" ");
  return placement.split("/").map((rank) => {
    const squares: string[] = [];
    for (const token of rank) {
      if (/\d/.test(token)) {
        squares.push(...Array.from({ length: Number(token) }, () => ""));
      } else {
        squares.push(token);
      }
    }
    return squares;
  });
}

interface BoardProps {
  fen: string;
}

const Board: FC<BoardProps> = ({ fen }) => {
  const board = parseFenBoard(fen);

  return (
    <div className="board-shell">
      <div className="board-grid" role="img" aria-label="Chess board">
        {board.flatMap((rank, rankIndex) =>
          rank.map((piece, fileIndex) => {
            const isDark = (rankIndex + fileIndex) % 2 === 1;
            return (
              <div
                key={`${rankIndex}-${fileIndex}`}
                className={isDark ? "square square-dark" : "square square-light"}
              >
                <span className="piece">{piece ? PIECES[piece] : ""}</span>
              </div>
            );
          }),
        )}
      </div>
      <div className="board-coordinates board-files">
        <span>a</span>
        <span>b</span>
        <span>c</span>
        <span>d</span>
        <span>e</span>
        <span>f</span>
        <span>g</span>
        <span>h</span>
      </div>
    </div>
  );
};

export default Board;
