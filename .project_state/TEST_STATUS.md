# TEST STATUS

**Checkpoint:** CP-0087 (tip `21f9e48`)  
**Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider -rfs`  
**Pytest:** 1297 passed / 17 failed / 3 skipped (2026-10-18 01:33 EDT, 124 s)  
**Baseline:** 1314 passed / 0 failed / 3 skipped (CP-0087)  
**Failures:** all 17 = missing untracked `dist/releases/*` artefacts after the 2026-10-17 workspace re-materialisation (see CURRENT_STATE.md). Not code regressions.  
**Skipped:** 3 opt-in real-HTTP tests (R2 / R3 / Gate6 incr).  
**Note:** `.venv/` was also lost; recreated 2026-10-18 with `uv venv .venv && uv pip install -e ".[dev]"` (pydantic 2.14.1, pytest 9.1.1).  
