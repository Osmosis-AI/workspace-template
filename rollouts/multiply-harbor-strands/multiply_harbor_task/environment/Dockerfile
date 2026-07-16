FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "osmosis-ai[server]>=0.2.28" \
    httpx \
    fastapi \
    uvicorn \
    harbor \
    strands-agents \
    strands-agents-tools

COPY workspace /workspace

CMD ["sleep", "infinity"]
