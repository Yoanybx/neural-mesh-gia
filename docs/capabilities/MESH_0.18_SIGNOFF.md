# Mesh 0.18 Theme-Set Signoff

**Capability:** `MESH_0.18_SIGNOFF`  
**Cycle / Checkpoint:** 42 / CP-0046  
**Version:** 0.18.0 (H1..H8 theme set CLOSED/FROZEN; package held at 0.18.0)  
**Channel:** `0.18.x` / schema `mesh.bundle/v1`  
**Scope:** signoff/closeout only — do not invent GIA / N>2 / train-70B unlocks

## Purpose

Close the frozen **0.18** nervous-hardening theme set after H1..H8 all shipped:

| # | Theme | CP |
|---|-------|----|
| H1 | identity + attestation + tiers | CP-0038 |
| H2 | recovery + rebuild | CP-0039 |
| H3 | dual-primary fence @N2 | CP-0040 |
| H4 | OBS telemetry contract | CP-0041 |
| H5 | packaging distribution | CP-0042 |
| H6 | minority_write @N2 | CP-0043 |
| H7 | clock_skew @N2 | CP-0044 |
| H8 | manifest parity @N2 | CP-0045 |

This capability records a machine-checkable **theme-set signoff** under
`dist/releases/0.18.0/`, optionally archives + local-tags `v0.18.0`, and runs a
post-signoff monitor `--once`. It does **not** reopen **0.16.3** or **0.17.0**.

## Line status

- **0.18.0 H1..H8 themes:** CLOSED / FROZEN  
- **Package version:** remains **0.18.0** until 0.19 bootstrap plan  
- **0.17.0 / 0.16.3:** CLOSED / FROZEN (do not retag / rebuild)  
- **L_nervous @N2:** COMPLETE (H1..H8 VERIFIED) — necessary, not sufficient for north star  
- **L_GIA:** NO_HELD — do **not** claim GIA; suprahuman remains aspirational only  
- **SaaS / economy:** PARKED  
- **70B:** DO_NOT_TRAIN_70B_NOW  
- **Next line:** docs-only `0.19_bootstrap_plan` (or `L_judge_adapter_design` docs-only)

## Gates

| Gate | Meaning |
|------|---------|
| `version_0180` | pyproject + `__init__` == 0.18.0 |
| `freeze_018x` | Freeze channel `0.18.x` |
| `themes_h1_h8_shipped` | Capability docs for H1..H8 present |
| `cps_0038_0045` | Snapshots CP-0038..0045 sealed |
| `cp_0045_verified` / `cp_0046_seal` | Prior + seal CPs |
| `dual_primary_zero` | dual_primary=0 |
| `no_held_documented` | NO_HELD still documented |
| `pytest_green` | Suite green (or injectable count) |
| `prior_releases_untouched` | 0.16.3 + 0.17.0 SIGNOFF still present |
| `no_gia_claim` | Signoff docs deny GIA / suprahuman achievement claims |

## Artifacts

- `dist/releases/0.18.0/SIGNOFF.json`
- `dist/releases/0.18.0/CHECKLIST.json`
- `dist/releases/0.18.0/TAG_MARKER.json` (+ optional local tag `v0.18.0`)
- `dist/releases/0.18.0/MONITOR.json` (post-signoff `--once`)
- `.project_state/THEME_SIGNOFF_0.18.0.json` (mirror)

## CLI

```bash
.venv/bin/python scripts/theme_signoff_018.py signoff
.venv/bin/python scripts/theme_signoff_018.py archive --tag
.venv/bin/python scripts/theme_signoff_018.py monitor --once
.venv/bin/python scripts/theme_signoff_018.py all --tag
```

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

Unchanged. GIA remains NO_HELD. Do **not** claim GIA. No Raft / N>2 / multi-primary /
plaintext / Vault-ACME-req / SLO chase / tag_schema / EVERY_fsync work in this cycle.

## Explicit non-goals (this cycle)

- Do **not** invent GIA / N>2 / multi-primary themes.
- Do **not** claim GIA (north star / suprahuman remains aspirational only).
- Do **not** reopen or retag 0.16.3 / 0.17.0.
- Do **not** bump package beyond 0.18.0 here.
- Do **not** train 70B; do **not** unpark SaaS / economy.
- Preferred next is docs-only (`0.19_bootstrap_plan` or `L_judge_adapter_design`).
