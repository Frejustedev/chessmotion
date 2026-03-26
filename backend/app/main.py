import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# ── Simple in-memory rate limiter ────────────────────────────────────────────────
_RATE_LIMIT_WINDOW = 60   # seconds
_RATE_LIMIT_MAX    = 10   # max render jobs per IP per window
_render_calls: dict[str, list[float]] = defaultdict(list)

@app.middleware("http")
async def rate_limit_renders(request: Request, call_next):
    if request.url.path in ("/api/render/start", "/api/render/batch-start"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        calls = _render_calls[ip]
        # Purge timestamps outside the window
        _render_calls[ip] = [t for t in calls if now - t < _RATE_LIMIT_WINDOW]
        if len(_render_calls[ip]) >= _RATE_LIMIT_MAX:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit: max {_RATE_LIMIT_MAX} renders per minute."},
            )
        _render_calls[ip].append(now)
    return await call_next(request)

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
