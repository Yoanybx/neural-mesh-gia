# Schema: minogan.uw/v0 (SPIKE — design/mock)

**Status:** SPIKE / DESIGN_ONLY (CP-0088 P0.1) — no code consumes it yet  
**Schema id:** `minogan.uw/v0` · JSON Schema: `uw_v0.schema.json` (draft 2020-12)  
**Compact form inside ScorerOutput:** `components.uw` — see `scorer_components_mesh_v0.schema.json`  
**Parent:** `council/NOTE_S0_MESH_MINOGAN_INTELLIGENCE.md` · `docs/planning/CP_0088_CAMINO_MINOGAN.md`

Minogan is **not an insurer**. This record is an **advisory hint** for a human
underwriter at a carrier/MGA; nothing here binds, prices or writes cover.
Derived **deterministically** from the Mesh score (no LLM). Metadata + trace ids
only; never prompts/completions.

## 1. Fields

| Field | Type | Notes |
|-------|------|-------|
| `schema` | const | `minogan.uw/v0` |
| `tenant_id` | string? | = ScorerInput `org_id` (tenant key) |
| `agent_id` | string? | = ScorerInput `agent.id` |
| `uw_score` | int 0–100 | higher = riskier. **v0 = ScorerOutput.score** (no separate UW model) |
| `tier` | `T1\|T2\|T3\|T4` | band of `uw_score` (§2) |
| `outcome` | `bind\|bind-with-terms\|refer\|decline` | recommendation (§3) |
| `conditions[]` | clause | `{code, text, evidence_trace_ids?}` — terms for bind-with-terms |
| `exclusions[]` | clause | behaviour classes suggested for exclusion |
| `evidence_window` | object | `{from, to}` epoch ms (= ScorerInput.window) + optional `memory_from`, `spans`, `signals` |
| `confidence` | number 0–1 | evidence-volume confidence (§4); **not** a calibrated probability |
| `methodology_version` | string | e.g. `mesh.minogan.score/v0+score_v0.3` |

Clause `code`: `^[A-Z][A-Z0-9_]{1,47}$`. `evidence_trace_ids` ⊆ input signal trace ids (same rule as pilot `validateOutput`).

## 2. Tier bands (v0, uncalibrated)

| Tier | uw_score |
|------|----------|
| T1 | < 40 |
| T2 | 40–64 |
| T3 | 65–84 |
| T4 | ≥ 85 |

Boundaries 40/65 mirror the pilot `uwOutcome()` (`src/shared/rules.js`). 85 = pilot `highFloorCap`.

## 3. Outcome rule (v0)

Pilot today (`uwOutcome(score)`): `<40 bind · <65 bind-with-terms · else refer` — **no decline**.

Mesh v0 keeps pilot parity and adds `decline` only behind long-horizon evidence:

1. `uw_score < 40` → `bind`
2. `uw_score < 65` → `bind-with-terms` (conditions from §5)
3. otherwise → `refer`
4. `decline` **only if** `tier = T4` **and** `AgentMemory.recurrence(rule, 30d)` shows the same
   high-severity `data exfil pattern` or `prompt injection attempt` rule in ≥ 2 distinct days
   **and** `confidence ≥ 0.6`.

Until `AgentMemory` lands (P0.4) rule 4 can never fire, so Mesh v0 output == pilot hint.
Thresholds are **placeholders** pending P1 calibration.

## 4. Confidence (v0 proposal, deterministic)

```
confidence = round3( 0.5·min(1, baselineSpans/200)
                   + 0.3·min(1, recentSpans/50)
                   + 0.2·[hasBaseline] )
```
Uses only `features`; no network, no LLM. Finalised (and frozen with a version bump) in P0.3.

## 5. Condition / exclusion codes (seed list)

| Code | Kind | Trigger (deterministic) |
|------|------|-------------------------|
| `HUMAN_APPROVAL_WRITES` | condition | `writes > 0` and `approvedWrites/writes < 1` |
| `TOOL_ALLOWLIST_ENFORCED` | condition | any `policy violation` signal (tool outside `allowed_tools`) |
| `OUTBOUND_DLP` | condition | any `data exfil pattern` signal |
| `INJECTION_GUARDRAIL` | condition | any `prompt injection attempt` signal |
| `CHANGE_CONTROL_MODELS` | condition | `distinctModels > 1` or `newTools24h > 0` |
| `EXCL_UNAPPROVED_PAYMENT_WRITES` | exclusion | write tool to external destination with `human_approved=false` (needs `events`) |
| `EXCL_UNKNOWN_DESTINATION_PII` | exclusion | high `pii_outbound` to a destination first seen < 24h |

Seed list only; P0.3 freezes v0 codes with tests.

## 6. Non-goals

Pricing, premium, limits, binding authority, claims, policy wording, LLM rationale in the number.
