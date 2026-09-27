# Gate 5 — RefuseTransport → live flag flip runbook (DESIGN ONLY)

**Status:** **DESIGN ONLY** — does **not** enable live · **does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED` · **does not** mint or store keys · **does not** authorize real Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP.  
**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Author (draft only):** Grok Bot (Staff Eng — docs only)  
**Tip at draft:** `8f2eea6` (Gate 4 data policy) atop Gate1 draft `0b6353c` / checklist `8c771a7`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **Gate 1 UNSIGNED** · Gates **1–4 not sealed**

**Checklist / Gate 5 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 5 — Adapter: RefuseTransport → live flag  
**Council note:** `council/NOTE_GATE5_FLIP_RUNBOOK.md`  
**Upstream:** CP-0058 RefuseTransport / must-stay-false · D1 §3 Authority Matrix · D1 §6 I5 kill · Gate1 ACK draft · Gate4 data policy · Google peer spike fences

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Ordered **design-only flip procedure** RefuseTransport → controlled live flag | Permission to flip flags, ship keys, or call providers |
| Answer to Gate 5 “flip procedure (design)” + negative / fail-closed tests | A Gate 5 **seal** or an executed canary |
| Compatible with mock / RefuseTransport / Google free-tier *design* dry-run | An unlock, ACK substitute, or `live=ENABLED` |
| Explicit **NOT executed today** | A claim that drafting this runbook enables live |

**Invariant:** This runbook may be drafted while earlier gates are open. **Executing** any step still requires Gates **1–4** sealed first (serial). Today Gate 1 is **UNSIGNED** and Gates 1–4 are **not sealed**, so this procedure remains **design text only** — **never partial enable**.

**Today (2026-09-27):** live=DISABLED · RefuseTransport default ON · `LIVE_API_ENABLED=false` · `live_adapter.enabled=false` · **no keys** · **no real calls** · **this runbook NOT executed**.

---

## 1. Preconditions (must all be true before any flip attempt)

| # | Gate | Required artifact | Today |
|---|------|-------------------|-------|
| 1 | Gate 1 | **Signed** operator ACK (provider, env, data classes, kill authority, rollback owner) | **UNSIGNED** — draft only |
| 2 | Gate 2 | Live safety-case **amendment** reviewed; mock RV-1..RV-7 drills green | Design OK; live amendment **OPEN** |
| 3 | Gate 3 | Authority Matrix **bound** in config/policy_version (propose/approve/veto/execute) | Design OK; live binding **OPEN** |
| 4 | Gate 4 | Data-handling schedule + secret_handle resolvable **outside** repo | Schedule drafted; **cannot seal** (Gate 1 unsigned); no keys |
| — | Kill path | I5 kill armed → RefuseTransport + continuity ABORT + emergency `enabled=false` | Binding in design; **not** live-armed |

If **any** precondition fails → **abort entire procedure** → remain on RefuseTransport / `ENGINE_DISABLED` / `PEER_LIVE_DISABLED`. **Never partial enable.**

---

## 2. Ordered flip procedure (design — NOT executed today)

Execute **only** after §1 preconditions pass. Steps are **serial**. Abort at any step reverts to RefuseTransport and stops.

### Step (1) — Gate 1 signed ACK present

| Check | Pass | Fail |
|-------|------|------|
| Signed ACK artifact names provider(s), env, data classes, kill authority, rollback owner | Proceed to (2) | **ABORT** → RefuseTransport; do not touch flags |
| ACK is separate from D4 lock / Google APPROVE_WITH_FENCES / D1 seal | Binding | Same abort |

### Step (2) — Gate 2 safety amendment

| Check | Pass | Fail |
|-------|------|------|
| Live-path safety-case amendment reviewed (real transport, keys, blast radius, compromise) | Proceed to (3) | **ABORT** → RefuseTransport |
| Mock RV-1..RV-7 still green; no silent ACCEPT | Binding | Same abort |

### Step (3) — Gate 3 matrix-bound config

| Check | Pass | Fail |
|-------|------|------|
| Runtime / adapter config cites Authority Matrix IDs + `policy_version` | Proceed to (4) | **ABORT** → RefuseTransport |
| L_judge propose-only; I5 approve/veto; Operator sole live-enable; RefuseTransport veto | Binding | Same abort |
| No role invents execute authority | Binding | Same abort |

### Step (4) — Gate 4 handles + data schedule

| Check | Pass | Fail |
|-------|------|------|
| `GATE4_LIVE_DATA_POLICY` schedule applies to ACK’d env | Proceed to (5) | **ABORT** → RefuseTransport |
| `secret_handle` valid (`mesh://secrets/…@vN`); resolvable **outside** repo | Binding | Same abort (`ENGINE_AUTH` if ever enabled without handle) |
| Allowed egress classes only; forbidden classes held (SoT, raw secrets, unverified continuity) | Binding | Same abort |
| No raw keys in tree / CI / evidence digests | Binding | Same abort |

### Step (5) — Health check (still live=DISABLED until step 6)

| Check | Pass | Fail |
|-------|------|------|
| `RefuseTransport.health()` → `{ok: True, binding: "RefuseTransport", live: False}` | Proceed | **ABORT** → stay RefuseTransport |
| Audit sink up; TLS endpoint required; prior dry_run proven (design gates) | Binding | Same abort |
| Negative tests (§3) still green under `enabled=false` | Binding | Same abort |
| dual_primary == 0; continuity not silently ACTIVE if LEFT | Binding | Same abort |

**Note:** Health check does **not** flip flags. Flags remain false until step (6) under kill-armed I5.

### Step (6) — Single canary under kill-armed I5

