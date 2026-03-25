import { useEffect, useRef, useCallback } from "react";
import { pollRenderStatus } from "@/lib/api";
import { useStore } from "@/store/useStore";

const POLL_MS = 1500;

export function useRenderJob() {
  const job    = useStore((s) => s.job);
  const setJob = useStore((s) => s.setJob);
  const timer  = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (timer.current) { clearInterval(timer.current); timer.current = null; }
  }, []);

  useEffect(() => {
    if (!job || job.status === "done" || job.status === "error") {
      stop();
      return;
    }

    stop(); // clear any existing timer before starting a new one
    timer.current = setInterval(async () => {
      try {
        const updated = await pollRenderStatus(job.job_id);
        setJob(updated);
        if (updated.status === "done" || updated.status === "error") stop();
      } catch {
        // network hiccup – keep polling
      }
    }, POLL_MS);

    return stop;
  }, [job?.job_id, job?.status, setJob, stop]);

  return job;
}
