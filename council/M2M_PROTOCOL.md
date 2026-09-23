# Neural Mesh ↔ DeepSeek M2M Protocol (Grok Bot)

Purpose: minimize tokens/latency while keeping verifiable gates. Spanish/English prose banned in posts; use this schema only.

## Envelope (every message)

```
NM/M2M v1
ROLE: GROK|DEEPSEEK
CYCLE: <n>
DIR: STATUS|VERDICT|NEXT|ACK|BLOCK
TS: <ISO8601>
```

## GROK → DeepSeek STATUS (post after cycle close)

```
NM/M2M v1
ROLE: GROK
CYCLE: <n>
DIR: STATUS
VER: <semver>
TIP: <gitsha7>
CP: CP-00NN=VERIFIED
CP_RANGE: CP-0001..00NN=VERIFIED
PYTEST: <pass>/<fail>
AUDIT: PASS|FAIL
DUAL_PRIMARY: 0
PLAINTEXT_FB: 0
STALE_REJECT_PCT: 100
DUP_IDEM_PCT: 100
METRICS_P99_MS: k=v,k=v,...
DONE: P0,P1,... (short tags)
NO_HELD: Raft,N>2,multi-primary,ML,plaintext,GIA
ASK: VERDICT+NEXT
CONSTRAINTS: DeepSeek-only; Search=OFF; inline-only
```

## DeepSeek → GROK VERDICT+NEXT (required reply shape)

```
NM/M2M v1
ROLE: DEEPSEEK
CYCLE: <n>
DIR: VERDICT
V: APPROVED|CHANGES|REJECT
NOTE: <≤120 chars or ->
DIR: NEXT
CYCLE_NEXT: <n+1>
CP_NEXT: CP-00NN
VER_NEXT: <semver>
PYTEST_MIN: <int>
TITLE: <≤60 chars>
SCOPE: tag,tag,tag
BOUNDS: k=v;k=v
ACCEPT: tag,tag
NO: tag,tag
P: P0=<..>;P1=<..>;...
```

## Rules
1. One NEXT only. No alternatives lists.
2. No PDF/export chatter. No motivational text.
3. Numbers only where measured; never invent metrics.
4. If CHANGES: list exact deltas in NOTE/P only.
5. Grok executes NEXT immediately without ChatGPT while DeepSeek-only mode is on.
