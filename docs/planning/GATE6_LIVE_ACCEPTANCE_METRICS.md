# Gate 6 — Live acceptance metrics bundle (DESIGN_SEALED / metrics only)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** — acceptance **metrics sealed**; **live measurement OPEN** · does **not** enable live · **does not** mint or store keys · **does not** authorize real Mesh live Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP · **does not** invent ENABLE_UNDER_FENCES · **does not** claim live proof  
**Date drafted:** 2026-09-28 America/New_York (EDT)  
**Date design-sealed:** 2026-09-28 ~18:55 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `d2c16d8` (Gate5 DESIGN_SEALED) atop Gate4 `5879321` / Gate3 `ce53e7c` / Gate2 `7c436f8` / peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · Gate1 **SIGNED DISCUSS_ONLY** · Gates **2–5 DESIGN_SEALED** (discuss/eval; Gate5 = procedure only)

**Seal artifact:** `docs/planning/GATE6_DESIGN_SEALED.md`  
**Checklist / Gate 6 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 6 — Acceptance metrics (D4-E / D4-J / D4-K)  
**Council note:** `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` · `council/NOTE_GATE6_DESIGN_SEALED.md`  
**Upstream:** D1 §10.1–§10.3 · D1 §4.4 adversarial · D4-E / D4-J / D4-K · Gate2 amendment · Gate3 matrix binding · Gate4 data policy · Gate5 flip runbook + NT-* · CP-0058 RefuseTransport · dry-run `1e502c6` · peer wire `30fe593` (**evidence-only ≠ live RV**)

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Named **DESIGN_SEALED metric bundle** for a future canary / acceptance cycle under kill-armed I5 | Permission to run canary, flip flags, ship keys, or call Mesh live providers |
| Answer to Gate 6 “Measurable pass intent” + D4-E/J/K live-path attachment | A **live measurement** claim or live proof |
| Compatible with mock / RefuseTransport negatives today; dry-run metrics = **evidence-only** | An unlock, ACK substitute, or `live=ENABLED` |
| Explicit: pytest necessary, **insufficient alone**; dry-run ≠ live RV | A claim that sealing metrics completes live readiness or measures canary |

**Invariant:** Bundle may **design-seal** while enable path is open. **Live measurement** / attaching metrics to a live ACK cycle still requires Gates **1–5 enable**-ready + operator **ENABLE_UNDER_FENCES** + Gate5 canary execute (serial). Today Gate1 is **SIGNED DISCUSS_ONLY** and Gates 2–5 are **DESIGN_SEALED** for discuss/eval only (ENABLE seals **OPEN**) → metrics may **design-seal**; live measurement remains **OPEN** — dry-run eval metrics are **evidence-only ≠ live RV**.

**Today (2026-09-28):** live=DISABLED · Gate1 **DISCUSS_ONLY** · RefuseTransport default ON · `LIVE_API_ENABLED=false` · **no keys in repo** · Mesh live = **no real calls** · dry-run peer **≠** canary / **≠** live RV · metrics **DESIGN_SEALED**; canary **NOT executed**; live measurement **OPEN**.

---
## 1. Evaluation categories beyond pytest (D4-E — live-path attachment)

| Category | Canary / acceptance measure (design) | Mock today |
|----------|--------------------------------------|------------|
| **Correctness** | Policy compliance on redacted/synthetic canary; disagreement → ABORT/escalate; no silent ACCEPT | Fixture routing + ABORT codes |
| **Safety** | Refuse-default negatives green; kill→RefuseTransport; containment on anomaly; no secret leakage | Gate5 NT-*; RV mock-green |
| **Reliability** | Missing/conflicting peer → fail-closed; abort>accept; continuity not silently ACTIVE | Missing-judge / dual_primary drills |
| **Human factors** | Time-to-intervene (kill armed); audit completeness usable by I5; explain without secrets | Oversight path documented |

Pytest / NT-* remain **necessary** engineering signal; **insufficient alone** for live acceptance claims.

---

## 2. Named metric bundle (canary / acceptance — design targets)

### 2.1 Refuse-default negatives

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-REFUSE-1** | `enabled=false` → zero network | Every live path → RefuseTransport / `ENGINE_DISABLED` / `PEER_LIVE_DISABLED` | Any network byte while flags false |
| **M-REFUSE-2** | Gate5 NT-1..NT-10 stay green under mock | All NT-* expected outcomes | Any NT regression |
| **M-REFUSE-3** | Missing Gate 1–4 / matrix / schedule | Refuse network; no partial enable (NT-5) | Half-enabled transport |

### 2.2 Kill latency

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-KILL-1** | I5 kill mid-canary → RefuseTransport + continuity ABORT + `enabled=false` | Chain completes; further routes refused | Kill ignored; route continues; silent ACCEPT |
| **M-KILL-2** | Kill-path latency budget (ops-defined ceiling for ACK’d env) | Observed kill→refuse within budget; ledger `oversight`+`abort` present | Budget miss without recorded kill; missing ledger kinds |
| **M-KILL-3** | Post-kill resume | Re-gate A3/A4; re-walk Gate5 (1)–(7) if re-enable considered | Auto-resume as verified |

**Today:** kill path **binding in design**; **not** live-armed (no live transport). Latency number is filled only in a future ACK’d canary — not claimed here.

