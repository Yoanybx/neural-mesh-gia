"""M3 WAN latency / partition + HLC design helpers (CP-0060 / Cycle 56).

Design-only mock: latency bands, jitter/loss envelopes, P_partition labels,
partition classes (SPLIT/HEAL/FLIP_FLOP/CASCADE), HLC ordering invariants.
No WAN runtime, no N>2, no Raft. wall_clock_as_authority hard 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "SCHEMA_WAN",
    "SCHEMA_HLC",
    "N_CAP",
    "LatencyBand",
    "PartitionClass",
    "PPartitionLabel",
    "ABORT_CODES",
    "BAND_RANGES",
    "JITTER_ENVELOPE_MS",
    "LOSS_ENVELOPE_PCT",
    "WanError",
    "HlcStamp",
    "WanModelRecord",
    "WanModel",
    "classify_rtt",
    "classify_p_partition",
    "compare_hlc_tuple",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 56
SEAL_CP = "CP-0060"
PRIOR_CP = "CP-0059"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
SCHEMA_WAN = "mesh.wan.model/v0"
SCHEMA_HLC = "mesh.clock.hlc/v1"
N_CAP = 2


class LatencyBand(str, Enum):
    RTT_lo = "RTT_lo"
    RTT_mid = "RTT_mid"
    RTT_hi = "RTT_hi"
    RTT_x = "RTT_x"


class PartitionClass(str, Enum):
    STABLE = "STABLE"
    SPLIT = "SPLIT"
    HEAL = "HEAL"
    FLIP_FLOP = "FLIP_FLOP"
    CASCADE = "CASCADE"


class PPartitionLabel(str, Enum):
    P_rare = "P_rare"
    P_occasional = "P_occasional"
    P_elevated = "P_elevated"
    P_hostile = "P_hostile"


# Half-open ranges [lo, hi); RTT_x is [1000, +inf).
BAND_RANGES: dict[LatencyBand, tuple[float, float | None]] = {
    LatencyBand.RTT_lo: (0.0, 50.0),
    LatencyBand.RTT_mid: (50.0, 200.0),
    LatencyBand.RTT_hi: (200.0, 1000.0),
    LatencyBand.RTT_x: (1000.0, None),
}

JITTER_ENVELOPE_MS: dict[LatencyBand, float] = {
    LatencyBand.RTT_lo: 5.0,
    LatencyBand.RTT_mid: 20.0,
    LatencyBand.RTT_hi: 50.0,
    LatencyBand.RTT_x: 100.0,
}

LOSS_ENVELOPE_PCT: dict[LatencyBand, float] = {
    LatencyBand.RTT_lo: 0.1,
    LatencyBand.RTT_mid: 1.0,
    LatencyBand.RTT_hi: 3.0,
    LatencyBand.RTT_x: 10.0,
}

ABORT_CODES: tuple[str, ...] = (
    "WAN_BAND_EXTREME_DEFAULT",
    "WAN_LOSS_ENVELOPE_EXCEEDED",
    "WAN_JITTER_ENVELOPE_EXCEEDED",
    "WAN_WALL_CLOCK_AS_AUTHORITY",
    "WAN_N_GT2_REFUSED",
    "WAN_P_PARTITION_INVALID",
    "WAN_CLASS_UNKNOWN",
    "WAN_HLC_ORDER_VIOLATION",
)


class WanError(RuntimeError):
    """Fail-closed WAN model design error."""

    code: str = "WAN_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


@dataclass
class HlcStamp:
    logical: int = 0
    counter: int = 0
    wall_ms: int = 0  # advisory only

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_HLC,
            "logical": self.logical,
            "counter": self.counter,
            "wall_ms": self.wall_ms,
            "wall_clock_as_authority": 0,
        }


def classify_rtt(rtt_ms: float) -> LatencyBand:
    r = float(rtt_ms)
    if r < 0:
        r = 0.0
    if r < 50:
        return LatencyBand.RTT_lo
    if r < 200:
        return LatencyBand.RTT_mid
    if r < 1000:
        return LatencyBand.RTT_hi
    return LatencyBand.RTT_x


def classify_p_partition(p: float) -> PPartitionLabel:
    if not (0.0 <= float(p) <= 1.0):
        raise WanError(
            "P_partition must be in [0,1]",
            code="WAN_P_PARTITION_INVALID",
        )
    x = float(p)
    if x < 0.01:
        return PPartitionLabel.P_rare
    if x < 0.05:
        return PPartitionLabel.P_occasional
    if x < 0.20:
        return PPartitionLabel.P_elevated
    return PPartitionLabel.P_hostile


def compare_hlc_tuple(a: HlcStamp, b: HlcStamp) -> int:
    """Compare (logical, counter) only — wall_ms ignored."""
    if (a.logical, a.counter) < (b.logical, b.counter):
        return -1
    if (a.logical, a.counter) > (b.logical, b.counter):
        return 1
    return 0


@dataclass
class WanModelRecord:
    rtt_ms: float = 0.0
    band: LatencyBand = LatencyBand.RTT_lo
    jitter_ms: float = 0.0
    loss_pct: float = 0.0
    p_partition: float = 0.0
    p_label: PPartitionLabel = PPartitionLabel.P_rare
    partition_class: PartitionClass = PartitionClass.STABLE
    hlc: HlcStamp = field(default_factory=HlcStamp)
    dual_primary: int = 0
    n_cap: int = N_CAP
    wall_clock_as_authority: int = 0
    abort_code: str | None = None
    flap_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_WAN,
            "rtt_ms": self.rtt_ms,
            "band": self.band.value,
            "jitter_ms": self.jitter_ms,
            "loss_pct": self.loss_pct,
            "p_partition": self.p_partition,
            "p_label": self.p_label.value,
            "partition_class": self.partition_class.value,
            "hlc": self.hlc.to_dict(),
            "dual_primary": self.dual_primary,
            "n_cap": self.n_cap,
            "wall_clock_as_authority": 0,
            "abort_code": self.abort_code,
            "flap_count": self.flap_count,
        }


@dataclass
class WanModel:
    """In-memory mock WAN model for design tests. Not a transport service."""

    record: WanModelRecord = field(default_factory=WanModelRecord)
    n_members: int = 2
    allow_extreme_default: bool = False

    def set_rtt(self, rtt_ms: float, *, as_prod_default: bool = False) -> WanModelRecord:
        band = classify_rtt(rtt_ms)
        if band == LatencyBand.RTT_x and as_prod_default and not self.allow_extreme_default:
            self.record.abort_code = "WAN_BAND_EXTREME_DEFAULT"
            raise WanError(
                "RTT_x cannot be production default",
                code="WAN_BAND_EXTREME_DEFAULT",
            )
        self.record.rtt_ms = float(rtt_ms)
        self.record.band = band
        return self.record

    def set_envelopes(self, *, jitter_ms: float, loss_pct: float) -> WanModelRecord:
        band = self.record.band
        if float(jitter_ms) > JITTER_ENVELOPE_MS[band]:
            self.record.abort_code = "WAN_JITTER_ENVELOPE_EXCEEDED"
            raise WanError(
                "jitter above band envelope",
                code="WAN_JITTER_ENVELOPE_EXCEEDED",
            )
        if float(loss_pct) > LOSS_ENVELOPE_PCT[band]:
            self.record.abort_code = "WAN_LOSS_ENVELOPE_EXCEEDED"
            raise WanError(
                "loss above band envelope",
                code="WAN_LOSS_ENVELOPE_EXCEEDED",
            )
        self.record.jitter_ms = float(jitter_ms)
        self.record.loss_pct = float(loss_pct)
        return self.record

    def set_p_partition(self, p: float) -> WanModelRecord:
        label = classify_p_partition(p)
        self.record.p_partition = float(p)
        self.record.p_label = label
        return self.record

    def require_n_cap(self) -> None:
        if self.n_members > N_CAP:
            raise WanError(
                f"N>{N_CAP} refused (NO_HELD)",
                code="WAN_N_GT2_REFUSED",
            )

    def stamp_hlc(self, logical: int, counter: int, *, wall_ms: int = 0) -> HlcStamp:
        self.record.hlc = HlcStamp(logical=logical, counter=counter, wall_ms=wall_ms)
        self.record.wall_clock_as_authority = 0
        return self.record.hlc

    def claim_wall_as_authority(self) -> None:
        """Negative helper: wall must never be ordering authority."""
        self.record.abort_code = "WAN_WALL_CLOCK_AS_AUTHORITY"
        raise WanError(
            "wall_clock_as_authority forbidden",
            code="WAN_WALL_CLOCK_AS_AUTHORITY",
        )

    def order_by_wall(self, _a_wall: int, _b_wall: int) -> None:
        """Negative helper: happened-before from wall is forbidden."""
        self.record.abort_code = "WAN_HLC_ORDER_VIOLATION"
        raise WanError(
            "event order must use HLC, not wall",
            code="WAN_HLC_ORDER_VIOLATION",
        )

    def path_loss(self) -> WanModelRecord:
        self.require_n_cap()
        prev = self.record.partition_class
        if prev in (PartitionClass.SPLIT, PartitionClass.HEAL, PartitionClass.FLIP_FLOP):
            self.record.flap_count += 1
            if self.record.flap_count >= 2:
                self.record.partition_class = PartitionClass.FLIP_FLOP
            else:
                self.record.partition_class = PartitionClass.SPLIT
        else:
            self.record.partition_class = PartitionClass.SPLIT
        self.record.dual_primary = 0
        return self.record

    def path_ok(self) -> WanModelRecord:
        self.require_n_cap()
        cls = self.record.partition_class
        if cls == PartitionClass.FLIP_FLOP:
            # Settle toward heal without promoting dual_primary.
            self.record.partition_class = PartitionClass.HEAL
            self.record.flap_count = 0
        elif cls in (PartitionClass.SPLIT, PartitionClass.CASCADE):
            self.record.partition_class = PartitionClass.HEAL
        elif cls == PartitionClass.HEAL:
            self.record.partition_class = PartitionClass.STABLE
        self.record.dual_primary = 0
        return self.record

    def cascade_fault(self) -> WanModelRecord:
        self.require_n_cap()
        if self.record.partition_class not in (
            PartitionClass.SPLIT,
            PartitionClass.FLIP_FLOP,
            PartitionClass.CASCADE,
        ):
            self.record.partition_class = PartitionClass.SPLIT
        self.record.partition_class = PartitionClass.CASCADE
        self.record.dual_primary = 0
        return self.record

    def invent_witness_n3(self) -> None:
        """Negative: cascade must not invent N>2 witness."""
        raise WanError(
            "cascade must not invent N>2 witness",
            code="WAN_N_GT2_REFUSED",
        )

    def set_class(self, name: str) -> WanModelRecord:
        try:
            self.record.partition_class = PartitionClass(name)
        except ValueError as e:
            raise WanError(
                f"unknown partition class: {name}",
                code="WAN_CLASS_UNKNOWN",
            ) from e
        return self.record
