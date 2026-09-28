# Gate 4 — Live data policy + secret_handle (DESIGN ONLY)

**Status:** **DESIGN ONLY** — does **not** enable live · **does not** mint or store keys · **does not** authorize real Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP.  
**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Author (draft only):** Grok Bot (Staff Eng — docs only)  
**Tip at draft:** `0b6353c` (Gate 1 ACK draft unsigned) atop `8c771a7` (live readiness checklist)  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **Gate 1 UNSIGNED**

**Checklist / Gate 4 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 4 — Keys + data policy  
**Council note:** `council/NOTE_GATE4_DATA_POLICY.md`  
**Upstream:** CP-0058 secret_handle / RefuseTransport · D1 §7.2 · Gate1 §2.3 data classes · Google peer spike fences

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Written **live data-handling schedule** + **secret_handle lifecycle** (design) | Permission to ship keys, network transports, or real Gemini traffic |
| Answer to Gate 4 “Needs explicit live data schedule” | A Gate 4 **seal** (Gate 1 still unsigned → Gate 4 **cannot seal**) |
| Compatible with mock / RefuseTransport / Google free-tier *design* dry-run | An unlock, ACK substitute, or `live=ENABLED` flip |
| Default today = **no real calls** | A claim that drafting this schedule enables free-tier Gemini |

**Invariant:** This document may be drafted while earlier gates are open. **Sealing** Gate 4 still requires Gates **1–3** satisfied first (serial gates). Today Gate 1 is **UNSIGNED**, so Gate 4 remains **OPEN** even with this schedule present.

---

## 1. Allowed vs forbidden egress classes

Aligns with Gate1 ACK draft §2.3 (operator fill still unsigned) and Google fence §6 (bounded data-handling).

### 1.1 Allowed (design — only if Gates 1–5 ever pass + kill-armed canary)

| Class | May leave the box? | Notes |
|-------|--------------------|-------|
| **Redacted / synthetic prompts** for eval | **Y** (design) | Synthetic fixtures preferred; any real prompt must be redacted of secrets, PII, and operational Mesh SoT |
| **Digests / evidence refs** (no secrets) | **Y** (design) | Hash digests, policy_version ids, handle ids, abort codes — never raw bodies with secrets |
| **Schema / contract envelopes** (redacted) | **Y** (design) | Prompt/schema exploration already allowed offline via AI Studio fence; live path still Gate-gated |
| **Advisory peer verdict digests** | **Y** (design) | Evaluation evidence only — **not** Mesh SoT, consensus, or execution authority |

### 1.2 Forbidden (binding — default N held)

| Class | May leave the box? | Notes |
|-------|--------------------|-------|
| **Operational Mesh SoT** / GoalRegistry plaintext / continuity payloads | **N** | Continuity preserves verified Mesh state **locally**; never egress as provider prompt SoT (D1 §5) |
| **Raw secrets** / API keys / Bearer / `sk-` / `api_key=` | **N** | Never in repo, CI logs, evidence digests, explain payloads, or provider prompts |
| **Unverified continuity** / orphan / ABORTED authority claims | **N** | Would launder bad decisions; refuse resume-as-verified (D1 §5.2–5.3) |
| **Provider billing keys / Vertex paid path** | **N** (default) | Vertex paid needs **separate** operator approval beyond Gate 1 / this schedule |
| **Live credentials inside continuity blobs** | **N** | secret_handle only; never in continuity persistence (D1 §5.2) |

**Today (2026-09-27):** live=DISABLED · RefuseTransport default ON · **no real calls**. Allowed classes above are **schedule design** for a future canary — not authorization to send anything now.

---

## 2. secret_handle lifecycle

Composes CP-0058 §5 + D1 §7.2 + schema `mesh.judge.live_adapter_safety/v0`.

### 2.1 Form (reference only)

```text
mesh://secrets/<scope>/<name>@<version>
```

Example **placeholder** (not a live credential): `mesh://secrets/judge/gemini-free@v1`

- Validated by `SECRET_HANDLE_RE` / `is_valid_secret_handle` in `l_judge_live_adapter_safety.py`
- Invalid if looks like raw `sk-…`, `Authorization: Bearer …`, or `api_key=…`

### 2.2 Lifecycle verbs (design)

| Verb | Who | Effect | Evidence |
|------|-----|--------|----------|
| **create** | Operator (out-of-band) | Mint handle id + bind raw secret in **outside-repo** store | Handle id + create outcome (`ok`) in audit; **never** raw material |
| **rotate** | Operator | New `@vN+1`; old version marked superseded | Rotation digest + old/new handle ids; revoke window logged |
| **revoke** | Operator / I5 (compromise path) | Handle unresolved → any enabled path ABORT `ENGINE_AUTH` | Revoke record + kill/RefuseTransport if compromise suspected |
| **resolve** | Runtime (future; **not shipped** this docs cycle) | Out-of-band: OS keyring / sealed env / OIDC→vault | Resolve outcome `ok\|fail` only; never secret in logs |

### 2.3 What I5 sees

