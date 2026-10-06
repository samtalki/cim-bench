FROM localhost/cim-bench/base:latest

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies (wheel cache persists across builds via cache mount)
COPY tool-configs/triplets/pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv uv sync

ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /benchmarks

CMD ["pytest", "triplets_svedala_benchmark.py", "--benchmark-only", \
     "--benchmark-json=/output/triplets_svedala_benchmark.json"]
