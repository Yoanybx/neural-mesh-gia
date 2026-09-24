# Mesh Packaging: N2 Final Release Audit

**Capability:** `MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT`  
**Cycle / Checkpoint:** 28 / CP-0032  
**Version:** 0.17.0 (held; open 0.17.x-n2 RC channel)  
**Scope:** N=2 packaging RC hardening only (`capability_not_tags_not_SLO`)  
**Schema:** `mesh.bundle.manifest/v1-n2` (**FROZEN** for 0.17.x-n2 RC)

## Purpose

Aggregate gate before calling the **N2** packaging RC release-ready. Mirrors
single-node Cycle 23 final audit patterns for the N2 product line.

Complements:

- **P30** `n2_rc_soak` — N-iteration dual-prefix install/verify soak
- **P32** `n2_rc_freeze` — embed `freeze: {channel:"0.17.x-n2", schema:v1-n2}`

Does **not** reopen or alter the closed single-node `0.16.3` / `0.16.x` freeze.

## Gates

| Gate | Meaning |
|------|---------|
| `version_match` | `pyproject` equals **0.17.0** (held) |
| `cp_tip` | Checkpoint tip present (CP-0032) |
| `n2_verify` | Build + `verify_n2_bundle` with freeze channel check |
| `freeze_channel_017x_n2` | Manifest freeze `{channel:"0.17.x-n2", schema:v1-n2}` |
| `schema_v1_n2` | Schema id `mesh.bundle.manifest/v1-n2` |
| `n2_soak` | Soak PASS (or injectable / skipped in unit tests) |
| `pytest_packaging_n2` | `pytest -m packaging_n2` green (or `--packaging-n2-count`) |
| `dual_primary_zero` | `dual_primary=0` documented / enforced |
| `no_held_documented` | NO_HELD list present in council/capability docs |

## CLI

```bash
.venv/bin/python scripts/n2_final_release_audit.py
.venv/bin/python scripts/n2_final_release_audit.py --json --skip-pytest --packaging-n2-count 26 --soak-ok true
```

Exit code **0** only if all gates pass. `--json` emits an M2M-friendly summary
under `dist/n2_final_audit/n2_final_release_audit.json`.

## Library

```python
from neural_mesh.packaging import run_n2_final_release_audit
r = run_n2_final_release_audit(
    "/path/to/repo",
    expect_version="0.17.0",
    expect_cp="CP-0032",
    soak_ok=True,
    packaging_n2_count=26,
)
assert r.ok
print(r.to_json())
```

## Related P30 / P32

```bash
.venv/bin/python scripts/n2_rc_soak.py --n 5 --ver 0.17.0
.venv/bin/python scripts/build_n2_bundle.py --out dist/n2   # always embeds freeze
.venv/bin/python scripts/verify_n2_bundle.py dist/n2/*.tar.gz --expect-freeze-channel 0.17.x-n2
```

## Schema freeze (P32)

N2 RC freeze metadata (additive on v1-n2; does **not** touch single-node v1):

```json
{
  "freeze": {
    "channel": "0.17.x-n2",
    "schema": "mesh.bundle.manifest/v1-n2",
    "single_node_schema_frozen": "mesh.bundle.manifest/v1"
  }
}
```

**FROZEN** for the 0.17.x-n2 RC channel. Single-node `mesh.bundle.manifest/v1`
for closed `0.16.x` remains untouched.

## dual_primary

**dual_primary=0** (N2 packaging; majority=`fenced_primary_heal` NOT Raft).

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Bounds

No Raft / N>2 / multi-primary / ML / plaintext / GIA / SLO chase / tag_schema /
EVERY_fsync. No reopen of 0.16.3 RC. Majority remains fenced_primary_heal.
