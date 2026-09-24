# Debt Gate Review — CP-0029 / P23

**Date:** 2026-09-23 America/New_York (EDT)  
**Cycle / Checkpoint:** 25 / CP-0029  
**Version:** 0.16.3 (held)  
**Script:** `scripts/debt_gate_review.py`

## Purpose

Review **CHECKPOINT_EVERY_FLOOR** SCHEMA-GATED status and confirm the schema
gate is still present. Report MET / GAP / SCHEMA-GATED for known SLOs
**without rebenchmarking**. Exit 0 when gates are consistent.

## Review checklist

| Gate | Expected | Action |
|------|----------|--------|
| `CHECKPOINT_EVERY_FLOOR` debt doc | Status **SCHEMA-GATED**; "No SLO chase" | Confirm present |
| `schema_gate_checkpoint_every_floor` | Present in `neural_mesh.tags` | Confirm gate still present |
| `checkpoint_durable_batch` | **MET** (documented) | Report only — no bench |
| `recovery` | **MET** (documented) | Report only — no bench |
| EVERY floor p99 | GAP ~1.32 ms (documented) | Report only — no chase |

## CLI

```bash
.venv/bin/python scripts/debt_gate_review.py
.venv/bin/python scripts/debt_gate_review.py --json
```

Writes `dist/releases/0.16.3/DEBT_GATE_REVIEW.json` (M2M-friendly).

## Consistency rule

Exit **0** iff:

1. Debt file `docs/debt/CHECKPOINT_EVERY_FLOOR.md` exists with SCHEMA-GATED + No SLO chase
2. Schema gate markers present in `src/neural_mesh/tags.py`
3. Known SLO documented states are coherent (MET / SCHEMA-GATED / GAP)

Exit **1** on missing debt file, missing schema gate, or forced inconsistency.

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
