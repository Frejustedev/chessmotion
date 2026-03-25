FROM python:3.11-slim

# System dependencies: libcairo for cairosvg, ffmpeg for moviepy fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p temp output assets/pieces assets/sounds

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
