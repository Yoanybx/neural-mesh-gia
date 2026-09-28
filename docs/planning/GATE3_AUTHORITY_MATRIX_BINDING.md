# Gate 3 — Authority Matrix config/ops binding (DESIGN ONLY)

**Status:** **DESIGN ONLY** — does **not** enable live · **does not** mint or store keys · **does not** authorize real Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP · **does not** invent execute authority for any role.  
**Date drafted:** 2026-09-28 America/New_York (EDT)  
**Author (draft only):** Grok Bot (Staff Eng — docs only)  
**Tip at draft:** `001211b` (Gate 2 safety-case amendment) atop Gate5 `45ccc16` / Gate4 `8f2eea6` / Gate1 draft `0b6353c` / checklist `8c771a7`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **Gate 1 UNSIGNED** · Gates **1–2 / 4–6 not sealed**

**Checklist / Gate 3 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 3 — Authority Matrix in use (D4-A)  
**Council note:** `council/NOTE_GATE3_AUTHORITY_MATRIX.md`  
**Upstream:** D1 §3 Authority Matrix (`docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`) · D4-A · Gate1 ACK draft §3 · Gate2 amendment §1 · Gate4 data policy · Gate5 flip step (3)

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Config/ops binding design** that makes D1 §3 Authority Matrix **referenceable** in runtime/adapter config + ops runbooks (propose / approve / veto / execute) | Permission to flip live, ship keys, or call providers |
| Answer to Gate 3 “In use” row — matrix not prose-only | A Gate 3 **seal** (Gate 1 unsigned → Gate 3 **cannot seal**) |
| Compatible with mock / RefuseTransport / Google free-tier *design* dry-run | An unlock, ACK substitute, or `live=ENABLED` flip |
| Explicit **design binding draft** — no role invents execute authority | A claim that drafting this binding completes Gate 3 exit |

**Invariant:** This document may be drafted while earlier gates are open. **Sealing** Gate 3 still requires Gates **1–2** satisfied first (serial). Today Gate 1 is **UNSIGNED** and Gate 2 cannot seal (Missing live proof), so Gate 3 remains **OPEN** even with this binding present.

**Today (2026-09-28):** live=DISABLED · RefuseTransport default ON · `LIVE_API_ENABLED=false` · `live_adapter.enabled=false` · **no keys** · **no real calls** · matrix **design-bound** here; **not** live-armed in production config.

---

## 1. Frozen Authority Matrix (cite D1 §3 / D4-A — do not amend roles here)

| Component | Can propose | Can approve | Can veto | Can execute | Matrix ID (design cite) |
|-----------|:-----------:|:-----------:|:--------:|:-----------:|-------------------------|
| **L_judge** (mock / future live-adapter) | **Y** | **N** | **N** | **N** | `AM-L_JUDGE` |
| **Oversight I5** (human plane) | **Y** | **Y** (A3/A4) | **Y** | **N** | `AM-I5` |
| **Continuity layer** | **N** | **N** | **Y** | **N** | `AM-CONTINUITY` |
| **Operator** (human seat(s)) | **Y** | **Y** (final A3/A4; **sole** live-enable ACK) | **Y** | **Y** (only via authorized Mesh path + evidence; never silent) | `AM-OPERATOR` |
| **OrchestratorRouter** (CP-0064) | **Y** | **N** | **Y** | **N** | `AM-ROUTER` |
| **RefuseTransport / safety gate** | **N** | **N** | **Y** | **N** | `AM-REFUSE` |

### Disagreement rules (binding; must appear in ops cite)

1. **Mesh ABORT beats judge ACCEPT** — adapter/judge cannot invent ACCEPT against Mesh policy.
2. **I5 post-advisory stop** — oversight may deny/pause/kill after advisory agreement; agreement ≠ execution authorization.
3. **Continuity cannot launder authority** — resume restores only **verified** Mesh state.
4. **Operator is final for live enablement** — separate Gate 1 ACK (F4); this binding does **not** pre-authorize.
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
| Config cites `authority_matrix_ref` + matrix IDs + `policy_version` | Gate5 step (3) may proceed (when Gates 1–2 sealed) | **ABORT** → RefuseTransport (Gate5 NT-5) |
| L_judge role = propose-only | Binding | Role invents approve/veto/execute → refuse |
| I5 = approve/veto/kill; **no** execute side-effects | Binding | I5 treated as sole Mesh SoT → refuse |
| Operator = sole live-enable ACK | Binding | Tool approval / Google fence / D1 seal counted as live ACK → refuse |
| RefuseTransport = fail-closed veto default | Binding | Missing refuse default → refuse network |
| No role invents execute authority | Binding | Same abort |

