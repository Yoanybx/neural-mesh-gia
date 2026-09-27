"""Tests for Cycle 55 / CP-0059: M2 membership + rejoin design (mock SM).

Markers: m2_membership_rejoin_cycle55
Design-only; no N>2 runtime; no Raft; dual_primary=0.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m2_membership_rejoin import (
    ABORT_CODES,
    ACTIVE_TIERS,
    CYCLE,
    HAPPY_PATH,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_MEMBERSHIP,
    SEAL_CP,
    MemberState,
    MembershipError,
    MembershipSM,
    TrustTierName,
)

pytestmark = [pytest.mark.m2_membership_rejoin_cycle55]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "fabric" / "M2_MEMBERSHIP_REJOIN_DESIGN.md"
POINTER = REPO / "docs" / "design" / "fabric" / "M2_MEMBERSHIP_REJOIN_POINTER.md"
CAP = REPO / "docs" / "capabilities" / "MESH_M2_MEMBERSHIP_REJOIN_DESIGN.md"
SCHEMA = REPO / "docs" / "schema" / "membership" / "v0.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE55.md"
PASTE = REPO / "council" / "PASTE_CYCLE55_M2M.md"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0059"
    assert PRIOR_CP == "CP-0058"
    assert CYCLE == 55
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_MEMBERSHIP == "mesh.membership/v0"
    assert N_CAP == 2


def test_design_doc_states_and_h1():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "DESIGN" in text
    assert "CP-0059" in text
    for s in ("JOINING", "ATTESTING", "ACTIVE", "DRAINING", "LEFT", "REJOIN"):
        assert s in text
    assert "T0" in text and "T3" in text
    assert "ACTIVE" in text and "T2" in text
    assert "NO_HELD" in text
    assert "no Raft" in text.lower() or "no Raft" in text or "Raft" in text
    assert "N>2" in text or "N≤2" in text or "n_members_active ≤ 2" in text
    assert "dual_primary" in text
    assert "Orthogonal to M1" in text or "orthogonal to M1" in text.lower()


def test_pointer_and_schema_and_capability():
    assert POINTER.is_file()
    ptext = POINTER.read_text(encoding="utf-8")
    assert "ATTESTING" in ptext
    assert "M2_MEMBERSHIP_REJOIN_DESIGN.md" in ptext
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.membership/v0" in stext
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0059" in ctext
    assert "NO_HELD" in ctext


def test_happy_path_constants():
    states = [MemberState.JOINING, MemberState.ATTESTING, MemberState.ACTIVE,
              MemberState.DRAINING, MemberState.LEFT, MemberState.REJOIN]
    assert [e.value for e in MemberState] == [s.value for s in states]
    assert HAPPY_PATH[0][0] == MemberState.JOINING
    assert HAPPY_PATH[-1][2] == MemberState.JOINING
    assert TrustTierName.T2 in ACTIVE_TIERS
    assert TrustTierName.T0 not in ACTIVE_TIERS


def test_t_m2a_rejoin_state_machine_happy():
    sm = MembershipSM()
    r = sm.join_intent("n1", fingerprint="fp1")
    assert r.state == MemberState.JOINING
    assert r.dual_primary == 0
    sm.begin_attest("n1")
    sm.attest_ok("n1", tier=TrustTierName.T2)
    assert sm.records["n1"].state == MemberState.ACTIVE
    assert sm.active_count == 1
    sm.drain("n1")
    sm.drain_complete("n1")
    assert sm.records["n1"].state == MemberState.LEFT
    sm.rejoin_intent("n1")
    assert sm.records["n1"].state == MemberState.REJOIN
    assert sm.records["n1"].rejoin is True
    sm.enter_joining_from_rejoin("n1")
    sm.begin_attest("n1")
    sm.attest_ok("n1", tier=TrustTierName.T3)
    assert sm.records["n1"].state == MemberState.ACTIVE
    assert sm.records["n1"].tier == TrustTierName.T3


def test_t_m2a_neg_attest_fail():
    sm = MembershipSM()
    sm.join_intent("n1")
    sm.begin_attest("n1")
    r = sm.attest_fail("n1")
    assert r.abort_code == "MEMBER_ATTEST_FAIL"
    assert r.state == MemberState.ATTESTING
    assert r.tier == TrustTierName.T0


def test_t_m2a_neg_n_gt2_refused():
    sm = MembershipSM()
    sm.join_intent("a")
    sm.begin_attest("a")
    sm.attest_ok("a")
    sm.join_intent("b")
    sm.begin_attest("b")
    sm.attest_ok("b")
    assert sm.active_count == 2
    with pytest.raises(MembershipError) as ei:
        sm.join_intent("c")
    assert ei.value.code == "MEMBER_N_GT2_REFUSED"


def test_t_m2a_neg_plaintext():
    sm = MembershipSM()
    with pytest.raises(MembershipError) as ei:
        sm.join_intent("n1", plaintext_claim=True)
    assert ei.value.code == "MEMBER_PLAINTEXT_FORBIDDEN"


def test_t_m2a_neg_tier_invariant():
    sm = MembershipSM()
    sm.join_intent("n1")
    sm.begin_attest("n1")
    with pytest.raises(MembershipError) as ei:
        sm.attest_ok("n1", tier=TrustTierName.T1)
    assert ei.value.code == "MEMBER_TIER_INVARIANT"


def test_t_m2a_neg_left_active_shortcut():
    sm = MembershipSM()
    sm.join_intent("n1")
    sm.begin_attest("n1")
    sm.attest_ok("n1")
    sm.drain("n1")
    sm.drain_complete("n1")
    with pytest.raises(MembershipError) as ei:
        sm.force_active_shortcut_from_left("n1")
    assert ei.value.code == "MEMBER_INVALID_TRANSITION"


def test_t_m2b_drain_no_loss():
    sm = MembershipSM()
    sm.join_intent("n1")
    sm.begin_attest("n1")
    sm.attest_ok("n1")
    sm.drain("n1")
    sm.records["n1"].pending_writes = 2
    with pytest.raises(MembershipError) as ei:
        sm.drain_complete("n1")
    assert ei.value.code == "MEMBER_DRAIN_ABORT"
    sm.records["n1"].pending_writes = 0
    sm.drain_complete("n1")
    assert sm.records["n1"].state == MemberState.LEFT


def test_t_m2b_neg_revoked_rejoin():
    sm = MembershipSM()
    sm.join_intent("n1")
    sm.begin_attest("n1")
    sm.attest_ok("n1")
    sm.drain("n1")
    sm.drain_complete("n1")
    sm.records["n1"].revoked = True
    with pytest.raises(MembershipError) as ei:
        sm.rejoin_intent("n1")
    assert ei.value.code == "MEMBER_REVOKED"


def test_abort_codes_documented():
    text = DESIGN.read_text(encoding="utf-8")
    for code in ABORT_CODES:
        assert code in text or code in SCHEMA.read_text(encoding="utf-8"), code


def test_no_gia_raft_runtime_claims():
    text = DESIGN.read_text(encoding="utf-8").lower()
    assert "we unlocked raft" not in text
    assert "n>2 is live" not in text
    assert "we are gia" not in text
    assert "agi achieved" not in text
    assert "no membership runtime" in text or "does **not** implement" in DESIGN.read_text(encoding="utf-8")


def test_no_live_secrets_in_docs():
    for path in (DESIGN, SCHEMA, CAP):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name


def test_council_paste_has_senior_proposals():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "SENIOR_PROPOSALS" in ptext
    assert "VERDICT" in ptext
    assert "ASK:" in ptext or "ASK" in ptext
    for i in ("SP1", "SP2", "SP3", "SP4"):
        assert i in ptext


def test_tags_untouched():
    assert subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode == 0


def test_record_dual_primary_zero():
    sm = MembershipSM()
    r = sm.join_intent("n1")
    d = r.to_dict()
    assert d["dual_primary"] == 0
    assert d["n_cap"] == 2
    assert d["schema"] == SCHEMA_MEMBERSHIP
