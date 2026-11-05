# neural-mesh-gia

**Intelligence backend components for AI-agent risk scoring** — analysis pipelines that turn agent activity and exposure data into explainable underwriting recommendations.

Insurance underwriters are being asked to price a risk they have no tooling for: autonomous AI agents that hold credentials, move money and act on production systems. This repository is the backend engineering for that problem — the scoring, contract and audit components of **Minogan**, an insurtech platform that scores AI-agent risk for insurers under a "recommend, don't insure" doctrine: the system produces an explainable recommendation; the underwriting decision stays with the insurer.

It is a component codebase, not a finished product: the reusable backend pieces live here, developed and tested as a Python package.

## The Minogan scoring component

`src/neural_mesh/minogan/` is the most product-shaped part of the repository:

- **`contract.py`** — the scoring contract: what an evaluation request must contain and what a well-formed recommendation looks like, validated before anything is scored.
- **`scorer.py`** — the scoring engine: turns an agent's declared capabilities, access and exposure into a risk score with the reasoning attached, so a recommendation can be explained to an underwriter, not just produced.
- **`ledger.py`** — every evaluation is written to a ledger that can be replayed and verified (`mesh minogan verify --root /data --replay`), so a score quoted later can be re-derived and audited rather than trusted.
- **`service.py`** — an HTTP service wrapper with per-tenant token authentication (tenants hold hashed tokens; unauthenticated requests are rejected).
- **`canonical.py` / `memory.py`** — canonical serialization of evaluation inputs and the component's working memory.

`deploy/minogan/` contains a container image for this service (slim Python 3.13, non-root, loopback bind, healthcheck) with a local smoke test. **It is a deployment proposal: nothing in `deploy/` has been deployed or pushed to a registry.**

## The wider mesh package

The scoring component grew out of a broader research codebase for networks of cooperating agents, which is the rest of `src/neural_mesh/`:

- **Identity & audit** — `identity/`, `git_audit.py`, `tags.py`.
- **Routing & network** — `router/`, `network/`, `clock/`.
- **Observation** — `obs/`, `obs_peers.py`, `obsidian.py`.
- **Safety research** — `safety.py`, `fence/`, `minority/`, `cram/`.
- **Simulation** — `digital_twin.py`, `twin/`: a digital-twin model of mesh topologies.
- **Lifecycle** — `checkpoint.py`, `recovery/`, `status.py`, `status_snapshot.py`, `packaging/`.
- **Benchmarks** — `benchmark/`: local microbenchmarks of the mesh primitives (see the perf-research markers in `pyproject.toml`).

## Layout

```
src/neural_mesh/     the package (CLI entry point: `mesh`)
  minogan/           scoring contract, scorer, ledger, service
tests/               pytest suite
deploy/minogan/      container proposal for the scoring service (not deployed)
notebooks/           analysis notebooks
experiments/         research experiments
docs/                design and planning documents
```

## Development

- Python ≥ 3.10; core dependencies are `pydantic` and `networkx`.
- Optional extras: `distributed` (Ray), `ml` (PyTorch), `telemetry` (OpenTelemetry), `dev` (pytest, pytest-cov, ruff).
- Install for development: `pip install -e ".[dev]"`, then run `pytest`.

## Status

Active research and development (package version 0.18.0). The scoring component's service image exists as a local, smoke-tested proposal only. Root-level cycle and status files are internal development records from a checkpoint-driven process; the engineering record they form is part of how this codebase was built, but they are not product documentation — this README and `docs/` are.

## Author

Joan Barrios — Miami, Florida, USA · ES/EN