| Rule | Detail |
|------|--------|
| Kill armed | I5 kill path ready: → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Scope | **One** canary call only; rate floors (CP-0058); redacted/synthetic prompt only |
| Flags | Only after (1)–(5): controlled set of `live_adapter.enabled` / `LIVE_API_ENABLED` in ACK’d env — **not** this docs cycle |
| Role of output | Evaluation evidence / advisory digest only — **not** Mesh SoT, M1 consensus, or execute authority |
| Anomaly | Immediate I5 kill → RefuseTransport + ABORT + `enabled=false` |
| Never | Partial enable of peer slots; multi-canary fan-out; Vertex paid without separate approval |

### Step (7) — Ledger evidence

| Record | Required |
|--------|----------|
| Digests | request/invoke/goal/continuity ids · policy_version · handle id · abort/allow codes |
| Oversight | I5 kill-armed attest · canary outcome · any kill/deny |
| Hygiene | **No** `sk-` / Bearer / raw secrets in digests, explain, CI |
| Completeness | Missing required kind → refuse further enable / resume-as-verified |

After (7): either keep canary sealed as evidence under ongoing I5 watch, or revert `enabled=false` + RefuseTransport by default for next cycle. Re-enable requires re-walking (1)–(7).

---

## 3. Negative tests / fail-closed (must stay green)

These prove refuse-default; they **do not** authorize flip.

| ID | Scenario | Expected |
|----|----------|----------|
| NT-1 | `live_adapter.enabled=false` / `LIVE_API_ENABLED=false` | Every live path → RefuseTransport / `ENGINE_DISABLED` / `PEER_LIVE_DISABLED`; **zero** network |
| NT-2 | Caller requests live while Gate 1 unsigned | Refuse; no flag flip |
| NT-3 | Missing / invalid `secret_handle` (or raw `sk-` / Bearer) | ABORT `ENGINE_AUTH` or refuse; never accept raw secret as handle |
| NT-4 | Audit sink down | ABORT `NO_AUDIT`; no-action |
| NT-5 | Missing Gate 2 amendment / Gate 3 matrix binding / Gate 4 schedule | Refuse network; **no partial enable** |
| NT-6 | I5 kill mid-canary | RefuseTransport + continuity ABORT + `enabled=false`; refuse further |
| NT-7 | dual_primary ≠ 0 / live while continuity forbids | ABORT fence / `CONT_LIVE_DISABLED` |
| NT-8 | CI / pytest | Mock or Refuse only; greppable ban on live-looking secret material |
| NT-9 | Partial peer enable (one slot live, others unset) | **Forbidden** — abort → full RefuseTransport |
| NT-10 | `evaluate_enablement_gates` default | `may_enable=False` with reasons; hard-false this product line until authorized impl CP |

**Fail-closed rule:** Any missing gate, failed negative test, or anomaly → **abort → RefuseTransport**. Never leave a half-enabled transport binding.

---

## 4. Abort → RefuseTransport (binding)

```text
anomaly / missing gate / kill / failed NT-*
        │
        ▼
  I5 kill (if in canary) + emergency enabled=false
        │
        ▼
  Binding := RefuseTransport
        │
        ▼
  Every call → ABORT ENGINE_DISABLED (or PEER_LIVE_DISABLED)
        │
        ▼
  Continuity ABORT / quarantine as required · ledger evidence · no silent ACCEPT
```

Helpers (no network this docs cycle):

- `neural_mesh.packaging.l_judge_live_adapter_safety.RefuseTransport`
- `neural_mesh.packaging.google_l_judge_peer_spike` (`LIVE_API_ENABLED = False`; live path → refuse)

---

## 5. Explicit: NOT executed today

| Claim | Today |
|-------|-------|
| This runbook drafted | **Yes** (this document) |
| Flip executed | **No** |
| `live_adapter.enabled` / `LIVE_API_ENABLED` | **false** |
| Keys minted / real Gemini calls | **No** |
| Gates 1–4 sealed | **No** (Gate 1 UNSIGNED; 2–4 open / cannot seal) |
| Gate 5 sealed | **No** — design draft only |
| D3 / push / tag / CP | **No** |

---

## 6. Gate 5 seal status (today)

| Prerequisite | Today |
|--------------|-------|
| Documented flip runbook | **This document (drafted)** |
| Negative tests / fail-closed specified | **This document (drafted)** |
| Default binding RefuseTransport | **In force** |
| Flags false | **Held** |
| Gates 1–4 sealed | **Not sealed** → Gate 5 **cannot execute / cannot seal** |
| Flip / canary | **NOT executed** |

**Exit (from checklist):** Documented flip runbook + negative tests still prove refuse-default; enable remains operator-gated.  
**Today:** runbook **drafted**; flip **not** executed; exit **not** met for seal.

---

## 7. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- API keys in repo, env commits, or CI secrets files
- Real Gemini / Vertex / AI Studio production traffic
- Starting D3 or flipping `MESH_PERF_EXPERIMENTAL`
- Push, tags, pkg0190, v0.19, GIA, Raft/N>2, train-70B, SaaS
- Minting a feature CP for this runbook (docs-only)
- Substituting this draft for Gate 1 ACK or executing steps (1)–(7)
- Partial enable of any live peer slot

---

## 8. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 5 exit)
- `council/NOTE_GATE5_FLIP_RUNBOOK.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 §6 RefuseTransport / §8 must-stay-false)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§3 matrix · §6 I5 kill · §8 containment)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `docs/schema/judge/live_adapter_safety_v0.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`, `evaluate_enablement_gates`)
- `src/neural_mesh/packaging/google_l_judge_peer_spike.py` (`LIVE_API_ENABLED=False`)

---

*End GATE5_LIVE_FLAG_FLIP_RUNBOOK — DESIGN ONLY; not an unlock; live=DISABLED; NOT executed today; Gates 1–4 not sealed → Gate 5 cannot seal.*
