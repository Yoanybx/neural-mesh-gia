# Gate 4 — Live data policy + secret_handle (DESIGN_SEALED / DISCUSS_ONLY eval)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** — does **not** enable live · **does not** mint keys into repo · **does not** authorize Mesh live Gemini/provider calls · **does not** start D3 · **does not** push/tag · **does not** mint a CP · **does not** claim ENABLE seal.  
**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Date design-sealed:** 2026-09-28 ~18:48 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `ce53e7c` (Gate3 DESIGN_SEALED) atop Gate2 `7c436f8` / peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · Gate1 **SIGNED DISCUSS_ONLY** · Gate2/3 **DESIGN_SEALED** (discuss/eval)

**Seal artifact:** `docs/planning/GATE4_DESIGN_SEALED.md`  
**Checklist / Gate 4 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 4 — Keys + data policy  
**Council note:** `council/NOTE_GATE4_DATA_POLICY.md` · `council/NOTE_GATE4_DESIGN_SEALED.md`  
**Upstream:** CP-0058 secret_handle / RefuseTransport · D1 §7.2 · Gate1 §2.3 data classes · Google peer spike fences · dry-run `1e502c6` · peer wire `30fe593`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Written **live data-handling schedule** + **secret_handle lifecycle** — **DESIGN_SEALED** for DISCUSS_ONLY / eval | Permission to ship keys into repo, Mesh live transports, or Gate5 canary without ENABLE chain |
| Answer to Gate 4 “Needs explicit live data schedule” for **eval design seal** | An **ENABLE** seal / Mesh live egress ACK |
| Compatible with mock / RefuseTransport / Gemini free-tier **flag-gated dry-run** | An unlock, ACK substitute, or `live=ENABLED` flip |
| Eval handle provisioned **oob**; default Mesh path = **no real live calls** | A claim that design-seal enables Mesh live adapter |

**Invariant:** Sealing Gate 4 for **DISCUSS_ONLY / eval** requires Gates **1–3** discuss/design-sealed (met). Sealing Gate 4 for **enable** still requires operator **ENABLE_UNDER_FENCES** + Gates 2–3 enable path — **OPEN**.

---

## 1. Allowed vs forbidden egress classes

Aligns with Gate1 SIGNED DISCUSS_ONLY §2.3 and Google fence §6 (bounded data-handling).

### 1.1 Allowed (design — only if Gates 1–5 ever pass + kill-armed canary for Mesh live; eval dry-run already uses redacted/synthetic only)

| Class | May leave the box? | Notes |
|-------|--------------------|-------|
| **Redacted / synthetic prompts** for eval | **Y** (design / eval dry-run) | Synthetic fixtures preferred; any real prompt must be redacted of secrets, PII, and operational Mesh SoT |
| **Digests / evidence refs** (no secrets) | **Y** (design) | Hash digests, policy_version ids, handle ids, abort codes — never raw bodies with secrets |
| **Schema / contract envelopes** (redacted) | **Y** (design) | Prompt/schema exploration offline via AI Studio fence; Mesh live path still Gate-gated |
| **Advisory peer verdict digests** | **Y** (design / eval) | Evaluation evidence only — **not** Mesh SoT, consensus, or execution authority |

### 1.2 Forbidden (binding — default N held)

| Class | May leave the box? | Notes |
|-------|--------------------|-------|
| **Operational Mesh SoT** / GoalRegistry plaintext / continuity payloads | **N** | Continuity preserves verified Mesh state **locally**; never egress as provider prompt SoT (D1 §5) |
| **Raw secrets** / API keys / Bearer / `sk-` / `api_key=` | **N** | Never in repo, CI logs, evidence digests, explain payloads, or provider prompts |
| **Unverified continuity** / orphan / ABORTED authority claims | **N** | Would launder bad decisions; refuse resume-as-verified (D1 §5.2–5.3) |
| **Provider billing keys / Vertex paid path** | **N** (default) | Vertex paid needs **separate** operator approval beyond Gate 1 / this schedule |
| **Live credentials inside continuity blobs** | **N** | secret_handle only; never in continuity persistence (D1 §5.2) |

