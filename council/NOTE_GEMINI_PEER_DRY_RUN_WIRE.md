# NOTE — Google L_judge peer spike: eval dry-run wired (NOT Mesh live)

**Date:** 2026-09-28 ~18:40 EDT (ET)  
**Base tip:** `1e502c6`  
**Operator auth:** Si — wire mock peer for real Gemini free-tier call **only** under explicit dry-run flag

## Posture (unchanged / held)

| Flag / gate | Value |
|-------------|-------|
| Gate1 | SIGNED DISCUSS_ONLY |
| live | **DISABLED** |
| `LIVE_API_ENABLED` | **False** (constant untouched) |
| Mesh live L_judge adapter | **NOT_ENABLED** |
| Push / tags / secrets in git | **NONE** |

## What was wired

| Piece | Path / symbol |
|-------|----------------|
| Spike module | `src/neural_mesh/packaging/google_l_judge_peer_spike.py` |
| Transport | `GeminiFreeDryRunTransport` — network **only** if `dry_run_enabled=True` |
| Flag helpers | `gemini_dry_run_flag_enabled`, env `GEMINI_DRY_RUN=1`, CLI `--gemini-dry-run` |
| Secret load | Gate4 out-of-band file `/home/box/.config/neural-mesh/gemini.env` (`GEMINI_API_KEY`); handle id `mesh://secrets/judge/gemini-free@v1` |
| Model | `gemini-flash-latest` (v1beta `generateContent`) — matches dry-run evidence |
| Default | `MockGeminiPeerTransport` / `build_peer_spike()` — **no network** even if key file exists |
| Mesh live slot | Envelope `use_live_gemini` / `live_api_enabled` still → `RefuseTransport` / `PEER_LIVE_DISABLED` |

## How to invoke

```bash
# Mock only (default) — no network
.venv/bin/python -m neural_mesh.packaging.google_l_judge_peer_spike

# ONE real free-tier eval call (explicit flag)
.venv/bin/python -m neural_mesh.packaging.google_l_judge_peer_spike --gemini-dry-run

# Equivalent env form
GEMINI_DRY_RUN=1 .venv/bin/python -m neural_mesh.packaging.google_l_judge_peer_spike --gemini-dry-run
```

Optional: `--model gemini-flash-latest` (default), `--secret-env /home/box/.config/neural-mesh/gemini.env`, `--prompt 'Reply with exactly: MESH_DRY_RUN_OK'`.

## Fences still held

- Explicit flag required; key file alone → `PEER_DRY_RUN_FLAG_REQUIRED`, no socket.
- Key never committed; `.gitignore` covers `gemini.env` / `.config/neural-mesh/`.
- Response JSON is sanitized (no key echo); digest / usage / marker only.
- Does **not** enable Mesh live adapter, flip `LIVE_API_ENABLED`, start Gate5 canary, push, or retag.

## Related

- `council/NOTE_GEMINI_DRY_RUN.md` · `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `tests/test_google_l_judge_peer_spike.py`

---
*End NOTE_GEMINI_PEER_DRY_RUN_WIRE — live=DISABLED; LIVE_API_ENABLED False; eval dry-run flag only.*
