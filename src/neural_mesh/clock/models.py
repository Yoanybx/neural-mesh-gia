"""Clock-skew fence models (Cycle 40 / CP-0044 / H7).

Schema: mesh.clock/v1
Capability: docs/capabilities/MESH_CLOCK_SKEW_FENCE.md

P-02: HLC + monotonic counters for ordering; wall-clock non-authoritative.
Invariant: wall_clock_as_authority hard 0.
ABORT→refuse join on clock_skew @N2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SCHEMA_ID = "mesh.clock/v1"
SCHEMA_STORE = "mesh.clock.store/v1"
SCHEMA_SAMPLE = "mesh.clock.sample/v1"
SCHEMA_JOIN = "mesh.clock.join/v1"
SCHEMA_HLC = "mesh.clock.hlc/v1"

# Default join-fence threshold (ms). Diagnostic wall delta only — never authority.
DEFAULT_SKEW_THRESHOLD_MS = 5000

JoinOutcome = Literal["accepted", "refused_skew", "refused_abort", "refused_unknown"]


class ClockError(RuntimeError):
    """Base clock-skew error (fail-closed)."""

    code: str = "CLOCK_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class ClockSkewDetected(ClockError):
    """Peer wall delta exceeds join threshold @N2."""

    code = "CLOCK_SKEW_DETECTED"


class ClockAbortRefuseJoin(ClockError):
    """ABORT→refuse join engaged or join already refused."""

    code = "CLOCK_ABORT_REFUSE_JOIN"


class ClockPlaintextForbidden(ClockError):
    code = "CLOCK_PLAINTEXT_FORBIDDEN"


class ClockN2Only(ClockError):
    """N>2 / Raft / multi-primary architecture refused."""

    code = "CLOCK_N2_ONLY"


class ClockNodeUnknown(ClockError):
    code = "CLOCK_NODE_UNKNOWN"


class ClockJoinRefused(ClockError):
    """Join refused while abort/skew fence engaged."""

    code = "CLOCK_JOIN_REFUSED"


@dataclass(order=True, frozen=True)
class HLC:
    """Hybrid Logical Clock tuple (P-02).

    Ordering authority is (logical, counter). ``wall_ms`` is advisory /
    diagnostic only and MUST NOT decide causal order or join alone.
    """

    logical: int = 0
    counter: int = 0
    wall_ms: int = 0  # advisory snapshot; non-authoritative
    schema: str = SCHEMA_HLC

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_HLC,
            "logical": int(self.logical),
            "counter": int(self.counter),
            "wall_ms": int(self.wall_ms),
            "wall_clock_as_authority": 0,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HLC":
        return cls(
            logical=int(data.get("logical") or 0),
            counter=int(data.get("counter") or 0),
            wall_ms=int(data.get("wall_ms") or 0),
        )

    def tick(self, *, wall_ms: int | None = None) -> "HLC":
        """Local event: advance logical/counter; wall is advisory only."""
        w = int(wall_ms) if wall_ms is not None else self.wall_ms
        if w > self.logical:
            return HLC(logical=w, counter=0, wall_ms=w)
        return HLC(logical=self.logical, counter=self.counter + 1, wall_ms=w)

    def merge(self, other: "HLC", *, wall_ms: int | None = None) -> "HLC":
        """Receive/merge remote HLC; wall never wins over logical max."""
        w = int(wall_ms) if wall_ms is not None else max(self.wall_ms, other.wall_ms)
        max_logical = max(self.logical, other.logical, w)
        if max_logical == self.logical == other.logical:
            return HLC(
                logical=max_logical,
                counter=max(self.counter, other.counter) + 1,
                wall_ms=w,
            )
        if max_logical == self.logical and max_logical > other.logical:
            return HLC(logical=max_logical, counter=self.counter + 1, wall_ms=w)
        if max_logical == other.logical and max_logical > self.logical:
            return HLC(logical=max_logical, counter=other.counter + 1, wall_ms=w)
        # wall pushed logical forward (advisory sync of physical sample)
        return HLC(logical=max_logical, counter=0, wall_ms=w)


@dataclass
class ClockSample:
    """Peer clock sample (diagnostic wall + authoritative HLC/mono)."""

    node_id: str
    wall_ms: int
    hlc: dict[str, Any]
    mono: int = 0
    schema: str = SCHEMA_SAMPLE
    wall_clock_as_authority: int = 0
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    ts: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wall_clock_as_authority"] = 0
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_SAMPLE
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClockSample":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        sample = cls(**kwargs)
        sample.wall_clock_as_authority = 0
        sample.dual_primary = 0
        sample.minority_writes = 0
        sample.vault_acme_required = 0
        sample.plaintext_fallback = 0
        sample.schema = SCHEMA_SAMPLE
        return sample


@dataclass
class ClockStatus:
    """Operator-facing clock-skew status. wall_clock_as_authority always 0."""

    ok: bool
    data_root: str
    pair: list[str]
    skew_ms: int = 0
    skew_threshold_ms: int = DEFAULT_SKEW_THRESHOLD_MS
    skew_detected: bool = False
    join_refused: bool = False
    abort_refuse_join: bool = False
    abort_reason: str = ""
    wall_clock_as_authority: int = 0
    dual_primary: int = 0
    minority_writes: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    local_hlc: dict[str, Any] = field(default_factory=dict)
    local_mono: int = 0
    sample_count: int = 0
    refused_join_count: int = 0
    issues: list[str] = field(default_factory=list)
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wall_clock_as_authority"] = 0
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d


@dataclass
class ProbeResult:
    """Probe of clock-skew condition @N2."""

    ok: bool
    skew_detected: bool
    skew_ms: int = 0
    skew_threshold_ms: int = DEFAULT_SKEW_THRESHOLD_MS
    wall_clock_as_authority: int = 0
    dual_primary: int = 0
    minority_writes: int = 0
    join_refused: bool = False
    abort_refuse_join: bool = False
    action: str = "none"  # none | refuse_join | abort_refuse_join
    skewed_nodes: list[str] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wall_clock_as_authority"] = 0
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        return d


@dataclass
class JoinCheckResult:
    """ABORT→refuse join outcome (or accept within threshold)."""

    ok: bool
    outcome: JoinOutcome
    node_id: str
    skew_ms: int = 0
    skew_threshold_ms: int = DEFAULT_SKEW_THRESHOLD_MS
    join_refused: bool = False
    abort_refuse_join: bool = False
    wall_clock_as_authority: int = 0
    dual_primary: int = 0
    minority_writes: int = 0
    reason: str = ""
    error: str | None = None
    error_code: str | None = None
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_JOIN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wall_clock_as_authority"] = 0
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_JOIN
        return d


__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "SCHEMA_SAMPLE",
    "SCHEMA_JOIN",
    "SCHEMA_HLC",
    "DEFAULT_SKEW_THRESHOLD_MS",
    "JoinOutcome",
    "ClockError",
    "ClockSkewDetected",
    "ClockAbortRefuseJoin",
    "ClockPlaintextForbidden",
    "ClockN2Only",
    "ClockNodeUnknown",
    "ClockJoinRefused",
    "HLC",
    "ClockSample",
    "ClockStatus",
    "ProbeResult",
    "JoinCheckResult",
]
