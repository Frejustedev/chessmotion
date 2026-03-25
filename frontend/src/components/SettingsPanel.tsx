"use client";
import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Film, Clock, Grid3x3, Volume2, BarChart2, MessageSquare, Upload, Loader2, CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";
import axios from "axios";
import { useStore } from "@/store/useStore";
import type { BoardTheme, PieceSet, OutputFormat, CommentaryStyle } from "@/types";

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

const COMMENTARY_STYLES: { value: CommentaryStyle; label: string; desc: string; icon: string }[] = [
  { value: "none",        label: "No commentary",   desc: "Silent – no text overlay",                    icon: "🔇" },
  { value: "grandmaster", label: "Grandmaster",      desc: "Formal, tactical chess analysis",             icon: "🏆" },
  { value: "casual",      label: "Casual / Fun",     desc: "Friendly & humorous, with emoji",             icon: "😄" },
  { value: "coach",       label: "Chess Coach",      desc: "Educational – explains concepts for learners",icon: "📚" },
];

export default function SettingsPanel() {
  const { settings, updateSettings } = useStore((s) => ({ settings: s.settings, updateSettings: s.updateSettings }));

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
            <button key={f} onClick={() => updateSettings({ output_format: f })}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold uppercase tracking-wide transition-all ${
                settings.output_format === f ? "bg-brand-600 text-white" : "bg-surface-50 text-slate-400 hover:text-white"
              }`}>{f}</button>
          ))}
        </div>
        <p className="text-xs text-slate-600 mt-1">
          {settings.output_format === "mp4" ? "H.264 + AAC — supports sound & commentary" : "Looping GIF — no audio, ideal for sharing"}
        </p>
      </Section>

      {/* Timing */}
      <Section icon={<Clock size={14} />} title="Timing">
        <SliderRow label="Delay between moves" value={settings.move_delay}
          min={0.5} max={6} step={0.5} format={(v) => `${v}s`}
          onChange={(v) => updateSettings({ move_delay: v })} />
        <SliderRow label="Board resolution" value={settings.board_size}
          min={400} max={1200} step={100} format={(v) => `${v}px`}
          onChange={(v) => updateSettings({ board_size: v })} />
      </Section>

      {/* Board Theme */}
      <Section icon={<Grid3x3 size={14} />} title="Board & Pieces">
        <div className="grid grid-cols-5 gap-2 mb-3">
          {THEMES.map((t) => (
            <button key={t.value} title={t.label} onClick={() => updateSettings({ board_theme: t.value })}
              className={`flex flex-col items-center gap-1 p-1.5 rounded-lg transition-all ${
                settings.board_theme === t.value ? "ring-2 ring-brand-500" : "hover:bg-white/5"
              }`}>
              <div className="grid grid-cols-2 rounded overflow-hidden w-8 h-8 border border-white/10">
                {[0,1,1,0].map((d, i) => <div key={i} style={{ background: d ? t.preview[1] : t.preview[0] }} />)}
              </div>
              <span className="text-[9px] text-slate-400">{t.label}</span>
            </button>
          ))}
        </div>
        <SelectRow label="Piece set" value={settings.piece_set} options={PIECE_SETS}
          onChange={(v) => updateSettings({ piece_set: v as PieceSet })} />
        <div className="mt-2 flex flex-col gap-2">
          <ToggleRow label="Flip board (Black POV)" checked={settings.flip_board} onChange={(v) => updateSettings({ flip_board: v })} />
          <ToggleRow label="Show coordinates" checked={settings.show_coordinates} onChange={(v) => updateSettings({ show_coordinates: v })} />
          <ToggleRow label="Highlight last move" checked={settings.highlight_last_move} onChange={(v) => updateSettings({ highlight_last_move: v })} />
        </div>
      </Section>

      {/* AI Commentary */}
      <Section icon={<MessageSquare size={14} />} title="AI Commentary">
        <div className="flex flex-col gap-1.5">
          {COMMENTARY_STYLES.map((s) => (
            <button key={s.value} onClick={() => updateSettings({ commentary_style: s.value })}
              className={`flex items-center gap-3 p-2.5 rounded-lg border text-left transition-all ${
                settings.commentary_style === s.value
                  ? "border-brand-500 bg-brand-600/15"
                  : "border-white/5 hover:border-white/15 hover:bg-white/5"
              }`}>
              <span className="text-lg shrink-0">{s.icon}</span>
              <div>
                <p className={`text-xs font-semibold ${settings.commentary_style === s.value ? "text-brand-300" : "text-slate-300"}`}>{s.label}</p>
                <p className="text-[10px] text-slate-600 leading-tight">{s.desc}</p>
              </div>
              {settings.commentary_style === s.value && <CheckCircle2 size={14} className="ml-auto text-brand-400 shrink-0" />}
            </button>
          ))}
        </div>
        {settings.commentary_style !== "none" && (
          <div className="mt-2 flex items-center gap-2">
            <ToggleRow label="Show on video frames" checked={settings.show_comments} onChange={(v) => updateSettings({ show_comments: v })} />
          </div>
        )}
      </Section>

      {/* Annotations */}
      <Section icon={<BarChart2 size={14} />} title="Annotations">
        <div className="flex flex-col gap-2">
          <ToggleRow label="Player names & ratings" checked={settings.show_player_names} onChange={(v) => updateSettings({ show_player_names: v })} />
          <ToggleRow label="Game result badge" checked={settings.show_result} onChange={(v) => updateSettings({ show_result: v })} />
          <ToggleRow label="Evaluation bar (Stockfish)" checked={settings.show_eval_bar} onChange={(v) => updateSettings({ show_eval_bar: v })} />
          {settings.show_eval_bar && (
            <p className="text-[10px] text-slate-600 ml-6 -mt-1">
              Requires Stockfish. Install it or set STOCKFISH_PATH in .env
            </p>
          )}
        </div>
      </Section>

      {/* Audio (MP4 only) */}
      {settings.output_format === "mp4" && (
        <Section icon={<Volume2 size={14} />} title="Audio">
          <ToggleRow label="Sound effects (move / capture / check)" checked={settings.sound_effects}
            onChange={(v) => updateSettings({ sound_effects: v })} />
          <div className="mt-3">
            <p className="text-xs text-slate-400 mb-2">Background music</p>
            <MusicUploader
              currentFile={settings.background_music}
              onUpload={(filename) => updateSettings({ background_music: filename })}
              onClear={() => updateSettings({ background_music: null })}
            />
          </div>
        </Section>
      )}
    </motion.div>
  );
}

// ── Music Uploader ──────────────────────────────────────────────────────────────

function MusicUploader({ currentFile, onUpload, onClear }: {
  currentFile: string | null;
  onUpload: (filename: string) => void;
  onClear: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await axios.post("/api/render/upload-music", form);
      onUpload(data.filename);
      toast.success(`Music uploaded: ${file.name} (${data.size_kb} KB)`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (currentFile) {
    return (
      <div className="flex items-center gap-2 bg-green-600/10 border border-green-600/20 rounded-lg px-3 py-2">
        <CheckCircle2 size={14} className="text-green-400 shrink-0" />
        <span className="text-xs text-green-300 flex-1 truncate">{currentFile}</span>
        <button onClick={onClear} className="text-slate-500 hover:text-white text-xs px-2 py-0.5 rounded hover:bg-white/5">✕</button>
      </div>
    );
  }

  return (
    <div>
      <input ref={inputRef} type="file" accept=".mp3,.wav,.ogg,.flac,.aac,.m4a" className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
      <button onClick={() => inputRef.current?.click()} disabled={uploading}
        className="w-full flex items-center justify-center gap-2 border border-dashed border-slate-600 hover:border-brand-500 rounded-lg py-2.5 text-xs text-slate-400 hover:text-white transition-all disabled:opacity-50">
        {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
        {uploading ? "Uploading…" : "Upload from your PC (MP3, WAV, OGG…)"}
      </button>
      <p className="text-[10px] text-slate-700 mt-1 text-center">Max 50 MB · loops automatically</p>
    </div>
  );
}

// ── Shared sub-components ────────────────────────────────────────────────────────

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
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none bg-slate-700 accent-brand-500 cursor-pointer" />
    </div>
  );
}

function SelectRow({ label, value, options, onChange }: {
  label: string; value: string; options: { value: string; label: string }[]; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-xs text-slate-400 mb-1 block">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input-field text-sm bg-surface-50">
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center justify-between cursor-pointer gap-3 py-0.5">
      <span className="text-xs text-slate-400">{label}</span>
      <button role="switch" aria-checked={checked} onClick={() => onChange(!checked)}
        className={`relative w-9 h-5 rounded-full transition-colors duration-200 shrink-0 ${checked ? "bg-brand-600" : "bg-slate-700"}`}>
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${checked ? "translate-x-4" : "translate-x-0"}`} />
      </button>
    </label>
  );
}
