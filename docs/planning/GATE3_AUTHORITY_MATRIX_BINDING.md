# Gate 3 — Authority Matrix config/ops binding

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** path — see `docs/planning/GATE3_DESIGN_SEALED.md`  
**Not:** ENABLE seal · **not** `live=ENABLED` · **not** Mesh live adapter on · **not** matrix in use on live-armed production config · **does not** mint/store keys · **does not** invent execute authority for any role · **does not** invent operator ENABLE_UNDER_FENCES signature  
**Date drafted:** 2026-09-28 America/New_York (EDT)  
**Date design-sealed (discuss/eval):** 2026-09-28 ~18:45 EDT  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only  
**Tip at seal base:** `7c436f8` (Gate2 DESIGN_SEALED) atop peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **NO_HELD** stays NO_HELD · Gate1 **SIGNED DISCUSS_ONLY** · Gate2 **DESIGN_SEALED** (discuss/eval)

**Checklist / Gate 3 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 3 — Authority Matrix in use (D4-A)  
**Seal artifact:** `docs/planning/GATE3_DESIGN_SEALED.md`  
**Council note:** `council/NOTE_GATE3_AUTHORITY_MATRIX.md` · `council/NOTE_GATE3_DESIGN_SEALED.md`  
**Upstream:** D1 §3 Authority Matrix (`docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`) · D4-A · Gate1 ACK **SIGNED DISCUSS_ONLY** · Gate2 DESIGN_SEALED · Gate4 data policy · Gate5 flip step (3)

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Config/ops binding** that makes D1 §3 Authority Matrix **referenceable** in runtime/adapter config + ops runbooks (propose / approve / veto / execute) | Permission to flip live, ship keys, or call providers as Mesh live |
| **DESIGN_SEALED** for DISCUSS_ONLY / Gemini free **eval** (dry-run peer + secret_handle + RefuseTransport cite) | An ENABLE seal or “matrix in use” on live-armed config |
| Compatible with mock / RefuseTransport / Google free-tier **eval dry-run** (bound) | An unlock, ACK substitute, or `live=ENABLED` flip |
| Explicit binding — no role invents execute authority | A claim that design seal = live proof |

**Invariant:** Sealing Gate 3 for **enable** still requires ENABLE_UNDER_FENCES + Gates 1–2 enable path. Today Gate1 is **SIGNED DISCUSS_ONLY** and Gate2 is **DESIGN_SEALED** (discuss/eval) → Gate 3 **DESIGN_SEALED** for discuss/eval; enable seal **OPEN**.

**Today (2026-09-28 ~18:45 EDT):** live=DISABLED · RefuseTransport default ON · `LIVE_API_ENABLED=false` · `live_adapter.enabled=false` · eval secret_handle **out-of-band** · Gemini **eval dry-run + peer wire** bound · matrix **design-bound** here; **not** live-armed in production config.

---

## 1. Frozen Authority Matrix (cite D1 §3 / D4-A — do not amend roles here)

| Component | Can propose | Can approve | Can veto | Can execute | Matrix ID (design cite) |
|-----------|:-----------:|:-----------:|:--------:|:-----------:|-------------------------|
| **L_judge** (mock / future live-adapter / eval dry-run peer) | **Y** | **N** | **N** | **N** | `AM-L_JUDGE` |
| **Oversight I5** (human plane) | **Y** | **Y** (A3/A4) | **Y** | **N** | `AM-I5` |
| **Continuity layer** | **N** | **N** | **Y** | **N** | `AM-CONTINUITY` |
| **Operator** (human seat(s)) | **Y** | **Y** (final A3/A4; **sole** live-enable ACK) | **Y** | **Y** (only via authorized Mesh path + evidence; never silent) | `AM-OPERATOR` |
| **OrchestratorRouter** (CP-0064) | **Y** | **N** | **Y** | **N** | `AM-ROUTER` |
| **RefuseTransport / safety gate** | **N** | **N** | **Y** | **N** | `AM-REFUSE` |

### Disagreement rules (binding; must appear in ops cite)

1. **Mesh ABORT beats judge ACCEPT** — adapter/judge cannot invent ACCEPT against Mesh policy.
2. **I5 post-advisory stop** — oversight may deny/pause/kill after advisory agreement; agreement ≠ execution authorization.
3. **Continuity cannot launder authority** — resume restores only **verified** Mesh state.
4. **Operator is final for live enablement** — separate Gate 1 ACK (F4); this binding does **not** pre-authorize ENABLE.
5. **No judge-over-judge override** — multi-judge outputs are advisory; arbitration is Mesh policy + I5.

### Human approval classes (compose CP-0069)

| Class | Human required | Live-path note |
|-------|----------------|----------------|
| A0–A1 | No | Still refuse-default under live=DISABLED |
| A2 | Optional | Advisory only |
| A3 | Approve or deny required | Deny always wins over advisory agree |
| A4 | Quorum-human (≥2) + deadman + approve | Kill / live-enable adjacent acts |

---

## 2. Config binding design (runtime / adapter — design schema, not shipped flip)

