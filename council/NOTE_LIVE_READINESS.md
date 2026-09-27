# Operator note — Live readiness checklist (design-only)

- **Date:** 2026-09-26 America/New_York (EDT)
- **Author:** Grok Bot (Staff Eng — docs only; not an unlock)
- **Tip context:** ~`74ce42e` / Google mock spike atop **CP-0074** (`4b43bf4`)
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** (N=2 permanent) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**
- **Planning doc:** `docs/planning/LIVE_READINESS_CHECKLIST.md`
- **CP minted:** **No** (docs+commit only; continues fenced Google spike; no cycle helpers/tests required)

## Operator ask

You asked what is missing for **live+API** after D4/D1 and the Google free-tools mock spike. Continue = **checklist only** — no enable, no keys, no real Gemini, no D3, no push/tags.

## Ordered gates (summary)

1. **Operator ACK** — separate live discussion/enable ACK (Google APPROVE_WITH_FENCES ≠ this)
2. **Safety evidence** — D1 design OK; **live safety-case amendment** still required
3. **Authority Matrix in use** — D1 §3 table exists; live ops must bind to it
4. **Keys + data policy** — no keys in repo; live data schedule + secret_handle before any real call
5. **Adapter RefuseTransport → live flag** — refuse-default stays; flip is runbook+ACK, not this note
6. **Acceptance metrics** — D4-E/J/K bundle for the live cycle
7. **Optional D3** — ACK-gated; does **not** unlock live/M1
8. **M1 N=2 posture** — permanent NO_CONSENSUS_YET **does not block** local/mock judge API; still blocks claiming consensus or enabling live network API

## Missing for live+API (one line)

**Gates 1–6 open** (ACK, live amendment, matrix-bound ops, keys/data schedule, controlled flag flip, acceptance bundle). Local mock judge work may continue under existing fences.

## Must stay false

`live_adapter.enabled` · `LIVE_API_ENABLED` · real provider calls · keys in tree · D3 without ACK · pkg0190 / v0.19 / GIA / Raft/N>2 / train-70B

## Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`
- `council/COUNCIL_AGREEMENT_D4.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`
- `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md`
