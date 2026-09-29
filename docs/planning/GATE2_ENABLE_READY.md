# Gate 2 — ENABLE_READY (docs seal under ENABLE_UNDER_FENCES)

**Status:** **ENABLE_READY** (docs) for Gemini **free-tier canary path under fences**  
**Non-goals:** full live RV is not yet measured · **not** `LIVE_API_ENABLED=true` · **not** Mesh live proven · **not** NO_HELD unlock  
**Date sealed (enable-ready):** 2026-09-28 ~19:41 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>`  
**Operator ENABLE ACK:** `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — **「Aprobado」** 2026-09-28 ~19:41 ET  
**Tip at seal base:** `a816c34`  
**Prior design seal:** `docs/planning/GATE2_DESIGN_SEALED.md` (DISCUSS_ONLY/eval) — retained

---

## 0. Honest split

| Layer | Status |
|-------|--------|
| DESIGN_SEALED (discuss/eval) | **YES** (prior) |
| Operator ENABLE_UNDER_FENCES | **SIGNED** |
| Gate2 **ENABLE_READY** (this artifact) | **YES** — amendment ACK’d as enable-ready for canary path under fences |
| Live RV-1..RV-7 under Mesh live transport | **OPEN** — post-canary / rollback measurement; CP-0075 canary evidence ≠ full live RV |
| `LIVE_API_ENABLED` flip | **DONE (runtime window)** under CP-0075 / Gate5 canary; module constant **False** final — `GATE5_CANARY_EVIDENCE.md` |

**Claim hygiene:** ENABLE_READY ≠ full live proof complete ≠ flag flipped; CP-0075 is executed advisory evidence, not Mesh ACCEPT/SoT.

---

## 1. What is ENABLE_READY

| Item | Cite | Ready? |
|------|------|--------|
| ENABLE ACK present | `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` | Yes |
| Live-safety amendment text | `GATE2_LIVE_SAFETY_CASE_AMENDMENT.md` — blast radius, key compromise, kill→Refuse+ABORT, continuity under peer failure | Yes (reviewed under ENABLE) |
| Authority Matrix cite | Gate3 AM-* / RefuseTransport / Operator sole enable | Yes |
| RefuseTransport fail-closed default | `l_judge_live_adapter_safety.py` · CP-0058 | In force |
| secret_handle hygiene | `mesh://secrets/judge/gemini-free@v1` · oob `/home/box/.config/neural-mesh/gemini.env` | Yes (oob; no keys in git) |
| Prior dry-run evidence | `1e502c6` / `30fe593` · model `gemini-flash-latest` · HTTP 200 · `MESH_DRY_RUN_OK` | Eval prior only — **≠** canary / live RV |
| Mock RV-1..RV-7 | Still mock-green (D1) | Yes |
| I5 kill path (design) | Kill → RefuseTransport + continuity ABORT + emergency `enabled=false` | Used for CP-0075; required for any re-walk |

---

## 2. Still OPEN after this seal

| Gap | Status / remaining condition |
|-----|-----------------------------|
| Gate5 canary execution + ledger | **DONE — CP-0075**; any re-walk remains under kill-armed I5 |
| Live RV under real Mesh transport | **OPEN** — post-canary / rollback cycle |
| Flag flip | Gate5 step (6) **executed** under CP-0075 (`may_enable`; NT-10 cleared for canary scope); final flag remains **False** |
| Gate6 live measurement | **OPEN** — subsequent evidence / measurement cycle |

---

## 3. Fences held

| Fence | Value |
|-------|-------|
| `LIVE_API_ENABLED` | **False** (not flipped in this seal) |
| RefuseTransport | **ON** (default) |
| Keys in git | **NONE** |
| NO_HELD | Raft / N>2 / GIA / train / SaaS / pkg0190 — **unchanged** |
| D3 | **NOT ACKed** |

---

## 4. Exit

| Exit | Met? |
|------|------|
| Gate2 **enable-ready** under ENABLE ACK + amendment reviewed + mock RV green + CP-0075 canary evidence | **YES — ENABLE_READY (docs)** |
| Gate2 live proof complete / RV under Mesh live | **NO — OPEN** |

---

*End GATE2_ENABLE_READY — docs ENABLE-ready; CP-0075 canary executed; no invented full live RV or permanent flag flip.*
