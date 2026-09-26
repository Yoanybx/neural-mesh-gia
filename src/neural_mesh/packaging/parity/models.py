"""Manifest parity models (Cycle 41 / CP-0045 / H8).

Schema: mesh.manifest.parity/v1
Capability: docs/capabilities/MESH_MANIFEST_PARITY.md

Byte-equality under concurrent build @N2; toolchain pin (P-09);
ABORT→reject build on mismatch.
Extends packaging/manifest_n2 — does not reopen 0.16.3 / 0.17.0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SCHEMA_ID = "mesh.manifest.parity/v1"
SCHEMA_STORE = "mesh.manifest.parity.store/v1"
SCHEMA_REPORT = "mesh.manifest.parity.report/v1"
SCHEMA_BUILD = "mesh.manifest.parity.build/v1"
SCHEMA_TOOLCHAIN = "mesh.manifest.parity.toolchain/v1"

# Reuse frozen N2 sibling schema id for source manifests (extend, don't mutate).
SOURCE_MANIFEST_SCHEMA_N2 = "mesh.bundle.manifest/v1-n2"
SOURCE_MANIFEST_SCHEMA = "mesh.bundle.manifest/v1"

PARITY_CHANNEL = "0.18.x"
FROZEN_CHANNELS = frozenset({"0.16.3", "0.16.x", "0.17.0", "0.17.x-n2"})

CheckOutcome = Literal[
    "matched",
    "mismatch",
    "rejected_abort",
    "pending",
    "incomplete",
]


class ParityError(RuntimeError):
    """Base manifest-parity error (fail-closed)."""

    code: str = "PARITY_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class ParityMismatch(ParityError):
    """Byte / checksum mismatch between N2 concurrent builds."""

    code = "PARITY_MISMATCH"


class ParityAbortRejectBuild(ParityError):
    """ABORT→reject build engaged or build already rejected."""

    code = "PARITY_ABORT_REJECT_BUILD"


class ParityPlaintextForbidden(ParityError):
    code = "PARITY_PLAINTEXT_FORBIDDEN"


class ParityN2Only(ParityError):
    """N>2 / Raft / multi-primary architecture refused."""

    code = "PARITY_N2_ONLY"


class ParityToolchainMismatch(ParityError):
    code = "PARITY_TOOLCHAIN_MISMATCH"


class ParityFrozenChannel(ParityError):
    """Refuse reopen of frozen 0.16.3 / 0.17.0 channels."""

    code = "PARITY_FROZEN_CHANNEL"


class ParityIncomplete(ParityError):
    """Both sides of the N2 pair required for a parity check."""

    code = "PARITY_INCOMPLETE"


@dataclass
class ToolchainPin:
    """P-09 toolchain pin: compiler + libc + locale → pin_hash."""

    compiler: str = "cpython"
    libc: str = "host"
    locale: str = "C.UTF-8"
    pin_hash: str = ""
    schema: str = SCHEMA_TOOLCHAIN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_TOOLCHAIN
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ToolchainPin":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        tc = cls(**kwargs)
        tc.schema = SCHEMA_TOOLCHAIN
        return tc


@dataclass
class BuildArtifact:
    """One side of an N=2 concurrent build (canonical bytes + digest)."""

    side: str  # "a" | "b" | node id
    digest_sha256: str
    canonical_bytes_len: int = 0
    checksums: dict[str, str] = field(default_factory=dict)
    bundle_sha256: str | None = None
    ver: str | None = None
    tip: str | None = None
    toolchain_pin_hash: str | None = None
    schema: str = SCHEMA_BUILD
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    ts: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_BUILD
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuildArtifact":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        art = cls(**kwargs)
        art.dual_primary = 0
        art.minority_writes = 0
        art.vault_acme_required = 0
        art.plaintext_fallback = 0
        art.schema = SCHEMA_BUILD
        return art


@dataclass
class ParityStatus:
    """Operator-facing manifest-parity status @N2."""

    ok: bool
    data_root: str
    pair: list[str]
    parity_ok: bool = False
    mismatch_detected: bool = False
    build_rejected: bool = False
    abort_reject_build: bool = False
    abort_reason: str = ""
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    toolchain: dict[str, Any] = field(default_factory=dict)
    last_digest_a: str = ""
    last_digest_b: str = ""
    mismatch_paths: list[str] = field(default_factory=list)
    check_count: int = 0
    reject_count: int = 0
    match_count: int = 0
    issues: list[str] = field(default_factory=list)
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d


@dataclass
class ParityCheckResult:
    """Result of a parity check or ABORT→reject build."""

    ok: bool
    outcome: CheckOutcome
    parity_ok: bool = False
    mismatch_detected: bool = False
    build_rejected: bool = False
    abort_reject_build: bool = False
    digest_a: str = ""
    digest_b: str = ""
    mismatch_paths: list[str] = field(default_factory=list)
    toolchain_pin_hash: str = ""
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    reason: str = ""
    error: str | None = None
    error_code: str | None = None
    action: str = "none"  # none | reject_build | abort_reject_build
    schema: str = SCHEMA_REPORT

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_REPORT
        return d


@dataclass
class ConcurrentBuildResult:
    """Outcome of two concurrent N2 builds compared for byte-equality."""

    ok: bool
    parity_ok: bool
    digest_a: str
    digest_b: str
    byte_equal: bool
    mismatch_paths: list[str] = field(default_factory=list)
    build_rejected: bool = False
    abort_reject_build: bool = False
    toolchain_pin_hash: str = ""
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    error: str | None = None
    error_code: str | None = None
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d


__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "SCHEMA_REPORT",
    "SCHEMA_BUILD",
    "SCHEMA_TOOLCHAIN",
    "SOURCE_MANIFEST_SCHEMA_N2",
    "SOURCE_MANIFEST_SCHEMA",
    "PARITY_CHANNEL",
    "FROZEN_CHANNELS",
    "CheckOutcome",
    "ParityError",
    "ParityMismatch",
    "ParityAbortRejectBuild",
    "ParityPlaintextForbidden",
    "ParityN2Only",
    "ParityToolchainMismatch",
    "ParityFrozenChannel",
    "ParityIncomplete",
    "ToolchainPin",
    "BuildArtifact",
    "ParityStatus",
    "ParityCheckResult",
    "ConcurrentBuildResult",
]