**Today (2026-09-28):** live=DISABLED · RefuseTransport default ON · Mesh live = **no real calls**. Flag-gated Gemini **dry-run** may use synthetic prompt + oob key only. Allowed classes above are **schedule design** for a future canary — not authorization to enable Mesh live now.

---

## 2. secret_handle lifecycle

Composes CP-0058 §5 + D1 §7.2 + schema `mesh.judge.live_adapter_safety/v0`.

### 2.1 Form (reference only)

```text
mesh://secrets/<scope>/<name>@<version>
```

**Eval handle (provisioned oob; not a raw credential in docs):** `mesh://secrets/judge/gemini-free@v1`

- Validated by `SECRET_HANDLE_RE` / `is_valid_secret_handle` in `l_judge_live_adapter_safety.py`
- Invalid if looks like raw `sk-…`, `Authorization: Bearer …`, or `api_key=…`

### 2.2 Lifecycle verbs (design)

| Verb | Who | Effect | Evidence |
|------|-----|--------|----------|
| **create** | Operator (out-of-band) | Mint handle id + bind raw secret in **outside-repo** store | Handle id + create outcome (`ok`) in audit; **never** raw material |
| **rotate** | Operator | New `@vN+1`; old version marked superseded | Rotation digest + old/new handle ids; revoke window logged |
| **revoke** | Operator / I5 (compromise path) | Handle unresolved → any enabled path ABORT `ENGINE_AUTH` | Revoke record + kill/RefuseTransport if compromise suspected |
| **resolve** | Runtime (future Mesh live; eval dry-run loads oob env) | Out-of-band: OS keyring / sealed env / OIDC→vault | Resolve outcome `ok\|fail` only; never secret in logs |

### 2.3 What I5 sees

| Visible to I5 | Never visible to I5 (or digests/CI) |
|---------------|-------------------------------------|
| Handle ids (`mesh://secrets/…@vN`) | Raw API keys / Bearer / `sk-` |
| Resolve outcome digests (`ok` / `fail` / `revoked`) | Provider billing secrets |
| Rotation / revoke audit rows | Continuity blobs containing credentials |

### 2.4 Where handles live (outside repo) — sealed for eval

| Location | Allowed? |
|----------|----------|
| Git tree / committed env files / CI secret **files in repo** | **Forbidden** |
| Operator OS keyring / sealed process env / external vault (OIDC) | **Design target** |
| **Eval oob path (DONE)** | `/home/box/.config/neural-mesh/gemini.env` — mode `0600`; `.gitignore` covers `gemini.env` / `.config/neural-mesh/` |
| Evidence digests / explain payloads | Handle id + outcome only |
| Continuity / GoalRegistry persistence | **Forbidden** for raw; handle id refs only if ever needed |

**When `enabled=true` without valid handle** → ABORT `ENGINE_AUTH` (fail closed). Today `enabled=false` → RefuseTransport / `ENGINE_DISABLED` regardless of handle.

---

## 3. Gemini free-tier dry-run vs Mesh live RefuseTransport

Provider bounds from `GOOGLE_L_JUDGE_PEER_SPIKE.md` + `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`.

### 3.1 Default today (Mesh live)

| Setting | Value |
|---------|-------|
| Mesh live Gemini / AI Studio / Vertex HTTPS | **OFF** — RefuseTransport |
| `LIVE_API_ENABLED` / `live_adapter.enabled` | **false** |
| Keys in repo | **none** |
| Mock peer / RefuseTransport spike | Allowed under existing fences |

### 3.2 Flag-gated dry-run (eval — NOT Gate5 canary)

| Setting | Value |
|---------|-------|
| Peer CLI / env | `--gemini-dry-run` / `GEMINI_DRY_RUN=1` → `GeminiFreeDryRunTransport` |
| Evidence | tips `1e502c6` · `30fe593` · `NOTE_GEMINI_DRY_RUN.md` · `NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` |
| Key load | **oob only** from `/home/box/.config/neural-mesh/gemini.env` |
| Relation to Mesh live | **Orthogonal** — dry-run ≠ Mesh live adapter enable ≠ Gate5 canary |

### 3.3 What may be sent *if* Gates 1–5 ever pass for enable (and Gate 6 bundle attached)

Hypothetical canary schedule (**not authorized today**):

