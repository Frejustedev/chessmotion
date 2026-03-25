"use client";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import MiniBoard from "./MiniBoard";
import { useStore } from "@/store/useStore";

const STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

const RESULT_STYLE: Record<string, { label: string; cls: string }> = {
  "1-0":     { label: "1–0",  cls: "bg-green-600/20 text-green-400 border-green-600/30" },
  "0-1":     { label: "0–1",  cls: "bg-red-600/20 text-red-400 border-red-600/30" },
  "1/2-1/2": { label: "½–½",  cls: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30" },
};

export default function GamePreview() {
  const gameData = useStore((s) => s.gameData);
  const flip = useStore((s) => s.settings.flip_board);
  const [cursor, setCursor] = useState(0);

  // Reset cursor whenever the active game changes
  useEffect(() => { setCursor(0); }, [gameData]);

  // Keyboard navigation
  const handleKey = useCallback((e: KeyboardEvent) => {
    if (!gameData) return;
    const n = gameData.moves.length;
    if (e.key === "ArrowRight") setCursor((c) => Math.min(n, c + 1));
    if (e.key === "ArrowLeft")  setCursor((c) => Math.max(0, c - 1));
    if (e.key === "ArrowUp")    setCursor(0);
    if (e.key === "ArrowDown")  setCursor(n);
  }, [gameData]);

  useEffect(() => {
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [handleKey]);

  if (!gameData) {
    return (
      <div className="glass rounded-xl p-8 flex flex-col items-center justify-center gap-4 text-center h-full min-h-[400px]">
        <span className="text-6xl opacity-20 select-none">♟</span>
        <p className="text-slate-500 text-sm">Load a game to preview it here</p>
        <p className="text-slate-600 text-xs">Upload a .pgn file or paste a Lichess / Chess.com URL</p>
      </div>
    );
  }

  const moves = gameData.moves;
  const total = moves.length;
  const currentFen = cursor === 0 ? (gameData.starting_fen ?? STARTING_FEN) : moves[cursor - 1].fen_after;
  const lastMoveUci = cursor > 0 ? moves[cursor - 1].uci : undefined;
  const resultStyle = RESULT_STYLE[gameData.result] ?? { label: gameData.result, cls: "bg-slate-700/50 text-slate-400 border-slate-600/30" };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      key={gameData.white.name + gameData.black.name}
      className="glass rounded-xl p-5 flex flex-col gap-4"
    >
      {/* Player header */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1.5">
          <PlayerRow name={gameData.black.name} rating={gameData.black.rating} color="black" />
          <PlayerRow name={gameData.white.name} rating={gameData.white.rating} color="white" />
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${resultStyle.cls}`}>
            {resultStyle.label}
          </span>
          {gameData.opening && (
            <span className="text-[10px] text-slate-500 max-w-[150px] text-right leading-tight">{gameData.opening}</span>
          )}
        </div>
      </div>

      {/* Board + Move list */}
      <div className="flex gap-4">
        {/* Board column */}
        <div className="flex flex-col gap-2 shrink-0">
          <MiniBoard fen={currentFen} lastMove={lastMoveUci} size={232} flip={flip} />
          {/* Navigation controls */}
          <div className="flex items-center justify-center gap-1">
            {([
              [<ChevronsLeft key="cl" size={13} />, () => setCursor(0)],
              [<ChevronLeft key="l" size={13} />,   () => setCursor((c) => Math.max(0, c - 1))],
              [<ChevronRight key="r" size={13} />,  () => setCursor((c) => Math.min(total, c + 1))],
              [<ChevronsRight key="cr" size={13} />, () => setCursor(total)],
            ] as [React.ReactNode, () => void][]).map(([icon, action], i) => (
              <button key={i} onClick={action} className="btn-ghost p-1.5 rounded-md text-slate-400 hover:text-white">
                {icon}
              </button>
            ))}
            <span className="text-[10px] text-slate-600 ml-1 font-mono">{cursor}/{total}</span>
          </div>
          <p className="text-[9px] text-slate-700 text-center">← → arrow keys to navigate</p>
        </div>

        {/* Move list */}
        <div className="flex-1 overflow-y-auto max-h-[270px]">
          <div className="grid grid-cols-[22px_1fr_1fr] gap-x-1 gap-y-px text-xs">
            {Array.from({ length: Math.ceil(moves.length / 2) }, (_, pair) => {
              const wi = pair * 2;
              const bi = pair * 2 + 1;
              return (
                <div key={pair} className="contents">
                  <span className="text-slate-700 py-0.5 font-mono text-[10px] flex items-center">{pair + 1}.</span>
                  <MoveBtn san={moves[wi].san} active={cursor === wi + 1} onClick={() => setCursor(wi + 1)} comment={moves[wi].comment} />
                  {moves[bi] ? (
                    <MoveBtn san={moves[bi].san} active={cursor === bi + 1} onClick={() => setCursor(bi + 1)} comment={moves[bi].comment} />
                  ) : <span />}
                </div>
              );
            })}
          </div>
          {/* current move comment */}
          {cursor > 0 && moves[cursor - 1].comment && (
            <p className="mt-2 text-[10px] text-slate-500 italic border-t border-white/5 pt-2">
              💬 {moves[cursor - 1].comment}
            </p>
          )}
        </div>
      </div>

      {/* Footer stats */}
      <div className="flex items-center gap-3 text-[10px] text-slate-600 border-t border-white/5 pt-2.5">
        <span><span className="text-slate-400 font-medium">{total}</span> moves</span>
        {gameData.event && <span className="truncate flex-1">{gameData.event}</span>}
        {gameData.date && <span className="shrink-0">{gameData.date}</span>}
      </div>
    </motion.div>
  );
}

function PlayerRow({ name, rating, color }: { name: string; rating?: number; color: "white" | "black" }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-3 h-3 rounded-full border shrink-0 ${
        color === "white" ? "bg-white border-slate-400" : "bg-slate-800 border-slate-500"
      }`} />
      <span className="text-sm text-slate-200 font-medium leading-none">{name}</span>
      {rating && <span className="text-xs text-slate-500">({rating})</span>}
    </div>
  );
}

function MoveBtn({ san, active, onClick, comment }: {
  san: string; active: boolean; onClick: () => void; comment?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={comment ?? undefined}
      className={`text-left px-1 py-0.5 rounded font-mono text-xs transition-colors truncate ${
        active ? "bg-brand-600/40 text-brand-300 font-semibold" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
      } ${comment ? "underline decoration-dotted decoration-slate-600" : ""}`}
    >
      {san}
    </button>
  );
}
