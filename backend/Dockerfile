FROM python:3.11-slim

# System dependencies for cairosvg (cairo, pango) — required
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Stockfish — optional, installed separately so its failure doesn't break the image
RUN apt-get update && apt-get install -y --no-install-recommends stockfish \
    && rm -rf /var/lib/apt/lists/* \
    || (rm -rf /var/lib/apt/lists/* && echo "Stockfish not available - eval bar will be disabled")

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p temp output assets/pieces assets/sounds

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
