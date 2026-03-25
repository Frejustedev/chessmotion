from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import games, render

app = FastAPI(
    title=settings.APP_NAME,
    description="Convert chess games to MP4 videos or animated GIFs",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────────
origins = settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app" if "*" not in origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (serve generated videos/GIFs) ───────────────────────────────────
app.mount("/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")

# ── API Routers ───────────────────────────────────────────────────────────────────
app.include_router(games.router, prefix="/api/games", tags=["Games"])
app.include_router(render.router, prefix="/api/render", tags=["Render"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
