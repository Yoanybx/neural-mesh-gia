"""Dual-primary fence models (Cycle 36 / CP-0040 / H3).

Schema: mesh.fence/v1
Capability: docs/capabilities/MESH_DUAL_PRIMARY_FENCE.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SCHEMA_ID = "mesh.fence/v1"
SCHEMA_STORE = "mesh.fence.store/v1"
SCHEMA_EPOCH = "mesh.fence.epoch/v1"
SCHEMA_ROLE = "mesh.fence.role/v1"

RoleName = Literal["primary", "secondary", "demoted", "none"]


class FenceError(RuntimeError):
    """Base fence error (fail-closed)."""

    code: str = "FENCE_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class FenceDualPrimary(FenceError):
    """Dual-primary condition detected (transient until demote+re-elect)."""

    code = "FENCE_DUAL_PRIMARY"


class FenceAbortDemoteReelect(FenceError):
    """ABORT→demote+re-elect engaged or exhausted."""

    code = "FENCE_ABORT_DEMOTE_REELECT"


class FencePlaintextForbidden(FenceError):
    code = "FENCE_PLAINTEXT_FORBIDDEN"


class FenceN2Only(FenceError):
    """N>2 / Raft / multi-primary architecture refused."""

    code = "FENCE_N2_ONLY"


class FenceUnresolved(FenceError):
    code = "FENCE_UNRESOLVED"


class FenceNodeUnknown(FenceError):
    code = "FENCE_NODE_UNKNOWN"


@dataclass
class NodeRole:
    """Primary-role claim for one node in an N=2 pair."""

    node_id: str
    role: RoleName = "none"
    fence_epoch: int = 0
    durable_token: str = ""
    schema: str = SCHEMA_ROLE
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ROLE
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeRole":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        nr = cls(**kwargs)
        nr.dual_primary = 0
        nr.vault_acme_required = 0
        nr.plaintext_fallback = 0
        nr.schema = SCHEMA_ROLE
        role = str(nr.role or "none")
        if role not in ("primary", "secondary", "demoted", "none"):
            nr.role = "none"  # type: ignore[assignment]
        return nr


@dataclass
class FenceEpoch:
    """Fence epoch + sole writable primary (durable token bound)."""

    epoch: int = 0
    writable_primary: str | None = None
    durable_token: str = ""
    pair: list[str] = field(default_factory=list)
    schema: str = SCHEMA_EPOCH
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_EPOCH
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FenceEpoch":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        fe = cls(**kwargs)
        fe.dual_primary = 0
        fe.vault_acme_required = 0
        fe.plaintext_fallback = 0
        fe.schema = SCHEMA_EPOCH
        if fe.pair is None:
            fe.pair = []
        return fe


@dataclass
class FenceStatus:
    """Operator-facing fence status. dual_primary intent always 0 after report."""

    ok: bool
    data_root: str
    pair: list[str]
    roles: dict[str, str]
    fence_epoch: int
    writable_primary: str | None
    durable_token: str
    dual_primary_detected: bool
    dual_primary: int = 0  # hard intent 0 in reports
    abort_demote_reelect: bool = False
    abort_reason: str = ""
    issues: list[str] = field(default_factory=list)
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
class ProbeResult:
    """Probe of dual-primary condition @N2."""

    ok: bool
    dual_primary_detected: bool
    dual_primary: int = 0  # intent always 0 after successful fence path
    primary_claimants: list[str] = field(default_factory=list)
    fence_epoch: int = 0
    writable_primary: str | None = None
    abort_demote_reelect: bool = False
    action: str = "none"  # none | demote_reelect | abort_demote_reelect
    error: str | None = None
    error_code: str | None = None
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
class DemoteResult:
    ok: bool
    demoted: str
    fence_epoch: int
    writable_primary: str | None
    dual_primary: int = 0
    abort_demote_reelect: bool = False
    error: str | None = None
    error_code: str | None = None
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
class ReelectResult:
    ok: bool
    elected: str
    fence_epoch: int
    durable_token: str
    dual_primary: int = 0
    abort_demote_reelect: bool = False
    error: str | None = None
    error_code: str | None = None
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
class FenceActionResult:
    """Combined ABORT→demote+re-elect outcome."""

    ok: bool
    demoted: list[str]
    elected: str | None
    fence_epoch: int
    durable_token: str = ""
    dual_primary: int = 0
    abort_demote_reelect: bool = False
    dual_primary_detected_before: bool = False
    error: str | None = None
    error_code: str | None = None
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
    "SCHEMA_EPOCH",
    "SCHEMA_ROLE",
    "RoleName",
    "FenceError",
    "FenceDualPrimary",
    "FenceAbortDemoteReelect",
    "FencePlaintextForbidden",
    "FenceN2Only",
    "FenceUnresolved",
    "FenceNodeUnknown",
    "NodeRole",
    "FenceEpoch",
    "FenceStatus",
    "ProbeResult",
    "DemoteResult",
    "ReelectResult",
    "FenceActionResult",
]
