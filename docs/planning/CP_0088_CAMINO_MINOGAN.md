# CP-0088 — Camino Minogan (Mesh as Minogan.ai intelligence backend) — OPEN

**Status:** **OPEN** · P0.1 (NOTE S0 + UW schema v0) **DONE in this commit**; P0.2–P0.7 **NOT STARTED**  
**Cycle / Checkpoint:** 84 / **CP-0088**  
**Date:** 2026-10-18 ~01:45 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at open:** `21f9e48` (after CP-0087 `6aba4c7` / `88f1276`)  
**Package:** **0.18.0 HELD** · `LIVE_API_ENABLED` unchanged (True on CP-0087 product path; this CP does not touch it) · **NO_HELD unchanged except SaaS → un-PARKED for this path only** · M1=**NO_CONSENSUS_YET** · D3 NOT ACKed  
**Intent note:** `council/NOTE_S0_MESH_MINOGAN_INTELLIGENCE.md`

---

## 0. Operator marks (recorded, not invented)

| Mark | Date | Meaning |
|------|------|---------|
| "El Mesh va a ser el backend de inteligencia de Minogan.ai …" | 2026-10-18 | path intent |
| "Abre un CP explícito 'camino Minogan'. SaaS deja de estar PARKED **solo para este camino**." | 2026-10-18 | this CP; scoped SaaS un-park |
| "Primero guarda NOTE S0 … y el spike de schema UW … Después sigue con el track B … solo para la integración con Minogan." | 2026-10-18 | answer to pending A/B/C question → order P0.1 then track B (Minogan-scoped) |
| "Ningún servicio pago, dominio, VM ni key nueva sin mi aprobación. No hagas push ni tags sin pedirlo." | 2026-10-18 | fences |

## 1. Is / is not

| Is | Is not |
|----|--------|
| Mesh-side contract, deterministic scorer, per-tenant agent memory, local HTTP service, score ledger + replay | Rewrite of `/workspace/minogan-pilot` (pilot owns ingest, signals, alerts, SaaS) |
| Deterministic number; L_judge advisory text only | LLM in the score; judge output feeding the number |
| Metadata-only memory (pilot redaction policy) | Storing prompts / completions / tool args / tool results |
| Tenant-keyed on one box (N=2 substrate as-is) | Hardened multi-tenant SaaS; Raft; N>2; GIA |
| Deployment **proposal** | Any deploy, paid service, domain, VM, key |

## 2. Fences (unchanged + this path)

GIA NO_HELD · no consciousness/AGI claims · no Raft / N>2 · no push/tags · never retag v0.16.3 / v0.17.0 / v0.18.0 ·
no secrets in git (`gemini.env` stays out of repo) · `LIVE_API_ENABLED` untouched · RefuseTransport/I5 still gate any network ·
Mesh Minogan scorer path makes **zero network calls**. If any P0 item would cross a fence → STOP and ask the operator.

## 3. P0 (in order; acceptance = ✔)

| # | Item | Acceptance |
|---|------|------------|
| P0.1 | NOTE S0 + UW schema v0 (`council/`, `docs/schema/minogan/`) + contract mapping | ✔ committed (this CP) |
| P0.2 | `neural_mesh/minogan/contract.py` (pydantic v2) | validates fixtures generated from pilot `scripts/synthetic.mjs` via pilot pipeline (see mapping §6); invalid inputs → typed error (`ContractError` subclasses); content keys rejected |
| P0.3 | Mesh scorer v0, deterministic | parity **±1** with pilot `computeScore` (score_v0.3) on **≥50** frozen fixtures; same input ⇒ byte-identical output; zero network (socket-blocked test) |
| P0.4 | `AgentMemory` on C-RAM, key `(tenant_id, agent_id)`: `append`, `history(since,until)`, `baseline(window)`, `recurrence(rule,days)` | survives kill -9; 90-day `history` without full scan (time-bucket index objects, not `list_keys`); negative cross-tenant leak test; every record carries `hash` + `prev_hash` |
| P0.5 | HTTP: `POST /v1/score`, `GET /health` (`model_version`, `contract`); Bearer per tenant; 1 MB limit | p95 < 300 ms local with 200 events; request timeout < 2 s |
| P0.6 | Hash-chained score ledger + `mesh minogan replay <id>` | replay output identical; tampered record ⇒ verify fails |
| P0.7 | Off-PC deployment plan (Dockerfile + hosting options with cost) | **proposal only**; no deploy without operator OK |

Per milestone report: commit SHA · test command + pass/fail · left out · risks. No "unlock" prose.

## 4. Track B (Minogan-scoped)

After P0.1, the full-adapter live verification (CP-0081 track B) continues **only** as far as the Minogan integration needs it:
the L_judge may produce `components.advisory` text for a score; it is invoked after the number is fixed, its output is never an input to
`score`/`uw`, and it stays behind I5/RefuseTransport. No new live surface beyond CP-0087.

## 5. P1 (deferred — do not start without operator notice)

Hard multi-tenant · ingest adapter · calibration on labelled data (AUC / Brier / FP rate) · false-positive learning from pilot `suppressions` ·
verifiable per-tenant retention/deletion · per-tenant metrics.

## 6. Known risks at open

- C-RAM is CAS only (no secondary index) → P0.4 needs an index layer; design before code.
- Pilot is **not under git** (`/workspace/minogan-pilot` has no `.git`) → contract drift risk; Mesh pins the contract by frozen fixtures + field list.
- Test suite currently 17 failures caused by missing untracked `dist/releases/*` artefacts (see `.project_state/CURRENT_STATE.md`); unrelated to this path, must not be "fixed" by re-minting frozen releases.
- Several suite tests write into the real repo (`dist/releases/0.16.3/`, `.project_state/*SIGNOFF*.json`, `post_rc_watch_report.json`) — pre-existing hygiene debt.
