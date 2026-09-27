# Fabric Ops UX v1 (ops surface)

**Blueprint theme:** L1 R1 — Fabric ops UX (0.17 frozen theme #2)  
**Capability:** `MESH_FABRIC_OPS_UX` — see `docs/capabilities/MESH_FABRIC_OPS_UX.md`  
**Evidence:** Cycle 29 / CP-0033 (tip `e1d5e50`); tests marker `fabric_ops_cycle29`  
**Package line:** shipped under 0.17.0; current package held at **0.18.0**

## Honest mapping vs blueprint star-line

Blueprint L1 R1 originally listed `C:mesh ctl|status|trace|pause|kill`. Those
full control-plane verbs belong to **L5 I2 / I5** (still MISSING) and were
**not** in the frozen 0.17 theme set.

0.17 R1 shipped as **Fabric ops UX** around the existing TLS fabric:

| Verb | CLI | Meaning |
|------|-----|---------|
| status | `mesh fabric status` | Cert layout + optional TLS heartbeat |
| diagnose | `mesh fabric diagnose` | Issues + recommendations (fail-closed) |
| reconnect | `mesh fabric reconnect` | TLS HEARTBEAT reconnect only |

ABORT→read-only: on `FABRIC_TLS_ERROR` / `FABRIC_PLAINTEXT_FORBIDDEN`, never
retry as unix/plaintext.

## Surfaces

| Surface | Location |
|---------|----------|
| Capability | `docs/capabilities/MESH_FABRIC_OPS_UX.md` |
| Library | `src/neural_mesh/network/ops.py` (`FabricOps`) |
| Tests | `tests/test_fabric_ops_cycle29.py` (T-R1a status; T-R1b diagnose; T-R1c reconnect +neg) |

## Related

- `docs/planning/L1_RESIDUE_CLOSEOUT.md`
- L5 I2 `mesh ctl …` remains deferred (not unlocked here)
