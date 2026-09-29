# L_judge Live-Adapter Safety Case

**Status:** DESIGN ONLY (safety case; **no live API**, no keys, no runtime codec)  
**Cycle / Checkpoint:** 54 / CP-0058  
**Date:** 2026-09-26 America/New_York (EDT)  
**Extends:** `L_JUDGE_LIVE_ADAPTER_DESIGN.md` (CP-0057) · `L_JUDGE_MIX_INTEGRATION.md` (CP-0052)  
**Authority:** DeepSeek C52–C53 Option1 (ranked) after live-adapter boundary design  
**Non-claim:** Mesh ≠ frontier model. DO_NOT_TRAIN_70B_NOW. L_GIA = NO_HELD.

---

## 1. Intent

Formalize **why** the live-adapter boundary is safe at design time:

| Claim | Evidence in this CP |
|-------|---------------------|
| RefuseTransport-by-default is fail-closed | Defaults + negative tests |
| `secret_handle` never carries raw keys | Rules + schema stub + tests |
| No src codec ⇒ no accidental live path | Ban list + test |
| Live stays DISABLED until evidence gates | Must-stay-false table (§8) |

This CP does **not** enable live calls. It documents the load-bearing safety
argument that later (gated) impl CPs must satisfy.

Upstream: CP-0057 design · CP-0052 integration+mock · CP-0051 stubs.  
Downstream (later, gated): optional impl CP; still forbids train/GIA/Raft.

---

## 2. Threat model (live external LLM judge)

Actors and assets when a **real** external engine is eventually attached:

### 2.1 Assets

| Asset | Owner | Damage if lost |
|-------|-------|----------------|
| API credentials | Operator secret store | Billing abuse; data exfil via provider |
| Goal / continuity SoT | Mesh substrate | Engine diary treated as authority |
| JudgeReceipt / OBS / EvidenceEntry | Mesh I6 | Unaudiated judgments; silent ACCEPT |
| InjectionEnv digests | Mesh | Prompt injection / goal rewrite |
| Operator trust in Mesh | Process | False “frontier Mesh” claims |

### 2.2 Adversaries / failure classes

| ID | Class | Example |
|----|-------|---------|
| T1 | Credential leakage | Key in git, logs, fixtures, design samples |
| T2 | Cleartext / MITM | `http://` endpoint; TLS skip |
| T3 | Silent ACCEPT on failure | Timeout/truncation mapped to ACCEPT |
| T4 | Audit bypass | Live call with no receipt / no OBS sink |
| T5 | Goal/continuity mutation by engine | Engine response mutates SoT |
| T6 | Rate / cost abuse | Unbounded retries or fan-out |
| T7 | Prompt / injection escape | Unfenced dual_primary; missing dry_run |
| T8 | Supply-chain / provider spoof | Wrong endpoint; auth to attacker |
| T9 | Policy override by adapter | Adapter invents ACCEPT against Mesh ABORT |
| T10 | Training / weight pull | Fine-tune or DO_NOT_TRAIN violation |

### 2.3 Non-threats (out of scope / permanent refuse)

- Making Mesh a frontier model (non-claim)
- GIA / consciousness unlock
- Raft / N>2 / multi-primary runtime
- SaaS settlement / economy
- Live CI calls without operator opt-in

---

## 3. Safety argument (design boundary)

```
RefuseTransport default
        +
secret_handle-only credentials
        +
no src/ live codec in this line
        +
Mesh owns policy/ABORT/fence/receipts
        ⇒
  no live external call can occur from this package/CI path
  until explicit operator enablement + evidence gates (§8)
```

| Concern | Mitigation | Residual risk (accepted until impl CP) |
|---------|------------|----------------------------------------|
| Accidental live | `enabled=false` + RefuseTransport | Operator misconfig later — gated by §8 |
| Key in repo | secret_handle ref only; sk- ban in tests | Operator paste into wrong file — process |
| Silent ACCEPT | Taxonomy: never invent ACCEPT | Impl bug — tests + receipt |
| Audit gap | no-audit=no-action | Sink down → ABORT only |
| Engine as SoT | Mesh substrate owns goals | Impl must refuse engine mutations |

