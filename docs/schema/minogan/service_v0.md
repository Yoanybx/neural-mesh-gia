# Mesh Minogan service v0 (CP-0088 P0.5)

Local loopback HTTP service exposing the deterministic Mesh scorer to the Minogan pilot. **stdlib only**
(`http.server.ThreadingHTTPServer`) — no new dependencies. **Not deployed** (deployment = P0.7, operator OK).

Code: `src/neural_mesh/minogan/service.py` · CLI: `mesh minogan serve|hash-token` · Tests:
`tests/test_minogan_service_cp0088.py` · Bench: `scripts/minogan/bench_service.py`.

## Endpoints

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/health` | none | `{ok, service:"mesh-minogan", model_version, contract:"minogan.scorer/v1", methodology, scorer:"mesh"}` |
| POST | `/v1/score` | Bearer | `ScorerOutput` (canonical JSON, byte-identical to `score(inp, memory)`), header `X-Mesh-Memory-Seq` |

`POST /v1/score` flow: auth → `Content-Length` (411 missing, 413 > 1 048 576 B, rejected before reading) → read
(socket timeout) → `parse_scorer_input` → `org_id == tenant(token)` → per-(tenant, agent) lock → `score(inp,
memory=AgentMemory)` → deadline check → `AgentMemory.append_score` → 200.

## Auth

- `Authorization: Bearer <token>`. Configured values are **only** `sha256:<hex>` of tokens (plaintext refused).
- Source: `--tokens-file` / `$MESH_MINOGAN_TOKENS_FILE` (JSON `{"tenants": {"<org_id>": ["sha256:<hex>", …]}}`,
  kept **outside the repo**) or `$MESH_MINOGAN_TOKENS` (`org:sha256hex,org2:sha256hex`).
- `mesh minogan hash-token` reads a token on stdin and prints its `sha256:` value.
- Lookup hashes the presented token and `hmac.compare_digest`s it against **every** configured hash (no early exit).
- Tenant = the token's tenant; body `org_id` must equal it, else **403 `tenant_mismatch`** (nothing written).

## Errors (JSON `{"error": {code, message, path?, errors?}}`, never echoing content)

| Status | code | When |
|--------|------|------|
| 400 | `short_body` | body shorter than Content-Length |
| 401 | `unauthorized` | missing / malformed / unknown bearer token |
| 403 | `tenant_mismatch` | `org_id` ≠ token tenant |
| 404 | `not_found` | other paths |
| 408 | `request_timeout` | body not received within the read timeout (1.0 s) |
| 409 | `memory_order` | `now` older than the agent's last memory record |
| 411 | `length_required` | no Content-Length |
| 413 | `payload_too_large` | Content-Length > 1 MB |
| 422 | `contract_version` / `validation` / `content_key` / `limit` | typed `ContractError` |
| 500 | `memory_*` | AgentMemory integrity error (corrupt / tenant) |
| 504 | `deadline` | processing exceeded 1.5 s; **the record is not appended** |

Messages are fixed strings per code; `path` / `errors[].loc` carry JSON paths and field names only (truncated),
`errors[].type` the pydantic error type. Input values never appear in responses or logs.

## Timeouts (all < 2 s; constructor refuses ≥ 2 s)

- Socket read timeout 1.0 s (slow body → 408; silent connection → closed).
- Processing deadline 1.5 s from request start (scoring in a worker pool; 504 on expiry; append skipped if the
  deadline passed while scoring).

## Logging

One JSON line per request on stderr: `ts, svc, method, path, status, latency_ms, tenant, agent, bytes, digest,
score, seq, err`. No bodies, tokens, agent names/functions, event names, trace ids, prompts or completions.

## Latency (local, 200-event input, 71 KB body, every request appends)

See `.project_state/TEST_STATUS.md` for the numbers recorded at commit time. Latency grows with the number of
records in the agent's 90-day memory window (history is re-read per request); P0.5 adds an in-process cache of
already-verified record hashes (bytes are still re-verified against the C-RAM key on every read).
