# Gate 4 — DESIGN_SEALED (DISCUSS_ONLY / Gemini free-tier eval path)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** data policy + secret_handle lifecycle  
**Not:** operator-SIGNed ENABLE seal · **not** `live=ENABLED` · **not** Mesh live adapter on · **not** Gate5 canary · **not** keys in repo/logs · **not** Mesh live egress authorized  
**Date sealed (design):** 2026-09-28 ~18:48 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `ce53e7c` (Gate3 DESIGN_SEALED) atop Gate2 `7c436f8` / peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **NO_HELD** (Raft/N>2/GIA/train/SaaS) stays NO_HELD · Gate1 **SIGNED DISCUSS_ONLY** · Gate2 **DESIGN_SEALED** · Gate3 **DESIGN_SEALED** (discuss/eval)

**Binding:** `docs/planning/GATE4_LIVE_DATA_POLICY.md`  
**Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 4  
**Council:** `council/NOTE_GATE4_DATA_POLICY.md` · `council/NOTE_GATE4_DESIGN_SEALED.md`

---

## 0. Honest split — sealed vs still needs operator ACK

| Layer | Status | Meaning |
|-------|--------|---------|
| **DESIGN_SEALED** (this artifact) | **YES** | Live **data-handling schedule** + **secret_handle lifecycle** for Gemini free-tier **eval / DISCUSS_ONLY** is complete: allowed vs forbidden egress classes, oob key load, dry-run flag vs Mesh live RefuseTransport, logging hygiene — **design/docs seal only** |
| **ENABLE seal / Mesh live data ACK** | **NO — OPEN** | Requires ENABLE_UNDER_FENCES + Gates 2–3 enable path + data schedule ACK’d for Mesh live egress — **Do not invent signature.** |
| **Gate5 canary** | **NO — OPEN** | Canary / flip **NOT** for execution until ENABLE chain + Gates 2–4 enable-ready |
| **Flag flip** | **FORBIDDEN now** | `LIVE_API_ENABLED` / `live_adapter.enabled` stay **false** |

**Claim hygiene (D4-F):** DESIGN_SEALED ≠ ENABLE seal ≠ live-ready ≠ Gate5 canary ≠ authorization to egress Mesh SoT / raw secrets.

---

## 1. What is DESIGN_SEALED (DISCUSS_ONLY / eval)

| Item | Bound evidence / cite | Sealed? |
|------|----------------------|---------|
| Allowed vs forbidden egress classes | `GATE4_LIVE_DATA_POLICY.md` §1 — redacted/synthetic prompts, digests, schema envelopes, advisory digests **Y (design)**; Mesh SoT / raw secrets / unverified continuity / Vertex paid / credentials in continuity **N** | Design yes |
| secret_handle form + lifecycle | `mesh://secrets/<scope>/<name>@<version>`; create/rotate/revoke/resolve; I5 sees handle ids/digests never raw | Design yes |
| **Eval secret_handle (provisioned oob)** | Handle id `mesh://secrets/judge/gemini-free@v1`; key path `/home/box/.config/neural-mesh/gemini.env` **outside repo**; `.gitignore` covers `gemini.env` / `.config/neural-mesh/`; raw key **never** in git/logs/evidence | Eval bind yes |
| Oob key load (eval) | Dry-run / peer wire load from oob env only; no key material in repo tree or CI digests | Eval bind yes |
| **Dry-run flag vs live RefuseTransport** | Peer dry-run: `--gemini-dry-run` / `GEMINI_DRY_RUN=1` → `GeminiFreeDryRunTransport` (tips `30fe593` / `1e502c6`); Mesh live path remains **RefuseTransport** / `LIVE_API_ENABLED=False` / `ENGINE_DISABLED` | Eval bind yes |
| Logging / evidence hygiene | Digests + handle ids + policy_version + abort codes only; ban `sk-` / Bearer in digests/CI/explain | Design yes |
| Gate1–3 serial | Gate1 **SIGNED DISCUSS_ONLY**; Gate2/3 **DESIGN_SEALED** discuss/eval | Serial yes |

---

## 2. What still needs operator ACK / later cycles (NOT sealed)

| Gap | Owner | Blocked until |
|-----|-------|---------------|
| Intent upgrade **ENABLE_UNDER_FENCES** | **Operator (user-written signature)** | Explicit ACK artifact — bots must **not** invent |
| Gate4 **ENABLE** seal (schedule ACK’d for Mesh live egress) | Operator + council | After ENABLE intent + Gates 2–3 enable seals |
| Gate5 **runbook DESIGN_SEALED** (docs/canary procedure) | Serial design seals | Next docs step — **not** execute canary |
| Gate5 **canary execution** | Serial Gates 2–4 **enable**-sealed + ENABLE ACK | Runbook may design-seal; flip **NOT executed** |
| Gate6 acceptance metrics DESIGN_SEALED / on canary | After Gate5 docs seal (then evidence after canary) | Bundle drafted; canary not run |
| Live RV-1..RV-7 under real Mesh transport | Gate5+rollback cycle | Mock-only / dry-run-only today |

---

## 3. Fences held at DESIGN_SEAL

| Fence | Value |
|-------|-------|
| `LIVE_API_ENABLED` | **False** (untouched) |
| `live_adapter.enabled` | **false** |
| Mesh live L_judge adapter | **NOT_ENABLED** (RefuseTransport) |
| Keys in repo / CI / digests | **NONE** — oob path only |
| Push / tags / secrets in git | **NONE** |
| Gate1 intent | **DISCUSS_ONLY** (no upgrade) |
| NO_HELD | Raft, N>2, GIA, train, SaaS, pkg0190 — **stay NO_HELD** |
| D3 / `MESH_PERF_EXPERIMENTAL` | **OFF** / NOT ACKed |
| Dry-run peer | Flag-gated eval only; **not** Mesh live / **not** Gate5 canary |

---

## 4. Exit rules (restated)

| Exit | Met? |
|------|------|
| Gate4 **design** exit for DISCUSS_ONLY / eval — written data-handling schedule + secret_handle lifecycle + eval handle oob + dry-run≠live RefuseTransport + no keys committed + Gate1 discuss + Gates 2–3 design-sealed | **YES — DESIGN_SEALED** |
| Gate4 **enable** exit (schedule ACK’d for Mesh live under ENABLE ACK) | **NO** |
| Checklist “Mesh live data / enable seal” | Still **OPEN** for enable path |
| Gate5 canary | **NOT** for execution until ENABLE chain |

---

## 5. Next serial blueprint step (no ask)

**Next (checklist order):** **Gate 5** — advance flip **runbook** toward **DESIGN_SEALED** (**docs / canary procedure only** — **do not** execute canary; still live=DISABLED).  
**Then:** Gate 6 metrics toward DESIGN_SEALED (docs).  
**Later (enable path):** ENABLE_UNDER_FENCES + Gates 2–4 enable seals → Gate5 canary execution under kill-armed I5.

---

## 6. Related

- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GATE2_DESIGN_SEALED.md` · `GATE3_DESIGN_SEALED.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `GEMINI_DRY_RUN_EVIDENCE.md`
- `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` · `council/NOTE_GEMINI_DRY_RUN.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 §5)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`, `is_valid_secret_handle`)

---

*End GATE4_DESIGN_SEALED — design/docs seal for DISCUSS_ONLY eval data policy + secret_handle; live=DISABLED; ENABLE still needs operator ACK; Gate5 canary not authorized.*
