# NOTE S0 — Mesh as the intelligence backend of Minogan.ai

- **Date:** 2026-10-18 ~01:40 EDT (America/New_York)
- **Author:** Grok Bot `<grok-bot@local>`
- **Tip base:** `21f9e48` (CP-0087 chain: `6aba4c7` → `88f1276` → `3a70a50` → `21f9e48`)
- **CP:** opens **CP-0088 — camino Minogan** (`docs/planning/CP_0088_CAMINO_MINOGAN.md`)
- **Authority:** operator (Joan) chat, 2026-10-18: "Primero guarda NOTE S0 … y el spike de schema UW … Después sigue con el track B … solo para la integración con Minogan." Also: "SaaS deja de estar PARKED **solo para este camino**."
- **Status:** INTENT SEALED (docs only). No code, no network, no LIVE flag change, no push/tags.

## 1. Intent (what Mesh is for, on this path)

Mesh becomes the **intelligence backend of Minogan.ai**: a persistent memory that
remembers the behaviour history of every monitored AI agent **over time**, isolated
**per tenant**. It produces a **deterministic, LLM-free** risk score with an audit
trail that an underwriter (or an enterprise risk team) can replay.

Minogan is **not an insurer** and writes **no policies**. Its three lanes:

| Lane | Customer | What Mesh provides |
|------|----------|--------------------|
| Command center | carriers / MGAs | per-agent risk score + UW hint (`minogan.uw/v0`) + long-horizon drift/recurrence |
| One-shot studies | enterprises | the same scorer over a bounded window; replayable evidence |
| Continuous monitoring | both | `AgentMemory` history beyond the pilot's 7-day window |

Integration point: the pilot's pluggable Scorer (`/workspace/minogan-pilot/src/shared/scorer.js`,
contract `minogan.scorer/v1`). Mesh plugs in as an external scorer
(`combineScorers([rules, mesh], {strategy:'max'})`); **the pilot is not rewritten**.

## 2. Honest state today (gap list)

Mesh today is **substrate**, not a Minogan product:

| Have (real, tested) | Do **not** have yet |
|---------------------|---------------------|
| C-RAM content-addressed store, WAL, checkpoint/fsck | Any Minogan code (contract, scorer, memory, service) |
| N=2 replica + fences (dual_primary=0), ledger/receipt hash chains | Secondary index / time-range query on C-RAM (CAS only: `put/get/list_keys`) |
| L_judge advisory path (Gemini free, F4 LIVE under fences) | Tenant isolation of any kind (no `tenant_id` anywhere) |
| RefuseTransport / I5 network gating | Per-tenant auth, retention, deletion |
| | `GoalRegistry` / `EvidenceLedger` are **in-memory mocks** (CP-0068) |
| | `ObjectType.MEMORY` exists in `cram/models.py` but is **unused** |
| | Calibration data (no labelled outcomes → no AUC/Brier/FP rates) |
| | Collectors / ingest for insured agents (the pilot owns ingest) |
| | Off-PC deployment (box-local only) |

Do not describe any of the right-hand column as done.

## 3. Rules carried into CP-0088 (non-negotiable)

1. Council / fences / CPs respected; every P0 milestone reported with SHA + tests + gaps + risks.
2. **SaaS un-PARKED only for the Minogan path.** Everything else in NO_HELD stays NO_HELD.
3. **GIA NO_HELD.** No consciousness / AGI claims. "Memory" = substrate persistence, not cognition.
4. **No Raft, no N>2.** M1 stays `NO_CONSENSUS_YET`.
5. **Score is deterministic, no LLM.** L_judge may only *explain* (advisory field), never changes the number; the number is computed before and independently of any judge call.
6. **Never store prompts / completions.** Metadata only, same redaction policy as the pilot ingest (content dropped at ingest; only names, counts, latencies, statuses, destinations, byte sizes, hashes).
7. No paid service, domain, VM or new key without operator approval. No push, no tags. `LIVE_API_ENABLED` not touched by this path.

## 4. Not claimed

- "Mesh is 100% ready" — false for Minogan (see §2).
- "Mesh writes cover / binds risk" — false; the UW outcome is a *hint* to a human underwriter.
- Calibrated / validated risk model — false until P1 calibration.
- Multi-tenant production — false; P0 is single-box, tenant-keyed, not hardened.

## 5. Next

CP-0088 P0 list (contract → parity scorer → AgentMemory → HTTP → score ledger/replay → deploy proposal).
Schema: `docs/schema/minogan/uw_v0.md`, `uw_v0.schema.json`, `scorer_contract_v1_mapping.md`.
