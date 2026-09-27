# L_judge MIX Live-Adapter Design

**Status:** DESIGN ONLY (boundary plan; **no live API**, no keys, no runtime codec)  
**Cycle / Checkpoint:** 53 / CP-0057  
**Date:** 2026-09-26 America/New_York (EDT)  
**Extends:** `L_JUDGE_MIX_DESIGN.md` · `L_JUDGE_MIX_INTEGRATION.md` · `docs/schema/judge/*`  
**Authority:** DeepSeek C50–C51 Option3; after C52 L1 residue CLOSED  
**Non-claim:** Mesh ≠ frontier model. DO_NOT_TRAIN_70B_NOW. L_GIA = NO_HELD.

---

## 1. Intent

Plan the **plug-in boundary** where a **real** (non-mock) external LLM/MLLM
transport would attach behind `LJudgeMixPort`, without implementing that
transport in this cycle.

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Live-adapter design + safety envelope | Live HTTPS/SDK calls |
| Config-ref / secret-handle contract | API keys in repo or env for CI |
| Parse / ABORT / receipt rules for live path | `src/neural_mesh/judge_*.py` codec |
| Failure taxonomy + kill-switch | SaaS multi-tenant judge product |

Upstream: CP-0047 design · CP-0051 stubs · CP-0052 integration+mock.  
Downstream (later, gated): optional impl CP that still forbids train/GIA/Raft.

---

## 2. Ownership boundary (hard)

```
┌─────────────────────────────────────────────────────────────┐
│ Mesh L_judge gate (I2/I4/I5/I6)                             │
│  • build InjectionEnv + JudgeRequest                        │
│  • dry_run required before live_advisory                    │
│  • schema/policy/fence/audit gates                          │
│  • parse → JudgeResponse; never invent ACCEPT on failure    │
│  • hash-chained JudgeReceipt + OBS + EvidenceEntry          │
└───────────────────────────┬─────────────────────────────────┘
                            │ EngineTransport.call(PromptBundle) → RawEngineResult
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Live adapter (planned; NOT shipped this CP)                 │
│  • resolve secret_handle → credential (OS keyring / CI oidc)│
│  • TLS outbound only; no plaintext fallback                 │
│  • timeout / retry / cancel mapped to Mesh taxonomy         │
│  • raw text or provider JSON → Mesh parser                  │
│  • NO goal/continuity mutation authority                    │
└─────────────────────────────────────────────────────────────┘
```

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Policy / ABORT / fence | Mesh | Adapter override |
| Goal / continuity SoT | Mesh substrate | Engine diary as SoT |
| Credentials | Operator secret store | Keys in git / test fixtures |
| Semantic judgment text | External engine | Mesh pretending to be frontier model |
| Receipts / OBS | Mesh | Unaudiated live calls |
| Training / fine-tune | **FORBIDDEN** | Either side |

---

## 3. Transport interface (design)

```text
@dataclass
class PromptBundle:
    schema: "mesh.judge.prompt_bundle/v0"
    request_id: str
    injection_digest: str
    system_digest: str          # content-addressed system prompt
    user_digest: str            # content-addressed user payload
    # bodies may be passed by digest+blob ref; never log secrets

@dataclass
class RawEngineResult:
    schema: "mesh.judge.raw_engine/v0"
    ok: bool
    http_status: int | None
    latency_ms: int | None
    raw_text: str | None        # truncated under max_bytes
    error_code: str | None      # ENGINE_TIMEOUT|ENGINE_HTTP|ENGINE_AUTH|...
    provider: str               # opaque label, e.g. "openai-compat"
    model_ref: str              # non-secret model id string
    truncated: bool

class EngineTransport:
    def call(self, bundle: PromptBundle, *, timeout_s: float) -> RawEngineResult
    def health(self) -> TransportHealth   # optional; fail-closed if down
```

**Bindings:**

| Binding | When |
|---------|------|
| `MockLJudgeTransport` | Tests (CP-0052); deterministic; no network |
| `LiveHttpTransport` (planned) | Later impl CP; config-ref only |
| `RefuseTransport` | Default if live disabled → `ABORT` / `ENGINE_DISABLED` |

Default for this design line: **live disabled**. Enabling requires explicit
operator config + secret_handle; CI must remain green with Refuse/Mock only.

---

## 4. Config + secret-handle contract

```json
{
  "schema": "mesh.judge.live_adapter_config/v0",
  "enabled": false,
  "provider": "openai-compat",
  "endpoint_url": "https://api.example/v1/chat/completions",
  "model_ref": "example-model",
  "secret_handle": "mesh://secrets/judge/live@v1",
  "timeout_s": 30,
  "max_retries": 1,
  "max_raw_bytes": 65536,
  "tls_required": true,
  "forbid_plaintext": true,
  "require_prior_dry_run": true
}
```