| Visible to I5 | Never visible to I5 (or digests/CI) |
|---------------|-------------------------------------|
| Handle ids (`mesh://secrets/…@vN`) | Raw API keys / Bearer / `sk-` |
| Resolve outcome digests (`ok` / `fail` / `revoked`) | Provider billing secrets |
| Rotation / revoke audit rows | Continuity blobs containing credentials |

### 2.4 Where handles live (outside repo)

| Location | Allowed? |
|----------|----------|
| Git tree / committed env files / CI secret **files in repo** | **Forbidden** |
| Operator OS keyring / sealed process env / external vault (OIDC) | **Design target** (resolution code not shipped here) |
| Evidence digests / explain payloads | Handle id + outcome only |
| Continuity / GoalRegistry persistence | **Forbidden** for raw; handle id refs only if ever needed |

**When `enabled=true` without valid handle** → ABORT `ENGINE_AUTH` (fail closed). Today `enabled=false` → RefuseTransport / `ENGINE_DISABLED` regardless of handle.

---

## 3. Gemini free-tier dry-run schedule (design)

Provider bounds from `GOOGLE_L_JUDGE_PEER_SPIKE.md` + `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`.

### 3.1 Default today

| Setting | Value |
|---------|-------|
| Real Gemini / AI Studio / Vertex HTTPS | **OFF** — no calls |
| Mock peer / RefuseTransport spike | Allowed under existing fences |
| `LIVE_API_ENABLED` / `live_adapter.enabled` | **false** |
| Keys in repo | **none** |

### 3.2 What may be sent *if* Gates 1–5 ever pass (and Gate 6 bundle attached)

Hypothetical canary schedule (**not authorized today**):

1. Gate 1 signed with provider = Gemini free-tier eval only; Vertex still OUT  
2. Gate 2 live safety-case amendment reviewed; RV drills green  
3. Gate 3 Authority Matrix bound in config/policy version  
4. Gate 4 this schedule + secret_handle resolvable **outside** repo  
5. Gate 5 flip runbook + negative tests; I5 kill armed  
6. **Single canary** under rate floors (CP-0058): redacted/synthetic prompt only; digests recorded; advisory-only verdict  
7. Any anomaly → I5 kill → RefuseTransport + continuity ABORT + `enabled=false`

**Role of output:** evaluation evidence / correlation input only — **not** Mesh SoT, M1 consensus, or execution authority. Dual advisory ≠ consensus (Gate 8 / M1 posture).

### 3.3 Still forbidden even after gates

- Vertex paid without separate approval  
- Operational Mesh SoT / raw secrets / unverified continuity in prompts  
- Claiming Gemini agree = safety proof or consensus  
- Colab / AI Studio as control plane  

---

## 4. Logging / evidence hygiene

| Surface | Rule |
|---------|------|
| Evidence digests | Digests + handle ids + policy_version + abort codes — **no** `sk-` / Bearer |
| CI logs / pytest | Refuse/Mock only; greppable ban on live-looking secret material (existing helpers) |
| Explain payloads (D1 §9.3) | Digests + handle ids only |
| Forensic capture on compromise | Freeze digest chain; **no** secret material in capture (D1 §8.2) |
| Design samples in docs | Placeholder handles only (`mesh://secrets/…@vN`); never paste real keys |

---

## 5. Gate 4 seal status (today)

| Prerequisite | Today |
|--------------|-------|
| Written data-handling schedule | **This document (drafted)** |
| secret_handle lifecycle documented | **This document (drafted)** |
| No keys committed | **Held** |
| Gate 1 signed ACK | **UNSIGNED** → Gate 4 **cannot seal** |
| Gates 2–3 | Design OK; live amendment / matrix-in-use still OPEN |
| Real calls | **None** |

**Exit (from checklist):** Written data-handling schedule + secret_handle lifecycle for the ACK’d env; still no keys committed.  
**Today:** schedule **drafted**; env **not** ACK’d (Gate 1 unsigned); exit **not** met for seal.

---

## 6. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- API keys in repo, env commits, or CI secrets files
- Real Gemini / Vertex / AI Studio production traffic
- Starting D3 or flipping `MESH_PERF_EXPERIMENTAL`
- Push, tags, pkg0190, v0.19, GIA, Raft/N>2, train-70B, SaaS
- Minting a feature CP for this schedule (docs-only)
- Substituting this draft for Gate 1 ACK

---

## 7. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 4 exit)
- `docs/planning/LIVE_100_OPERATOR_WALL.md` — operator wall; live track **FROZEN** under HOLD (A)
- `docs/planning/HOLD_MOCK_NEXT.md` · `council/NOTE_OPERATOR_HOLD_POST_WALL.md` · `council/NOTE_HOLD_MOCK_ROADMAP_COMPLETE.md`
- `council/NOTE_GATE4_DATA_POLICY.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` (§2.3 data classes)
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 §5 secret_handle)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§7.2)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`
- `docs/schema/judge/live_adapter_safety_v0.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`, `is_valid_secret_handle`)

---

*End GATE4_LIVE_DATA_POLICY — DESIGN ONLY; not an unlock; live=DISABLED; Gate 1 unsigned → Gate 4 cannot seal.*
