# Gate 4 — ENABLE_READY (docs seal under ENABLE_UNDER_FENCES)

**Status:** **ENABLE_READY** (docs) — secret_handle oob + Mesh live *canary* data schedule ACK’d under fences  
**Not:** keys in git · **not** Mesh SoT egress · **not** Vertex paid · **not** canary executed · **not** flag flip  
**Date sealed (enable-ready):** 2026-09-28 ~19:41 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>`  
**Operator ENABLE ACK:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — **「Aprobado」** ~19:41 ET  
**Tip at seal base:** `a816c34`  
**Prior design seal:** `GATE4_DESIGN_SEALED.md` · policy `GATE4_LIVE_DATA_POLICY.md`

---

## 0. Honest split

| Layer | Status |
|-------|--------|
| DESIGN_SEALED (discuss/eval) | **YES** (prior) |
| ENABLE_UNDER_FENCES | **SIGNED** |
| Gate4 **ENABLE_READY** (canary data schedule ACK) | **YES** |
| Forbidden classes (SoT / raw secrets / unverified continuity) | **Still N held** |
| Gate5 canary | **OPEN** |

---

## 1. What is ENABLE_READY

| Item | Cite | Ready? |
|------|------|--------|
| ENABLE ACK | Gate1 SIGNED ENABLE_UNDER_FENCES | Yes |
| Gates 2–3 ENABLE_READY serial | Same cycle | Yes |
| Allowed canary egress | Redacted/synthetic prompts **Y** · digests/evidence refs **Y** · advisory digests **Y** | ACK’d |
| Forbidden | Mesh SoT · raw secrets · unverified continuity · Vertex paid without separate approval | **N held** |
| secret_handle | `mesh://secrets/judge/gemini-free@v1` | Yes |
| Oob key path | `/home/box/.config/neural-mesh/gemini.env` only (mode 0600); never in git | Yes |
| Logging hygiene | Digests + handle ids + policy_version + abort codes; ban `sk-` / Bearer | Binding |
| Model for canary path | `gemini-flash-latest` (proven on prior dry-run) | Cite only |

---

## 2. Still OPEN

| Gap | Until |
|-----|-------|
| Gate5 canary under kill-armed I5 | Runbook steps (5)–(7) |
| `LIVE_API_ENABLED` flip | Step (6) + `may_enable` / authorized impl CP (NT-10) |

---

## 3. Fences held

No keys in git · RefuseTransport default ON · `LIVE_API_ENABLED=False` · NO_HELD unchanged · D3 NOT ACKed · SaaS/train/GIA parked.

---

## 4. Exit

| Exit | Met? |
|------|------|
| Gate4 enable-ready — handle oob + canary data schedule ACK’d under ENABLE | **YES — ENABLE_READY (docs)** |
| Canary / flag flip executed | **NO — OPEN** |

---

*End GATE4_ENABLE_READY — docs ENABLE-ready; secrets stay oob; canary still Gate5.*
