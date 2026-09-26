"""Minority-write service: detect @N2, ABORT→halt writes, MINORITY_WRITES=0.

Fail-closed. Builds on fence/cram consistency ideas (sole writable primary).
No Raft. No N>2. No multi-primary. No Vault/ACME. No plaintext. No GIA.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_ID,
    HaltResult,
    MinorityAbortHaltWrites,
    MinorityError,
    MinorityN2Only,
    MinorityNodeUnknown,
    MinorityStatus,
    MinorityWriteDetected,
    MinorityWritesHalted,
    ProbeResult,
    WriteAttempt,
    WriteResult,
)
from .store import MinorityStore, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MinorityService:
    """H6 minority-write safety around a local data root (N=2; no Raft)."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.store = MinorityStore(self.data_root)

    # --- bootstrap ---

    def bootstrap_pair(
        self,
        node_a: str,
        node_b: str,
        *,
        primary: str | None = None,
        mode: str = "local",
    ) -> dict[str, Any]:
        """Register exactly two nodes; elect an initial writable primary."""
        require_no_plaintext(mode)
        if not node_a or not node_b:
            raise MinorityError("both node_a and node_b required")
        if str(node_a) == str(node_b):
            raise MinorityN2Only("pair requires two distinct node ids")
        pair = self.store.set_pair([str(node_a), str(node_b)])
        elected = str(primary) if primary else sorted(pair)[0]
        if elected not in pair:
            raise MinorityNodeUnknown(f"primary {elected!r} not in pair {pair}")
        self.store.set_writable_primary(elected)
        return {
            "schema": SCHEMA_ID,
            "pair": pair,
            "writable_primary": elected,
            "minority_writes": 0,
            "dual_primary": 0,
            "writes_halted": False,
        }

    # --- detect / status ---

    def detect_minority_write(self) -> tuple[bool, list[str]]:
        """Return (detected, claimants) from pending minority attempts."""
        st = self.store.state()
        pending = bool(st.get("minority_write_pending"))
        claimants = list(st.get("pending_claimants") or [])
        # also consider recent rejected_minority attempts as diagnostic history
        if not pending:
            attempts = self.store.list_attempts()
            recent = [
                a.node_id
                for a in attempts
                if a.is_minority and a.outcome == "rejected_minority"
            ]
            # pending flag is authoritative for live detection
            return False, recent[-2:] if recent else []
        return True, claimants

    def status(self) -> MinorityStatus:
        st = self.store.state()
        detected, claimants = self.detect_minority_write()
        issues: list[str] = []
        if detected:
            issues.append("minority_write_detected")
        if st.get("writes_halted") or st.get("abort_halt_writes"):
            issues.append("writes_halted")
        pair = list(st.get("pair") or [])
        if len(pair) > 2:
            issues.append("n_gt_2")
        if len(pair) == 2 and not st.get("writable_primary"):
            issues.append("no_primary")
        attempts = self.store.list_attempts()
        # ok when no live pending minority AND (halt is intentional ABORT path, but
        # operator status is not "ok" while halted — fail-closed)
        ok = (not detected) and (not st.get("writes_halted")) and ("n_gt_2" not in issues)
        return MinorityStatus(
            ok=ok,
            data_root=str(self.data_root),
            pair=pair,
            writable_primary=st.get("writable_primary"),
            writes_halted=bool(st.get("writes_halted")),
            abort_halt_writes=bool(st.get("abort_halt_writes")),
            abort_reason=str(st.get("abort_reason") or ""),
            minority_write_detected=detected,
            minority_writes=0,
            attempt_count=len(attempts),
            rejected_minority_count=int(st.get("rejected_minority_count") or 0),
            issues=issues,
        )

    # --- try_write ---

    def try_write(
        self,
        node_id: str,
        key: str,
        *,
        mode: str = "local",
        auto_halt: bool = True,
    ) -> WriteResult:
        """Attempt a write. Non-primary → minority detect + ABORT→halt; never commit.

        MINORITY_WRITES stays 0: rejected attempts are logged but not committed.
        """
        require_no_plaintext(mode)
        pair = self.store.pair
        if node_id not in pair:
            raise MinorityNodeUnknown(f"node {node_id!r} not in pair {pair}")
        if self.store.writes_halted:
            attempt = WriteAttempt(
                node_id=node_id,
                key=key,
                outcome="rejected_halted",
                is_minority=(node_id != self.store.writable_primary),
                ts=_utcnow(),
            )
            self.store.append_attempt(attempt)
            return WriteResult(
                ok=False,
                outcome="rejected_halted",
                node_id=node_id,
                key=key,
                is_minority=attempt.is_minority,
                writes_halted=True,
                minority_writes=0,
                abort_halt_writes=True,
                error="writes halted (ABORT→halt writes)",
                error_code="MINORITY_WRITES_HALTED",
            )

        primary = self.store.writable_primary
        if primary is None:
            raise MinorityError("no writable primary elected")

        if node_id == primary:
            attempt = WriteAttempt(
                node_id=node_id,
                key=key,
                outcome="accepted",
                is_minority=False,
                ts=_utcnow(),
            )
            self.store.append_attempt(attempt)
            return WriteResult(
                ok=True,
                outcome="accepted",
                node_id=node_id,
                key=key,
                is_minority=False,
                writes_halted=False,
                minority_writes=0,
            )

        # Minority side attempted a write — never commit; ABORT→halt
        attempt = WriteAttempt(
            node_id=node_id,
            key=key,
            outcome="rejected_minority",
            is_minority=True,
            ts=_utcnow(),
        )
        self.store.append_attempt(attempt)
        self.store.mark_pending([node_id])
        if auto_halt:
            self.store.halt_writes(
                f"ABORT→halt writes: minority write by {node_id!r} key={key!r}"
            )
            self.store.clear_pending_detection()
        else:
            self.store.enter_abort(
                f"minority write by {node_id!r}; auto_halt=false",
                claimants=[node_id],
            )
        return WriteResult(
            ok=False,
            outcome="rejected_minority",
            node_id=node_id,
            key=key,
            is_minority=True,
            writes_halted=True,
            minority_writes=0,  # hard 0 — never committed
            abort_halt_writes=True,
            error="minority write rejected; ABORT→halt writes",
            error_code="MINORITY_WRITE_DETECTED",
        )

    # --- probe ---

    def probe(
        self,
        *,
        auto_halt: bool = True,
        mode: str = "local",
    ) -> ProbeResult:
        """Probe minority-write @N2. If detected and auto_halt, ABORT→halt writes."""
        require_no_plaintext(mode)
        detected, claimants = self.detect_minority_write()
        primary = self.store.writable_primary
        if not detected:
            return ProbeResult(
                ok=not self.store.writes_halted,
                minority_write_detected=False,
                minority_writes=0,
                writable_primary=primary,
                writes_halted=self.store.writes_halted,
                abort_halt_writes=self.store.abort_halt_writes,
                action="none",
                minority_claimants=claimants,
            )
        if not auto_halt:
            self.store.enter_abort(
                f"minority-write detected (claimants={claimants}); auto_halt=false",
                claimants=claimants,
            )
            return ProbeResult(
                ok=False,
                minority_write_detected=True,
                minority_writes=0,
                writable_primary=primary,
                writes_halted=True,
                abort_halt_writes=True,
                action="abort_halt_writes",
                minority_claimants=claimants,
                error="minority-write unresolved; ABORT pending halt writes",
                error_code="MINORITY_WRITE_DETECTED",
            )
        # ABORT→halt writes
        halt = self.abort_halt_writes(
            reason=f"probe auto-halt claimants={claimants}",
            mode=mode,
        )
        return ProbeResult(
            ok=halt.ok and halt.writes_halted,
            minority_write_detected=False,  # consumed into halt
            minority_writes=0,
            writable_primary=primary,
            writes_halted=halt.writes_halted,
            abort_halt_writes=halt.abort_halt_writes,
            action="abort_halt_writes",
            minority_claimants=claimants,
            error=halt.error,
            error_code=halt.error_code,
        )

    # --- ABORT→halt writes ---

    def abort_halt_writes(
        self,
        *,
        reason: str = "ABORT→halt writes",
        mode: str = "local",
    ) -> HaltResult:
        """ABORT path: never silent minority_writes>0; halt all further writes."""
        require_no_plaintext(mode)
        detected_before, claimants = self.detect_minority_write()
        self.store.halt_writes(
            reason or f"ABORT→halt writes (detected={detected_before}, claimants={claimants})"
        )
        self.store.clear_pending_detection()
        return HaltResult(
            ok=True,
            writes_halted=True,
            abort_halt_writes=True,
            minority_writes=0,
            reason=str(reason or ""),
        )

    def halt(
        self,
        *,
        reason: str = "operator halt",
        mode: str = "local",
    ) -> HaltResult:
        """Explicit operator halt (same ABORT→halt writes surface)."""
        return self.abort_halt_writes(reason=reason, mode=mode)


__all__ = ["MinorityService", "require_no_plaintext"]
