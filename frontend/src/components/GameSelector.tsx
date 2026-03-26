"use client";
import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { List, ChevronDown, Search, ChevronLeft, ChevronRight, PackageOpen, Loader2, Download } from "lucide-react";
import toast from "react-hot-toast";
import { useStore } from "@/store/useStore";
import { parsePgnPage, startBatchRender, pollBatchStatus, getBatchDownloadUrl } from "@/lib/api";
import type { GameInfo } from "@/types";

const PAGE_SIZE = 50;

export default function GameSelector() {
  const { games, gameData, settings, totalGames, currentPage, pgnFile,
          setSelectedGame, setGames, setPage } = useStore((s) => ({
    games: s.games, gameData: s.gameData, settings: s.settings,
    totalGames: s.totalGames, currentPage: s.currentPage, pgnFile: s.pgnFile,
    setSelectedGame: s.setSelectedGame, setGames: s.setGames, setPage: s.setPage,
  }));

  const [open, setOpen]       = useState(false);
  const [search, setSearch]   = useState("");
  const [paging, setPaging]   = useState(false);
  const [batchIds, setBatchIds] = useState<string[] | null>(null);
  const [batchDone, setBatchDone] = useState(0);
  const [batchRunning, setBatchRunning] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  if (totalGames <= 1) return null;

  const totalPages = Math.ceil(totalGames / PAGE_SIZE);
  const current = games[settings.game_index] ?? games[0];

  // ── Filtered list ───────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    if (!search.trim()) return games;
    const q = search.toLowerCase();
    return games.filter((g) =>
      g.white.name.toLowerCase().includes(q) ||
      g.black.name.toLowerCase().includes(q) ||
      (g.opening ?? "").toLowerCase().includes(q) ||
      g.result.includes(q)
    );
  }, [games, search]);

  // ── Result distribution ─────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const w = games.filter((g) => g.result === "1-0").length;
    const b = games.filter((g) => g.result === "0-1").length;
    const d = games.filter((g) => g.result === "1/2-1/2").length;
    return { w, b, d };
  }, [games]);

  // ── Page navigation ─────────────────────────────────────────────────────────
  const goToPage = async (page: number) => {
    if (!pgnFile || page < 0 || page >= totalPages) return;
    setPaging(true);
    try {
      const result = await parsePgnPage(pgnFile, PAGE_SIZE, page * PAGE_SIZE);
      setGames(result.games, result.total, page);
      setPage(page);
    } catch {
      toast.error("Failed to load page");
    } finally {
      setPaging(false);
    }
  };

  // ── Batch export ────────────────────────────────────────────────────────────
  const handleBatchExport = async () => {
    if (games.length === 0) return;
    setBatchRunning(true);
    setBatchDone(0);
    try {
      const { job_ids } = await startBatchRender(games, settings);
      setBatchIds(job_ids);
      // Poll until all done
      let pending = [...job_ids];
      let done = 0;
      while (pending.length > 0) {
        await new Promise((r) => setTimeout(r, 2500));
        const statuses = await pollBatchStatus(pending);
        const nowDone = statuses.filter((s) => s.status === "done").map((s) => s.job_id);
        const failed  = statuses.filter((s) => s.status === "error").map((s) => s.job_id);
        done += nowDone.length;
        setBatchDone(done);
        pending = pending.filter((id) => !nowDone.includes(id) && !failed.includes(id));
        if (failed.length > 0) toast.error(`${failed.length} job(s) failed`);
      }
      toast.success(`${done} videos ready! Click Download ZIP.`);
    } catch (e: any) {
      toast.error(e?.message ?? "Batch export failed");
      setBatchRunning(false);
      setBatchIds(null);
    } finally {
      setBatchRunning(false);
    }
  };

  const allDone = batchIds && batchDone >= batchIds.length;

  return (
    <div className="glass rounded-xl p-4 flex flex-col gap-3">
      {/* Header row */}
      <div className="flex items-center gap-2">
        <List size={14} className="text-brand-500 shrink-0" />
        <span className="section-title mb-0 flex-1">Games</span>
        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full shrink-0">
          {totalGames} total
        </span>
      </div>

      {/* Result stats bar */}
      <div className="flex gap-1 text-[10px]">
        <StatPill label={`${stats.w} White wins`} color="bg-emerald-700/40 text-emerald-300" />
        <StatPill label={`${stats.d} Draws`}      color="bg-yellow-700/30 text-yellow-300" />
        <StatPill label={`${stats.b} Black wins`} color="bg-rose-700/40 text-rose-300" />
      </div>

      {/* Current game + dropdown toggle */}
      <div className="relative">
        <button onClick={() => { setOpen((v) => !v); setTimeout(() => searchRef.current?.focus(), 80); }}
          className="w-full input-field flex items-center justify-between text-sm">
          <span className="truncate text-left">
            <span className="text-brand-400 font-mono mr-1.5">#{settings.game_index + 1}</span>
            {current?.white.name} vs {current?.black.name}
            {current?.result && <span className="ml-2 text-slate-500">{current.result}</span>}
          </span>
          <ChevronDown size={14} className={`shrink-0 ml-2 transition-transform ${open ? "rotate-180" : ""}`} />
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -6, scaleY: 0.95 }}
              animate={{ opacity: 1, y: 0, scaleY: 1 }}
              exit={{ opacity: 0, y: -6, scaleY: 0.95 }}
              className="absolute z-30 left-0 right-0 top-[calc(100%+4px)] bg-[#0f172a] border border-white/10 rounded-xl shadow-2xl overflow-hidden"
            >
              {/* Search */}
              <div className="p-2 border-b border-white/5 flex items-center gap-2">
                <Search size={12} className="text-slate-500 shrink-0" />
                <input ref={searchRef} value={search} onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search player, opening…"
                  className="flex-1 bg-transparent text-xs text-slate-200 outline-none placeholder-slate-600" />
              </div>
              {/* List */}
              <ul className="max-h-52 overflow-y-auto">
                {filtered.length === 0 && (
                  <li className="py-4 text-center text-xs text-slate-600">No match</li>
                )}
                {filtered.map((g, i) => {
                  const realIdx = games.indexOf(g);
                  return (
                    <li key={i}>
                      <button onClick={() => { setSelectedGame(realIdx); setOpen(false); setSearch(""); }}
                        className={`w-full text-left px-3 py-1.5 text-xs hover:bg-white/5 transition-colors flex items-center gap-2 ${
                          realIdx === settings.game_index ? "text-brand-400 bg-brand-600/10" : "text-slate-300"
                        }`}>
                        <span className="text-slate-600 font-mono w-6 shrink-0">#{currentPage * PAGE_SIZE + realIdx + 1}</span>
                        <span className="truncate flex-1">{g.white.name} vs {g.black.name}</span>
                        {g.opening && <span className="text-slate-600 truncate max-w-[80px] hidden sm:block">{g.opening}</span>}
                        <span className="text-slate-500 shrink-0">{g.result}</span>
                        <span className="text-slate-700 shrink-0">{g.moves.length}m</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-3 py-2 border-t border-white/5 text-xs text-slate-500">
                  <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 0 || paging}
                    className="hover:text-white disabled:opacity-30 flex items-center gap-1">
                    <ChevronLeft size={12} /> Prev
                  </button>
                  <span>Page {currentPage + 1} / {totalPages}{paging && " …"}</span>
                  <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages - 1 || paging}
                    className="hover:text-white disabled:opacity-30 flex items-center gap-1">
                    Next <ChevronRight size={12} />
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Batch export section */}
      <div className="border-t border-white/5 pt-3">
        {!batchIds ? (
          <button onClick={handleBatchExport} disabled={batchRunning || games.length === 0}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium border border-brand-600/40 text-brand-400 hover:bg-brand-600/15 transition-all disabled:opacity-40">
            {batchRunning ? <Loader2 size={12} className="animate-spin" /> : <PackageOpen size={12} />}
            Export all {games.length} game{games.length > 1 ? "s" : ""} as videos
          </button>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div className="h-full bg-brand-500 rounded-full"
                  animate={{ width: `${(batchDone / batchIds.length) * 100}%` }} />
              </div>
              <span className="font-mono shrink-0">{batchDone}/{batchIds.length}</span>
            </div>
            {allDone && (
              <a href={getBatchDownloadUrl(batchIds)}
                className="flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold bg-green-600/20 border border-green-600/30 text-green-400 hover:bg-green-600/30 transition-all">
                <Download size={12} /> Download ZIP ({batchIds.length} videos)
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatPill({ label, color }: { label: string; color: string }) {
  return <span className={`px-2 py-0.5 rounded-full font-medium ${color}`}>{label}</span>;
}
