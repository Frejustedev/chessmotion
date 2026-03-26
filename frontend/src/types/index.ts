// ── Enums ───────────────────────────────────────────────────────────────────────
export type OutputFormat = "mp4" | "gif";
export type BoardTheme = "wood" | "green" | "dark" | "blue" | "purple";
export type PieceSet = "staunton" | "neo" | "alpha" | "merida";
export type RenderJobStatus = "queued" | "processing" | "done" | "error";
export type CommentaryStyle = "none" | "grandmaster" | "casual" | "coach";

// ── Render Settings ─────────────────────────────────────────────────────────────
export interface RenderSettings {
  output_format: OutputFormat;
  move_delay: number;
  board_theme: BoardTheme;
  piece_set: PieceSet;
  board_size: number;
  show_coordinates: boolean;
  show_player_names: boolean;
  show_result: boolean;
  show_comments: boolean;
  show_eval_bar: boolean;
  flip_board: boolean;
  background_music: string | null;
  sound_effects: boolean;
  highlight_last_move: boolean;
  game_index: number;
  commentary_style: CommentaryStyle;
  show_move_arrow: boolean;
  show_nag: boolean;
  show_captured_pieces: boolean;
  show_opening_name: boolean;
}

// ── Game Data ───────────────────────────────────────────────────────────────────
export interface PlayerInfo {
  name: string;
  rating?: number;
  title?: string;
}

export interface MoveInfo {
  san: string;
  uci: string;
  fen_after: string;
  comment?: string;
  eval_score?: number;
  clock?: string;
}

export interface GameInfo {
  white: PlayerInfo;
  black: PlayerInfo;
  result: string;
  event?: string;
  site?: string;
  date?: string;
  opening?: string;
  moves: MoveInfo[];
  starting_fen: string;
  total_games: number;
}

// ── Render Job ──────────────────────────────────────────────────────────────────
export interface RenderJobResponse {
  job_id: string;
  status: RenderJobStatus;
  progress: number;
  message: string;
  download_url?: string;
}

// ── App State ───────────────────────────────────────────────────────────────────
export type InputSource = "file" | "url";

export interface AppState {
  inputSource: InputSource;
  pgnFile: File | null;
  url: string;
  games: GameInfo[];          // full list for multi-game PGNs
  gameData: GameInfo | null;  // currently selected game
  settings: RenderSettings;
  job: RenderJobResponse | null;
}
