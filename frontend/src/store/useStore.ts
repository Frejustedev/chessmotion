import { create } from "zustand";
import type { AppState, RenderSettings, GameInfo, RenderJobResponse, InputSource } from "@/types";

const DEFAULT_SETTINGS: RenderSettings = {
  output_format: "mp4",
  move_delay: 1.5,
  board_theme: "green",
  piece_set: "staunton",
  board_size: 800,
  show_coordinates: true,
  show_player_names: true,
  show_result: true,
  show_comments: true,
  show_eval_bar: false,
  flip_board: false,
  background_music: null,
  sound_effects: true,
  highlight_last_move: true,
  game_index: 0,
  commentary_style: "none" as const,
  show_move_arrow: true,
  show_nag: true,
  show_captured_pieces: true,
  show_opening_name: true,
};

interface Store extends AppState {
  // Pagination state
  totalGames: number;
  currentPage: number;
  pageSize: number;
  pgnFile: File | null;

  setInputSource: (s: InputSource) => void;
  setPgnFile: (f: File | null) => void;
  setUrl: (url: string) => void;
  setGames: (games: GameInfo[], total?: number, page?: number) => void;
  setSelectedGame: (index: number) => void;
  updateSettings: (patch: Partial<RenderSettings>) => void;
  setJob: (job: RenderJobResponse | null) => void;
  setPage: (page: number) => void;
  reset: () => void;
}

const INITIAL: AppState & { totalGames: number; currentPage: number; pageSize: number } = {
  inputSource: "file",
  pgnFile: null,
  url: "",
  games: [],
  gameData: null,
  settings: DEFAULT_SETTINGS,
  job: null,
  totalGames: 0,
  currentPage: 0,
  pageSize: 50,
};

export const useStore = create<Store>((set, get) => ({
  ...INITIAL,

  setInputSource: (inputSource) => set({ inputSource }),
  setPgnFile: (pgnFile) => set({ pgnFile }),
  setUrl: (url) => set({ url }),

  setGames: (games, total?, page?) =>
    set({
      games,
      gameData: games[0] ?? null,
      totalGames: total ?? games.length,
      currentPage: page ?? 0,
      settings: { ...get().settings, game_index: 0 },
    }),

  setSelectedGame: (index) => {
    const games = get().games;
    if (games[index]) {
      set({ gameData: games[index], settings: { ...get().settings, game_index: index } });
    }
  },

  updateSettings: (patch) =>
    set((s) => ({ settings: { ...s.settings, ...patch } })),

  setJob: (job) => set({ job }),

  setPage: (page) => set({ currentPage: page }),

  reset: () => set({ ...INITIAL }),
}));
