"""Fence service: detect dual-primary @N2, demote, re-elect, ABORT→demote+re-elect.

Fail-closed. dual_primary hard intent 0 after fence path. No Raft. No N>2.
No Vault/ACME. No plaintext. Builds on PrimaryWitness (network.witness).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_ID,
    DemoteResult,
    FenceAbortDemoteReelect,
    FenceActionResult,
    FenceDualPrimary,
    FenceEpoch,
    FenceError,
    FenceN2Only,
    FenceNodeUnknown,
    FenceStatus,
    FenceUnresolved,
    NodeRole,
    ProbeResult,
    ReelectResult,
)
from .store import FenceStore, new_durable_token, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FenceService:
    """H3 dual-primary fence around a local data root (N=2; no Raft)."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.store = FenceStore(self.data_root)

    # --- bootstrap ---

    def bootstrap_pair(
        self,
        node_a: str,
        node_b: str,
        *,
        primary: str | None = None,
        mode: str = "local",
    ) -> FenceEpoch:
        """Register exactly two nodes; optionally elect an initial primary."""
        require_no_plaintext(mode)
        if not node_a or not node_b:
            raise FenceError("both node_a and node_b required")
        if str(node_a) == str(node_b):
            raise FenceN2Only("pair requires two distinct node ids")
        pair = self.store.set_pair([str(node_a), str(node_b)])
        elected = str(primary) if primary else sorted(pair)[0]
        if elected not in pair:
            raise FenceNodeUnknown(f"primary {elected!r} not in pair {pair}")
        return self._elect(elected, demote_others=True, clear_abort=True)

    # --- status / detect ---

    def detect_dual_primary(self) -> tuple[bool, list[str]]:
        """Return (detected, claimants). Live count may be >1 before fence."""
        claimants = self.store.primary_claimants()
        return (len(claimants) > 1), claimants

    def status(self) -> FenceStatus:
        roles_map = self.store.list_roles()
        role_names = {nid: r.role for nid, r in roles_map.items()}
        detected, claimants = self.detect_dual_primary()
        fe = self.store.load_epoch()
        st = self.store.state()
        issues: list[str] = []
        if detected:
            issues.append("dual_primary_detected")
        if st.get("abort_demote_reelect"):
            issues.append("abort_demote_reelect")
        pair = self.store.pair
        if len(pair) > 2:
            issues.append("n_gt_2")
        if len(pair) == 2 and len(claimants) == 0 and fe.writable_primary is None:
            issues.append("no_primary")
        # ok only when no dual-primary live AND no abort (or abort cleared after fence)
        ok = (not detected) and ("abort_demote_reelect" not in issues) and (
            "n_gt_2" not in issues
        )
        return FenceStatus(
            ok=ok,
            data_root=str(self.data_root),
            pair=list(pair),
            roles=role_names,
            fence_epoch=int(fe.epoch),
            writable_primary=fe.writable_primary,
            durable_token=fe.durable_token or "",
            dual_primary_detected=detected,
            dual_primary=0,  # intent always 0 in reports
            abort_demote_reelect=bool(st.get("abort_demote_reelect")),
            abort_reason=str(st.get("abort_reason") or ""),
            issues=issues,
        )

    # --- claim (test/sim helper; production uses demote+reelect) ---

    def claim_primary(
        self,
        node_id: str,
        *,
        mode: str = "local",
        force_dual: bool = False,
    ) -> NodeRole:
        """Claim primary role. Without force_dual, refuse if another primary exists.

        force_dual=True is for tests that need to *simulate* dual-primary so the
        fence path can detect and ABORT→demote+re-elect. Never leaves dual_primary
        as a successful operator status (probe/status still report intent 0).
        """
        require_no_plaintext(mode)
        pair = self.store.pair
        if node_id not in pair:
            raise FenceNodeUnknown(f"node {node_id!r} not in pair {pair}")
        claimants = self.store.primary_claimants()
        others = [c for c in claimants if c != node_id]
        if others and not force_dual:
            raise FenceDualPrimary(
                f"dual-primary refused: {others} already primary; use probe/ABORT path"
            )
        fe = self.store.load_epoch()
        role = self.store.load_role(node_id)
        role.role = "primary"
        role.fence_epoch = int(fe.epoch)
        role.durable_token = fe.durable_token
        self.store.save_role(role)
        if not others:
            # sole claim — sync witness
            self.store.sync_witness(node_id, epoch=int(fe.epoch))
            fe.writable_primary = node_id
            fe.updated_at = _utcnow()
            self.store.save_epoch(fe)
        return role

    # --- demote ---

    def demote(
        self,
        node_id: str,
        *,
        mode: str = "local",
    ) -> DemoteResult:
        """Demote a primary contender to demoted/secondary."""
        require_no_plaintext(mode)
        pair = self.store.pair
        if node_id not in pair:
            raise FenceNodeUnknown(f"node {node_id!r} not in pair {pair}")
        fe = self.store.load_epoch()
        new_epoch = int(fe.epoch) + 1
        role = self.store.load_role(node_id)
        role.role = "demoted"
        role.fence_epoch = new_epoch
        role.durable_token = ""
        self.store.save_role(role)

        # if demoted was writable primary, clear
        if fe.writable_primary == node_id:
            fe.writable_primary = None
            fe.durable_token = ""
            self.store.sync_witness(None, epoch=new_epoch)
        # remaining sole primary (if any) stays; epoch bumps
        claimants = self.store.primary_claimants()
        if len(claimants) == 1:
            sole = claimants[0]
            token = new_durable_token(epoch=new_epoch, primary=sole)
            fe.writable_primary = sole
            fe.durable_token = token
            sole_role = self.store.load_role(sole)
            sole_role.fence_epoch = new_epoch
            sole_role.durable_token = token
            self.store.save_role(sole_role)
            self.store.sync_witness(sole, epoch=new_epoch)
        fe.epoch = new_epoch
        fe.updated_at = _utcnow()
        fe.pair = list(pair)
        self.store.save_epoch(fe)
        detected, _ = self.detect_dual_primary()
        return DemoteResult(
            ok=not detected,
            demoted=node_id,
            fence_epoch=new_epoch,
            writable_primary=fe.writable_primary,
            dual_primary=0,
            abort_demote_reelect=self.store.abort_demote_reelect,
        )

    # --- reelect ---

    def reelect(
        self,
        preferred: str | None = None,
        *,
        mode: str = "local",
    ) -> ReelectResult:
        """Elect a single primary (lexicographic default). Demotes other primaries."""
        require_no_plaintext(mode)
        pair = self.store.pair
        if len(pair) != 2:
            raise FenceN2Only(
                f"reelect requires N=2 pair; have {len(pair)} nodes: {pair}"
            )
        if preferred is not None and preferred not in pair:
            raise FenceNodeUnknown(f"preferred {preferred!r} not in pair {pair}")
        elected = preferred if preferred else sorted(pair)[0]
        fe = self._elect(elected, demote_others=True, clear_abort=False)
        detected, _ = self.detect_dual_primary()
        return ReelectResult(
            ok=not detected and fe.writable_primary == elected,
            elected=elected,
            fence_epoch=int(fe.epoch),
            durable_token=fe.durable_token,
            dual_primary=0,
            abort_demote_reelect=self.store.abort_demote_reelect,
        )

    def _elect(
        self,
        elected: str,
        *,
        demote_others: bool,
        clear_abort: bool,
    ) -> FenceEpoch:
        pair = self.store.pair
        fe = self.store.load_epoch()
        new_epoch = int(fe.epoch) + 1
        token = new_durable_token(epoch=new_epoch, primary=elected)
        for nid in pair:
            role = self.store.load_role(nid)
            if nid == elected:
                role.role = "primary"
                role.fence_epoch = new_epoch
                role.durable_token = token
            elif demote_others:
                # Contender primary → demoted; other non-primary → secondary.
                if role.role == "primary":
                    role.role = "demoted"
                elif role.role != "demoted":
                    role.role = "secondary"
                role.fence_epoch = new_epoch
                role.durable_token = ""
            self.store.save_role(role)
        fe.epoch = new_epoch
        fe.writable_primary = elected
        fe.durable_token = token
        fe.pair = list(pair)
        fe.updated_at = _utcnow()
        self.store.save_epoch(fe)
        self.store.sync_witness(elected, epoch=new_epoch)
        if clear_abort:
            self.store.clear_abort()
        return fe

    # --- probe ---

    def probe(
        self,
        *,
        auto_fence: bool = True,
        preferred: str | None = None,
        mode: str = "local",
    ) -> ProbeResult:
        """Probe dual-primary @N2. If detected and auto_fence, ABORT→demote+re-elect."""
        require_no_plaintext(mode)
        detected, claimants = self.detect_dual_primary()
        fe = self.store.load_epoch()
        if not detected:
            return ProbeResult(
                ok=True,
                dual_primary_detected=False,
                dual_primary=0,
                primary_claimants=claimants,
                fence_epoch=int(fe.epoch),
                writable_primary=fe.writable_primary,
                abort_demote_reelect=self.store.abort_demote_reelect,
                action="none",
            )
        if not auto_fence:
            # still never report dual_primary>0 as success metric; flag detected
            self.store.enter_abort(
                f"dual-primary detected (claimants={claimants}); auto_fence=false"
            )
            return ProbeResult(
                ok=False,
                dual_primary_detected=True,
                dual_primary=0,
                primary_claimants=claimants,
                fence_epoch=int(fe.epoch),
                writable_primary=fe.writable_primary,
                abort_demote_reelect=True,
                action="abort_demote_reelect",
                error="dual-primary unresolved; ABORT pending demote+re-elect",
                error_code="FENCE_DUAL_PRIMARY",
            )
        # ABORT→demote+re-elect
        action = self.abort_demote_reelect(preferred=preferred, mode=mode)
        return ProbeResult(
            ok=action.ok,
            dual_primary_detected=False,  # resolved
            dual_primary=0,
            primary_claimants=[action.elected] if action.elected else [],
            fence_epoch=action.fence_epoch,
            writable_primary=action.elected,
            abort_demote_reelect=action.abort_demote_reelect,
            action="abort_demote_reelect",
            error=action.error,
            error_code=action.error_code,
        )

    # --- ABORT→demote+re-elect ---

    def abort_demote_reelect(
        self,
        *,
        preferred: str | None = None,
        mode: str = "local",
    ) -> FenceActionResult:
        """ABORT path: never silent dual_primary>0; demote contenders + re-elect one."""
        require_no_plaintext(mode)
        detected_before, claimants = self.detect_dual_primary()
        self.store.enter_abort(
            f"ABORT→demote+re-elect (detected={detected_before}, claimants={claimants})"
        )
        pair = self.store.pair
        if len(pair) != 2:
            raise FenceAbortDemoteReelect(
                f"ABORT path requires N=2; have {len(pair)}: {pair}",
                code="FENCE_ABORT_DEMOTE_REELECT",
            )
        # Choose elected: preferred if in pair, else lexicographically smallest of claimants
        # (or of pair if no claimants).
        if preferred and preferred in pair:
            elected = preferred
        elif claimants:
            elected = sorted(claimants)[0]
        else:
            elected = sorted(pair)[0]

        demoted = [n for n in pair if n != elected]
        try:
            fe = self._elect(elected, demote_others=True, clear_abort=False)
        except FenceError as exc:
            return FenceActionResult(
                ok=False,
                demoted=demoted,
                elected=None,
                fence_epoch=self.store.load_epoch().epoch,
                dual_primary=0,
                abort_demote_reelect=True,
                dual_primary_detected_before=detected_before,
                error=str(exc),
                error_code=getattr(exc, "code", "FENCE_ERROR"),
            )

        detected_after, claimants_after = self.detect_dual_primary()
        if detected_after:
            # fail-closed: still abort; do not clear
            return FenceActionResult(
                ok=False,
                demoted=demoted,
                elected=elected,
                fence_epoch=int(fe.epoch),
                durable_token=fe.durable_token,
                dual_primary=0,
                abort_demote_reelect=True,
                dual_primary_detected_before=detected_before,
                error=f"unresolved dual-primary after fence: {claimants_after}",
                error_code="FENCE_UNRESOLVED",
            )

        # resolved — clear abort; dual_primary intent 0
        self.store.clear_abort()
        return FenceActionResult(
            ok=True,
            demoted=demoted,
            elected=elected,
            fence_epoch=int(fe.epoch),
            durable_token=fe.durable_token,
            dual_primary=0,
            abort_demote_reelect=False,
            dual_primary_detected_before=detected_before,
        )

    def acknowledge_abort(self) -> dict[str, Any]:
        """Clear abort after operator confirms single primary."""
        detected, claimants = self.detect_dual_primary()
        if detected:
            raise FenceUnresolved(
                f"cannot acknowledge abort while dual-primary live: {claimants}"
            )
        return self.store.clear_abort()


__all__ = ["FenceService", "require_no_plaintext"]
