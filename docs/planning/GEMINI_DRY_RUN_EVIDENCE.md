# Gemini free-tier dry-run evidence

**Captured:** 2026-09-28 18:09:36 EDT (ET) (`2026-09-28T22:09:36.818251+00:00`)  
**Repo tip at capture base:** `fc4ef9e`  
**Scope:** Operator-authorized **eval dry-run** only (Google Generative Language API free)

## Posture

- Gate1: **SIGNED DISCUSS_ONLY**
- live: **DISABLED**
- `LIVE_API_ENABLED`: **false** (untouched)
- Mesh live adapter: **not enabled**
- No push, no tags, no secrets in tree

## Secret handle (path only)

```
/home/box/.config/neural-mesh/gemini.env
```

- Env var: `GEMINI_API_KEY` (sourced in shell for the one-shot call)
- Prefix/len recorded for handle hygiene only: prefix=`AQ.A...`, len=53
- Value never written to repo evidence

## Request

| Field | Value |
|-------|-------|
| API | Google Generative Language `generateContent` (v1beta) |
| Endpoint (redacted) | `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=<REDACTED>` |
| Prompt | `Reply with exactly: MESH_DRY_RUN_OK` |
| Model (used) | `gemini-flash-latest` |
| Temperature | 0 |
| maxOutputTokens | 256 |

Preferred IDs `gemini-2.0-flash` and `gemini-1.5-flash` returned **HTTP 404 / error_class=model** (retired). Proceeded with free-tier alias accepted by this key: **`gemini-flash-latest`**.

## Response digest

| Field | Value |
|-------|-------|
| HTTP status | **200** |
| Body text | `MESH_DRY_RUN_OK` |
| OK marker | `True` |
| SHA-256 (raw HTTP body) | `6425bf176545c93c236d3fea4444a782422b70f0a9f03dd2582b2057452ab4f0` |
| modelVersion | `gemini-3.8-flash` |

### UsageMetadata (sanitized)

```json
{
  "promptTokenCount": 13,
  "candidatesTokenCount": 8,
  "totalTokenCount": 92,
  "thoughtsTokenCount": 71,
  "serviceTier": "standard"
}
```

## Error classes encountered (probes)

| Model | HTTP | error_class | Notes |
|-------|------|-------------|-------|
| gemini-2.0-flash | 404 | model | no longer available |
| gemini-1.5-flash | 404 | model | not found for v1beta |
| gemini-2.5-flash | 404 | model | no longer available to new users |
| gemini-flash-latest | 200 | — | success; marker present |

No **auth** or **quota** failure on the successful call.

## Git hygiene

- `.gitignore` includes `gemini.env`, `**/gemini.env`, `.config/neural-mesh/`, `**/.config/neural-mesh/`
- Key remains only under `/home/box/.config/neural-mesh/`

## Explicit non-actions

- Did **not** flip `LIVE_API_ENABLED`
- Did **not** enable Mesh live adapter
- Did **not** commit `gemini.env` or any key material
- Did **not** push or tag

---
*Evidence only — Gate1 DISCUSS_ONLY; live=DISABLED.*
