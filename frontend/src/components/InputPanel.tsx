"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, Link2, FileText, Loader2, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import { parsePgn, importFromUrl } from "@/lib/api";
import { useStore } from "@/store/useStore";

export default function InputPanel() {
  const { inputSource, setInputSource, setPgnFile, setUrl, url, setGames } = useStore((s) => ({
    inputSource: s.inputSource,
    setInputSource: s.setInputSource,
    setPgnFile: s.setPgnFile,
    setUrl: s.setUrl,
    url: s.url,
    setGames: s.setGames,
  }));

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);

  const onDrop = useCallback(async (accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    setPgnFile(file);
    setFilename(file.name);
    setError(null);
    setLoading(true);
    try {
      const result = await parsePgn(file, 50, 0);
      setGames(result.games, result.total, 0);
      const extra = result.total > result.games.length
        ? ` — showing first ${result.games.length} of ${result.total}`
        : "";
      toast.success(`${result.total} game${result.total > 1 ? "s" : ""} loaded!${extra}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to parse PGN.");
    } finally {
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/octet-stream": [".pgn"], "text/plain": [".pgn"] },
    maxFiles: 1,
  });

  const handleUrlImport = async () => {
    if (!url.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const games = await importFromUrl(url.trim());
      setGames(games);
      toast.success(`${games.length} game${games.length > 1 ? "s" : ""} imported!`);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to import from URL.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-xl p-5 flex flex-col gap-4">
      <p className="section-title">Input Source</p>

      {/* Tabs */}
      <div className="flex rounded-lg bg-surface-50 p-1 gap-1">
        {(["file", "url"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setInputSource(tab)}
            className={`flex-1 py-1.5 text-sm rounded-md font-medium transition-all duration-200 ${
              inputSource === tab
                ? "bg-brand-600 text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {tab === "file" ? "Upload PGN" : "URL Import"}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {inputSource === "file" ? (
          <motion.div key="file" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? "border-brand-500 bg-brand-500/10"
                  : "border-slate-700 hover:border-slate-500 hover:bg-white/5"
              }`}
            >
              <input {...getInputProps()} />
              <UploadCloud className="mx-auto mb-3 text-slate-500" size={36} />
              {filename ? (
                <div className="flex items-center justify-center gap-2 text-brand-400">
                  <FileText size={16} />
                  <span className="text-sm font-medium">{filename}</span>
                </div>
              ) : (
                <>
                  <p className="text-slate-300 text-sm font-medium">
                    {isDragActive ? "Drop your PGN here" : "Drag & drop a .pgn file"}
                  </p>
                  <p className="text-slate-600 text-xs mt-1">or click to browse — single or multi-game</p>
                </>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div key="url" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-3">
            <input
              type="url"
              className="input-field"
              placeholder="https://lichess.org/ABC123  or  chess.com/game/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleUrlImport()}
            />
            <div className="flex gap-2 text-xs text-slate-500">
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">Lichess</span>
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">Chess.com</span>
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">Tournament</span>
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">User games</span>
            </div>
            <button
              onClick={handleUrlImport}
              disabled={loading || !url.trim()}
              className="btn-primary flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Link2 size={16} />}
              Import Game
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {loading && inputSource === "file" && (
        <div className="flex items-center gap-2 text-brand-400 text-sm">
          <Loader2 size={14} className="animate-spin" />
          <span>Parsing PGN…</span>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
