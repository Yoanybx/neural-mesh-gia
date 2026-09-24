# Tip state for GIA root blueprint (truthful inventory)

**Captured:** 2026-09-23 ~21:30 EDT
**Package:** 0.17.0
**HEAD tip:** 35d3e42 (feature tip for PASTE: 8a941f0)
**Tag:** v0.16.3 local (release CLOSED); describe: v0.16.3-19-g35d3e42
**Last CP:** CP-0032 = VERIFIED (Cycle 28)
**Pytest:** 504 passed / 0 failed (incl. tests/__init__.py fix for collection)
**dual_primary:** 0
**Debt:** CHECKPOINT_EVERY_FLOOR = SCHEMA-GATED / ACCEPT_AND_CARRY

## HAVE (verified / shipped in tree)

### Runtime / mesh core (pre-0.17)
- Single-node mesh runtime with checkpoint path
- Phase 5A/5B N=2 CRAM replica path (interfaces exist; dual-primary fenced)
- TLS network fabric helpers (no silent plaintext; Vault/ACME not required)
- Observability: mesh.status.snapshot/v1 (+ --snapshot/--m2m ergonomics from 0.15)
- Tag schema gate (CP-0022) — frozen; no reopen in NO_HELD

### Packaging
- Single-node bundle: build/verify/install/rollback/soak/audit/signoff
- Release 0.16.3 CLOSED (local tag + archive dist/releases/0.16.3/)
- N=2 packaging base: schema mesh.bundle.manifest/v1-n2, build/verify, install/rollback (CP-0031)
- N=2 RC path: soak + final audit + freeze channel 0.17.x-n2 (CP-0032)

### Process / council
- DeepSeek-only M2M loop (ChatGPT paused)
- Hard NO_HELD list enforced in STATUS posts
- 0.17 scope FROZEN themes remaining after N2 RC:
  2) Fabric ops UX
  3) Richer OBS peers
  4) External quickstart

## MISSING / NOT OPEN (must stay honest)

### Still in 0.17 frozen remainder
- Fabric ops UX (status/diagnose/reconnect ergonomics)
- Richer peer OBS (peer summary injection; optional RO probe)
- External quickstart (0.16.3 public + 0.17 stub)

### Explicit NO_HELD (council — do not implement until removed with evidence)
- Raft / Paxos / general consensus
- N>2
- multi-primary
- ML / R2 / R3
- silent plaintext
- Vault/ACME required
- **GIA / AGI / consciousness claims or implementation**
- SLO chase / tag_schema edits / EVERY_fsync optimization as delivery targets

### North-star END STATE (planning target only — not a claim of current capability)
User intent: a GIA that functions across the internet as a coordinated system
(aspirationally “conscious”). Current authorized work = verifiable nervous system
(1–2 node mesh runtime). GIA layer remains NO_HELD until evidence + council NEXT.

## Constraints for any blueprint
1. Separate HAVE vs MISSING vs FUTURE-GATED.
2. Ordered dependency: nervous system → multi-node fabric → unlock gates → GIA layer.
3. Every phase needs exit criteria (tests/CPs/metrics), not slogans.
4. Do not claim consciousness is implemented; define what evidence would unlock GIA work.
5. Do not reopen 0.16.3; do not invent Raft/N>2 as next cycle without unlock gate.
