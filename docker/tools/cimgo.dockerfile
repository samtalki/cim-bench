FROM docker.io/golang:1.25-bookworm AS builder
ARG CIMGO_VERSION=v0.0.5
RUN apt-get update && apt-get install -y --no-install-recommends git protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch ${CIMGO_VERSION} --recurse-submodules \
    https://github.com/m-mirz/cimgo.git /src
WORKDIR /src
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go
RUN go generate ./...
RUN go build -o /cimcli ./cmd/cimcli

FROM localhost/cim-bench/base:latest
COPY --from=builder /cimcli /usr/local/bin/cimcli
WORKDIR /app
COPY tool-configs/cimgo/pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv uv sync
ENV CIMGO_BIN="/usr/local/bin/cimcli"
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /benchmarks
