"""Minority-write safety models (Cycle 39 / CP-0043 / H6).

Schema: mesh.minority/v1
Capability: docs/capabilities/MESH_MINORITY_WRITE_FENCE.md

Invariant: MINORITY_WRITES hard 0 (successful minority commits never succeed).
ABORT→halt writes on minority-write detection @N2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SCHEMA_ID = "mesh.minority/v1"
SCHEMA_STORE = "mesh.minority.store/v1"
SCHEMA_ATTEMPT = "mesh.minority.attempt/v1"
SCHEMA_HALT = "mesh.minority.halt/v1"

WriteOutcome = Literal["accepted", "rejected_minority", "rejected_halted", "rejected_unknown"]


class MinorityError(RuntimeError):
    """Base minority-write error (fail-closed)."""

    code: str = "MINORITY_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class MinorityWriteDetected(MinorityError):
    """A non-primary / minority side attempted a write @N2."""

    code = "MINORITY_WRITE_DETECTED"


class MinorityAbortHaltWrites(MinorityError):
    """ABORT→halt writes engaged or writes already halted."""

    code = "MINORITY_ABORT_HALT_WRITES"


class MinorityPlaintextForbidden(MinorityError):
    code = "MINORITY_PLAINTEXT_FORBIDDEN"


class MinorityN2Only(MinorityError):
    """N>2 / Raft / multi-primary architecture refused."""

    code = "MINORITY_N2_ONLY"


class MinorityNodeUnknown(MinorityError):
    code = "MINORITY_NODE_UNKNOWN"


class MinorityWritesHalted(MinorityError):
    """All writes refused while halt is engaged."""

    code = "MINORITY_WRITES_HALTED"


@dataclass
class WriteAttempt:
    """Record of a write attempt (diagnostic; never a committed minority write)."""

    node_id: str
    key: str
    outcome: WriteOutcome
    is_minority: bool = False
    schema: str = SCHEMA_ATTEMPT
    minority_writes: int = 0  # hard 0
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    ts: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["minority_writes"] = 0
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ATTEMPT
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriteAttempt":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        wa = cls(**kwargs)
        wa.minority_writes = 0
        wa.dual_primary = 0
        wa.vault_acme_required = 0
        wa.plaintext_fallback = 0
        wa.schema = SCHEMA_ATTEMPT
        return wa


@dataclass
class MinorityStatus:
    """Operator-facing minority-write status. minority_writes intent always 0."""

    ok: bool
    data_root: str
    pair: list[str]
    writable_primary: str | None
    writes_halted: bool
    abort_halt_writes: bool
    abort_reason: str = ""
    minority_write_detected: bool = False
    minority_writes: int = 0  # hard intent 0
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    attempt_count: int = 0
    rejected_minority_count: int = 0
    issues: list[str] = field(default_factory=list)
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["minority_writes"] = 0
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d


@dataclass
class ProbeResult:
    """Probe of minority-write condition @N2."""

    ok: bool
    minority_write_detected: bool
    minority_writes: int = 0
    dual_primary: int = 0
    writable_primary: str | None = None
    writes_halted: bool = False
    abort_halt_writes: bool = False
    action: str = "none"  # none | halt_writes | abort_halt_writes
    minority_claimants: list[str] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["minority_writes"] = 0
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        return d


@dataclass
class HaltResult:
    """ABORT→halt writes outcome."""

    ok: bool
    writes_halted: bool
    abort_halt_writes: bool
    minority_writes: int = 0
    dual_primary: int = 0
    reason: str = ""
    error: str | None = None
    error_code: str | None = None
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_HALT

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["minority_writes"] = 0
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_HALT
        return d


@dataclass
class WriteResult:
    """Outcome of try_write (primary accept or minority reject)."""

    ok: bool
    outcome: WriteOutcome
    node_id: str
    key: str
    is_minority: bool = False
    writes_halted: bool = False
    minority_writes: int = 0
    dual_primary: int = 0
    abort_halt_writes: bool = False
    error: str | None = None
    error_code: str | None = None
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["minority_writes"] = 0
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        return d


__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "SCHEMA_ATTEMPT",
    "SCHEMA_HALT",
    "WriteOutcome",
    "MinorityError",
    "MinorityWriteDetected",
    "MinorityAbortHaltWrites",
    "MinorityPlaintextForbidden",
    "MinorityN2Only",
    "MinorityNodeUnknown",
    "MinorityWritesHalted",
    "WriteAttempt",
    "MinorityStatus",
    "ProbeResult",
    "HaltResult",
    "WriteResult",
]