1. Gate 1 upgraded to ENABLE_UNDER_FENCES (user-written) with provider = Gemini free-tier eval only; Vertex still OUT  
2. Gate 2 live safety-case **enable** seal + RV drills green  
3. Gate 3 Authority Matrix **live-armed** in config/policy version  
4. Gate 4 this schedule + secret_handle resolvable **outside** repo (**eval design sealed**; enable seal still open)  
5. Gate 5 flip runbook + negative tests; I5 kill armed; **canary executed** under kill  
6. **Single canary** under rate floors (CP-0058): redacted/synthetic prompt only; digests recorded; advisory-only verdict  
7. Any anomaly → I5 kill → RefuseTransport + continuity ABORT + `enabled=false`

**Role of output:** evaluation evidence / correlation input only — **not** Mesh SoT, M1 consensus, or execution authority. Dual advisory ≠ consensus (Gate 8 / M1 posture).

### 3.4 Still forbidden even after gates

- Vertex paid without separate approval  
- Operational Mesh SoT / raw secrets / unverified continuity in prompts  
- Claiming Gemini agree = safety proof or consensus  
- Colab / AI Studio as control plane  
- Treating dry-run as Gate5 canary / Mesh live enable

---

## 4. Logging / evidence hygiene

| Surface | Rule |
|---------|------|
| Evidence digests | Digests + handle ids + policy_version + abort codes — **no** `sk-` / Bearer |
| CI logs / pytest | Refuse/Mock only by default; greppable ban on live-looking secret material |
| Explain payloads (D1 §9.3) | Digests + handle ids only |
| Forensic capture on compromise | Freeze digest chain; **no** secret material in capture (D1 §8.2) |
| Design samples in docs | Placeholder handles only (`mesh://secrets/…@vN`); never paste real keys |

---

## 5. Gate 4 seal status (today)

| Prerequisite | Today |
|--------------|-------|
| Written data-handling schedule | **DESIGN_SEALED** (this document + `GATE4_DESIGN_SEALED.md`) |
| secret_handle lifecycle documented | **DESIGN_SEALED** |
| Eval handle oob + no keys committed | **Held / DONE** — `mesh://secrets/judge/gemini-free@v1` @ oob path |
| Dry-run flag vs live RefuseTransport | **Bound** — dry-run flag-gated; Mesh live RefuseTransport ON |
| Gate 1 | **SIGNED DISCUSS_ONLY** |
| Gates 2–3 | **DESIGN_SEALED** (discuss/eval); enable seals **OPEN** |
| Gate 4 ENABLE seal / Mesh live data ACK | **OPEN** |
| Real Mesh live calls | **None** |
| Gate5 canary | **NOT** for execution until ENABLE chain |

**Exit (design/discuss):** Written data-handling schedule + secret_handle lifecycle for DISCUSS_ONLY/eval env; eval handle oob; still no keys committed.  
**Today:** design exit **MET** → **DESIGN_SEALED**; enable exit **not** met.

---

## 6. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- API keys in repo, env commits, or CI secrets files
- Real Mesh live Gemini / Vertex / AI Studio production traffic
- Executing Gate5 canary / inventing ENABLE_UNDER_FENCES signature
- Starting D3 or flipping `MESH_PERF_EXPERIMENTAL`
- Push, tags, pkg0190, v0.19, GIA, Raft/N>2, train-70B, SaaS
- Minting a feature CP for this schedule (docs-only)
- Substituting this design seal for Gate 1 ENABLE ACK

---

## 7. Related

- `docs/planning/GATE4_DESIGN_SEALED.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 4 exit)
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `council/NOTE_GATE4_DATA_POLICY.md` · `council/NOTE_GATE4_DESIGN_SEALED.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GATE2_DESIGN_SEALED.md` · `GATE3_DESIGN_SEALED.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 §5 secret_handle)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§7.2)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` · `NOTE_GEMINI_DRY_RUN.md` · `NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `docs/schema/judge/live_adapter_safety_v0.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`, `is_valid_secret_handle`)

---

*End GATE4_LIVE_DATA_POLICY — DESIGN_SEALED for DISCUSS_ONLY/eval; live=DISABLED; ENABLE seal OPEN; Gate5 canary not authorized.*
