# NOTE — IMPL CP-0079 multi-canary pack + permanent enable policy

**Date:** 2026-09-28 ~22:40 EDT  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip base:** `ee0c0c6`

- Harness `l_judge_multi_canary_pack.py` runs n≥N_min=5 with E-KILL / E-ABORT-ACCEPT / E-AUTH / E-ANOMALY / E-RESUME + happy-path.
- Permanent enable policy written; Gate5 runbook §8 updated; default after pack = module LIVE **False**.
- F4 product-enable still OPEN; NO_HELD unchanged; no push/tags/secrets.
- Evidence: `GATE5_MULTI_CANARY_*` · Gate6 measurement update.
- **Claim hygiene (I-5):** prefer **「pack n=6 (1 real, 5 mock)」**; `n_real_http=1` · `n_mock=5`; seal_candidate = **n=6 total**, not 5 live.

*End note.*
