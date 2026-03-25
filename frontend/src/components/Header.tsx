"use client";
import { motion } from "framer-motion";

export default function Header() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex items-center justify-between px-8 py-4 border-b border-white/10"
    >
      <div className="flex items-center gap-3">
        <span className="text-3xl select-none">♟</span>
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Chess<span className="text-brand-500">Motion</span>
          </h1>
          <p className="text-xs text-slate-500 leading-none">Chess games → MP4 / GIF</p>
        </div>
      </div>

      <nav className="flex items-center gap-2">
        <a
          href="/api/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost text-sm py-1.5 px-3"
        >
          API Docs
        </a>
        <a
          href="https://lichess.org"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-500 hover:text-slate-300 transition-colors text-sm px-3 py-1.5"
        >
          Lichess
        </a>
      </nav>
    </motion.header>
  );
}
