# syntax=docker/dockerfile:1
# Mesh Minogan scorer service — CP-0088 P0.7 (PROPOSAL ONLY: not deployed, no registry push).
#
# Build (from repo root):  docker build -f deploy/minogan/Dockerfile -t mesh-minogan:local .
# Run (local smoke):       see deploy/minogan/README.md
#
# Design:
# - slim Python, multi-stage (wheel built in builder; runtime has no compiler / pip cache / source tree)
# - non-root uid 10001, read-only root FS friendly (only /data is written)
# - /data   = persistent volume: AgentMemory + score ledger + C-RAM (single writer: run exactly ONE replica)
# - tokens  = secret file mounted at /run/secrets/minogan_tokens (sha256 hashes only; never baked into the image)
# - the service binds 127.0.0.1 ONLY (code guard unchanged). Exposure is done by a co-located connector sharing the
#   network namespace (cloudflared sidecar / same container), see docs/planning/CP_0088_P0_7_DEPLOY_PROPOSAL.md.
# - HEALTHCHECK probes 127.0.0.1:8787/health from inside the container (works with the loopback bind).
#
# Pin the base image by digest at build time (operator step): FROM python:3.13-slim@sha256:<digest>

ARG PYTHON_IMAGE=python:3.13-slim

FROM ${PYTHON_IMAGE} AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip wheel --wheel-dir /wheels .

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MESH_MINOGAN_TOKENS_FILE=/run/secrets/minogan_tokens \
    MESH_MINOGAN_PORT=8787
RUN groupadd --system --gid 10001 mesh \
 && useradd --system --uid 10001 --gid mesh --home-dir /nonexistent --shell /usr/sbin/nologin mesh \
 && mkdir -p /data \
 && chown mesh:mesh /data \
 && chmod 0700 /data
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links /wheels neural-mesh-gia \
 && rm -rf /wheels
USER 10001:10001
WORKDIR /data
VOLUME ["/data"]
# No EXPOSE: nothing listens on a routable interface. A connector in the same network namespace reaches 127.0.0.1:8787.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import json,os,sys,urllib.request as u; r=u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('MESH_MINOGAN_PORT','8787'), timeout=2); sys.exit(0 if json.load(r).get('ok') else 1)"]
# SIGINT → KeyboardInterrupt → serve() closes the socket cleanly (state is kill -9 safe regardless).
STOPSIGNAL SIGINT
ENTRYPOINT ["mesh", "minogan", "serve", "--host", "127.0.0.1", "--memory-root", "/data"]
CMD ["--port", "8787"]