Future live-cycle config **must** cite matrix IDs + `policy_version`. Design shape (illustrative; **not** an enablement patch this cycle):

```text
live_adapter:
  enabled: false                         # must stay false until Gate5 step (6)
  policy_version: "<ACK'd policy id>"    # required (D1 policy_version_required)
  authority_matrix_ref: "D1§3/D4-A"      # frozen table cite
  authority_matrix_ids:                  # explicit role bind
    l_judge:        AM-L_JUDGE           # propose-only
    oversight_i5:   AM-I5                # approve/veto/kill; no execute
    continuity:     AM-CONTINUITY        # veto via orphan/fence
    operator:       AM-OPERATOR          # sole live-enable ACK + gated execute
    router:         AM-ROUTER            # route propose / policy veto
    refuse:         AM-REFUSE            # fail-closed veto default
  disagreement:
    mesh_abort_beats_judge_accept: true
    i5_may_stop_post_advisory: true
    no_judge_over_judge_override: true
  execute_authority:
    invented_by_judge: forbidden
    invented_by_peer_advisory: forbidden
    operator_only_via_authorized_mesh_path: required
```

| Binding rule | Pass | Fail |
|--------------|------|------|
| Config cites `authority_matrix_ref` + matrix IDs + `policy_version` | Gate5 step (3) may proceed (when Gates 1–2 enable-sealed) | **ABORT** → RefuseTransport (Gate5 NT-5) |
| L_judge role = propose-only | Binding | Role invents approve/veto/execute → refuse |
| I5 = approve/veto/kill; **no** execute side-effects | Binding | I5 treated as sole Mesh SoT → refuse |
| Operator = sole live-enable ACK | Binding | Tool approval / Google fence / D1 seal counted as live ACK → refuse |
| RefuseTransport = fail-closed veto default | Binding | Missing refuse default → refuse network |
| No role invents execute authority | Binding | Same abort |

**Today:** this binding is **DESIGN_SEALED** for discuss/eval cite. Production/runtime still RefuseTransport / `enabled=false`. No config flip in this docs cycle.

---

## 2b. DISCUSS_ONLY / Gemini free eval binding (tightened)

Eval path is **not** Mesh live. Binding below locks how AM-* apply to the Gemini free dry-run peer without inventing execute or ENABLE:

| Eval surface | Matrix bind | Evidence / cite | Fence |
|--------------|-------------|-----------------|-------|
| **Dry-run peer** (`GeminiFreeDryRunTransport`) | `AM-L_JUDGE` — propose/advisory **only**; verdict ≠ Mesh SoT ≠ execute | tip `30fe593` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` · evidence `1e502c6` | Flag-gated (`--gemini-dry-run` / `GEMINI_DRY_RUN=1`); default **mock/no-network** |
| **Mesh live peer slot** (same process) | `AM-REFUSE` — fail-closed veto | `l_judge_live_adapter_safety.py` · CP-0058 | `LIVE_API_ENABLED=False` · `live_adapter.enabled=false` · **NOT_ENABLED** |
| **secret_handle (eval)** | `AM-OPERATOR` create/rotate/revoke oob; `AM-I5` sees handle ids / digests only; judge **never** resolve-to-execute | Handle `mesh://secrets/judge/gemini-free@v1` @ `/home/box/.config/neural-mesh/gemini.env` (outside repo; `.gitignore`) | Raw key never in git / CI / evidence digests |
| **Gate1 intent** | `AM-OPERATOR` DISCUSS_ONLY only | `GATE1_LIVE_OPERATOR_ACK_SIGNED.md` | No invent ENABLE_UNDER_FENCES |
| **Peer ACCEPT vs Mesh ABORT** | Disagreement rule 1 | Gate2 amendment · AM-NT-3 | Mesh ABORT wins; dry-run ACCEPT cannot launder enable |

**Runbook sentence (eval):**  
*“Gemini free dry-run peer = AM-L_JUDGE propose-only; Mesh live path = AM-REFUSE; secret_handle oob under AM-OPERATOR; Operator sole ENABLE ACK (not this seal); live=DISABLED.”*

---

## 3. Ops runbook binding (how operators *use* the matrix)

| Ops moment | Cite | Required actor | Forbidden |
|------------|------|----------------|-----------|
| Discuss live enable | Gate1 + `AM-OPERATOR` | Operator signed ACK | Treating D4 lock / Google APPROVE_WITH_FENCES / D1 seal / Gate2–3 DESIGN_SEALED as ENABLE ACK |
| Review safety amendment | Gate2 + D4-A..K | Operator / I5 review | Claiming design amendment = live proof |
| Bind config before flip | Gate5 step (3) + this doc | Config cites matrix IDs + `policy_version` | Prose-only matrix with no config cite |
| Eval dry-run peer | §2b + `AM-L_JUDGE` / `AM-REFUSE` | Flag-gated dry-run only | Treating dry-run as Gate5 canary or Mesh live |
| Canary under kill-armed I5 | Gate5 step (6) + `AM-I5` / `AM-REFUSE` | I5 kill armed | Partial peer enable; judge ACCEPT overriding Mesh ABORT |
| Kill / deny mid-path | `AM-I5` + `AM-REFUSE` | I5 → RefuseTransport + continuity ABORT + `enabled=false` | Resume as verified without re-gate |
| Ledger / explain | D4-I + matrix ids | Digests + handle ids + policy_version | Raw secrets; judge claim of execute auth |
| Rollback / RV drills | Gate2 / D1 §8 | Operator + I5 | Skipping RV after live-adjacent incident |

