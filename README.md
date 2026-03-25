# ♟ ChessMotion

> Convert any chess game into a beautiful MP4 video or animated GIF.

## Status : All 6 steps complete ✅

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
python run.py
# → http://localhost:8000/api/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

## Project Structure

```
ChessMotion/
├── backend/
│   ├── app/
│   │   ├── api/routes/       ← FastAPI routers (games, render)
│   │   ├── core/             ← Settings / config
│   │   ├── models/           ← Pydantic schemas
│   │   └── services/         ← Business logic
│   │       ├── pgn_parser.py
│   │       ├── lichess_api.py
│   │       ├── chesscom_api.py
│   │       ├── board_renderer.py
│   │       └── video_engine.py
│   ├── assets/
│   │   ├── pieces/           ← Piece set PNGs (staunton, neo…)
│   │   └── sounds/           ← SFX + background music
│   ├── temp/                 ← Ephemeral render frames
│   ├── output/               ← Final MP4 / GIF files
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/              ← Next.js App Router pages
        ├── components/       ← UI components
        ├── hooks/            ← Custom React hooks
        ├── lib/              ← API client
        └── types/            ← TypeScript types
```

## Development Roadmap

| Étape | Description | Status |
|-------|-------------|--------|
| 1 | Initialisation & Architecture | ✅ Done |
| 2 | Backend – PGN Parsing + APIs | ✅ Done |
| 3 | Backend – Board Renderer (Pillow) | ✅ Done |
| 4 | Backend – Video Engine (MoviePy) | ✅ Done |
| 5 | Frontend – Full UI (Next.js + Tailwind) | ✅ Done |
| 6 | Full Integration | ✅ Done |
