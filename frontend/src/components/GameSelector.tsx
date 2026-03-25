"use client";
import { motion, AnimatePresence } from "framer-motion";
import { List, ChevronDown } from "lucide-react";
import { useState } from "react";
import { useStore } from "@/store/useStore";

export default function GameSelector() {
  const games = useStore((s) => s.games);
  const gameData = useStore((s) => s.gameData);
  const setSelectedGame = useStore((s) => s.setSelectedGame);
  const settings = useStore((s) => s.settings);
  const [open, setOpen] = useState(false);

  if (games.length <= 1) return null;

  const current = games[settings.game_index] ?? games[0];

  return (
    <div className="glass rounded-xl p-4 relative">
      <div className="flex items-center gap-2 mb-2">
        <List size={14} className="text-brand-500" />
        <span className="section-title mb-0">Game Selection</span>
        <span className="ml-auto text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">
          {games.length} games
        </span>
      </div>

      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full input-field flex items-center justify-between text-sm"
      >
        <span className="truncate text-left">
          <span className="text-brand-400 font-mono mr-1.5">#{settings.game_index + 1}</span>
          {current?.white.name} vs {current?.black.name}
          {current?.result && <span className="ml-2 text-slate-500">{current.result}</span>}
        </span>
        <ChevronDown size={14} className={`shrink-0 ml-2 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="absolute z-20 left-4 right-4 top-[calc(100%-8px)] bg-surface-50 border border-white/10 rounded-lg shadow-xl max-h-56 overflow-y-auto"
          >
            {games.map((g, i) => (
              <li key={i}>
                <button
                  onClick={() => { setSelectedGame(i); setOpen(false); }}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors flex items-center gap-2 ${
                    i === settings.game_index ? "text-brand-400 bg-brand-600/10" : "text-slate-300"
                  }`}
                >
                  <span className="text-slate-600 font-mono w-6 shrink-0">#{i + 1}</span>
                  <span className="truncate flex-1">{g.white.name} vs {g.black.name}</span>
                  <span className="text-slate-500 shrink-0">{g.result}</span>
                  <span className="text-slate-600 shrink-0">{g.moves.length}m</span>
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
