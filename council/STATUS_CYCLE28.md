# STATUS — Cycle 28 / CP-0032

**Date:** 2026-09-23 21:22 EDT (America/New_York)  
**Version:** 0.17.0  
**Checkpoint:** CP-0032 = VERIFIED  
**Pytest:** 504 passed / 0 failed  
**Packaging_n2:** 27 (14 cycle27 + 13 cycle28)  
**dual_primary:** 0  
**NO_HELD:** unchanged

## Done

- P30 `n2_rc_soak` + `scripts/n2_rc_soak.py`
- P31 `n2_final_release_audit` + capability doc
- P32 N2 freeze always-on + verify channel gate; schema FROZEN for 0.17.x-n2
- tests/test_packaging_n2_cycle28.py (13)
- Snapshots/CP-0032 VERIFIED

## Bounds

No Raft, no N>2, no multi-primary, no SLO chase, no tag_schema, no EVERY_fsync, no reopen 0.16.3.
