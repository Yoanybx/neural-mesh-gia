# Mesh External Quickstart

**Capability:** `MESH_EXTERNAL_QUICKSTART`  
**Cycle / Checkpoint:** 31 / CP-0035  
**Version:** 0.17.0 (hold; do **not** reopen 0.16.3 RC)  
**Theme:** 0.17 frozen theme **#4** — External quickstart  
**Depends on:** signed-off `MESH_PACKAGING_RELEASE_SIGNOFF` (0.16.3 CLOSED), themes 1–3 docs

## Purpose

Ship a **public / external** quickstart for the signed-off **0.16.3 single-node**
bundle, plus a **forward-looking 0.17 stub** that points at shipped themes
without claiming unfinished features or reopening the closed packaging channel.

## What shipped

| Surface | Location |
|---------|----------|
| External 0.16.3 quickstart | `docs/quickstart/QUICKSTART_0.16.3.md` |
| 0.17 forward stub | `docs/quickstart/QUICKSTART_0.17_STUB.md` |
| Dry-run / fail-closed helper | `scripts/quickstart_0.16.3.sh` |
| Tests | `tests/test_quickstart_cycle31.py` (marker `quickstart_cycle31`) |

### Operator flows

1. **Dry-run (default)** — `bash scripts/quickstart_0.16.3.sh`  
   Checks release artifact presence under `dist/releases/0.16.3/`; prints plan;
   does not extract or rebuild.
2. **Execute verify** — `bash scripts/quickstart_0.16.3.sh --execute`  
   `sha256sum -c SHA256SUMS` + `scripts/verify_bundle.py` with `--expected-ver 0.16.3`.
3. **Manual install / smoke** — follow Path A/B in `QUICKSTART_0.16.3.md`
   (`rc_install_verify.py`, `clean_node_smoke.py`, or extract + `pip install -e .`).
4. **0.17 orientation** — read `QUICKSTART_0.17_STUB.md` for shipped themes vs
   EXPERIMENTAL; do not treat 0.17.0 as an external release until signoff.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No reopen 0.16.3 | Helper never calls `build_bundle`; docs forbid retag |
| No Raft / N>2 / multi-primary | Stub + quickstart never claim these |
| No silent plaintext | Helper / docs state fail-closed TLS contract |
| No Vault/ACME required | Single-node path does not hard-require external PKI |
| No GIA / AGI claims | Explicit non-claim in both docs |
| No SLO chase / tag_schema / EVERY_fsync | Unchanged |
| dual_primary | **Hard 0** |

## Exit criteria

- [x] `docs/quickstart/QUICKSTART_0.16.3.md` present (install/verify/smoke + bounds)
- [x] `docs/quickstart/QUICKSTART_0.17_STUB.md` present (shipped vs EXPERIMENTAL; no unfinished claims)
- [x] `scripts/quickstart_0.16.3.sh` dry-run safe / fail-closed / no plaintext / no rebuild
- [x] Capability doc present
- [x] ≥10 pytest cases (marker `quickstart_cycle31`)
- [x] Full suite green; version **0.17.0**; CP-0035 VERIFIED
- [x] PREFERRED_NEXT after seal: `0.17_signoff`

## Non-goals

- Rebuilding or retagging 0.16.3
- Shipping a 0.17 external release tarball in this cycle
- Claiming Raft / N>2 / GIA / multi-primary / plaintext / Vault-ACME-req
- 0.18.x nervous hardening (H1..H8) — after signoff

## Related

- `docs/planning/0.17_SCOPE_FROZEN.md` theme 4
- `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`
- `docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md`
- `docs/capabilities/MESH_FABRIC_OPS_UX.md`
- `docs/capabilities/MESH_OBS_PEERS.md`
- `council/DEEPSEEK_REPLY_CYCLE30.md` NEXT=`external_quickstart`
