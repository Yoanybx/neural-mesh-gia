# Google / Gemini — optional second L_judge peer (design spike)

**Status:** DESIGN ONLY (dry-run / mock; **live=DISABLED**)  
**Date:** 2026-09-26 America/New_York (EDT)  
**Authority:** `council/CHATGPT_REPLY_GOOGLE_AI_TOOLS_APPROVAL.md` VERDICT **APPROVE_WITH_FENCES**  
**Council note:** `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`  
**Stub:** `src/neural_mesh/packaging/google_l_judge_peer_spike.py`  
**Tests:** `tests/test_google_l_judge_peer_spike.py`  
**Non-claim:** No live API · no API keys in repo · no Mesh authority · dual advisory ≠ M1 consensus · no pkg0190 · no GIA · no Raft/N>2 · no Vertex paid · no train-70B.

---

## 1. Intent

Treat **Gemini free-tier** as an **optional second L_judge peer** for design-stage **correlation / independence** experiments — composed with the existing mock multi-judge path (CP-0065) and fail-closed **RefuseTransport** default (CP-0058).

```
Primary mock L_judge ──┐
                       ├──► correlation / independence harness (mock)
Gemini peer (mock) ────┘         │
                                 ▼
                    evidence digests only (not Mesh SoT)
RefuseTransport ──► every "live" path ABORTs ENGINE_DISABLED
```

**Google AI Studio:** prompt/schema contract exploration offline — not a runtime component.  
**Colab free:** optional offline notebooks under `notebooks/colab/` — evaluation artifacts only; **no Colab login required** to keep the placeholder path in-repo.

---

## 2. Fences (must hold)

| Fence | Rule |
|-------|------|
| **live** | **DISABLED** — stub keeps `LIVE_API_ENABLED = False`; live path → RefuseTransport / `PEER_LIVE_DISABLED` |
| **keys** | **No API keys in repo**; no `sk-` / Bearer material; secret_handle pattern only if ever authorized later |
| **authority** | Gemini outputs are **evaluation evidence**, not consensus, safety proof, or orchestration SoT |
| **independence** | Peer participation must surface correlation risk, disagreement, failure modes, provenance |
| **runtime** | Not production Mesh runtime; not Colab/AI Studio as orchestrator |
| **order** | Does not bypass D1→D2→D3 or existing CP fences |
| **ACK** | Future live Gemini use needs **separate operator ACK** + safety-case amendment |

---

## 3. Dry-run / mock scenarios

| ID | Scenario | Expect |
|----|----------|--------|
| **T-gemini-a** | Dual mock peers agree on advisory digest | `correlated=True`; `advisory_only=True`; `m1_status=NO_CONSENSUS_YET`; evidence provenance recorded |
| **T-gemini-b** | Dual mock peers disagree | `correlated=False`; disagreement recorded; **no** invented Mesh ACCEPT / consensus |
| **T-gemini-c** | Caller requests live Gemini transport while live=DISABLED | **RefuseTransport** / `PEER_LIVE_DISABLED`; no network |
| **T-gemini-d** | Independence probe (identical prompts → identical mock digests) | Flag `independence_risk=HIGH` when digests match under forced-correlation fixture |
| **T-gemini-e** | N>2 peer roster / Raft / keys-in-payload | Fence ABORT (`PEER_N_GT2_REFUSED` / `PEER_FENCE` / secret refuse) |

---

## 4. RefuseTransport binding

Default binding for any Gemini/"live" peer slot:

- Reuse `neural_mesh.packaging.l_judge_live_adapter_safety.RefuseTransport`
- Every `.call(...)` → `ok=False`, `error_code=ENGINE_DISABLED`, `verdict=ABORT`
- Health: `{ok: True, binding: "RefuseTransport", live: False}`

Mock peer transport (`MockGeminiPeerTransport`) is **in-process only** — returns canned digests; never opens sockets; never reads env API keys.

---

## 5. Correlation / independence tests (design)

1. **Correlation:** compare primary mock digest vs Gemini-mock digest on the same envelope; record `correlation_score` in `[0,1]` from digest equality / Hamming of truncated digests (mock heuristic only).
2. **Independence review:** when correlation is forced-high, mark `independence_risk` and require human/I5 review in any future live design — **does not** auto-approve.
3. **Disagreement handling:** mismatch → evidence row + continue advisory; Mesh policy / I5 arbitrate; peer cannot override Mesh ABORT.
4. **Provenance:** each peer attribution includes `provider`, `model_ref` (mock), `digest`, `transport=mock|refuse`.

---

## 6. Explicit non-goals

- Real Gemini HTTPS / SDK / AI Studio production traffic  
- Keys, tokens, or Vertex billing in repo or CI  
- Replacing Neural Mesh orchestration with Google tooling  
- Claiming Google models prove consensus or safety  
- Colab as control plane / execution layer  
- live=ENABLED · GIA · Raft/N>2 · train-70B · SaaS · pkg0190

---

## 7. Colab placeholder

Path: `notebooks/colab/README.md` (+ optional future `.ipynb` under that directory).

- Offline scorecard / eval harness **placeholder only**
- Does **not** require Colab login, Google account, or network for repo CI
- Artifacts remain evaluation-only (fence §7 in council note)

---

## 8. Implementation map

| Artifact | Role |
|----------|------|
| `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` | ALLOWED / FENCES / FORBIDDEN + tip state |
| `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md` | This spike |
| `src/neural_mesh/packaging/google_l_judge_peer_spike.py` | Mock peer + correlation helpers + RefuseTransport default |
| `tests/test_google_l_judge_peer_spike.py` | Negative + mock correlation tests |
| `notebooks/colab/README.md` | Colab path note |

---

## 9. Tip / package posture

| Item | Value |
|------|-------|
| Package | **0.18.0 HELD** |
| live | **DISABLED** |
| pkg0190 | **NOT_OPENED** |
| M1 | **NO_CONSENSUS_YET** |
| Cycle tip at write | `b3e84fb` / sealed feature `4b43bf4` (CP-0074); this spike is design-only under fences |

**ONE_LINE:** Gemini free tier is a fenced optional mock second L_judge peer for correlation/independence dry-runs; RefuseTransport default; no keys; live=DISABLED.
