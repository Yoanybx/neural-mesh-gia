"""HLC + monotonic counter helpers (blueprint P-02).

Wall-clock samples are advisory / diagnostic only.
Ordering authority is HLC (logical, counter) and local mono counters.
"""

from __future__ import annotations

import time
from typing import Any

from .models import HLC


def wall_ms_now() -> int:
    """Capture wall milliseconds (diagnostic only; never join/order authority)."""
    return int(time.time() * 1000)


class MonotonicCounter:
    """Strictly increasing local counter (independent of wall clock)."""

    def __init__(self, start: int = 0):
        self._value = int(start)

    @property
    def value(self) -> int:
        return self._value

    def next(self) -> int:
        self._value += 1
        return self._value

    def observe(self, remote: int) -> int:
        """Advance at least past remote (still monotonic locally)."""
        if int(remote) >= self._value:
            self._value = int(remote) + 1
        else:
            self._value += 1
        return self._value

    def to_dict(self) -> dict[str, Any]:
        return {"mono": self._value, "wall_clock_as_authority": 0}


class HLCClock:
    """Node-local HLC state with advisory wall snapshots."""

    def __init__(self, *, logical: int = 0, counter: int = 0, wall_ms: int = 0):
        self._hlc = HLC(logical=logical, counter=counter, wall_ms=wall_ms)

    @property
    def hlc(self) -> HLC:
        return self._hlc

    def now(self, *, wall_ms: int | None = None) -> HLC:
        w = wall_ms if wall_ms is not None else wall_ms_now()
        self._hlc = self._hlc.tick(wall_ms=w)
        return self._hlc

    def receive(self, remote: HLC | dict[str, Any], *, wall_ms: int | None = None) -> HLC:
        other = remote if isinstance(remote, HLC) else HLC.from_dict(remote)
        w = wall_ms if wall_ms is not None else wall_ms_now()
        self._hlc = self._hlc.merge(other, wall_ms=w)
        return self._hlc

    def to_dict(self) -> dict[str, Any]:
        return self._hlc.to_dict()


def compare_hlc(a: HLC | dict[str, Any], b: HLC | dict[str, Any]) -> int:
    """Compare HLC tuples: -1 if a<b, 0 if equal, 1 if a>b.

    Uses (logical, counter) only — wall_ms ignored (non-authoritative).
    """
    aa = a if isinstance(a, HLC) else HLC.from_dict(a)
    bb = b if isinstance(b, HLC) else HLC.from_dict(b)
    if (aa.logical, aa.counter) < (bb.logical, bb.counter):
        return -1
    if (aa.logical, aa.counter) > (bb.logical, bb.counter):
        return 1
    return 0


def skew_ms_diagnostic(wall_a: int, wall_b: int) -> int:
    """Absolute wall delta for skew fence diagnostics (not ordering)."""
    return abs(int(wall_a) - int(wall_b))


__all__ = [
    "wall_ms_now",
    "MonotonicCounter",
    "HLCClock",
    "compare_hlc",
    "skew_ms_diagnostic",
]
