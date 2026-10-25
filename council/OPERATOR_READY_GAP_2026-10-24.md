# Operator ready gap — carrier/MGA can use Minogan for agent UW today?

**Date:** 2026-10-24 (America/New_York)  
**Verdict:** **NO.** There is a working **dev/preview pilot** (synthetic data) and a **mock Command Center UI**. There is **not** a finished product that a carrier desk can underwrite real AI agents on.

**Product fence (unchanged):** Minogan does **not** write policies. Product = risk scores + evidence for carriers/MGAs who write cover.

---

## What exists today (verified on box + public HTTP)

### A. Marketing / investor (production-ish Pages)

| URL | What it is |
|-----|------------|
| https://minogan.ai/ | Marketing landing (Command Center mentioned as product story; no live UW desk) |
| https://minogan.ai/investors/ | Investor area on production domain (HTTP 200) |
| https://investor-preview.minogan.pages.dev/ | Guest-gated white papers preview (`MINOGAN-SEED`) |

Landing repo (`/workspace/minogan-landing`): marketing + investor papers only. **No** `/insurer/*` or `/enterprise/*` app routes. `minogan.ai/insurer/portfolio/` → **404**.

### B. Pilot backend (Cloudflare Workers + D1) — **env: `dev`**

| Piece | URL / id |
|-------|----------|
| Ingest | https://minogan-pilot-ingest-dev.astra-department-store.workers.dev (`score_v0.3`) |
| Read API | https://minogan-pilot-api-dev.astra-department-store.workers.dev (`env: "dev"`) |
| D1 | `minogan-pilot-dev` |

**Endpoints (auth Bearer required for `/v1/*` reads; unauth `/v1/agents` → 401):**
- Ingest: `POST /v1/traces` (OTLP JSON/protobuf), `POST /v1/events`, `POST /v1/score`
- API: session, agents, signals, events, timeline, alerts+actions, suppressions, evidence-pack + verify, keys, webhook
- Cron every 5 min scores stale agents

**Data today:** README states **SYNTHETIC TEST DATA** only (`org_synthetic_pilot`). No customer data.  
**Auth:** per-org API keys (ingest/read/admin/demo); org isolation from key’s `org_id`; demo keys blocked on non-synthetic orgs.  
**Multi-tenant:** soft — schema has `orgs` + keys; **not** hard SaaS multi-tenant (no SSO, no per-tenant retention/delete proof, free-tier caps).  
**Scorer:** built-in `rules` / `score_v0.3` only. Hook for external Mesh exists; **`getScorer` → `ruleScorer` only. “Not integrated yet.”**  
**UW outcome in rules:** `uwOutcome(score)` → bind | bind-with-terms | refer (threshold heuristic). **No `decline` persistence path for a desk.**  
**Repo:** `/workspace/minogan-pilot` — **not a git repo** (contract can drift without SHA).

### C. SaaS / Command Center UI

| URL | What it is |
|-----|------------|
| https://pilot-live-preview.minogan-saas.pages.dev/ | “Agent Risk Command Center” preview (HTTP 200) |
| Local `/workspace/minogan-saas` | README: **local preview only. No production deploy.** |

- **Login:** UI shell / localStorage persona — **not** real IdP.
- **Live mode** (optional build flags): Overview, Agents, Agent 360, Events, Alerts, Integrations, Evidence pack can hit the **dev** pilot API.
- **Insurer lane** (`/insurer/portfolio`, `/insurer/agents/[id]`, `/uw`, studies): still **`mock-data.ts`**. Bind / Bind-with-terms / Refer = **toasts** (“audit appended (mock)”). No backend persistence of UW decisions.
- Default build = **mock**.

### D. Neural Mesh (CP-0088 P0) — tip `c2881eb`

Local only on the box: contract, deterministic scorer (parity 228/228 vs pilot), AgentMemory, loopback HTTP, hash ledger + replay, **deploy proposal only**.  
**Not on Cloudflare. Not called by the pilot. Not reachable by a carrier.**

---

## What a carrier/MGA CAN do TODAY

