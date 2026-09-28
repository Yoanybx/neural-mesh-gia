# Gate 5 — RefuseTransport → live flag flip runbook (DESIGN_SEALED / procedure only)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** — **procedure sealed**; **execute OPEN** · does **not** enable live · **does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED` · **does not** mint or store keys · **does not** authorize real Mesh live Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP · **does not** invent ENABLE_UNDER_FENCES  
**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Date design-sealed:** 2026-09-28 ~18:50 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `5879321` (Gate4 DESIGN_SEALED) atop Gate3 `ce53e7c` / Gate2 `7c436f8` / peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · Gate1 **SIGNED DISCUSS_ONLY** · Gates 2–4 **DESIGN_SEALED** (discuss/eval)

**Seal artifact:** `docs/planning/GATE5_DESIGN_SEALED.md`  
**Checklist / Gate 5 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 5 — Adapter: RefuseTransport → live flag  
**Council note:** `council/NOTE_GATE5_FLIP_RUNBOOK.md` · `council/NOTE_GATE5_DESIGN_SEALED.md`  
**Upstream:** CP-0058 RefuseTransport / must-stay-false · D1 §3 Authority Matrix · D1 §6 I5 kill · Gate1 ACK SIGNED DISCUSS_ONLY · Gate4 data policy DESIGN_SEALED · Google peer spike fences · dry-run `1e502c6` · peer wire `30fe593` (**NOT** a live canary)

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Ordered **DESIGN_SEALED flip procedure** RefuseTransport → controlled live flag (docs) | Permission to flip flags, ship keys, or call Mesh live providers |
| Answer to Gate 5 “flip procedure (design)” + negative / fail-closed tests | A **canary execution** or Mesh live enable |
| Compatible with mock / RefuseTransport / Google free-tier *flag-gated* dry-run | An unlock, ACK substitute, or `live=ENABLED` |
| Explicit **canary NOT STARTED / NOT AUTHORIZED** under DISCUSS_ONLY | A claim that design-seal authorizes flip or that dry-run `30fe593` = canary |

**Invariant:** **Executing** any flip step requires Gates **1–4 enable-ready** + operator **ENABLE_UNDER_FENCES** ACK (serial). Today Gate1 is **SIGNED DISCUSS_ONLY** and Gates 2–4 are **DESIGN_SEALED** for discuss/eval only (ENABLE seals **OPEN**) → procedure may **design-seal**; canary remains **NOT STARTED / NOT AUTHORIZED** — **never partial enable**.

**Today (2026-09-28):** live=DISABLED · Gate1 **DISCUSS_ONLY** · RefuseTransport default ON · `LIVE_API_ENABLED=false` · `live_adapter.enabled=false` · **no keys in repo** · Mesh live = **no real calls** · dry-run peer **≠** canary · **this runbook NOT executed** · canary **NOT AUTHORIZED**.

---

## 1. Preconditions (must all be true before any flip attempt)

| # | Gate | Required artifact | Today |
|---|------|-------------------|-------|
| 1 | Gate 1 | Operator ACK with intent **ENABLE_UNDER_FENCES** (user-written; bots must not invent) naming provider, env, data classes, kill authority, rollback owner | **SIGNED DISCUSS_ONLY** — ENABLE ACK **OPEN / not invented** |
| 2 | Gate 2 | Live safety-case **amendment** **enable**-sealed; mock RV-1..RV-7 drills green; live proof path ready | **DESIGN_SEALED** discuss/eval; ENABLE seal **OPEN** |
| 3 | Gate 3 | Authority Matrix **bound** / live-armed in config/policy_version (propose/approve/veto/execute) | **DESIGN_SEALED** discuss/eval; live-armed **OPEN** |
| 4 | Gate 4 | Data-handling schedule + secret_handle ACK’d for **Mesh live** egress; resolvable **outside** repo | **DESIGN_SEALED** discuss/eval; Mesh live data ENABLE seal **OPEN** |
| — | Kill path | I5 kill armed → RefuseTransport + continuity ABORT + emergency `enabled=false` | Binding in design; **not** live-armed |
| — | Operator ENABLE ACK | Explicit ENABLE_UNDER_FENCES artifact | **Missing** under DISCUSS_ONLY |

If **any** precondition fails → **abort entire procedure** → remain on RefuseTransport / `ENGINE_DISABLED` / `PEER_LIVE_DISABLED`. **Never partial enable.** Under DISCUSS_ONLY today → **all flip attempts forbidden**.

---

## 2. Ordered flip procedure (design — NOT executed / NOT AUTHORIZED today)

Execute **only** after §1 preconditions pass (ENABLE chain). Steps are **serial**. Abort at any step reverts to RefuseTransport and stops.

### Step (1) — Gate 1 ENABLE ACK present

| Check | Pass | Fail |
|-------|------|------|
| Signed ACK artifact names provider(s), env, data classes, kill authority, rollback owner; intent **ENABLE_UNDER_FENCES** | Proceed to (2) | **ABORT** → RefuseTransport; do not touch flags |
| ACK is separate from D4 lock / Google APPROVE_WITH_FENCES / D1 seal / DISCUSS_ONLY | Binding | Same abort |

### Step (2) — Gate 2 safety amendment (enable-ready)

| Check | Pass | Fail |
|-------|------|------|
| Live-path safety-case amendment enable-sealed (real transport, keys, blast radius, compromise) | Proceed to (3) | **ABORT** → RefuseTransport |
| Mock RV-1..RV-7 still green; no silent ACCEPT | Binding | Same abort |

### Step (3) — Gate 3 matrix-bound config (live-armed cite)

