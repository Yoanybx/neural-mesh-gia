# Schema: mesh.recovery/v1

**Status:** ACTIVE (Cycle 35 / CP-0039)  
**Schema id:** `mesh.recovery/v1`  
**Store schema:** `mesh.recovery.store/v1`  
**Snapshot schema:** `mesh.recovery.snapshot/v1`

## DurableState

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.recovery/v1` |
| `epoch` | int | durable epoch |
| `seq` | int | monotonic apply sequence |
| `payload` | object | projection key/values |
| `last_snapshot_id` | string | last SNAP-id written into state |
| `updated_at` | string | UTC ISO-ish |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |

## SnapshotMeta

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.recovery.snapshot/v1` |
| `snapshot_id` | string | `SNAP-NNNN` |
| `content_hash` | string | SHA-256 over schema tag + wal_offset + state.json bytes |
| `wal_offset` | int | WAL line count at snapshot time |
| `epoch` / `seq` | int | frozen from durable |
| `created_at` | string | |
| `reason` | string | |

## RecoveryStatus

| Field | Type | Notes |
|-------|------|-------|
| `ok` | bool | |
| `data_root` | string | |
| `durable` | object | DurableState dict |
| `last_good_snapshot` | string | |
| `snapshot_count` / `wal_entries` | int | |
| `abort_restore` | bool | ABORT mode |
| `abort_reason` | string | |
| `issues` | string[] | |

## Error codes

| Code | Meaning |
|------|---------|
| `RECOVERY_TAMPER` | content hash mismatch / integrity fail |
| `RECOVERY_MISSING_SNAPSHOT` | snapshot id or last_good absent |
| `RECOVERY_ABORT_RESTORE` | ABORT→snapshot restore engaged / exhausted |
| `RECOVERY_REBUILD_FAILED` | WAL replay / rebuild failure |
| `RECOVERY_VERIFY_FAILED` | verify path failure |
| `RECOVERY_PLAINTEXT_FORBIDDEN` | plaintext mode refused |

## Layout

```
<data-root>/
  recovery/
    recovery_state.json      # abort_restore, last_good_snapshot
    durable/state.json       # DurableState projection
    wal/wal.jsonl            # append-only apply log
    snapshots/
      SNAP-0001/
        snapshot.json
        state.json
        content.sha256
```