Rules:

1. `secret_handle` is a **reference**, never a raw key. Resolution is out-of-band
   (OS keyring, sealed env at process start, OIDC→vault). Repo must not contain
   live credentials.
2. `enabled=false` → RefuseTransport (safe default).
3. `tls_required=true` + `forbid_plaintext=true` — ABORT on cleartext endpoint.
4. Tests assert design docs forbid embedding `sk-` / `api_key=` samples as live secrets.

---

## 5. Live call sequence

1. Mesh validates `JudgeRequest` + `InjectionEnv` (schema, fence, audit sink).
2. If `mode=live_advisory`: require prior dry_run ACCEPT for idempotency family.
3. Build `PromptBundle` (digests recorded on request / receipt).
4. `EngineTransport.call` with timeout; map errors → taxonomy (§6).
5. Parse `raw_text` → `JudgeResponse` (same gates as CP-0052 §5).
6. Emit `JudgeReceipt` + OBS + EvidenceEntry; return to caller.
7. On any ABORT: no side-effecting act; receipt still recorded when audit up.

**Kill-switch:** operator sets `enabled=false` or Mesh I5 pause/kill → all live
submits ABORT / `HUMAN_ABORT` or `ENGINE_DISABLED`.

---

## 6. Failure taxonomy (live-specific)

| Condition | Mesh code | Notes |
|-----------|-----------|-------|
| Live disabled / RefuseTransport | `ENGINE_DISABLED` | Default |
| Secret_handle unresolved | `ENGINE_AUTH` | Fail closed |
| TLS/plaintext violation | `ENGINE_TLS` / `PLAINTEXT_FORBIDDEN` | Never fallback |
| HTTP 401/403 | `ENGINE_AUTH` | No retry with alternate key invent |
| HTTP 5xx / network | `ENGINE_HTTP` | ≤ max_retries then ABORT/ABSTAIN |
| Timeout | `ENGINE_TIMEOUT` | Never silent ACCEPT |
| Truncated raw | `SCHEMA_INVALID` or policy ABORT | Default ABORT if `forbid_silent_accept` |
| Parse / unknown verdict | `SCHEMA_INVALID` | Never invent ACCEPT |
| dual_primary ≠ 0 | `FENCE` | Unchanged |
| No audit sink | `NO_AUDIT` | no-audit=no-action |

---

## 7. ABORT / allow (live path)

Inherited from CP-0052, plus:

| Extra live rule | Result |
|-----------------|--------|
| `enabled=false` | ABORT `ENGINE_DISABLED` |
| Missing/invalid secret_handle when enabled | ABORT `ENGINE_AUTH` |
| Endpoint not HTTPS when tls_required | ABORT `PLAINTEXT_FORBIDDEN` |
| Provider returns non-JSON / tool-calls-only blob without schema | ABORT `SCHEMA_INVALID` |

**Allow path:** config enabled + secret resolved + dry_run ACCEPT → live submit →
parse ACCEPT/REJECT/ABSTAIN → receipt chain.

---

## 8. What “done” means for a later impl CP

A future impl CP (still NO_HELD-safe) may:

1. Ship `LiveHttpTransport` behind feature flag default-off.
2. Resolve secrets via handle only; document operator setup.
3. Reuse CP-0052 parse/receipt gates; extend tests with **recorded fixtures**
   (cassettes) — never live CI calls unless operator opt-in + secret present.
4. Keep Mock path as default for pytest.

Still forbidden then: train/fine-tune, GIA unlock, Raft/N>2, SaaS settlement,
prose unlock of NO_HELD ML product layer.

---

## 9. Non-goals (this CP)

- No live API calls from this repository cycle
- No API keys committed or required for green CI
- No `src/` judge runtime codec
- No train / 70B / ML-as-product-layer (NO_HELD ML / R2 / R3 product)
- No GIA / consciousness claims
- No Raft / N>2 / multi-primary
- No SaaS / economy / settlement

---

## 10. Related

- `docs/design/L_JUDGE_MIX_DESIGN.md` (CP-0047)
- `docs/design/L_JUDGE_MIX_INTEGRATION.md` (CP-0052)
- `docs/schema/judge/v0.md` · `injection_v0.md` (CP-0051)
- `docs/planning/L1_RESIDUE_CLOSEOUT.md` (CP-0056; L1 CLOSED)
- `docs/planning/0.19_NON_GOALS.md`
