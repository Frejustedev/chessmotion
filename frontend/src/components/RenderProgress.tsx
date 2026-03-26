"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, FolderOpen, X, CheckCircle2, AlertCircle, Loader2, Film } from "lucide-react";
import toast from "react-hot-toast";
import { getDownloadUrl } from "@/lib/api";
import { useStore } from "@/store/useStore";
import type { RenderJobResponse } from "@/types";

// Check if the File System Access API is available (Chrome/Edge)
const hasSavePicker = typeof window !== "undefined" && "showSaveFilePicker" in window;

export default function RenderProgress() {
  const job    = useStore((s) => s.job);
  const setJob = useStore((s) => s.setJob);
  const gameData = useStore((s) => s.gameData);

  return (
    <AnimatePresence>
      {job && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="glass rounded-2xl p-8 w-[460px] shadow-2xl border border-white/10 relative"
          >
            {job.status !== "processing" && job.status !== "queued" && (
              <button onClick={() => setJob(null)}
                className="absolute top-4 right-4 btn-ghost p-1.5 rounded-lg">
                <X size={16} />
              </button>
            )}

            <div className="flex flex-col items-center gap-6 text-center">
              <StatusIcon status={job.status} />

              <div>
                <h3 className="text-lg font-semibold text-white mb-1">
                  {statusTitle(job.status)}
                </h3>
                <p className="text-sm text-slate-400">{job.message || statusSubtitle(job.status)}</p>
              </div>

              {(job.status === "processing" || job.status === "queued") && (
                <div className="w-full">
                  <div className="flex justify-between text-xs text-slate-500 mb-2">
                    <span>Progress</span>
                    <span className="font-mono text-brand-400">{job.progress}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${job.progress}%` }}
                      transition={{ duration: 0.4 }}
                    />
                  </div>
                  <p className="text-xs text-slate-600 mt-3">
                    This may take a minute — your file is being rendered on the server.
                  </p>
                </div>
              )}

              {job.status === "done" && (
                <DownloadSection job={job} gameData={gameData} onClose={() => setJob(null)} />
              )}

              {job.status === "error" && (
                <button onClick={() => setJob(null)} className="btn-ghost text-sm">Dismiss</button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Download section ─────────────────────────────────────────────────────────────

function DownloadSection({ job, gameData, onClose }: {
  job: RenderJobResponse;
  gameData: import("@/types").GameInfo | null;
  onClose: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const settings = useStore((s) => s.settings);

  const ext = settings.output_format;
  const defaultName = gameData
    ? `${gameData.white.name}_vs_${gameData.black.name}.${ext}`.replace(/[^a-zA-Z0-9._-]/g, "_")
    : `chessmotion_video.${ext}`;

  const handleSaveAs = async () => {
    setSaving(true);
    try {
      const url = getDownloadUrl(job.job_id);
      const response = await fetch(url);
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();

      if (hasSavePicker) {
        const fileHandle = await (window as any).showSaveFilePicker({
          suggestedName: defaultName,
          types: [
            {
              description: ext === "mp4" ? "MP4 Video" : "GIF Animation",
              accept: ext === "mp4"
                ? { "video/mp4": [".mp4"] }
                : { "image/gif": [".gif"] },
            },
          ],
          startIn: "videos",   // pre-opens the Videos folder
        });
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
        toast.success(`Saved to: ${fileHandle.name}`);
      } else {
        // Fallback: standard download
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = objUrl;
        a.download = defaultName;
        a.click();
        URL.revokeObjectURL(objUrl);
        toast.success("Download started!");
      }
    } catch (e: any) {
      if (e?.name === "AbortError") return; // user cancelled the picker
      toast.error("Download error: " + (e?.message ?? "Unknown"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 w-full">
      {/* Suggested filename display */}
      <div className="bg-surface-50 rounded-lg px-3 py-2 flex items-center gap-2 text-left">
        <Film size={14} className="text-brand-400 shrink-0" />
        <span className="text-xs text-slate-400 truncate font-mono">{defaultName}</span>
      </div>

      {/* Save As (with folder picker on Chrome/Edge) */}
      <button onClick={handleSaveAs} disabled={saving}
        className="btn-primary flex items-center justify-center gap-2 py-3 text-base disabled:opacity-60">
        {saving
          ? <Loader2 size={18} className="animate-spin" />
          : hasSavePicker ? <FolderOpen size={18} /> : <Download size={18} />}
        {saving
          ? "Saving…"
          : hasSavePicker ? "Choose folder & save" : "Download"}
      </button>

      {hasSavePicker && (
        <p className="text-[11px] text-slate-600">
          Opens a dialog so you can choose any folder on your PC.
        </p>
      )}

      <button onClick={onClose} className="btn-ghost text-sm">Close</button>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────────

function StatusIcon({ status }: { status: RenderJobResponse["status"] }) {
  const base = "w-16 h-16 rounded-full flex items-center justify-center";
  if (status === "done")
    return (
      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}
        className={`${base} bg-green-500/20`}>
        <CheckCircle2 size={36} className="text-green-400" />
      </motion.div>
    );
  if (status === "error")
    return (
      <div className={`${base} bg-red-500/20`}>
        <AlertCircle size={36} className="text-red-400" />
      </div>
    );
  return (
    <div className={`${base} bg-brand-500/20`}>
      <Film size={28} className="text-brand-400" />
      <Loader2 size={20} className="text-brand-400 animate-spin absolute" />
    </div>
  );
}

function statusTitle(s: RenderJobResponse["status"]) {
  return { queued: "Job Queued", processing: "Rendering…", done: "Ready!", error: "Render Failed" }[s];
}

function statusSubtitle(s: RenderJobResponse["status"]) {
  return {
    queued: "Your job is waiting in the queue…",
    processing: "Generating frames and assembling video…",
    done: "",
    error: "An unexpected error occurred.",
  }[s];
}
