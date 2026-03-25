"use client";
import { motion, AnimatePresence } from "framer-motion";
import { Download, X, CheckCircle2, AlertCircle, Loader2, Film } from "lucide-react";
import { getDownloadUrl } from "@/lib/api";
import { useStore } from "@/store/useStore";
import type { RenderJobResponse } from "@/types";

export default function RenderProgress() {
  const job = useStore((s) => s.job);
  const setJob = useStore((s) => s.setJob);

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
            className="glass rounded-2xl p-8 w-[440px] shadow-2xl border border-white/10 relative"
          >
            {job.status !== "processing" && job.status !== "queued" && (
              <button
                onClick={() => setJob(null)}
                className="absolute top-4 right-4 btn-ghost p-1.5 rounded-lg"
              >
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
                <div className="flex flex-col gap-3 w-full">
                  <a
                    href={getDownloadUrl(job.job_id)}
                    download
                    className="btn-primary flex items-center justify-center gap-2 py-3 text-base"
                  >
                    <Download size={18} />
                    Download File
                  </a>
                  <button
                    onClick={() => setJob(null)}
                    className="btn-ghost text-sm"
                  >
                    Close
                  </button>
                </div>
              )}

              {job.status === "error" && (
                <button onClick={() => setJob(null)} className="btn-ghost text-sm">
                  Dismiss
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

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
  return { queued: "Job Queued", processing: "Rendering…", done: "Ready to Download!", error: "Render Failed" }[s];
}

function statusSubtitle(s: RenderJobResponse["status"]) {
  return {
    queued: "Your job is waiting in the queue…",
    processing: "Generating frames and assembling video…",
    done: "",
    error: "An unexpected error occurred.",
  }[s];
}
