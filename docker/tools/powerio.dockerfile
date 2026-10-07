# Build a reviewed source revision; POWERIO_REF must be an immutable commit.
FROM docker.io/library/rust:1-bookworm AS wheel
ARG POWERIO_REF=39ca2dcffef47e0437ebadbb8e1aa9f88a0bbcc2
RUN test -n "$POWERIO_REF"
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
RUN git clone https://github.com/eigenergy/powerio.git /src && cd /src && git checkout "$POWERIO_REF"
WORKDIR /src
RUN uv python install 3.14 && uv venv --python 3.14 /buildenv && uv pip install --python /buildenv/bin/python maturin==1.15.0
RUN /buildenv/bin/maturin build --release --locked --out /wheels --interpreter /buildenv/bin/python

FROM localhost/cim-bench/base:latest
WORKDIR /app
COPY tool-configs/powerio/pyproject.toml .
COPY --from=wheel /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/uv uv venv --python 3.14 && uv pip install --python .venv/bin/python -r pyproject.toml /wheels/*.whl
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /benchmarks
CMD ["pytest", "powerio_svedala_benchmark.py", "--benchmark-only", "--benchmark-json=/output/powerio_svedala_benchmark.json"]
