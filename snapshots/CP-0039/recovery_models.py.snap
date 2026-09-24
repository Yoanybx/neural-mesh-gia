"""Recovery + rebuild models (Cycle 35 / CP-0039 / H2).

Schema: mesh.recovery/v1
Capability: docs/capabilities/MESH_RECOVERY_REBUILD.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_ID = "mesh.recovery/v1"
SCHEMA_STORE = "mesh.recovery.store/v1"
SCHEMA_SNAPSHOT = "mesh.recovery.snapshot/v1"


class RecoveryError(RuntimeError):
    """Base recovery / rebuild error (fail-closed)."""

    code: str = "RECOVERY_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class RecoveryTamper(RecoveryError):
    code = "RECOVERY_TAMPER"


class RecoveryMissingSnapshot(RecoveryError):
    code = "RECOVERY_MISSING_SNAPSHOT"


class RecoveryAbortRestore(RecoveryError):
    """ABORT→snapshot restore: recovery failed; restore path taken or required."""

    code = "RECOVERY_ABORT_RESTORE"


class RecoveryPlaintextForbidden(RecoveryError):
    code = "RECOVERY_PLAINTEXT_FORBIDDEN"


class RecoveryRebuildFailed(RecoveryError):
    code = "RECOVERY_REBUILD_FAILED"


class RecoveryVerifyFailed(RecoveryError):
    code = "RECOVERY_VERIFY_FAILED"


@dataclass
class DurableState:
    """Operator-facing durable projection reconstructed from snapshot + WAL."""

    epoch: int = 0
    seq: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    last_snapshot_id: str = ""
    schema: str = SCHEMA_ID
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DurableState":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        st = cls(**kwargs)
        st.dual_primary = 0
        st.vault_acme_required = 0
        st.plaintext_fallback = 0
        st.schema = SCHEMA_ID
        if st.payload is None:
            st.payload = {}
        return st


@dataclass
class SnapshotMeta:
    """Recovery snapshot metadata (content-hash sealed)."""

    snapshot_id: str
    content_hash: str
    wal_offset: int
    epoch: int = 0
    seq: int = 0
    created_at: str | None = None
    reason: str = ""
    schema: str = SCHEMA_SNAPSHOT
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_SNAPSHOT
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotMeta":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        meta = cls(**kwargs)
        meta.dual_primary = 0
        meta.vault_acme_required = 0
        meta.plaintext_fallback = 0
        meta.schema = SCHEMA_SNAPSHOT
        return meta


@dataclass
class RecoveryStatus:
    """Operator-facing recovery status."""

    ok: bool
    data_root: str
    durable: dict[str, Any]
    last_good_snapshot: str
    snapshot_count: int
    wal_entries: int
    abort_restore: bool
    abort_reason: str = ""
    issues: list[str] = field(default_factory=list)
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d


@dataclass
class RestoreResult:
    ok: bool
    snapshot_id: str
    content_hash: str = ""
    restored_seq: int = 0
    abort_restore: bool = False
    error: str | None = None
    error_code: str | None = None
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        return d


@dataclass
class RebuildResult:
    ok: bool
    snapshot_id: str
    wal_replayed: int = 0
    final_seq: int = 0
    abort_restore: bool = False
    error: str | None = None
    error_code: str | None = None
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        return d


__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "SCHEMA_SNAPSHOT",
    "RecoveryError",
    "RecoveryTamper",
    "RecoveryMissingSnapshot",
    "RecoveryAbortRestore",
    "RecoveryPlaintextForbidden",
    "RecoveryRebuildFailed",
    "RecoveryVerifyFailed",
    "DurableState",
    "SnapshotMeta",
    "RecoveryStatus",
    "RestoreResult",
    "RebuildResult",
]
