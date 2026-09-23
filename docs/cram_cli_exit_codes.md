# C-RAM CLI exit codes (frozen Cycle 5)

ChatGPT ∩ DeepSeek freeze — do not renumber without a new council ADR.

| Code | Meaning |
|------|---------|
| **0** | PASS |
| **1** | Generic CLI error (unexpected exception). **Do not reuse 2/3.** |
| **2** | Integrity failure (corrupt blob / CRAM_CORRUPT) |
| **3** | Missing or unavailable (`ObjectMissing` / `NodeUnavailable`) |

## Commands

- `mesh cram put` → 0 on success, 1 on generic error
- `mesh cram get <key>` → 0 / 3 / 1
- `mesh cram verify <key>` → 0 / 2 / 3 / 1
- `mesh cram fsck [--json]` → worst case found: **2** if any corrupt, else **3** if any missing, else **0**

## `fsck --json` schema

Must include versioned field:

```json
{ "fsck_schema": 1, "status": "OK|CORRUPT|INCOMPLETE|ORPHANS", ... }
```
