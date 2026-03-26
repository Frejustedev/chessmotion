import axios from "axios";
import type { GameInfo, RenderJobResponse, RenderSettings } from "@/types";

const client = axios.create({ baseURL: "/api", timeout: 30_000 });

// ── Games ────────────────────────────────────────────────────────────────────────

export async function parsePgn(file: File): Promise<GameInfo[]> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<GameInfo[]>("/games/parse-pgn", form);
  return data;
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
