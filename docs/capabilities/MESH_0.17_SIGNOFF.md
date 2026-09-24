# Mesh 0.17 Theme-Set Signoff

**Capability:** `MESH_0.17_SIGNOFF`  
**Cycle / Checkpoint:** 32 / CP-0036  
**Version:** 0.17.0 (theme set CLOSED/FROZEN; package held at 0.17.0)  
**Channel:** `0.17.x-n2` / schema `mesh.bundle.manifest/v1-n2`  
**Scope:** signoff/closeout only — do not implement H1..H8

## Purpose

Close the frozen **0.17** theme set after themes 1–4 all shipped:

| # | Theme | CP |
|---|-------|----|
| 1 | N=2 multi-node packaging RC | CP-0031 / CP-0032 |
| 2 | Fabric ops UX | CP-0033 |
| 3 | Richer OBS peers | CP-0034 |
| 4 | External quickstart | CP-0035 |

This capability records a machine-checkable **theme-set signoff** under
`dist/releases/0.17.0/`, optionally archives + local-tags `v0.17.0`, and runs a
post-signoff monitor `--once`. It does **not** reopen single-node **0.16.3**.

## Line status

- **0.17.0 themes:** CLOSED / FROZEN  
- **Package version:** remains **0.17.0** until 0.18 bootstrap  
- **0.16.3:** CLOSED / FROZEN (do not retag / rebuild)  
- **Next line:** 0.18.x H1..H8 planning only after council NEXT  
  (default preferred next: `0.18_bootstrap`)

## Gates

| Gate | Meaning |
|------|---------|
| `version_0170` | pyproject + `__init__` == 0.17.0 |
| `freeze_017x_n2` | Freeze channel `0.17.x-n2` |
| `themes_1_4_shipped` | Capability docs for themes 1–4 present |
| `cps_0031_0035` | Snapshots CP-0031..0035 sealed |
| `cp_0035_verified` / `cp_0036_seal` | Prior + seal CPs |
| `dual_primary_zero` | dual_primary=0 |
| `no_held_documented` | NO_HELD still documented |
| `pytest_green` | Suite green (or injectable count) |
| `release_0163_untouched` | 0.16.3 SIGNOFF still present |

## Artifacts

- `dist/releases/0.17.0/SIGNOFF.json`
- `dist/releases/0.17.0/CHECKLIST.json`
- `dist/releases/0.17.0/TAG_MARKER.json` (+ optional local tag `v0.17.0`)
- `dist/releases/0.17.0/MONITOR.json` (post-signoff `--once`)
- `.project_state/THEME_SIGNOFF_0.17.0.json` (mirror)

## CLI

```bash
.venv/bin/python scripts/theme_signoff_017.py signoff
.venv/bin/python scripts/theme_signoff_017.py archive --tag
.venv/bin/python scripts/theme_signoff_017.py monitor --once
.venv/bin/python scripts/theme_signoff_017.py all --tag
```

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

Unchanged. GIA remains NO_HELD. No Raft / N>2 / multi-primary / plaintext /
Vault-ACME-req / SLO chase / tag_schema / EVERY_fsync work in this cycle.

## Explicit non-goals (this cycle)

- Do not implement H1..H8 (0.18 nervous hardening) (identity, recovery, fence@N2, OBS contract,
  packaging distribution, minority_write, clock_skew, manifest parity).
- Do **not** reopen or retag 0.16.3.
- Do **not** bump package beyond 0.17.0 here.
