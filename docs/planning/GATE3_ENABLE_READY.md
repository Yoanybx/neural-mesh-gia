# Gate 3 — ENABLE_READY (docs seal under ENABLE_UNDER_FENCES)

**Status:** **ENABLE_READY** (docs) — Authority Matrix cited for Gemini free-tier canary ops under fences  
**Not:** production live-armed Mesh · **not** flag flip · **not** canary executed · **not** NO_HELD unlock  
**Date sealed (enable-ready):** 2026-09-28 ~19:41 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>`  
**Operator ENABLE ACK:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — **「Aprobado」** ~19:41 ET  
**Tip at seal base:** `a816c34`  
**Prior design seal:** `GATE3_DESIGN_SEALED.md` · binding `GATE3_AUTHORITY_MATRIX_BINDING.md`

---

## 0. Honest split

| Layer | Status |
|-------|--------|
| DESIGN_SEALED (discuss/eval) | **YES** (prior) |
| ENABLE_UNDER_FENCES | **SIGNED** |
| Gate3 **ENABLE_READY** (matrix cite for canary ops) | **YES** |
| Runtime `live_adapter.enabled=true` armed | **NO** — Gate5 only |
| Role invents execute | **Forbidden** (unchanged) |

---

## 1. What is ENABLE_READY

| Item | Cite | Ready? |
|------|------|--------|
| ENABLE ACK | Gate1 SIGNED ENABLE_UNDER_FENCES | Yes |
| Gate2 ENABLE_READY serial | `GATE2_ENABLE_READY.md` | Yes (same cycle) |
| Frozen AM-* IDs | `AM-L_JUDGE` propose-only · `AM-I5` kill · `AM-OPERATOR` sole enable · `AM-REFUSE` | Yes |
| Ops sentence | L_judge propose-only; I5 approve/veto/kill; Operator sole live-enable; RefuseTransport veto; Mesh ABORT > judge ACCEPT | Binding |
| Canary peer role | Advisory / evidence only — not Mesh SoT / M1 / execute | Binding |
| secret_handle cite | `mesh://secrets/judge/gemini-free@v1` oob | Yes |
| RefuseTransport on Mesh live slot until Gate5 step (6) | In force | Yes |

---

## 2. Still OPEN

| Gap | Until |
|-----|-------|
| Live-armed production config with `enabled=true` | Gate5 step (6) + impl posture |
| Gate5 canary / Gate6 measurement | Serial |

---

## 3. Fences held

`LIVE_API_ENABLED=False` · RefuseTransport ON · no keys in git · NO_HELD unchanged · D3 NOT ACKed.

---

## 4. Exit

| Exit | Met? |
|------|------|
| Gate3 enable-ready — matrix IDs bound for canary ops under ENABLE ACK | **YES — ENABLE_READY (docs)** |
| Matrix in use on live-enabled runtime | **NO — OPEN** (Gate5) |

---

*End GATE3_ENABLE_READY — docs ENABLE-ready; not a flag flip.*
