"use client";
import { motion } from "framer-motion";
import { Film, Clock, Grid3x3, Volume2, BarChart2, FlipVertical2 } from "lucide-react";
import { useStore } from "@/store/useStore";
import type { BoardTheme, PieceSet, OutputFormat } from "@/types";

const THEMES: { value: BoardTheme; label: string; preview: [string, string] }[] = [
  { value: "green",  label: "Classic",  preview: ["#eeeed2", "#769656"] },
  { value: "wood",   label: "Wood",     preview: ["#f0d9b5", "#b58863"] },
  { value: "dark",   label: "Dark",     preview: ["#5a5a6e", "#282837"] },
  { value: "blue",   label: "Blue",     preview: ["#dee7f3", "#5279aa"] },
  { value: "purple", label: "Purple",   preview: ["#ebdcf5", "#825aa0"] },
];

const PIECE_SETS: { value: PieceSet; label: string }[] = [
  { value: "staunton", label: "Staunton (cburnett)" },
  { value: "neo",      label: "Neo" },
  { value: "alpha",    label: "Alpha" },
  { value: "merida",   label: "Merida" },
];

export default function SettingsPanel() {
  const { settings, updateSettings } = useStore((s) => ({
    settings: s.settings,
    updateSettings: s.updateSettings,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.1 }}
      className="glass rounded-xl p-5 flex flex-col gap-5 overflow-y-auto max-h-[calc(100vh-120px)]"
    >
      {/* Output Format */}
      <Section icon={<Film size={14} />} title="Output">
        <div className="flex gap-2">
          {(["mp4", "gif"] as OutputFormat[]).map((f) => (
            <button
              key={f}
              onClick={() => updateSettings({ output_format: f })}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold uppercase tracking-wide transition-all ${
                settings.output_format === f
                  ? "bg-brand-600 text-white"
                  : "bg-surface-50 text-slate-400 hover:text-white"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="mt-2 p-2 bg-surface-50 rounded-lg text-xs text-slate-400">
          {settings.output_format === "mp4"
            ? "H.264 video with AAC audio. Best quality, supports sound effects."
            : "Looping animation. Smaller file, no audio, ideal for sharing."}
        </div>
      </Section>

      {/* Timing */}
      <Section icon={<Clock size={14} />} title="Timing">
        <SliderRow
          label="Delay between moves"
          value={settings.move_delay}
          min={0.5} max={6} step={0.5}
          format={(v) => `${v}s`}
          onChange={(v) => updateSettings({ move_delay: v })}
        />
        <SliderRow
          label="Board resolution"
          value={settings.board_size}
          min={400} max={1200} step={100}
          format={(v) => `${v}px`}
          onChange={(v) => updateSettings({ board_size: v })}
        />
      </Section>

      {/* Board Theme */}
      <Section icon={<Grid3x3 size={14} />} title="Board & Pieces">
        <div className="grid grid-cols-5 gap-2 mb-3">
          {THEMES.map((t) => (
            <button
              key={t.value}
              title={t.label}
              onClick={() => updateSettings({ board_theme: t.value })}
              className={`flex flex-col items-center gap-1 p-1.5 rounded-lg transition-all ${
                settings.board_theme === t.value ? "ring-2 ring-brand-500" : "hover:bg-white/5"
              }`}
            >
              <div className="grid grid-cols-2 rounded overflow-hidden w-8 h-8 border border-white/10">
                {[0,1,1,0].map((dark, i) => (
                  <div key={i} style={{ background: dark ? t.preview[1] : t.preview[0] }} />
                ))}
              </div>
              <span className="text-[9px] text-slate-400">{t.label}</span>
            </button>
          ))}
        </div>

        <SelectRow
          label="Piece set"
          value={settings.piece_set}
          options={PIECE_SETS}
          onChange={(v) => updateSettings({ piece_set: v as PieceSet })}
        />

        <div className="mt-2 flex flex-col gap-2">
          <ToggleRow label="Flip board (Black POV)" checked={settings.flip_board}
            onChange={(v) => updateSettings({ flip_board: v })} />
          <ToggleRow label="Show coordinates" checked={settings.show_coordinates}
            onChange={(v) => updateSettings({ show_coordinates: v })} />
          <ToggleRow label="Highlight last move" checked={settings.highlight_last_move}
            onChange={(v) => updateSettings({ highlight_last_move: v })} />
        </div>
      </Section>

      {/* Annotations */}
      <Section icon={<BarChart2 size={14} />} title="Annotations">
        <div className="flex flex-col gap-2">
          <ToggleRow label="Player names & ratings" checked={settings.show_player_names}
            onChange={(v) => updateSettings({ show_player_names: v })} />
          <ToggleRow label="Game result badge" checked={settings.show_result}
            onChange={(v) => updateSettings({ show_result: v })} />
          <ToggleRow label="PGN comments" checked={settings.show_comments}
            onChange={(v) => updateSettings({ show_comments: v })} />
          <ToggleRow label="Evaluation bar (Stockfish)" checked={settings.show_eval_bar}
            onChange={(v) => updateSettings({ show_eval_bar: v })} />
        </div>
      </Section>

      {/* Audio (MP4 only) */}
      {settings.output_format === "mp4" && (
        <Section icon={<Volume2 size={14} />} title="Audio">
          <ToggleRow label="Sound effects (move / capture / check)" checked={settings.sound_effects}
            onChange={(v) => updateSettings({ sound_effects: v })} />
          <div className="mt-2">
            <label className="text-xs text-slate-400 mb-1 block">Background music (filename)</label>
            <input
              className="input-field text-sm"
              placeholder="e.g. chill.mp3  (place in assets/sounds/)"
              value={settings.background_music ?? ""}
              onChange={(e) => updateSettings({ background_music: e.target.value || null })}
            />
          </div>
        </Section>
      )}
    </motion.div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────────

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-brand-500">{icon}</span>
        <span className="section-title mb-0">{title}</span>
      </div>
      {children}
    </div>
  );
}

function SliderRow({ label, value, min, max, step, format, onChange }: {
  label: string; value: number; min: number; max: number; step: number;
  format: (v: number) => string; onChange: (v: number) => void;
}) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-400">{label}</span>
        <span className="text-brand-400 font-mono font-semibold">{format(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none bg-slate-700 accent-brand-500 cursor-pointer"
      />
    </div>
  );
}

function SelectRow({ label, value, options, onChange }: {
  label: string; value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-xs text-slate-400 mb-1 block">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field text-sm bg-surface-50"
      >
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: {
  label: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between cursor-pointer gap-3 py-0.5">
      <span className="text-xs text-slate-400">{label}</span>
      <button
        role="switch" aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-9 h-5 rounded-full transition-colors duration-200 shrink-0 ${
          checked ? "bg-brand-600" : "bg-slate-700"
        }`}
      >
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? "translate-x-4" : "translate-x-0"
        }`} />
      </button>
    </label>
  );
}
