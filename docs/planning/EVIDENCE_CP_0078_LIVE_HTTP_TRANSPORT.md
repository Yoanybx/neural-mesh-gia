# Evidence — CP-0078 LiveHttpTransport v0

**Date:** 2026-09-28 ~22:35 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Impl CP:** **CP-0078**  
**Base tip:** `46858e1`  
**LIVE_API module final:** **False**  
**src_live_codec_shipped:** **True** (packaging v0)  
**NO_HELD:** unchanged

## What was proven (unit / mock)

| ID | Scenario | Result |
|----|----------|--------|
| T-lht-a | live off → RefuseTransport | PASS (zero network) |
| T-lht-b | invalid secret_handle | PASS → ENGINE_AUTH |
| T-lht-c | plaintext endpoint | PASS → PLAINTEXT_FORBIDDEN |
| T-lht-d | idempotent replay | PASS (single invoke) |
| T-lht-e | idempotency conflict | PASS → CONT_IDEMPOTENCY_CONFLICT |
| T-lht-f | 5xx exhaust retries | PASS → ENGINE_HTTP; no ACCEPT |
| T-lht-g | hard timeout | PASS → ENGINE_TIMEOUT |
| T-lht-h | I5 kill / cancel | PASS → ABORT + refuse |
| T-lht-i | missing audit | PASS → NO_AUDIT |
| T-lht-j | streaming mode | PASS → ABORT; no half-ACCEPT |
| T-lht-k | live_api_in_ci | PASS → may_enable False |
| T-lht-l | DESIGN_ONLY vs IMPL | PASS — codec under CP-0078 only |
| NT default | may_enable without auth | PASS fail-closed |
| Compose | CP-0075 canary skip_network | PASS unchanged |

Prefer **unit + mock HTTP**; no permanent LIVE flip. Optional single fenced CLI call is operator-gated (`--execute`) and always restores runtime LIVE false.

## Not claimed

- **Activate live** — authorize = merge v0 **default-off**; does **NOT** activate live / flip module True (I-11)  
- Gate6 live seal / n≥5 multi-canary  
- Permanent product enable  
- Streaming codec  
- advisory = SoT / M1  
- Keys in git / push / tags  

## Test module

`tests/test_l_judge_live_http_transport_cycle74.py` · marker `l_judge_live_http_transport_cycle74`