---

## 4. ABORT conditions (live path)

Inherited from CP-0052 / CP-0057, consolidated for the safety case:

| Condition | Code | Side effects |
|-----------|------|--------------|
| Live disabled / RefuseTransport | `ENGINE_DISABLED` | none; receipt if audit up |
| Missing/invalid secret_handle when enabled | `ENGINE_AUTH` | none |
| Secret unresolved | `ENGINE_AUTH` | none |
| Endpoint not HTTPS / tls_required | `PLAINTEXT_FORBIDDEN` / `ENGINE_TLS` | none; never fallback |
| HTTP 401/403 | `ENGINE_AUTH` | no alternate-key invent |
| HTTP 5xx / network after retries | `ENGINE_HTTP` | ABORT/ABSTAIN |
| Timeout | `ENGINE_TIMEOUT` | never silent ACCEPT |
| Truncated / non-JSON / unknown verdict | `SCHEMA_INVALID` | default ABORT |
| dual_primary ≠ 0 | `FENCE` | refuse submit |
| No audit sink | `NO_AUDIT` | no-audit=no-action |
| Prior dry_run missing for live_advisory | `POLICY_ABORT` | none |
| Human I5 pause/deny/kill | `HUMAN_ABORT` | kill-switch |
| Idempotency key conflict (compose CP-0068 / CP-0078) | `CONT_IDEMPOTENCY_CONFLICT` | none |
| Live path missing continuity key / live-disabled compose | `CONT_LIVE_DISABLED` | none |
| Rate limit exceeded | `ENGINE_RATE_LIMIT` | no further call |
| Adapter would override Mesh ABORT | `POLICY_ABORT` | Mesh wins |

**Invariant:** on any ABORT, never invent `ACCEPT`; no side-effecting act.

---

## 5. secret_handle rules

1. **Reference only** — form `mesh://secrets/<scope>/<name>@<version>` (or
   operator-equivalent URI). Never a raw key, Bearer token, or `sk-…` blob.
2. **Resolution out-of-band** — OS keyring, sealed env at process start,
   OIDC→vault. Resolution code is **not** shipped in this design CP.
3. **Repo / CI** — no live credentials; CI green with Refuse/Mock only.
4. **Logs / receipts** — record handle id + resolve outcome (`ok|fail`), never
   secret material; digests of prompts, not bodies with secrets.
5. **Design samples** — may show placeholder handles; tests forbid
   live-looking `sk-` blobs and Bearer-token embeddings as live secrets.
6. **When enabled=true without valid handle** → ABORT `ENGINE_AUTH` (fail closed).

---

## 6. RefuseTransport defaults

| Setting | Default | Rationale |
|---------|---------|-----------|
| `enabled` | `false` | Fail closed |
| Binding | `RefuseTransport` | Every call → ABORT `ENGINE_DISABLED` |
| CI / pytest | Mock or Refuse only | No network |
| Kill-switch | `enabled=false` or I5 | Immediate refuse |

`RefuseTransport.call(...)` returns a structured failure mapped to Mesh taxonomy;
it performs **zero** network I/O. Default for this design line until §8 evidence
gates are met **and** an authorized impl CP ships.

---

## 7. Rate limits (design envelope)

Design-only defaults (operator may tighten; may not loosen below floor without
new evidence):

| Limit | Floor default | On exceed |
|-------|---------------|-----------|
| `max_calls_per_minute` | 10 | ABORT `ENGINE_RATE_LIMIT` |
| `max_calls_per_hour` | 120 | ABORT `ENGINE_RATE_LIMIT` |
| `max_retries` | 1 | then ABORT `ENGINE_HTTP` / timeout |
| `timeout_s` | 30 | ABORT `ENGINE_TIMEOUT` |
| `max_raw_bytes` | 65536 | truncate → policy ABORT if forbid_silent_accept |
| `max_concurrent` | 1 | queue or ABORT |

