"""M2 membership + rejoin design helpers (CP-0059 / Cycle 55).

Design-only mock state machine: JOINING → ATTESTING → ACTIVE → DRAINING →
LEFT → REJOIN. Composes with H1 tiers T0..T3. No fabric membership runtime,
no N>2, no Raft.
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
    "SCHEMA_MEMBERSHIP",
    "N_CAP",
    "MemberState",
    "TrustTierName",
    "ABORT_CODES",
    "ACTIVE_TIERS",
    "HAPPY_PATH",
    "MembershipRecord",
    "MembershipSM",
    "MembershipError",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 55
SEAL_CP = "CP-0059"
PRIOR_CP = "CP-0058"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
SCHEMA_MEMBERSHIP = "mesh.membership/v0"
N_CAP = 2


class MemberState(str, Enum):
    JOINING = "JOINING"
    ATTESTING = "ATTESTING"
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    LEFT = "LEFT"
    REJOIN = "REJOIN"


class TrustTierName(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


ACTIVE_TIERS = frozenset({TrustTierName.T2, TrustTierName.T3})

ABORT_CODES: tuple[str, ...] = (
    "MEMBER_ATTEST_FAIL",
    "MEMBER_PLAINTEXT_FORBIDDEN",
    "MEMBER_N_GT2_REFUSED",
    "MEMBER_DRAIN_ABORT",
    "MEMBER_REVOKED",
    "MEMBER_INVALID_TRANSITION",
    "MEMBER_TIER_INVARIANT",
)

# Canonical happy-path edge list (REJOIN is entry mode into JOINING).
HAPPY_PATH: tuple[tuple[MemberState, str, MemberState], ...] = (
    (MemberState.JOINING, "begin_attest", MemberState.ATTESTING),
    (MemberState.ATTESTING, "attest_ok", MemberState.ACTIVE),
    (MemberState.ACTIVE, "drain", MemberState.DRAINING),
    (MemberState.DRAINING, "drain_complete", MemberState.LEFT),
    (MemberState.LEFT, "rejoin_intent", MemberState.REJOIN),
    (MemberState.REJOIN, "enter_joining", MemberState.JOINING),
)


class MembershipError(RuntimeError):
    """Fail-closed membership design error."""

    code: str = "MEMBER_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


@dataclass
class MembershipRecord:
    node_id: str
    state: MemberState = MemberState.JOINING
    tier: TrustTierName = TrustTierName.T0
    rejoin: bool = False
    fingerprint: str = ""
    prior_fingerprints: list[str] = field(default_factory=list)
    dual_primary: int = 0
    n_cap: int = N_CAP
    pending_writes: int = 0
    revoked: bool = False
    abort_code: str | None = None
    plaintext_claim: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_MEMBERSHIP,
            "node_id": self.node_id,
            "state": self.state.value,
            "tier": self.tier.value,
            "rejoin": self.rejoin,
            "fingerprint": self.fingerprint,
            "prior_fingerprints": list(self.prior_fingerprints),
            "dual_primary": self.dual_primary,
            "n_cap": self.n_cap,
            "pending_writes": self.pending_writes,
            "abort_code": self.abort_code,
        }


@dataclass
class MembershipSM:
    """In-memory mock SM for design tests. Not a fabric service."""

    active_count: int = 0
    records: dict[str, MembershipRecord] = field(default_factory=dict)

    def join_intent(
        self,
        node_id: str,
        *,
        fingerprint: str = "fp-new",
        rejoin: bool = False,
        plaintext_claim: bool = False,
    ) -> MembershipRecord:
        if plaintext_claim:
            raise MembershipError(
                "plaintext trust claim forbidden",
                code="MEMBER_PLAINTEXT_FORBIDDEN",
            )
        # Refuse if activating would push beyond N_CAP once ACTIVE;
        # also refuse excess JOINING when already at cap ACTIVE.
        if self.active_count >= N_CAP and not rejoin:
            raise MembershipError(
                f"N>{N_CAP} refused (NO_HELD)",
                code="MEMBER_N_GT2_REFUSED",
            )
        rec = MembershipRecord(
            node_id=node_id,
            state=MemberState.JOINING,
            tier=TrustTierName.T1 if fingerprint else TrustTierName.T0,
            rejoin=rejoin,
            fingerprint=fingerprint,
            dual_primary=0,
            n_cap=N_CAP,
        )
        self.records[node_id] = rec
        return rec

    def begin_attest(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.JOINING)
        rec.state = MemberState.ATTESTING
        return rec

    def attest_ok(
        self, node_id: str, *, tier: TrustTierName = TrustTierName.T2
    ) -> MembershipRecord:
        rec = self._req(node_id, MemberState.ATTESTING)
        if tier not in ACTIVE_TIERS:
            rec.abort_code = "MEMBER_TIER_INVARIANT"
            raise MembershipError(
                "ACTIVE requires T2|T3",
                code="MEMBER_TIER_INVARIANT",
            )
        if self.active_count >= N_CAP:
            raise MembershipError(
                f"N>{N_CAP} refused (NO_HELD)",
                code="MEMBER_N_GT2_REFUSED",
            )
        rec.tier = tier
        rec.state = MemberState.ACTIVE
        rec.abort_code = None
        self.active_count += 1
        return rec

    def attest_fail(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.ATTESTING)
        rec.abort_code = "MEMBER_ATTEST_FAIL"
        # Remain ATTESTING / non-ACTIVE; caller may drop to JOINING.
        rec.tier = TrustTierName.T0
        return rec

    def drain(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.ACTIVE)
        rec.state = MemberState.DRAINING
        return rec

    def drain_complete(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.DRAINING)
        if rec.pending_writes > 0:
            rec.abort_code = "MEMBER_DRAIN_ABORT"
            raise MembershipError(
                "drain refused while pending_writes>0",
                code="MEMBER_DRAIN_ABORT",
            )
        rec.state = MemberState.LEFT
        if self.active_count > 0:
            self.active_count -= 1
        return rec

    def rejoin_intent(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.LEFT)
        if rec.revoked:
            raise MembershipError(
                "rejoin while revoked",
                code="MEMBER_REVOKED",
            )
        # No shortcut to ACTIVE.
        prior = rec.fingerprint
        if prior and prior not in rec.prior_fingerprints:
            rec.prior_fingerprints.append(prior)
        rec.state = MemberState.REJOIN
        rec.rejoin = True
        rec.tier = TrustTierName.T1
        return rec

    def enter_joining_from_rejoin(self, node_id: str) -> MembershipRecord:
        rec = self._req(node_id, MemberState.REJOIN)
        rec.state = MemberState.JOINING
        return rec

    def force_active_shortcut_from_left(self, node_id: str) -> None:
        """Negative helper: LEFT→ACTIVE must fail."""
        rec = self.records.get(node_id)
        if rec is None:
            raise MembershipError("unknown node", code="MEMBER_INVALID_TRANSITION")
        if rec.state == MemberState.LEFT:
            raise MembershipError(
                "LEFT→ACTIVE shortcut forbidden; use REJOIN",
                code="MEMBER_INVALID_TRANSITION",
            )

    def _req(self, node_id: str, expected: MemberState) -> MembershipRecord:
        rec = self.records.get(node_id)
        if rec is None:
            raise MembershipError("unknown node", code="MEMBER_INVALID_TRANSITION")
        if rec.dual_primary != 0:
            raise MembershipError(
                "dual_primary must be 0",
                code="MEMBER_INVALID_TRANSITION",
            )
        if rec.state != expected:
            raise MembershipError(
                f"expected {expected.value}, got {rec.state.value}",
                code="MEMBER_INVALID_TRANSITION",
            )
        return rec
