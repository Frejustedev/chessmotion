import axios from "axios";
import type { GameInfo, RenderJobResponse, RenderSettings, PgnParseResult, BatchJobStatus } from "@/types";

const client = axios.create({ baseURL: "/api", timeout: 30_000 });

// ── Games ────────────────────────────────────────────────────────────────────────

export async function parsePgn(
  file: File,
  limit = 50,
  skip = 0
): Promise<PgnParseResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<PgnParseResult>(
    `/games/parse-pgn?limit=${limit}&skip=${skip}`,
    form
  );
  return data;
}

export async function parsePgnPage(
  file: File,
  limit: number,
  skip: number
): Promise<PgnParseResult> {
  return parsePgn(file, limit, skip);
}

export async function importFromUrl(
  url: string,
  maxGames = 50
): Promise<GameInfo[]> {
  const { data } = await client.post<GameInfo[]>(
    `/games/import-url?max_games=${maxGames}`,
    { url, settings: {} }
  );
  return data;
}

// ── Render ───────────────────────────────────────────────────────────────────────

export async function startRender(
  game: GameInfo,
  settings: RenderSettings
): Promise<RenderJobResponse> {
  const { data } = await client.post<RenderJobResponse>("/render/start", {
    game,
    settings,
  });
  return data;
}

export async function pollRenderStatus(jobId: string): Promise<RenderJobResponse> {
  const { data } = await client.get<RenderJobResponse>(`/render/status/${jobId}`);
  return data;
}

export function getDownloadUrl(jobId: string): string {
  return `/api/render/download/${jobId}`;
}

export async function startBatchRender(
  games: GameInfo[],
  settings: RenderSettings
): Promise<{ job_ids: string[]; total: number }> {
  const { data } = await client.post("/render/batch-start", { games, settings });
  return data;
}

export async function pollBatchStatus(jobIds: string[]): Promise<BatchJobStatus[]> {
  const { data } = await client.get<BatchJobStatus[]>(
    `/render/batch-status?job_ids=${jobIds.join(",")}`
  );
  return data;
}

export function getBatchDownloadUrl(jobIds: string[]): string {
  return `/api/render/batch-download?job_ids=${jobIds.join(",")}`;
}