Rate counters are Mesh-owned (not provider honor-system). Receipts record
`rate_limited=true` when tripped. No automatic backoff that invents ACCEPT.

---

## 8. What must stay false until evidence

These flags / claims **must remain false / unasserted** until an evidence bundle
exists (tests + audit + operator config + authorized CP). Prose alone cannot
flip them (GOV.6):

| Flag / claim | Must stay | Until evidence |
|--------------|-----------|----------------|
| `live_adapter.enabled` | `false` | Impl CP + operator secret_handle + dry_run gate tests |
| `live_api_in_ci` | `false` | Explicit operator opt-in + secret present |
| `src_live_codec_shipped` | `true` under **CP-0078** | Authorized impl CP shipped packaging v0 (still default-off) |
| `mesh_is_frontier_model` | `false` | **Permanent** non-claim |
| `train_70b` / fine-tune | `false` | **Permanent** DO_NOT_TRAIN_70B_NOW |
| `gia_unlocked` | `false` | **NO_HELD** |
| `raft_runtime` / `n_gt_2` | `false` | **NO_HELD** |
| `saas_settlement` | `false` | **Forbidden** this line |
| `engine_is_goal_sot` | `false` | **Permanent** — Mesh owns SoT |
| `silent_accept_on_error` | `false` | **Permanent** |

**Enablement checklist (future; NOT this cycle):**

1. Safety case (this doc) VERIFIED  
2. CP-0057 boundary design VERIFIED  
3. secret_handle resolvable in operator env (not in git)  
4. TLS-only endpoint; refuse plaintext  
5. Prior dry_run ACCEPT path proven in tests  
6. Receipt + OBS + EvidenceEntry path proven  
7. Rate-limit floors enforced in tests  
8. Kill-switch (`enabled=false` / I5) proven  
9. Authorized impl CP minted; package still holds NO_HELD  
10. CI remains green with live disabled by default  

---

## 9. Audit / receipt requirements

| Requirement | Rule |
|-------------|------|
| no-audit ⇒ no-action | Missing audit sink → ABORT `NO_AUDIT` |
| Hash-chained `JudgeReceipt` | Every dry_run / submit / ABORT (when sink up) |
| OBS + EvidenceEntry | Append on allow and ABORT paths |
| Digests not secrets | `injection_digest`, prompt digests, handle id |
| dual_primary | Hard **0** on receipts |
| Live metadata | `provider` label, `model_ref` (non-secret), `latency_ms`, `error_code` |
| Rate-limit trips | Recorded on receipt |
| Reconstructibility | Walk evidence by `goal_id` / `continuity_id` |

Unaudiated live calls are **forbidden** even if a future impl exists.

---

## 10. Helpers / schema (this CP)

- Schema stub: `docs/schema/judge/live_adapter_safety_v0.md`
- Python helpers (no network): `neural_mesh.packaging.l_judge_live_adapter_safety`
  — constants, `secret_handle` validate, RefuseTransport mock, enablement gate
  evaluation (all live flags false by default).

---

## 11. Non-goals (this CP)

- No live API calls from this repository cycle
- No API keys committed or required for green CI
- No `src/` judge live HTTP/SDK codec
- No train / 70B / ML-as-product-layer
- No GIA / consciousness claims
- No Raft / N>2 / multi-primary
- No SaaS / economy / settlement
- No flipping `enabled=true`

---

## 12. Related

- `docs/design/L_JUDGE_LIVE_ADAPTER_DESIGN.md` (CP-0057)
- `docs/design/L_JUDGE_MIX_INTEGRATION.md` (CP-0052)
- `docs/design/L_JUDGE_MIX_DESIGN.md` (CP-0047)
- `docs/schema/judge/v0.md` · `injection_v0.md` · `live_adapter_safety_v0.md`
- `docs/planning/0.19_NON_GOALS.md`
