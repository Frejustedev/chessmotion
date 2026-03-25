"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Clapperboard, Loader2, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import { startRender } from "@/lib/api";
import { useStore } from "@/store/useStore";

export default function RenderButton() {
  const { gameData, settings, setJob } = useStore((s) => ({
    gameData: s.gameData,
    settings: s.settings,
    setJob: s.setJob,
  }));

  const [loading, setLoading] = useState(false);

  const handleRender = async () => {
    if (!gameData) return;
    setLoading(true);
    try {
      const job = await startRender(gameData, settings);
      setJob(job);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Failed to start render.");
    } finally {
      setLoading(false);
    }
  };

  const disabled = !gameData || loading;

  return (
    <div className="flex flex-col gap-2">
      <motion.button
        onClick={handleRender}
        disabled={disabled}
        whileHover={disabled ? {} : { scale: 1.02 }}
        whileTap={disabled ? {} : { scale: 0.98 }}
        className={`w-full py-3.5 rounded-xl font-bold text-base flex items-center justify-center gap-3 transition-all duration-200
          ${disabled
            ? "bg-slate-800 text-slate-600 cursor-not-allowed"
            : "bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-lg shadow-brand-600/30 hover:shadow-brand-600/50"
          }`}
      >
        {loading ? (
          <Loader2 size={20} className="animate-spin" />
        ) : (
          <Clapperboard size={20} />
        )}
        {loading ? "Submitting…" : `Export as ${settings.output_format.toUpperCase()}`}
      </motion.button>

      {!gameData && (
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <AlertCircle size={12} />
          <span>Load a game first to enable rendering</span>
        </div>
      )}

      {gameData && (
        <p className="text-xs text-slate-600 text-center">
          {gameData.moves.length} moves · {settings.board_size}px ·{" "}
          {(gameData.moves.length * settings.move_delay).toFixed(0)}s estimated duration
        </p>
      )}
    </div>
  );
}
