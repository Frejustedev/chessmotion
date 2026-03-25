"use client";
import { Toaster } from "react-hot-toast";
import { motion } from "framer-motion";
import Header from "@/components/Header";
import InputPanel from "@/components/InputPanel";
import GamePreview from "@/components/GamePreview";
import GameSelector from "@/components/GameSelector";
import SettingsPanel from "@/components/SettingsPanel";
import RenderButton from "@/components/RenderButton";
import RenderProgress from "@/components/RenderProgress";
import { useRenderJob } from "@/hooks/useRenderJob";

export default function Home() {
  useRenderJob();

  return (
    <div className="min-h-screen flex flex-col bg-surface">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1e293b",
            color: "#e2e8f0",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "10px",
          },
          success: { iconTheme: { primary: "#0ea5e9", secondary: "#fff" } },
          error:   { iconTheme: { primary: "#f87171", secondary: "#fff" } },
        }}
      />

      <RenderProgress />
      <Header />

      <main className="flex-1 p-5 max-w-[1400px] mx-auto w-full">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-5 text-center"
        >
          <h2 className="text-2xl font-bold text-white">
            Turn any chess game into a{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-cyan-400">
              cinematic video
            </span>
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Upload PGN · Paste a Lichess or Chess.com link · Export MP4 or GIF
          </p>
        </motion.div>

        {/* 3-column grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr_272px] gap-4 items-start">

          {/* ── Left : Input + Game selector + Render ── */}
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.25 }}
            className="flex flex-col gap-3"
          >
            <InputPanel />
            <GameSelector />
            <RenderButton />
          </motion.div>

          {/* ── Center : Preview ── */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col gap-3"
          >
            <GamePreview />
            <HowItWorks />
          </motion.div>

          {/* ── Right : Settings ── */}
          <motion.div
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.35 }}
          >
            <SettingsPanel />
          </motion.div>
        </div>
      </main>

      <footer className="py-3 text-center text-xs text-slate-800 border-t border-white/5">
        ChessMotion · FastAPI + Next.js · Pillow + MoviePy
      </footer>
    </div>
  );
}

function HowItWorks() {
  return (
    <div className="grid grid-cols-3 gap-2">
      {[
        { n: "1", t: "Load a game",  s: "Upload .pgn or paste a URL" },
        { n: "2", t: "Customise",    s: "Theme, timing, audio & more" },
        { n: "3", t: "Export",       s: "Download your MP4 or GIF" },
      ].map((item) => (
        <div key={item.n} className="glass rounded-lg p-3 text-center">
          <div className="w-5 h-5 rounded-full bg-brand-600/30 text-brand-400 text-[10px] font-bold flex items-center justify-center mx-auto mb-1.5">
            {item.n}
          </div>
          <p className="text-xs font-semibold text-slate-300">{item.t}</p>
          <p className="text-[10px] text-slate-600 mt-0.5 leading-tight">{item.s}</p>
        </div>
      ))}
    </div>
  );
}
