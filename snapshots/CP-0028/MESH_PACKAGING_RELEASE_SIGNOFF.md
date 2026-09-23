# Mesh Packaging: Release Signoff

**Capability:** `MESH_PACKAGING_RELEASE_SIGNOFF`  
**Cycle / Checkpoint:** 24 / CP-0028  
**Version:** 0.16.3 (signed-off release; Cycle 24 = release closeout of 0.16.3)  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Schema:** `mesh.bundle.manifest/v1` (**FROZEN** for 0.16.x)  
**Signoff schema:** `mesh.release.signoff/v1`

## Purpose

Machine-checkable **release signoff** that single-node RC **0.16.3** is
release-ready. Complements P16 final release audit and seals **CP-0028**.

## Gates

| Gate | Meaning |
|------|---------|
| `final_release_audit` | Prior audit PASS (reuse report) or re-run |
| `version_0163` | `pyproject` + `__init__` == **0.16.3** |
| `freeze_016x` | Freeze channel `0.16.x` + schema v1 |
| `cp_0027_verified` | CP-0027 snapshot / checkpoint verified |
| `cp_0028_seal` | Cycle 24 seals CP-0028 |
| `pytest_packaging` | Packaging tests green (or `--packaging-count` inject) |

## Artifacts

- `dist/releases/0.16.3/SIGNOFF.json`
- `.project_state/RELEASE_SIGNOFF_0.16.3.json` (mirror)

Fields: `tip`, `ver`, `cp`, `prior_cp`, `audit_hashes`, `timestamp`,
`signer=council:DeepSeek+Grok`.

## CLI

```bash
.venv/bin/python scripts/release_signoff.py
.venv/bin/python scripts/release_signoff.py --json --packaging-count 53 --skip-pytest
.venv/bin/python scripts/release_signoff.py --timestamp 2026-09-23T00:00:00Z
```

## Library

```python
from neural_mesh.packaging import run_release_signoff
r = run_release_signoff("/path/to/repo", packaging_count=53, skip_pytest=True,
                        timestamp="2026-09-23T00:00:00Z")
assert r.ok
print(r.signoff_path)
```

## Related

- **P19** `release_tag_archive` — local tag + `dist/releases/0.16.3/` archive
- **P20** `post_release_monitor` — `--once` post-release checks

## dual_primary

**dual_primary=0** (single-node RC; peers=0; no multi-primary).

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Bounds

No tag schema edits, no SLO chase, no Raft/N>2/consensus, no plaintext/GIA, no EVERY fsync optimization.
Manifest schema v1 remains frozen for 0.16.x.
