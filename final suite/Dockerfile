FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl \
        libexpat1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY backend/firefighter_engine.py \
     backend/main.py \
     backend/map_to_graph.py \
     backend/osm_cache.py \
     backend/sim_with_states.py \
     backend/tile_cache.py \
     /app/

# Pre-baked cache so the default Köyceğiz–Marmaris demo renders without
# hitting Overpass or downloading the 93 MB ESA WorldCover tile on first
# user click. The tile is fetched at *build* time (runs on the host's
# builder, not the user's machine) so the git repo stays small enough to
# push without git-lfs.
RUN mkdir -p /app/cache/tiles /app/cache/osm /app/cache/graphs && \
    curl -fsSL -o /app/cache/tiles/N36E027.tif \
      "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36E027_Map.tif"
COPY backend/cache/osm/ /app/cache/osm/

# HF Spaces sets PORT=8080 via the README app_port field; keep the same
# default so this image is also runnable locally / on Cloud Run / on Fly.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