**Today:** this binding is **design text**. Production/runtime still RefuseTransport / `enabled=false`. No config flip in this docs cycle.

---

## 3. Ops runbook binding (how operators *use* the matrix)

| Ops moment | Cite | Required actor | Forbidden |
|------------|------|----------------|-----------|
| Discuss live enable | Gate1 + `AM-OPERATOR` | Operator signed ACK | Treating D4 lock / Google APPROVE_WITH_FENCES / D1 seal as ACK |
| Review safety amendment | Gate2 + D4-A..K | Operator / I5 review | Claiming design amendment = live proof |
| Bind config before flip | Gate5 step (3) + this doc | Config cites matrix IDs + `policy_version` | Prose-only matrix with no config cite |
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
| **Gate 2** | Safety amendment §1 cites D4-A unchanged; kill→RefuseTransport+ABORT honors `AM-I5` / `AM-REFUSE`; Mesh ABORT > judge ACCEPT |
| **Gate 4** | Data schedule + secret_handle: I5 sees handle ids only (`AM-I5`); Operator create/rotate/revoke out-of-band (`AM-OPERATOR`); no judge execute over secrets |
| **Gate 5** | Step (3) requires this binding in config/`policy_version`; NT-5 fails closed if matrix binding missing; canary output advisory only (`AM-L_JUDGE` propose-only) |

Serial seal rule: Gate 3 **cannot seal** while Gate 1 **UNSIGNED** (and Gate 2 still Missing live proof / cannot seal).

---

## 5. Negative / fail-closed checks (design — prove matrix-in-use intent)

| ID | Scenario | Expected |
|----|----------|----------|
| AM-NT-1 | Config missing `authority_matrix_ref` / matrix IDs / `policy_version` | Refuse network; Gate5 NT-5 |
| AM-NT-2 | L_judge marked approve or execute in config | Reject config; refuse enable |
| AM-NT-3 | Peer advisory ACCEPT vs Mesh ABORT | Mesh ABORT wins; no silent ACCEPT |
| AM-NT-4 | I5 kill mid-canary | RefuseTransport + ABORT + `enabled=false` (`AM-I5`/`AM-REFUSE`) |
| AM-NT-5 | Attempt to count Google fence / D1 seal as live ACK | Refuse; only `AM-OPERATOR` Gate1 signed ACK |
| AM-NT-6 | Judge-over-judge override path | Forbidden; escalate Mesh policy + I5 |

These prove **in-use binding intent**; they **do not** authorize flip.

---

## 6. Exit criteria vs Today

| Exit (checklist) | Today |
|------------------|-------|
| Live cycle cites matrix IDs in config/policy version | **Design binding drafted** — `GATE3_AUTHORITY_MATRIX_BINDING.md`; runtime still Refuse default / flags false |
| No role invents execute authority | Binding in design + disagreement rules |
| Gate 1 signed + Gate 2 sealable | Gate 1 **UNSIGNED** · Gate 2 amendment design-only / Missing live proof → Gate 3 **cannot seal** |

**Today:** binding **drafted as design**; live ops **not** armed; Gate 3 **OPEN / cannot seal**.

---

## 7. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- Shipping a production config that sets matrix-bound live=true
- Amending D1 §3 role cells (cite only)
- API keys, real Gemini/Vertex calls, D3, push, tags, CP mint
- Claiming Gate 3 sealed or “matrix in use” as live proof

---

## 8. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `council/NOTE_GATE3_AUTHORITY_MATRIX.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§3 Authority Matrix)
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` (§3 summary)
- `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` (step 3 · NT-5)
- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md` (D4-A)
- `src/neural_mesh/packaging/d1_l_judge_safety_maturation.py` (`authority_matrix_as_rows`)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End GATE3_AUTHORITY_MATRIX_BINDING — DESIGN ONLY; not an unlock; live=DISABLED; Gate 1 UNSIGNED → Gate 3 cannot seal.*
