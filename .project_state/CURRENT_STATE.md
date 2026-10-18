# CURRENT STATE

**Cycle:** 84  
**Checkpoint:** CP-0088 OPEN — camino Minogan (P0.1–P0.5 DONE; P0.6–P0.7 not started) · prior CP-0087 SEALED (R5 F4 product ACK SIGNED + LIVE product path)  
**CP-0087 tip:** `21f9e48` (state truth-up `b9ffe44`; chain `6aba4c7` CP-0087 R5 → `88f1276` residual tests → `3a70a50` / `21f9e48` docs)  
**Theme:** camino_minogan (Mesh = Minogan.ai intelligence backend; `docs/planning/CP_0088_CAMINO_MINOGAN.md`) · prior: l_judge_full_adapter_live_rv (R0–R5 DONE, streaming DEFER)  
**Version:** 0.18.0 HELD  
**Pytest:** 1405 passed / 17 known-failed / 3 skipped (2026-10-18; failures = lost untracked release artefacts, accepted; see TEST_STATUS.md)  
**Date:** 2026-10-18 02:19 EDT  
**live:** `LIVE_API_ENABLED=True` on CP-0087 product modules only (peer / canary / LHT / multi-canary / R1–R4 / Gate6 incr); others False; I5 / RefuseTransport gate network  
**M1:** NO_CONSENSUS_YET (PERMANENT under N=2 scope)  
**HOLD:** Active · D3 NOT ACKed · MESH_PERF_EXPERIMENTAL OFF · pkg0190 NOT_OPENED  
**NO_HELD:** unchanged (GIA / Raft / N>2 / train / economy) · **SaaS un-PARKED only for the CP-0088 Minogan path** (operator 2026-10-18)  
**Minogan honesty:** contract (`neural_mesh/minogan/contract.py`) + deterministic scorer v0 (parity with pilot score_v0.3) + AgentMemory on C-RAM (`ObjectType.MEMORY` now used; per-(tenant, agent) hash chain, day-bucket index, kill -9 safe) + local loopback HTTP service (`mesh minogan serve`, stdlib, not deployed) exist; NO score ledger/replay, deployment, hard multi-tenancy or calibration yet; GoalRegistry/EvidenceLedger still in-memory mocks  
**Tags:** v0.16.3 / v0.17.0 / v0.18.0 untouched

## dist/ shows deleted — root cause (2026-10-18)

- `.gitignore` ignores `dist/` (CP-0024), but 4 files were force-added: `dist/releases/0.16.3/{DEBT_GATE_REVIEW.json,MONITOR.json,monitor_history.jsonl}` (`f54c8f0`, CP-0029) and `dist/releases/m1-no-consensus-n2-scope/M1_NO_CONSENSUS_N2_SCOPE.json` (`b3e84fb`, CP-0074).
- The workspace was re-materialised on **2026-10-17 12:15–12:17 EDT** (every file mtime in the tree falls in that window; reflog ends 2026-09-28 at `21f9e48`). The copy did **not** include `dist/` or `.venv/` (other ignored dirs such as `experiments/`, `.cram/` did survive). So the whole `dist/` tree vanished → the 4 tracked files read as ` D`.
- No commit, clean script or build deleted them (`git log -- dist` has only the two adds; no code path `rmtree`s `dist/releases`).
- Collateral: untracked frozen release artefacts (`dist/releases/0.16.3/*.tar.gz`, `SIGNOFF.json`, `0.17.0/`, `0.18.0/` archives) are also gone and are **not** recoverable from git → 17 suite failures (`test_017_signoff_cycle32`, `test_018_signoff_cycle42`, `test_018_bootstrap_cycle33`, `test_019_bootstrap_plan_cycle43`, `test_quickstart_cycle31`).
- **Operator option A (2026-10-18):** the 4 tracked files were restored with `git checkout -- dist` (blob hashes verified = HEAD). The lost untracked release archives are **intentionally not rebuilt** (would re-hash frozen releases / rewrite audit history). 17 failures are known and accepted (TEST_STATUS.md).
- Separate pre-existing debt: the suite writes into the real repo (`dist/releases/0.16.3/`, `.project_state/THEME_SIGNOFF_0.17.0.json`, `RELEASE_SIGNOFF_0.16.3.json`, `post_rc_watch_report.json`). The uncommitted diffs in the two SIGNOFF mirrors (dated 2026-09-29, `tip: cli017`, `pytest_count: 50`) are that pollution, not real signoffs; left uncommitted.