| Check | Pass | Fail |
|-------|------|------|
| Runtime / adapter config cites Authority Matrix IDs + `policy_version` | Proceed to (4) | **ABORT** → RefuseTransport |
| L_judge propose-only; I5 approve/veto; Operator sole live-enable; RefuseTransport veto | Binding | Same abort |
| No role invents execute authority | Binding | Same abort |

### Step (4) — Gate 4 handles + data schedule (Mesh live ACK’d)

| Check | Pass | Fail |
|-------|------|------|
| `GATE4_LIVE_DATA_POLICY` schedule applies to ACK’d Mesh live env | Proceed to (5) | **ABORT** → RefuseTransport |
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

**Note:** Health check does **not** flip flags. Flags remain false until step (6) under kill-armed I5. Dry-run peer `30fe593` does **not** satisfy step (6).

### Step (6) — Single canary under kill-armed I5

| Rule | Detail |
|------|--------|
| Kill armed | I5 kill path ready: → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Scope | **One** canary call only; rate floors (CP-0058); redacted/synthetic prompt only |
| Flags | Only after (1)–(5): controlled set of `live_adapter.enabled` / `LIVE_API_ENABLED` in ACK’d env — **not** this docs cycle |
| Role of output | Evaluation evidence / advisory digest only — **not** Mesh SoT, M1 consensus, or execute authority |
| Anomaly | Immediate I5 kill → RefuseTransport + ABORT + `enabled=false` |
| Never | Partial enable of peer slots; multi-canary fan-out; Vertex paid without separate approval; treat dry-run as canary |

**Today:** Step (6) **NOT STARTED / NOT AUTHORIZED** under DISCUSS_ONLY.

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
| NT-2 | Caller requests live while Gate 1 is DISCUSS_ONLY / ENABLE unsigned | Refuse; no flag flip |
| NT-3 | Missing / invalid `secret_handle` (or raw `sk-` / Bearer) | ABORT `ENGINE_AUTH` or refuse; never accept raw secret as handle |
| NT-4 | Audit sink down | ABORT `NO_AUDIT`; no-action |
| NT-5 | Missing Gate 2 amendment / Gate 3 matrix binding / Gate 4 schedule (enable path) | Refuse network; **no partial enable** |
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

Helpers (no Mesh live network this docs cycle):

- `neural_mesh.packaging.l_judge_live_adapter_safety.RefuseTransport`
- `neural_mesh.packaging.google_l_judge_peer_spike` (`LIVE_API_ENABLED = False`; live path → refuse; dry-run flag ≠ canary)

---

## 5. Explicit: NOT executed / NOT AUTHORIZED today

| Claim | Today |
|-------|-------|
| This runbook **DESIGN_SEALED** (procedure) | **Yes** (this document + `GATE5_DESIGN_SEALED.md`) |
| Flip / canary executed | **No — NOT STARTED / NOT AUTHORIZED** |
| `live_adapter.enabled` / `LIVE_API_ENABLED` | **false** |
| Keys minted into repo / Mesh live Gemini calls | **No** |
| Gates 1–4 discuss/eval sealed | **Yes** (Gate1 DISCUSS_ONLY; 2–4 DESIGN_SEALED) |
| Gates 1–4 **enable**-ready + ENABLE ACK | **No** → canary forbidden |
| Dry-run peer `30fe593` | Eval only — **NOT** Gate5 canary |
| D3 / push / tag / CP | **No** |

---

## 6. Gate 5 seal status (today)

| Prerequisite | Today |
|--------------|-------|
| Documented flip runbook | **DESIGN_SEALED** (procedure) |
| Negative tests / fail-closed specified | **DESIGN_SEALED** (procedure) |
| Default binding RefuseTransport | **In force** |
| Flags false | **Held** |
| Canary | **NOT STARTED / NOT AUTHORIZED** under DISCUSS_ONLY |
| Gates 1–4 enable + ENABLE ACK | **OPEN** → Gate 5 **execute OPEN** |
| Flip / canary | **NOT executed** |

**Exit (from checklist):** Documented flip runbook + negative tests still prove refuse-default; enable remains operator-gated.  
**Today:** procedure **DESIGN_SEALED**; flip **not** executed; execute exit **not** met.

---

## 7. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- API keys in repo, env commits, or CI secrets files
- Real Mesh live Gemini / Vertex / AI Studio production traffic
- Treating dry-run peer `30fe593` as Gate5 canary
- Starting D3 or flipping `MESH_PERF_EXPERIMENTAL`
- Push, tags, pkg0190, v0.19, GIA, Raft/N>2, train-70B, SaaS
- Minting a feature CP for this runbook (docs-only)
- Inventing ENABLE_UNDER_FENCES or executing steps (1)–(7) under DISCUSS_ONLY
- Partial enable of any live peer slot

---

## 8. Related

- `docs/planning/GATE5_DESIGN_SEALED.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 5 exit)
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `docs/planning/HOLD_MOCK_NEXT.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `council/NOTE_GATE5_FLIP_RUNBOOK.md` · `council/NOTE_GATE5_DESIGN_SEALED.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GATE2_DESIGN_SEALED.md` · `GATE3_DESIGN_SEALED.md` · `GATE4_DESIGN_SEALED.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 §6 RefuseTransport / §8 must-stay-false)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§3 matrix · §6 I5 kill · §8 containment)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `docs/schema/judge/live_adapter_safety_v0.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`, `evaluate_enablement_gates`)
- `src/neural_mesh/packaging/google_l_judge_peer_spike.py` (`LIVE_API_ENABLED=False`)

---

*End GATE5_LIVE_FLAG_FLIP_RUNBOOK — DESIGN_SEALED procedure; canary NOT STARTED / NOT AUTHORIZED; live=DISABLED; LIVE_API_ENABLED=False; ENABLE still needs operator ACK.*
