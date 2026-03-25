"use client";

const PIECE_UNICODE: Record<string, string> = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

function parseFen(fen: string): (string | null)[][] {
  const board: (string | null)[][] = Array.from({ length: 8 }, () => Array(8).fill(null));
  const rows = fen.split(" ")[0].split("/");
  rows.forEach((row, r) => {
    let c = 0;
    for (const ch of row) {
      if (ch >= "1" && ch <= "8") c += parseInt(ch);
      else { board[r][c] = ch; c++; }
    }
  });
  return board;
}

interface Props {
  fen: string;
  lastMove?: string;
  size?: number;
  flip?: boolean;
}

export default function MiniBoard({ fen, lastMove, size = 240, flip = false }: Props) {
  const board = parseFen(fen);
  const sq = Math.floor(size / 8);

  const fromSq = lastMove ? { r: 8 - parseInt(lastMove[1]), c: lastMove[0].charCodeAt(0) - 97 } : null;
  const toSq   = lastMove ? { r: 8 - parseInt(lastMove[3]), c: lastMove[2].charCodeAt(0) - 97 } : null;

  const rows = flip ? [...Array(8)].map((_, i) => 7 - i) : [...Array(8)].map((_, i) => i);
  const cols = flip ? [...Array(8)].map((_, i) => 7 - i) : [...Array(8)].map((_, i) => i);

  return (
    <div
      className="rounded-lg overflow-hidden shadow-2xl border border-white/10 shrink-0"
      style={{ width: size, height: size }}
    >
      {rows.map((r) => (
        <div key={r} className="flex">
          {cols.map((c) => {
            const isLight = (r + c) % 2 === 0;
            const piece = board[r][c];
            const isHighlighted =
              (fromSq && fromSq.r === r && fromSq.c === c) ||
              (toSq   && toSq.r   === r && toSq.c   === c);

            return (
              <div
                key={c}
                style={{ width: sq, height: sq, fontSize: sq * 0.72, lineHeight: `${sq}px` }}
                className={`flex items-center justify-center select-none
                  ${isHighlighted
                    ? isLight ? "bg-yellow-300" : "bg-yellow-500"
                    : isLight ? "bg-[#eeeed2]" : "bg-[#769656]"
                  }`}
              >
                {piece && (
                  <span
                    style={{
                      color: piece === piece.toUpperCase() ? "#fff" : "#1a1a1a",
                      textShadow:
                        piece === piece.toUpperCase()
                          ? "0 1px 3px #000,0 0 2px #000"
                          : "0 1px 2px #fff8",
                    }}
                  >
                    {PIECE_UNICODE[piece]}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
