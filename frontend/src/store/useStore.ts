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
};

interface Store extends AppState {
  setInputSource: (s: InputSource) => void;
  setPgnFile: (f: File | null) => void;
  setUrl: (url: string) => void;
  setGames: (games: GameInfo[]) => void;
  setSelectedGame: (index: number) => void;
  updateSettings: (patch: Partial<RenderSettings>) => void;
  setJob: (job: RenderJobResponse | null) => void;
  reset: () => void;
}

const INITIAL: AppState = {
  inputSource: "file",
  pgnFile: null,
  url: "",
  games: [],
  gameData: null,
  settings: DEFAULT_SETTINGS,
  job: null,
};

export const useStore = create<Store>((set, get) => ({
  ...INITIAL,

  setInputSource: (inputSource) => set({ inputSource }),
  setPgnFile: (pgnFile) => set({ pgnFile }),
  setUrl: (url) => set({ url }),

  setGames: (games) =>
    set({
      games,
      gameData: games[0] ?? null,
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

  reset: () => set({ ...INITIAL }),
}));
