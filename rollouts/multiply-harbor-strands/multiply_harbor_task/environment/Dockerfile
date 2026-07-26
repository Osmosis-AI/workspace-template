FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# harbor is intentionally absent: osmosis-ai pins the version this sandbox must
# agree with, so naming it again could only disagree.
RUN pip install --no-cache-dir \
    "osmosis-ai[server]>=0.2.30" \
    httpx \
    fastapi \
    uvicorn \
    strands-agents \
    strands-agents-tools

COPY workspace /workspace

CMD ["sleep", "infinity"]