1. Read marketing and (if invited) investor papers on minogan.ai / investor-preview.
2. With a **dev** API key: send **synthetic** OTel/simple events to the **dev** ingest Worker; read scores/signals/alerts/evidence-pack JSON from the **dev** API.
3. Open the **preview** Command Center UI and click through mock insurer UX; optionally a live build against **synthetic** pilot data.
4. Run the local Mesh scorer offline (box) — irrelevant to production UW.

## What they CANNOT do yet (honest gaps)

| Gap | Reality |
|-----|---------|
| Production UW desk | No production SaaS; insurer routes are mock; minogan.ai has no Command Center app |
| Real customer tenants | Only synthetic org; pilot labeled `env: "dev"` |
| Mesh memory / long-horizon drift in prod | Mesh P0 local; pilot not wired; CF Containers disk ephemeral for Python path |
| Persist Bind / Terms / Refer / Decline | UI toasts only; no durable UW decision API for carriers |
| Evidence packs as production UW file | API exists on **dev**; SaaS evidence UI live-capable but not a carrier production workflow |
| Hard multi-tenant isolation + delete proof | Soft org+key only; retention/borrado verificable = P1 |
| SSO / enterprise auth | Key/session HMAC; login UI is shell |
| SLA / SOC2 / insurance-grade claims | Nothing in repo supports claiming these |
| Calibrated model | Heuristic score_v0.3; Mesh decline thresholds provisional; no AUC/Brier |
| Email alerting | Explicitly not enabled |
| Write policies | **Out of scope forever** — carriers write paper |

---

## Minimum path — “usable for a **pilot** UW desk” entirely on Cloudflare

Acceptance = one **named pilot carrier org** (still can be synthetic-first), real auth, durable scores+evidence, UW recommendation recorded, Mesh-or-rules scoring on CF — **not** “finished product / SOC2 / production book.”

Ordered steps (no spend until operator OK):

1. **Freeze pilot in git** — SHA-pin `minogan.scorer/v1`; stop unversioned contract drift.  
   ✔ Pilot is a repo; tag or commit hash cited by Mesh parity tests.

2. **Promote a `pilot` (not `dev`) Workers+D1 stack** on Cloudflare — separate D1, keys, no shared synthetic demo key in the UI.  
   ✔ Health returns `env: "pilot"`; unauthenticated reads 401; org isolation tested with 2 orgs.

3. **Wire SaaS live build for insurer lane** — `/insurer/*` and `/uw` read pilot API; drop mock for that build.  
   ✔ Portfolio and agent detail show live scores; evidence-pack page verifies HMAC against API.

4. **UW decision API on Workers/D1** — `POST /v1/agents/:id/uw-decision {outcome, conditions[], note}` with audit_log; outcomes bind|bind-with-terms|refer|decline as **recommendations**.  
   ✔ Replay of decisions in API; UI no longer toast-only; disclaimer “Minogan does not bind cover” on every action.

5. **Auth for desk users** — at minimum invite + hashed password or Cloudflare Access in front of Pages; session tied to org.  
   ✔ No shared demo key in production UI; Access or equivalent blocks anonymous `/insurer/*`.

6. **Scorer on Cloudflare (no Python VM required for pilot desk)** — keep `ruleScorer` as primary; optional later: port AgentMemory+ledger to **Durable Objects SQLite** (one DO per tenant/agent) if Mesh memory is required for the pilot.  
   ✔ Pilot scores without calling loopback Mesh; if Mesh DO path chosen: kill/restart Worker does not lose memory; cross-tenant read fails.

7. **One end-to-end pilot script** — OTel demo agent → ingest → score → evidence-pack → UW decision recorded → printable pack.  
   ✔ Documented runbook; under 15 minutes for operator; synthetic labeled.

**Out of this minimum:** SOC2, SLA, multi-region HA, calibrated decline, Raft/N>2, GIA, paid email, claiming “ready for all carriers.”

---

## Bottom line for Joan

- **No:** the finished product for insurers to use on real policies is **not** ready.  
- **Yes:** there is a **credible technical pilot** (Workers/D1 + score_v0.3 + evidence-pack API + preview UI) on synthetic data, plus a **local** Mesh brain not yet on Cloudflare.  
- Next operator choice: approve the Cloudflare pilot-desk path above (steps 1–7), or stay on marketing/investor-only until that work is done.
