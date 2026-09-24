# Mesh Fabric Ops UX

**Capability:** `MESH_FABRIC_OPS_UX`  
**Cycle / Checkpoint:** 29 / CP-0033  
**Version:** 0.17.0 (hold; do **not** reopen 0.16.3 RC)  
**Theme:** 0.17 frozen theme **#2** — Fabric ops UX  
**Depends on:** Phase 4 Network Fabric v0 + mTLS (`docs/network_fabric_tls.md`, Cycle 11)

## Purpose

Ship **operator-facing** status / diagnose / reconnect ergonomics around the
**existing** TLS network fabric helpers (`src/neural_mesh/network/*`). This is
UX and probing only — **not** a new transport, consensus layer, or PKI product.

## What shipped

| Surface | Location |
|---------|----------|
| Library API | `src/neural_mesh/network/ops.py` — `FabricOps`, status / diagnose / reconnect |
| Schemas | `mesh.fabric.status/v1`, `mesh.fabric.diagnose/v1`, `mesh.fabric.reconnect/v1` |
| CLI | `mesh fabric status \| diagnose \| reconnect` |
| Layout | LocalCA root (`ca.crt`, `nodes/<id>/node.{crt,key}`) + optional `endpoints.json` |
| Tests | `tests/test_fabric_ops_cycle29.py` (marker `fabric_ops_cycle29`) |

### Operator flows

1. **`mesh fabric status --fabric-root DIR --node-id ID [--endpoints PATH] [--json]`**  
   Cert presence + optional live TLS heartbeat probes of configured peers.
2. **`mesh fabric diagnose ...`**  
   Same probe data plus issue list and recommendations (bootstrap leafs, fix TLS,
   start endpoint). Always documents fail-closed / no plaintext fallback.
3. **`mesh fabric reconnect ... [--peer ID] [--attempts N]`**  
   Safe reconnect: TLS connect + HEARTBEAT only. On `FABRIC_TLS_ERROR` /
   `FABRIC_PLAINTEXT_FORBIDDEN` **fail closed** — never retry as unix/plaintext.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Ops do not invent consensus or topology |
| No silent plaintext | `tls_required` default true; unix/plaintext refused |
| No Vault/ACME required | Local CA leafs only; external PKI remains optional debt |
| No GIA / AGI claims | Operator UX only |
| No SLO chase / tag_schema / EVERY_fsync | Unchanged |
| dual_primary | **Hard 0** in every report |

## Exit criteria

- [x] Capability doc present
- [x] `FabricOps.status` / `.diagnose` / `.reconnect` wrap existing session/TLS
- [x] CLI `mesh fabric {status,diagnose,reconnect}`
- [x] ≥10 pytest cases: fail-closed TLS, no plaintext fallback, diagnose fields,
      reconnect on tmp roots
- [x] Full suite green; version **0.17.0**; CP-0033 VERIFIED
- [x] dual_primary=0; plaintext_fallback=0 in reports

## Non-goals

- Replacing or weakening Cycle 11 trust model
- Requiring Vault / ACME / public CA
- Richer OBS peer injection (0.17 theme #3 — later)
- External quickstart (0.17 theme #4 — later)
- WAN multi-host ops hardening (remains EXPLICIT DEBT in `docs/debt/TLS.md`)

## Related

- `docs/network_fabric_tls.md` (FROZEN trust model)
- `docs/debt/TLS.md`
- `docs/planning/0.17_SCOPE_FROZEN.md` theme 2
- `council/PASTE_CYCLE28_M2M.md` PREFERRED_NEXT: fabric_ops_UX