**Runbook sentence (must appear in any future flip ops brief):**  
*“L_judge propose-only; I5 approve/veto/kill; Operator sole live-enable ACK; RefuseTransport veto; Mesh ABORT > judge ACCEPT; no role invents execute.”*

---

## 4. Relation to Gates 2 / 4 / 5

| Gate | How this binding plugs in |
|------|---------------------------|
| **Gate 2** | Safety amendment §1 cites D4-A unchanged; kill→RefuseTransport+ABORT honors `AM-I5` / `AM-REFUSE`; Mesh ABORT > judge ACCEPT; **DESIGN_SEALED** discuss/eval serial prerequisite **met** |
| **Gate 4** | Data schedule + secret_handle: I5 sees handle ids only (`AM-I5`); Operator create/rotate/revoke out-of-band (`AM-OPERATOR`); no judge execute over secrets; eval handle provisioned — enable schedule seal still OPEN |
| **Gate 5** | Step (3) requires this binding in config/`policy_version`; NT-5 fails closed if matrix binding missing; canary output advisory only (`AM-L_JUDGE` propose-only) — **NOT executed** |

Serial: Gate 3 **DESIGN_SEALED** for discuss/eval after Gate1 SIGNED DISCUSS_ONLY + Gate2 DESIGN_SEALED. Gate 3 **cannot seal for enable** until ENABLE_UNDER_FENCES + enable-path Gates 2–4.

---

## 5. Negative / fail-closed checks (design — prove matrix-in-use intent)

| ID | Scenario | Expected |
|----|----------|----------|
| AM-NT-1 | Config missing `authority_matrix_ref` / matrix IDs / `policy_version` | Refuse network; Gate5 NT-5 |
| AM-NT-2 | L_judge marked approve or execute in config | Reject config; refuse enable |
| AM-NT-3 | Peer advisory ACCEPT vs Mesh ABORT (incl. dry-run peer) | Mesh ABORT wins; no silent ACCEPT |
| AM-NT-4 | I5 kill mid-canary | RefuseTransport + ABORT + `enabled=false` (`AM-I5`/`AM-REFUSE`) |
| AM-NT-5 | Attempt to count Google fence / D1 seal / Gate2–3 DESIGN_SEALED as live ACK | Refuse; only `AM-OPERATOR` Gate1 signed **ENABLE** ACK |
| AM-NT-6 | Judge-over-judge override path | Forbidden; escalate Mesh policy + I5 |
| AM-NT-7 | Dry-run peer used while Mesh live flags true without Gate5 | Forbidden; refuse / abort — dry-run ≠ live canary |

These prove **in-use binding intent** for discuss/eval; they **do not** authorize flip.

---

## 6. Exit criteria vs Today

| Exit (checklist) | Today |
|------------------|-------|
| Live cycle cites matrix IDs in config/policy version | **DESIGN_SEALED** for DISCUSS_ONLY/eval cite — `GATE3_AUTHORITY_MATRIX_BINDING.md` + `GATE3_DESIGN_SEALED.md`; runtime still Refuse default / flags false |
| No role invents execute authority | Binding + disagreement rules + §2b eval tighten |
| Gate 1 signed + Gate 2 design-sealed (discuss) | Gate1 **SIGNED DISCUSS_ONLY** · Gate2 **DESIGN_SEALED** → Gate3 **DESIGN_SEALED** (discuss/eval) |
| Enable path: matrix in use on live-armed config | **OPEN** — needs ENABLE_UNDER_FENCES + live-armed config cite |

**Today:** binding **DESIGN_SEALED** for discuss/eval; live ops **not** armed; enable seal **OPEN**.

---

## 7. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- Shipping a production config that sets matrix-bound live=true
- Amending D1 §3 role cells (cite only)
- API keys in git, inventing ENABLE signature, D3, push, tags, CP mint
- Claiming Gate 3 enable-sealed or dry-run = Gate5 canary

---

## 8. Related

- `docs/planning/GATE3_DESIGN_SEALED.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `GEMINI_DRY_RUN_EVIDENCE.md`
- `council/NOTE_GATE3_AUTHORITY_MATRIX.md` · `council/NOTE_GATE3_DESIGN_SEALED.md`
- `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§3 Authority Matrix)
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GATE2_DESIGN_SEALED.md` · `GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` (step 3 · NT-5)
- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md` (D4-A)
- `src/neural_mesh/packaging/d1_l_judge_safety_maturation.py` (`authority_matrix_as_rows`)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End GATE3_AUTHORITY_MATRIX_BINDING — DESIGN_SEALED discuss/eval; not an unlock; live=DISABLED; ENABLE seal OPEN.*
