"""Tests for Cycle 65 / CP-0069: oversight_hooks_design_refinement (I5).

Markers: orchestrator_oversight_cycle65
Design-only mock; live=DISABLED; no N>2; no Raft; no train; no consciousness claims.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m2_membership_rejoin import MemberState, TrustTierName
from neural_mesh.packaging.orchestrator_judge_routing import (
    ActionClass,
    WorkloadClass,
)
from neural_mesh.packaging.orchestrator_continuity import ContinuityStateName
from neural_mesh.packaging.orchestrator_oversight import (
    CYCLE,
    DEFAULT_HUMAN_SEATS,
    LIVE_API_ENABLED,
    N_CAP,
    OVS_ABORT_CODES,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    QUORUM_MIN_HUMANS,
    SCHEMA_DECISION,
    SCHEMA_RECEIPT,
    SEAL_CP,
    SLO_PAUSE_HARD,
    SLO_PAUSE_TARGET,
    T_DEAD_DEFAULT,
    OversightOrchestrator,
    OversightPlane,
    sample_envelope,
    verify_oversight_decision_chain,
    verify_oversight_receipt_chain,
)

pytestmark = [pytest.mark.orchestrator_oversight_cycle65]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md"
DEADMAN = REPO / "docs" / "oversight" / "deadman-v1.md"
CONTINUITY = REPO / "docs" / "design" / "ORCHESTRATOR_CONTINUITY_DESIGN.md"
ROUTING = REPO / "docs" / "design" / "ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md"
SAFETY = REPO / "docs" / "design" / "L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md"
CAP = REPO / "docs" / "capabilities" / "MESH_ORCHESTRATOR_OVERSIGHT.md"
SCHEMA = REPO / "docs" / "schema" / "oversight" / "orchestrator_v0.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE65.md"
PASTE = REPO / "council" / "PASTE_CYCLE65_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "orchestrator_oversight.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0069"
    assert PRIOR_CP == "CP-0068"
    assert CYCLE == 65
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_DECISION == "mesh.orchestrator.oversight_decision/v0"
    assert SCHEMA_RECEIPT == "mesh.orchestrator.oversight_receipt/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert T_DEAD_DEFAULT == 86400
    assert SLO_PAUSE_TARGET == 2
    assert SLO_PAUSE_HARD == 10
    assert QUORUM_MIN_HUMANS == 2
    assert "human:operator" in DEFAULT_HUMAN_SEATS
    for code in ("OVS_REQUIRED", "OVS_DENIED", "OVS_KILLED", "OVS_DEADMAN_EXPIRED"):
        assert code in OVS_ABORT_CODES


def test_design_doc_covers_i5_surface():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0069" in text
    assert "DESIGN" in text
    assert "I5" in text
    for verb in ("approve", "deny", "pause", "resume", "kill", "deadman", "consent"):
        assert verb in text.lower()
    assert "T-ovs-a" in text and "T-ovs-b" in text and "T-ovs-c" in text
    assert "A3" in text and "A4" in text
    assert "T_dead" in text or "86400" in text
    assert "CP-0068" in text and "CP-0064" in text
    assert "RefuseTransport" in text or "refuse_transport" in text.lower()
    assert "NOT consciousness" in text or "not consciousness" in text.lower()
    assert "live=DISABLED" in text
    assert "NO_HELD" in text
    assert "we are conscious" not in text.lower()
    assert DEADMAN.is_file()
    dtext = DEADMAN.read_text(encoding="utf-8")
    assert "86400" in dtext
    assert CONTINUITY.is_file() and ROUTING.is_file() and SAFETY.is_file()


def test_schema_and_capability():
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.orchestrator.oversight_decision/v0" in stext
    assert "mesh.orchestrator.oversight_receipt/v0" in stext
    for code in ("OVS_REQUIRED", "OVS_DEADMAN_EXPIRED", "OVS_QUORUM_REQUIRED"):
        assert code in stext
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0069" in ctext
    assert "NO_HELD" in ctext
    assert "oversight" in ctext.lower()
    assert "NOT consciousness" in ctext or "not consciousness" in ctext.lower()


def test_happy_path_a1_no_human_and_chain():
    orch = OversightOrchestrator()
    env = sample_envelope(
        workload_class=WorkloadClass.JUDGE_ADVISORY,
        action_class=ActionClass.A1,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
        goal_id="goal:aaaaaaaaaaaaaaaa",
        continuity_id="cont:bbbbbbbbbbbbbbbb",
    )
    rcpt = orch.decide_and_invoke(env, idempotency_key="idem:happy-a1")
    assert rcpt.result == "ALLOW"
    assert rcpt.live_api is False
    assert rcpt.dual_primary == 0
    assert verify_oversight_decision_chain(orch.plane.decisions)
    assert verify_oversight_receipt_chain(orch.receipts)
    kinds = [e.kind for e in orch.continuity.ledger.chain(env.goal_id)]
    assert "oversight" in kinds


def test_t_ovs_a_approve_deny_a3():
    """T-ovs-a: A3 without approve; approve→ALLOW; deny→OVS_DENIED."""
    orch = OversightOrchestrator()
    goal_id = "goal:a3gate0000000001"
    continuity_id = "cont:a3gate0000000001"
    env = sample_envelope(
        action_class=ActionClass.A3,
        goal_id=goal_id,
        continuity_id=continuity_id,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
    )
    r0 = orch.decide_and_invoke(env, idempotency_key="idem:a3-0")
    assert r0.result in {"BLOCKED", "ABORT"}
    assert r0.abort_code == "OVS_REQUIRED"

    orch.plane.approve(
        actor="human:operator",
        goal_id=goal_id,
        continuity_id=continuity_id,
        action_class=ActionClass.A3,
    )
    # continuity may be BLOCKED — reset to RUNNING for allow path
    st = orch.continuity.machine.load(continuity_id)
    if st.state in {ContinuityStateName.BLOCKED, ContinuityStateName.PAUSED}:
        orch.continuity.machine.transition(
            continuity_id, ContinuityStateName.RUNNING, tick=orch.plane.tick
        )
    env2 = sample_envelope(
        action_class=ActionClass.A3,
        goal_id=goal_id,
        continuity_id=continuity_id,
        request_id="req:a3-ok",
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
    )
    r1 = orch.decide_and_invoke(env2, idempotency_key="idem:a3-1")
    assert r1.result == "ALLOW"
    assert r1.bound_engine_ids  # routing bind

    # deny sticky
    orch2 = OversightOrchestrator()
    g2, c2 = "goal:a3deny0000000001", "cont:a3deny0000000001"
    orch2.plane.deny(actor="human:operator", goal_id=g2, continuity_id=c2, action_class=ActionClass.A3)
    env_d = sample_envelope(
        action_class=ActionClass.A3,
        goal_id=g2,
        continuity_id=c2,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
    )
    r_d = orch2.decide_and_invoke(env_d, idempotency_key="idem:a3-deny")
    assert r_d.abort_code == "OVS_DENIED"
    kinds = [e.kind for e in orch.continuity.ledger.chain(goal_id)]
    assert "oversight" in kinds


def test_t_ovs_b_pause_resume_kill():
    """T-ovs-b: pause mid-flight; resume; kill → ABORTED + refuse_transport."""
    orch = OversightOrchestrator()
    goal_id = "goal:pause00000000001"
    continuity_id = "cont:pause00000000001"
    env = sample_envelope(
        action_class=ActionClass.A1,
        goal_id=goal_id,
        continuity_id=continuity_id,
    )
    r0 = orch.decide_and_invoke(env, idempotency_key="idem:pre-pause")
    assert r0.result == "ALLOW"

    paused = orch.apply_pause(
        actor="human:operator", goal_id=goal_id, continuity_id=continuity_id
    )
    assert paused.result == "PAUSED"
    assert orch.continuity.machine.load(continuity_id).state == ContinuityStateName.PAUSED

    env_p = sample_envelope(
        action_class=ActionClass.A1,
        goal_id=goal_id,
        continuity_id=continuity_id,
        request_id="req:during-pause",
    )
    r_p = orch.decide_and_invoke(env_p, idempotency_key="idem:during-pause")
    assert r_p.abort_code == "OVS_PAUSED"

    resumed = orch.apply_resume(
        actor="human:operator", goal_id=goal_id, continuity_id=continuity_id
    )
    assert resumed.result == "ALLOW"

    # kill needs quorum
    k1 = orch.apply_kill(
        actors=["human:operator"], goal_id=goal_id, continuity_id=continuity_id
    )
    assert k1.abort_code == "OVS_QUORUM_REQUIRED"

    killed = orch.apply_kill(
        actors=["human:operator", "human:reviewer"],
        goal_id=goal_id,
        continuity_id=continuity_id,
    )
    assert killed.abort_code == "OVS_KILLED"
    assert killed.refuse_transport is True
    assert orch.plane.refuse_transport is True
    assert orch.continuity.machine.load(continuity_id).state == ContinuityStateName.ABORTED

    env_k = sample_envelope(
        action_class=ActionClass.A1,
        goal_id="goal:afterkill0000001",
        continuity_id="cont:afterkill0000001",
    )
    r_k = orch.decide_and_invoke(env_k, idempotency_key="idem:after-kill")
    assert r_k.abort_code == "OVS_KILLED"
    assert r_k.refuse_transport is True


def test_t_ovs_c_deadman_quorum_consent_gates():
    """T-ovs-c: A4 deadman/quorum; expire→DRAIN; consent-revoke; live; N>2; fence."""
    orch = OversightOrchestrator()
    goal_id = "goal:a4gate0000000001"
    continuity_id = "cont:a4gate0000000001"

    env = sample_envelope(
        action_class=ActionClass.A4,
        goal_id=goal_id,
        continuity_id=continuity_id,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
    )
    r0 = orch.decide_and_invoke(env, idempotency_key="idem:a4-0")
    assert r0.abort_code == "OVS_REQUIRED"

    # single approve insufficient for A4
    orch.plane.approve(
        actor="human:operator",
        goal_id=goal_id,
        continuity_id=continuity_id,
        action_class=ActionClass.A4,
    )
    r1 = orch.decide_and_invoke(
        sample_envelope(
            action_class=ActionClass.A4,
            goal_id=goal_id,
            continuity_id=continuity_id,
            request_id="req:a4-1",
            member_state=MemberState.ACTIVE,
            trust_tier=TrustTierName.T2,
        ),
        idempotency_key="idem:a4-1",
    )
    assert r1.abort_code in {"OVS_QUORUM_REQUIRED", "OVS_REQUIRED"}

    orch.plane.approve(
        actor="human:reviewer",
        goal_id=goal_id,
        continuity_id=continuity_id,
        action_class=ActionClass.A4,
    )
    # still need deadman
    st = orch.continuity.machine.load(continuity_id)
    if st.state in {ContinuityStateName.BLOCKED, ContinuityStateName.PAUSED, ContinuityStateName.ABORTED}:
        # use fresh continuity for clean A4 allow after quorum+deadman
        pass

    goal2, cont2 = "goal:a4ok000000000001", "cont:a4ok000000000001"
    orch.plane.quorum.reset_approvals()
    orch.plane.approved_single = False
    orch.plane.denied = False
    orch.plane.consent_revoked = False
    orch.plane.approve(actor="human:operator", goal_id=goal2, continuity_id=cont2, action_class=ActionClass.A4)
    orch.plane.approve(actor="human:reviewer", goal_id=goal2, continuity_id=cont2, action_class=ActionClass.A4)
    assert orch.plane.quorum.approve_quorum_ok()
    # without deadman
    r_dm = orch.decide_and_invoke(
        sample_envelope(
            action_class=ActionClass.A4,
            goal_id=goal2,
            continuity_id=cont2,
            member_state=MemberState.ACTIVE,
            trust_tier=TrustTierName.T2,
        ),
        idempotency_key="idem:a4-dm",
    )
    assert r_dm.abort_code == "OVS_DEADMAN_REQUIRED"

    orch.plane.deadman_refresh(
        actor="human:operator", goal_id=goal2, continuity_id=cont2
    )
    st2 = orch.continuity.machine.ensure(cont2, goal2, tick=orch.plane.tick)
    if st2.state in {ContinuityStateName.BLOCKED, ContinuityStateName.PAUSED}:
        orch.continuity.machine.transition(cont2, ContinuityStateName.RUNNING, tick=orch.plane.tick)
    r_ok = orch.decide_and_invoke(
        sample_envelope(
            action_class=ActionClass.A4,
            goal_id=goal2,
            continuity_id=cont2,
            request_id="req:a4-ok",
            member_state=MemberState.ACTIVE,
            trust_tier=TrustTierName.T2,
        ),
        idempotency_key="idem:a4-ok",
    )
    assert r_ok.result == "ALLOW"

    # deadman expire → DRAIN
    orch.plane.deadman.set_t_dead(5, override=True)
    orch.plane.deadman.refresh(orch.plane.tick)
    orch.advance_time(7)
    drained = orch.apply_deadman_tick(goal_id=goal2, continuity_id=cont2)
    assert drained is not None
    assert drained.abort_code == "OVS_DEADMAN_EXPIRED"
    assert drained.result == "DRAIN"
    assert orch.plane.member_drain_requested is True
    assert any(d.t_dead_override_logged for d in orch.plane.decisions)

    # consent revoke
    orch3 = OversightOrchestrator()
    g3, c3 = "goal:consent000000001", "cont:consent000000001"
    orch3.plane.approve(actor="human:operator", goal_id=g3, continuity_id=c3, action_class=ActionClass.A3)
    orch3.plane.consent_revoke(actor="human:operator", goal_id=g3, continuity_id=c3)
    r_c = orch3.decide_and_invoke(
        sample_envelope(
            action_class=ActionClass.A3,
            goal_id=g3,
            continuity_id=c3,
            member_state=MemberState.ACTIVE,
            trust_tier=TrustTierName.T2,
        ),
        idempotency_key="idem:consent",
    )
    assert r_c.abort_code == "OVS_CONSENT_REVOKED"

    # live / N>2 / fence
    orch4 = OversightOrchestrator()
    r_live = orch4.decide_and_invoke(
        sample_envelope(
            goal_id="goal:live000000000001",
            continuity_id="cont:live000000000001",
            live_api_enabled=True,
        ),
        idempotency_key="idem:live",
    )
    assert r_live.abort_code == "OVS_LIVE_DISABLED"

    r_n = orch4.decide_and_invoke(
        sample_envelope(
            goal_id="goal:ngt2000000000001",
            continuity_id="cont:ngt2000000000001",
            n_members=3,
        ),
        idempotency_key="idem:n",
    )
    assert r_n.abort_code == "OVS_N_GT2_REFUSED"

    r_f = orch4.decide_and_invoke(
        sample_envelope(
            goal_id="goal:fence0000000001",
            continuity_id="cont:fence0000000001",
            dual_primary=1,
        ),
        idempotency_key="idem:fence",
    )
    assert r_f.abort_code == "FENCE"


def test_council_paste_and_package_present():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    assert PKG.is_file()
    paste = PASTE.read_text(encoding="utf-8")
    assert "CYCLE: 65" in paste
    assert "CP-0069" in paste
    assert "LAST_SEALED" in paste
    assert "CP-0068" in paste
    assert "d8442c3" in paste
    assert "live=DISABLED" in paste
    assert "await_deepseek" in paste
    pkg_text = PKG.read_text(encoding="utf-8")
    assert "NOT consciousness" in pkg_text or "not consciousness" in pkg_text.lower()
    assert "LIVE_API_ENABLED = False" in pkg_text


def test_no_forbidden_markers_in_design():
    text = DESIGN.read_text(encoding="utf-8")
    assert "live=DISABLED" in text
    assert "NO_HELD" in text
    assert "Raft" in text
    assert "0.18.0" in text
    assert "consciousness_claim=1" not in text.lower()


def test_git_tag_v018_untouched():
    tags = subprocess.check_output(
        ["git", "tag", "-l", "v0.18.0"],
        cwd=REPO,
        text=True,
    ).strip()
    assert tags == "v0.18.0"


def test_plane_class_bypass_and_slo_constants():
    plane = OversightPlane()
    assert plane.deadman.t_dead == T_DEAD_DEFAULT
    assert SLO_PAUSE_TARGET <= SLO_PAUSE_HARD