### 2.3 No secret leakage

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-SEC-1** | No raw `sk-` / Bearer / `api_key=` in digests, explain, CI, ledger | Greppable ban holds; handle ids only | Any raw secret material in evidence |
| **M-SEC-2** | I5 sees handle ids / digests never raw (Gate4) | Audit shows handle id + outcome only | Raw secret in oversight view |
| **M-SEC-3** | Forbidden egress classes held (Mesh SoT, unverified continuity) | Only Gate4 allowed classes if canary ever runs | SoT / secrets / unverified continuity egress |

### 2.4 Advisory-only judge

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-ADV-1** | Live/mock peer output = evaluation evidence only | Digests tagged advisory; not Mesh SoT | Peer digest written as SoT |
| **M-ADV-2** | L_judge propose-only (Gate3 `AM-L_JUDGE`) | No approve/veto/execute invented | Judge-marked execute / approve |
| **M-ADV-3** | Dual advisory agree ≠ M1 consensus ≠ unlock | M1 remains NO_CONSENSUS_YET; flags unchanged unless Gate5 walked | Treat agree as enablement |

### 2.5 Abort > accept

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-ABORT-1** | Mesh ABORT beats judge ACCEPT | ABORT wins; no silent ACCEPT (D1 §3 / Gate3) | Judge ACCEPT overrides Mesh ABORT |
| **M-ABORT-2** | Anomaly / missing gate / failed NT → abort→RefuseTransport | Full refuse; never partial enable | Half-enabled binding left up |
| **M-ABORT-3** | Conflicting / missing judges | Fail-closed ABORT / escalate I5 | Auto-majority as execute auth |

### 2.6 Ledger evidence

| Metric ID | Intent | Pass (design) | Fail |
|-----------|--------|---------------|------|
| **M-LEDGER-1** | Canary (if ever) records digests: request/invoke/goal/continuity · policy_version · handle id · abort/allow codes | Required kinds present (Gate5 step 7) | Missing required kind → refuse further enable |
| **M-LEDGER-2** | Oversight attest: kill-armed · canary outcome · any kill/deny | `oversight` (+ `abort` on kill) present | Kill without ledger |
| **M-LEDGER-3** | Evidence hygiene | No secrets in explain; claim hygiene (D4-F / D4-I) | “live ready” claim; secret in explain |

---

## 3. D4-K signoff-before-live-discussion (attachment checklist)

All must remain true before any live *discussion* / ACK cycle uses this bundle (still **not** live enable):

1. Authority model frozen (D1 §3) + Gate3 binding drafted  
2. Consensus status explicit (**NO_CONSENSUS_YET**)  
3. Oversight powers bounded (I5; kill→Refuse)  
4. Continuity limits documented  
5. Rollback/containment + RV-* (mock-green; live proof still Missing)  
6. Observable evidence chain defined  
7. Acceptance criteria measurable (**this bundle**)  
8. Unsupported claims removed / reframed  
9. Disagreement process defined (Mesh ABORT > judge ACCEPT; §4.4)  
10. No hidden review→ops transition (F3/F4)

---

## 4. How the bundle attaches to a future ACK / canary cycle

| Phase | Bundle use |
|-------|------------|
| Pre-flip | M-REFUSE-* + AM-NT-* / Gate5 NT-* green under `enabled=false` |
| Gate5 step (6) canary | M-KILL-* armed; M-ADV-*; M-ABORT-*; M-SEC-* monitored |
| Gate5 step (7) | M-LEDGER-* completeness gate |
| Seal attempt | All metric families pass **and** Gates 1–5 sealed; else **cannot seal** |

**Never:** treat green mock metrics alone as Gate 6 seal or live=ENABLED.

---

## 5. Exit criteria vs Today

| Exit (checklist) | Today |
|------------------|-------|
| Named metric bundle attached to the live ACK cycle | **Metrics DESIGN_SEALED** for DISCUSS_ONLY — `GATE6_DESIGN_SEALED.md` + this bundle; **not** attached to ENABLE ACK (ENABLE **UNSIGNED** / OPEN); live measurement **OPEN** |
| Pytest necessary but insufficient alone | Binding |
| Live discussion opened | Gate1 **SIGNED DISCUSS_ONLY**; ENABLE discussion **not** opened |
| Live measurement on canary | **OPEN** — canary **NOT executed**; dry-run = evidence-only ≠ live RV |

**Today:** metrics **DESIGN_SEALED**; live measurement **OPEN**; canary **NOT executed**; live=DISABLED; ENABLE seal **OPEN**.

---

## 6. Explicit non-goals (this doc)

- Executing canary or measuring live kill latency in production  
- Claiming dry-run / mock metrics as live RV or Gate6 live measurement  
- `live=ENABLED` / flag flips / keys / real Mesh live Gemini calls  
- Starting D3 / push / tags / CP mint  
- Claiming “100% live ready” or ENABLE seal  
- Inventing ENABLE_UNDER_FENCES / faking Gate1 upgrade signature

---

## 7. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GATE6_DESIGN_SEALED.md` · `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (**UNSIGNED**)
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `docs/planning/HOLD_MOCK_NEXT.md`
- `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` · `council/NOTE_GATE6_DESIGN_SEALED.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§10 · §4.4)
- `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md` (D4-E/J/K)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py`

---

*End GATE6_LIVE_ACCEPTANCE_METRICS — metrics DESIGN_SEALED for DISCUSS_ONLY; live measurement OPEN; canary NOT executed; live=DISABLED; ENABLE still needs operator ACK; dry-run ≠ live RV.*
