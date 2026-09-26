# Schema: mesh.goal/v0 (STUB)

**Status:** STUB (Cycle 47 / CP-0051)  
**Schema id:** `mesh.goal/v0`  
**Design:** `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`

## GoalRecord

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.goal/v0` |
| `goal_id` | string | `goal:<hash16>` |
| `version` | int | starts at 1 |
| `content_digest` | string | sha256 |
| `title` | string | short |
| `assignee` | string | human: \| agent: \| mesh: |
| `priority` | int | |
| `created_hlc` / `updated_hlc` | string | |
| `parent_goal_id` | string\|null | |
| `terminal` | bool | |
| `continuity_id` | string | `cont:<hash16>` |

Restart-safe registry; NOT transformer infinite-context; NOT consciousness.

**NO_HELD** unchanged.
