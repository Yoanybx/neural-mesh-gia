"""Clock-skew service: detect @N2, ABORT→refuse join, HLC/mono helpers.

Fail-closed. Blueprint P-02: HLC + monotonic counters; wall-clock
non-authoritative (wall_clock_as_authority=0).
No Raft. No N>2. No multi-primary. No Vault/ACME. No plaintext. No GIA.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hlc import (
    HLCClock,
    MonotonicCounter,
    compare_hlc,
    skew_ms_diagnostic,
    wall_ms_now,
)
from .models import (
    DEFAULT_SKEW_THRESHOLD_MS,
    SCHEMA_ID,
    ClockAbortRefuseJoin,
    ClockError,
    ClockN2Only,
    ClockNodeUnknown,
    ClockSample,
    ClockStatus,
    ClockSkewDetected,
    HLC,
    JoinCheckResult,
    ProbeResult,
)
from .store import ClockStore, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ClockService:
    """H7 clock-skew join fence around a local data root (N=2; no Raft)."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.store = ClockStore(self.data_root)
        st = self.store.state()
        h = HLC.from_dict(st.get("local_hlc") or {})
        self._hlc = HLCClock(logical=h.logical, counter=h.counter, wall_ms=h.wall_ms)
        self._mono = MonotonicCounter(int(st.get("local_mono") or 0))

    def _persist_local(self) -> None:
        self.store.set_local_clock(hlc=self._hlc.to_dict(), mono=self._mono.value)

    # --- bootstrap ---

    def bootstrap_pair(
        self,
        node_a: str,
        node_b: str,
        *,
        skew_threshold_ms: int = DEFAULT_SKEW_THRESHOLD_MS,
        mode: str = "local",
    ) -> dict[str, Any]:
        """Register exactly two nodes; set skew join threshold."""
        require_no_plaintext(mode)
        if not node_a or not node_b:
            raise ClockError("both node_a and node_b required")
        if str(node_a) == str(node_b):
            raise ClockN2Only("pair requires two distinct node ids")
        pair = self.store.set_pair([str(node_a), str(node_b)])
        self.store.set_threshold(int(skew_threshold_ms))
        self._hlc.now()
        self._mono.next()
        self._persist_local()
        return {
            "schema": SCHEMA_ID,
            "pair": pair,
            "skew_threshold_ms": int(skew_threshold_ms),
            "wall_clock_as_authority": 0,
            "dual_primary": 0,
            "minority_writes": 0,
            "join_refused": False,
            "local_hlc": self._hlc.to_dict(),
            "local_mono": self._mono.value,
        }

    # --- HLC / mono helpers ---

    def tick(self, *, wall_ms: int | None = None) -> HLC:
        """Advance local HLC (wall advisory)."""
        h = self._hlc.now(wall_ms=wall_ms)
        self._mono.next()
        self._persist_local()
        return h

    def receive_hlc(self, remote: HLC | dict[str, Any], *, wall_ms: int | None = None) -> HLC:
        h = self._hlc.receive(remote, wall_ms=wall_ms)
        self._mono.observe(
            int(remote.counter if isinstance(remote, HLC) else (remote.get("counter") or 0))
        )
        self._persist_local()
        return h

    def mono_next(self) -> int:
        n = self._mono.next()
        self._persist_local()
        return n

    @property
    def local_hlc(self) -> HLC:
        return self._hlc.hlc

    @property
    def local_mono(self) -> int:
        return self._mono.value

    # --- samples / detect ---

    def record_sample(
        self,
        node_id: str,
        *,
        wall_ms: int | None = None,
        hlc: HLC | dict[str, Any] | None = None,
        mono: int | None = None,
        mode: str = "local",
    ) -> ClockSample:
        """Record a peer/local clock sample (wall diagnostic; HLC authoritative)."""
        require_no_plaintext(mode)
        pair = self.store.pair
        if pair and node_id not in pair:
            raise ClockNodeUnknown(f"node {node_id!r} not in pair {pair}")
        w = int(wall_ms) if wall_ms is not None else wall_ms_now()
        if hlc is None:
            h_dict = self.tick(wall_ms=w).to_dict()
        else:
            h_obj = hlc if isinstance(hlc, HLC) else HLC.from_dict(hlc)
            h_dict = self.receive_hlc(h_obj, wall_ms=w).to_dict()
        m = int(mono) if mono is not None else self._mono.value
        sample = ClockSample(
            node_id=node_id,
            wall_ms=w,
            hlc=h_dict,
            mono=m,
            ts=_utcnow(),
        )
        self.store.append_sample(sample)
        self.store.record_wall(node_id, w)
        return sample

    def detect_skew(self) -> tuple[bool, int, list[str]]:
        """Return (detected, skew_ms, nodes).

        Live detection uses ``skew_pending`` (authoritative), same pattern as
        minority pending. Wall deltas remain diagnostic; after ABORT→refuse
        clears pending, detected is False even if last_walls still exceed
        threshold (join_refused captures the abort).
        """
        st = self.store.state()
        threshold = int(st.get("skew_threshold_ms") or DEFAULT_SKEW_THRESHOLD_MS)
        walls = dict(st.get("last_walls") or {})
        pair = list(st.get("pair") or [])
        skew = int(st.get("skew_ms") or 0)
        nodes: list[str] = []
        if len(pair) == 2 and all(n in walls for n in pair):
            skew = skew_ms_diagnostic(walls[pair[0]], walls[pair[1]])
            nodes = list(pair)
        if st.get("skew_pending"):
            return True, skew if skew else int(st.get("skew_ms") or 0), list(
                st.get("pending_nodes") or nodes
            )
        # If not yet refused and walls exceed threshold, treat as live detect
        # so probe/join-check can engage ABORT (first observation path).
        if (
            not st.get("join_refused")
            and not st.get("abort_refuse_join")
            and len(pair) == 2
            and nodes
            and skew > threshold
        ):
            return True, skew, nodes
        return False, skew, nodes if skew > threshold else []

    def status(self) -> ClockStatus:
        st = self.store.state()
        detected, skew, nodes = self.detect_skew()
        issues: list[str] = []
        if detected:
            issues.append("clock_skew_detected")
        if st.get("join_refused") or st.get("abort_refuse_join"):
            issues.append("join_refused")
        pair = list(st.get("pair") or [])
        if len(pair) > 2:
            issues.append("n_gt_2")
        samples = self.store.list_samples()
        ok = (not detected) and (not st.get("join_refused")) and ("n_gt_2" not in issues)
        return ClockStatus(
            ok=ok,
            data_root=str(self.data_root),
            pair=pair,
            skew_ms=skew,
            skew_threshold_ms=int(st.get("skew_threshold_ms") or DEFAULT_SKEW_THRESHOLD_MS),
            skew_detected=detected,
            join_refused=bool(st.get("join_refused")),
            abort_refuse_join=bool(st.get("abort_refuse_join")),
            abort_reason=str(st.get("abort_reason") or ""),
            wall_clock_as_authority=0,
            local_hlc=dict(st.get("local_hlc") or self._hlc.to_dict()),
            local_mono=int(st.get("local_mono") or self._mono.value),
            sample_count=len(samples),
            refused_join_count=int(st.get("refused_join_count") or 0),
            issues=issues,
        )

    # --- probe ---

    def probe(
        self,
        *,
        auto_refuse: bool = True,
        mode: str = "local",
    ) -> ProbeResult:
        """Probe clock-skew @N2. If detected and auto_refuse, ABORT→refuse join."""
        require_no_plaintext(mode)
        detected, skew, nodes = self.detect_skew()
        threshold = self.store.skew_threshold_ms
        if not detected:
            return ProbeResult(
                ok=not self.store.join_refused,
                skew_detected=False,
                skew_ms=skew,
                skew_threshold_ms=threshold,
                wall_clock_as_authority=0,
                join_refused=self.store.join_refused,
                abort_refuse_join=self.store.abort_refuse_join,
                action="none",
                skewed_nodes=nodes,
            )
        if not auto_refuse:
            self.store.enter_abort(
                f"clock-skew detected skew_ms={skew} (nodes={nodes}); auto_refuse=false",
                nodes=nodes,
            )
            return ProbeResult(
                ok=False,
                skew_detected=True,
                skew_ms=skew,
                skew_threshold_ms=threshold,
                wall_clock_as_authority=0,
                join_refused=True,
                abort_refuse_join=True,
                action="abort_refuse_join",
                skewed_nodes=nodes,
                error="clock-skew unresolved; ABORT pending refuse join",
                error_code="CLOCK_SKEW_DETECTED",
            )
        # ABORT→refuse join
        jr = self.abort_refuse_join(
            reason=f"probe auto-refuse skew_ms={skew} nodes={nodes}",
            mode=mode,
        )
        return ProbeResult(
            ok=False,
            skew_detected=False,  # consumed into refuse
            skew_ms=skew,
            skew_threshold_ms=threshold,
            wall_clock_as_authority=0,
            join_refused=jr.join_refused,
            abort_refuse_join=jr.abort_refuse_join,
            action="abort_refuse_join",
            skewed_nodes=nodes,
            error=jr.error,
            error_code=jr.error_code or "CLOCK_ABORT_REFUSE_JOIN",
        )

    # --- join-check ---

    def join_check(
        self,
        node_id: str,
        *,
        peer_wall_ms: int | None = None,
        local_wall_ms: int | None = None,
        peer_hlc: HLC | dict[str, Any] | None = None,
        mode: str = "local",
        auto_refuse: bool = True,
    ) -> JoinCheckResult:
        """Check whether node may join. Excess wall skew → ABORT→refuse join.

        Ordering still uses HLC merge; wall delta is fence-only diagnostic.
        """
        require_no_plaintext(mode)
        pair = self.store.pair
        if pair and node_id not in pair:
            raise ClockNodeUnknown(f"node {node_id!r} not in pair {pair}")
        if self.store.join_refused:
            self.store.bump_refused()
            return JoinCheckResult(
                ok=False,
                outcome="refused_abort",
                node_id=node_id,
                skew_ms=int(self.store.state().get("skew_ms") or 0),
                skew_threshold_ms=self.store.skew_threshold_ms,
                join_refused=True,
                abort_refuse_join=True,
                wall_clock_as_authority=0,
                reason="join already refused (ABORT→refuse join)",
                error="join refused (ABORT→refuse join)",
                error_code="CLOCK_JOIN_REFUSED",
            )

        # Record samples: local + joining peer
        local_id = None
        if pair:
            others = [n for n in pair if n != node_id]
            local_id = others[0] if others else pair[0]
        lw = int(local_wall_ms) if local_wall_ms is not None else wall_ms_now()
        pw = int(peer_wall_ms) if peer_wall_ms is not None else lw
        if local_id:
            self.record_sample(local_id, wall_ms=lw, mode=mode)
        self.record_sample(
            node_id,
            wall_ms=pw,
            hlc=peer_hlc,
            mode=mode,
        )
        # Merge peer HLC for ordering (wall never decides causality alone)
        if peer_hlc is not None:
            self.receive_hlc(peer_hlc, wall_ms=lw)

        skew = skew_ms_diagnostic(lw, pw)
        threshold = self.store.skew_threshold_ms
        self.store.record_wall(node_id, pw)
        if local_id:
            self.store.record_wall(local_id, lw)

        if skew <= threshold:
            self.store.bump_accepted()
            return JoinCheckResult(
                ok=True,
                outcome="accepted",
                node_id=node_id,
                skew_ms=skew,
                skew_threshold_ms=threshold,
                join_refused=False,
                abort_refuse_join=False,
                wall_clock_as_authority=0,
                reason="skew within threshold; HLC/mono authoritative",
            )

        # Excess skew — never join; ABORT→refuse
        nodes = [n for n in [local_id, node_id] if n]
        self.store.mark_pending(nodes, skew_ms=skew)
        self.store.bump_refused()
        if auto_refuse:
            self.store.refuse_join(
                f"ABORT→refuse join: skew_ms={skew} > threshold={threshold} "
                f"node={node_id!r}"
            )
            self.store.clear_pending_detection()
        else:
            self.store.enter_abort(
                f"skew_ms={skew} > threshold={threshold}; auto_refuse=false",
                nodes=nodes,
            )
        return JoinCheckResult(
            ok=False,
            outcome="refused_skew",
            node_id=node_id,
            skew_ms=skew,
            skew_threshold_ms=threshold,
            join_refused=True,
            abort_refuse_join=True,
            wall_clock_as_authority=0,
            reason="clock skew exceeds threshold; ABORT→refuse join",
            error="clock skew; ABORT→refuse join",
            error_code="CLOCK_SKEW_DETECTED",
        )

    # --- ABORT→refuse join ---

    def abort_refuse_join(
        self,
        *,
        reason: str = "ABORT→refuse join",
        mode: str = "local",
    ) -> JoinCheckResult:
        """ABORT path: never silent join under skew; refuse further joins."""
        require_no_plaintext(mode)
        detected_before, skew, nodes = self.detect_skew()
        self.store.refuse_join(
            reason
            or f"ABORT→refuse join (detected={detected_before}, skew_ms={skew}, nodes={nodes})"
        )
        self.store.clear_pending_detection()
        return JoinCheckResult(
            ok=True,
            outcome="refused_abort",
            node_id=",".join(nodes) if nodes else "",
            skew_ms=skew,
            skew_threshold_ms=self.store.skew_threshold_ms,
            join_refused=True,
            abort_refuse_join=True,
            wall_clock_as_authority=0,
            reason=str(reason or ""),
        )


__all__ = [
    "ClockService",
    "require_no_plaintext",
    "compare_hlc",
    "skew_ms_diagnostic",
    "wall_ms_now",
]
