# Mapping: minogan.scorer/v1 ⇄ Mesh (CP-0088)

**Status:** DESIGN (CP-0088 P0.1). Field names confirmed against the pilot source on 2026-10-18:  
`/workspace/minogan-pilot/src/shared/scorer.js` (contract + `validateOutput` + `combineScorers`),
`src/shared/engine.js` (input builder, ~L253–268), `src/shared/rules.js` (`computeScore`, `METHODOLOGY='score_v0.3'`, `uwOutcome`),
`docs/SCHEMA.md` ("Scorer contract"), `scripts/synthetic.mjs` (OTLP generator).  
**Pilot is not modified.** Mesh implements the contract on its side (`neural_mesh/minogan/contract.py`, P0.2).

## 1. ScorerInput (pilot → Mesh), exact names

| Key | Type | Source in pilot (`engine.js`) | Mesh use |
|-----|------|-------------------------------|----------|
| `contract` | `"minogan.scorer/v1"` | `SCORER_CONTRACT_VERSION` | reject anything else (typed error) |
| `now` | int epoch ms | scoring time | sole clock for decay (no wall clock in Mesh scorer) |
| `org_id` | string | agent row | **`tenant_id`** for AgentMemory / auth |
| `window{from,to}` | int ms | 7-day baseline window | `evidence_window` |
| `agent{id,name,function,framework,autonomy,data_sensitivity,criticality,allowed_tools[]}` | | agents row | `agent.id` = `agent_id`; `autonomy`, `data_sensitivity` → exposure axes (default 50 if null) |
| `features{distinctTools,writeTools,writes,approvedWrites,distinctModels,newTools24h,toolCalls24h,newToolCalls24h,hasBaseline,recentSpans,recentErrors,baselineSpans,baselineErrors}` | ints + bool | D1 aggregates | exposure axes; confidence |
| `signals[{id,type,rule,severity,title,ts,pattern,trace_ids[]}]` | ACTIVE only (FP/suppressed excluded) | ≤200/agent, `trace_ids` sliced to 10 | behavior + floor; `cited_trace_ids` universe |
| `baseline_score` | int \| null | mean of 24h–7d snapshots | drift |
| `events[]` (optional) | ≤200 `{trace_id,span_id,type,name,tool,model,latency_ms,status,is_write,human_approved,destination,out_bytes,ts}` | only if scorer `needs` includes `"events"` | exclusions; AgentMemory append |

Notes:
- `computeScore` reads only `features.{distinctTools,writeTools,writes,approvedWrites,distinctModels,newTools24h,toolCalls24h,newToolCalls24h,hasBaseline}`, `agent.{autonomy,data_sensitivity}`, `signals`, `baseline_score`, `now`. `recent*/baseline*` span/error counts are unused by the score (Mesh uses them for confidence).
- `severity ∈ {info,warn,high}`; `type` is one of the 6 pilot SignalTypes: `tool-call loop`, `policy violation`, `latency spike`, `off-task`, `prompt injection attempt`, `data exfil pattern`.
- **No content keys.** `contract.py` must reject (typed error) any `prompt`, `completion`, `messages`, `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` key at any depth; `events` items are `extra="forbid"`.
- Limits enforced by Mesh: body ≤ 1 MB; `events` ≤ 200; `signals` ≤ 200; `trace_ids` ≤ 10 per signal.

## 2. ScorerOutput (Mesh → pilot), exact names

| Key | Type | Mesh v0 |
|-----|------|---------|
| `score` | int 0–100 | parity target: `computeScore` score_v0.3 ±1 |
| `exposure`, `behavior` | int 0–100 | same formulas |
| `driftPct` | number (1 decimal) | short-horizon: as pilot; long-horizon from AgentMemory goes in `components.drift_long` (does **not** change `driftPct` in v0) |
| `driftStatus` | `stable\|watch\|elevated\|critical` | `<10 · <25 · <50 · ≥50` |
| `axes{}` | `{autonomy,toolSurface,dataSensitivity,humanOversight,changeVelocity,taskDrift}` | same keys |
| `components{methodology,formula,explain,…}` | object | + Mesh keys below |
| `cited_trace_ids[]` | ⊆ input signal `trace_ids`, max 50 | pilot re-filters anyway |
| `methodology` | string | `mesh.minogan.score/v0+score_v0.3` |
| `scorer` | string | `mesh` |

Pilot `validateOutput()` clamps numbers to 0–100 (`Math.round`), coerces unknown drift status to `stable`, filters `cited_trace_ids`, and keeps `components` (spread) adding `cited_trace_ids` + `scorer`. So Mesh-added component keys persist in the D1 `scores.components` JSON.

## 3. Mesh additions inside `components` (`scorer_components_mesh_v0.schema.json`)

| Key | Type | Definition |
|-----|------|------------|
| `confidence` | 0–1 | `uw_v0.md` §4 |
| `reasons[]` | `{code, weight, evidence_trace_ids[]}` | one per score driver (axis contribution, signal category, floor); `weight` = signed points; Σ weights reproduces `score` within rounding |
| `model_version` | string | `mesh.minogan.score/v0` (bumped on any formula/threshold change) |
| `input_digest` | `sha256:<hex64>` | sha256 of canonical ScorerInput (§4) |
| `uw` | `{outcome, conditions[]}` | compact `minogan.uw/v0` |
| `advisory` | object \| null | optional L_judge text; `affects_score: false`; computed **after** the number, never fed back |

## 4. Canonical input for `input_digest`

- UTF-8 JSON, object keys sorted lexicographically (code points), separators `,` `:` and no whitespace.
- Numbers: integral values serialised without fraction (`1`, not `1.0`) to match JS `JSON.stringify`; non-integral via shortest round-trip repr; NaN/Inf rejected. Target: RFC 8785 (JCS) compatible.
- Absent optional keys omitted (not `null`); `events` absent ≠ `events: []` (both are distinct digests, by design).
- Digest covers the **validated** input (after `contract.py`), so replay recomputes the same digest.

## 5. Parity hazards to handle in P0.3

- JS `Math.round` rounds .5 toward +∞; Python `round()` is banker's → use `math.floor(x + 0.5)`.
- `Math.exp` vs `math.exp`: ≤1 ulp; only matters near .5 boundaries (hence ±1 tolerance).
- Category order: `Object.entries` insertion order after sorting contributions by points desc; ties → stable sort by original index.
- `explain` string should match pilot format for v0 (helps the SaaS UI), but parity is judged on numbers.

## 6. Fixtures

`scripts/synthetic.mjs` emits **OTLP spans**, not ScorerInput, and is non-deterministic (`crypto.getRandomValues`, `Math.random`, `Date.now`). Fixtures for P0.2/P0.3 are therefore produced by running pilot ingest → `scoreAgents`/`scoreAll` (`engine.js`) on the sql.js D1 shim (`scripts/d1-shim.mjs`) and capturing each ScorerInput. `getScorer(env)` is hard-wired to `ruleScorer`, so capture happens in a **throw-away copy** of the pilot `src/` under `/tmp` (or a Node module hook) — never by editing the pilot. Inputs are then **frozen** to JSON (`input`, `expected` from `computeScore`). Generation is a one-time, local, read-only use of the pilot code; the frozen fixtures make Mesh tests independent of Node.
