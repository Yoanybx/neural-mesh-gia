# TEST STATUS

**Checkpoint:** CP-0088 OPEN (P0.1–P0.7 done; P0 complete)  
**Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider -rfs`  
**Pytest:** 1440 passed / 17 known-failed / 3 skipped (2026-10-18 02:43 EDT; +143 CP-0088 tests: contract 46, scorer parity 13, agent memory 21, service 28, score ledger 30, deploy proposal 5)
**Previous:** 1435 / 17 / 3 (02:45 EDT)
**Previous:** 1405 / 17 / 3 (02:19 EDT)
**Previous:** 1376 / 17 / 3 (02:08 EDT)
**Previous:** 1356 / 17 / 3 (01:58 EDT)
**Previous:** 1297 / 17 / 3 (01:48 EDT, after `git checkout -- dist`)
**Minogan only:** `.venv/bin/python -m pytest -q -m minogan_cp0088` → 143 passed  
**Baseline:** 1314 passed / 0 failed / 3 skipped (CP-0087)  
**Skipped:** 3 opt-in real-HTTP tests (R2 / R3 / Gate6 incr).

## P0.5 latency (local loopback, 200-event / 71 KB ScorerInput, every request appends to AgentMemory)

`.venv/bin/python scripts/minogan/bench_service.py -n 300` → bench 300 req: p50 20.95 ms / p95 26.95 ms; 1000 req (1000-record memory): p50 37.24 / p95 61.43 ms; pytest 60 req p95 33–42 ms. With the P0.6 score ledger (3 more CAS puts + 2 head writes per request): 300 req p50 31.84 / p95 45.81 / p99 54.84 ms. Target p95 < 300 ms. Latency grows with records in the agent's 90-day window.

## Known failures (17) — accepted, intentionally not fixed

Cause: the **untracked** frozen release artefacts under `dist/releases/` (0.16.3 `SIGNOFF.json`, `neural-mesh-gia-single-node-0.16.3.tar.gz`, 0.17.0 / 0.18.0 archives) were lost when the workspace was re-materialised on 2026-10-17 (see CURRENT_STATE.md). They are **intentionally NOT rebuilt**: re-minting would create new hashes for frozen releases and rewrite audit history (operator decision, option A, 2026-10-18).

Known-failing tests:
- `tests/test_017_signoff_cycle32.py` (6): signoff_pass_real_repo, archive_builds_without_tag, archive_mock_tag, script_cli_signoff, no_0163_reopen_and_no_h_impl, post_signoff_monitor_once
- `tests/test_018_signoff_cycle42.py` (6): signoff_pass_real_repo, archive_builds_without_tag, archive_mock_tag, script_cli_signoff, no_prior_reopen_and_no_gia, post_signoff_monitor_once
- `tests/test_018_bootstrap_cycle33.py::test_017_release_archive_and_tag_untouched`
- `tests/test_019_bootstrap_plan_cycle43.py::test_prior_018_release_and_tags_untouched`
- `tests/test_quickstart_cycle31.py` (3): release_artifacts_referenced_exist, helper_dry_run_pass, helper_help_and_default_is_dry_run

Any failure outside this list is a real regression.

## dist/ (operator option A, 2026-10-18)

Only the 4 **tracked** files were restored with `git checkout -- dist`; git blob hashes verified equal to HEAD:
| File | git blob | sha256 |
|------|----------|--------|
| `dist/releases/0.16.3/DEBT_GATE_REVIEW.json` | `c9f2e8a7` | `7e1881ef…978146` |
| `dist/releases/0.16.3/MONITOR.json` | `4e23ae10` | `1051696c…50e018` |
| `dist/releases/0.16.3/monitor_history.jsonl` | `b5f707ad` | `68381b64…3caf02` |
| `dist/releases/m1-no-consensus-n2-scope/M1_NO_CONSENSUS_N2_SCOPE.json` | `37f5920c` | `6c714c89…f971` |

Test hygiene: the suite writes into `dist/releases/0.16.3/` and `.project_state/*SIGNOFF*.json` / `post_rc_watch_report.json`; after each run, revert with `git clean -fdXq dist && git checkout -- dist` and restore `.project_state` from a pre-run copy.

**Env:** `.venv/` recreated 2026-10-18 (`uv venv .venv && uv pip install -e ".[dev]"`; pydantic 2.14.1, pytest 9.1.1).
