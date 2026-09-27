"""Tests for Cycle 64 / CP-0068: orchestrator_continuity_design.

Markers: orchestrator_continuity_cycle64
Design-only mock; live=DISABLED; no N>2; no Raft; no train; no consciousness claims.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m2_membership_rejoin import MemberState, TrustTierName
from neural_mesh.packaging.m3_wan_model import LatencyBand
from neural_mesh.packaging.orchestrator_judge_routing import (
    ActionClass,
    WorkloadClass,
    sample_envelope,
)
from neural_mesh.packaging.orchestrator_continuity import (
    CONT_ABORT_CODES,
    CYCLE,
    HARD_TIMEOUT_UNITS,
    LIVE_API_ENABLED,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_CONT_RECEIPT,
    SCHEMA_CONTINUITY,
    SCHEMA_EVIDENCE,
    SCHEMA_GOAL,
    SCHEMA_INFLIGHT,
    SEAL_CP,
    SOFT_TIMEOUT_UNITS,
    ContinuityOrchestrator,
    ContinuityStateName,
    InFlightStatus,
    verify_continuity_receipt_chain,
    verify_evidence_chain,
)

pytestmark = [pytest.mark.orchestrator_continuity_cycle64]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "ORCHESTRATOR_CONTINUITY_DESIGN.md"
DURABLE = REPO / "docs" / "design" / "DURABLE_GOALS_CONTINUITY_DESIGN.md"
ROUTING = REPO / "docs" / "design" / "ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md"
CAP = REPO / "docs" / "capabilities" / "MESH_ORCHESTRATOR_CONTINUITY.md"
SCHEMA = REPO / "docs" / "schema" / "continuity" / "orchestrator_v0.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE64.md"
PASTE = REPO / "council" / "PASTE_CYCLE64_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "orchestrator_continuity.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0068"
    assert PRIOR_CP == "CP-0067"
    assert CYCLE == 64
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_INFLIGHT == "mesh.orchestrator.inflight/v0"
    assert SCHEMA_CONT_RECEIPT == "mesh.orchestrator.continuity_receipt/v0"
    assert SCHEMA_GOAL == "mesh.goal/v0"
    assert SCHEMA_EVIDENCE == "mesh.evidence/v0"
    assert SCHEMA_CONTINUITY == "mesh.continuity/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert SOFT_TIMEOUT_UNITS == 30
    assert HARD_TIMEOUT_UNITS == 120
    for code in (
        "CONT_ORPHAN_LEFT",
        "CONT_IDEMPOTENCY_CONFLICT",
        "CONT_TIMEOUT_HARD",
        "CONT_LIVE_DISABLED",
    ):
        assert code in CONT_ABORT_CODES


def test_design_doc_covers_continuity_surface():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0068" in text
    assert "DESIGN" in text
    assert "orchestrator_continuity" in text.lower() or "Orchestrator Continuity" in text
    assert "durable" in text.lower()
    assert "EvidenceLedger" in text or "evidence" in text.lower()
    assert "resume" in text.lower()
    assert "LEFT" in text and "REJOIN" in text
    assert "orphan" in text.lower()
    assert "idempotency" in text.lower()
    assert "timeout" in text.lower()
    assert "ABORT" in text
    assert "T-cont-a" in text and "T-cont-b" in text and "T-cont-c" in text
    assert "substrate memory" in text.lower() or "Substrate memory" in text
    assert "NOT consciousness" in text or "not consciousness" in text.lower()
    assert "live=DISABLED" in text or "LIVE_API_ENABLED" in text
    assert "NO_HELD" in text
    assert "receipt_hash_chain" in text or "CP-0067" in text
    assert "GIA" in text
    assert "we are conscious" not in text.lower()
    assert DURABLE.is_file()
    dtext = DURABLE.read_text(encoding="utf-8")
    assert "ORCHESTRATOR_CONTINUITY_DESIGN.md" in dtext
    assert ROUTING.is_file()


def test_schema_and_capability():
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.orchestrator.inflight/v0" in stext
    assert "mesh.orchestrator.continuity_receipt/v0" in stext
    for code in ("CONT_ORPHAN_LEFT", "CONT_IDEMPOTENCY_CONFLICT", "CONT_TIMEOUT_HARD"):
        assert code in stext
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0068" in ctext
    assert "NO_HELD" in ctext
    assert "continuity" in ctext.lower()
    assert "NOT consciousness" in ctext or "not consciousness" in ctext.lower()


def test_happy_path_allow_and_ledger_chain():
    orch = ContinuityOrchestrator()
    env = sample_envelope(
        workload_class=WorkloadClass.JUDGE_ADVISORY,
        action_class=ActionClass.A1,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
        goal_id="goal:aaaaaaaaaaaaaaaa",
        continuity_id="cont:bbbbbbbbbbbbbbbb",
    )
    rcpt = orch.invoke(env, idempotency_key="idem:happy-1")
    assert rcpt.decision == "ALLOW"
    assert rcpt.continuity_state == ContinuityStateName.RUNNING.value
    assert rcpt.live_api is False
    assert rcpt.dual_primary == 0
    assert orch.invoke_count == 1
    assert orch.ledger.verify(env.goal_id)
    kinds = [e.kind for e in orch.ledger.chain(env.goal_id)]
    assert "invoke_start" in kinds
    assert "routing_receipt" in kinds
    assert "invoke_end" in kinds
    assert verify_continuity_receipt_chain(orch.receipts)


def test_t_cont_a_orphan_left_rejoin():
    """T-cont-a: in-flight across DRAINING→LEFT→REJOIN; no silent ACTIVE; audited orphan."""
    orch = ContinuityOrchestrator()
    goal_id = "goal:orphan000000001"
    continuity_id = "cont:orphan000000001"
    env = sample_envelope(
        member_state=MemberState.ACTIVE,
        goal_id=goal_id,
        continuity_id=continuity_id,
    )
    rec = orch.begin_invoke(env, idempotency_key="idem:orphan-1")
    assert rec.status == InFlightStatus.OPEN

    drained = orch.notify_member_churn(
        goal_id=goal_id,
        continuity_id=continuity_id,
        new_state=MemberState.DRAINING,
    )
    assert drained
    assert drained[0].orphan_code == "CONT_ORPHAN_DRAIN"
    assert drained[0].decision == "BLOCKED"

    # Re-open for LEFT path (prior was ORPHANED)
    env2 = sample_envelope(
        member_state=MemberState.ACTIVE,
        goal_id=goal_id,
        continuity_id=continuity_id,
        request_id="req:0002",
    )
    # Continuity may be BLOCKED — begin_invoke still allowed only if not terminal
    st = orch.machine.load(continuity_id)
    assert st.state == ContinuityStateName.BLOCKED
    # Force back to RUNNING for second mid-flight (design: unblock then re-open)
    orch.machine.transition(continuity_id, ContinuityStateName.RUNNING, tick=orch.tick)
    rec2 = orch.begin_invoke(env2, idempotency_key="idem:orphan-2")
    assert rec2.status == InFlightStatus.OPEN

    left = orch.notify_member_churn(
        goal_id=goal_id,
        continuity_id=continuity_id,
        new_state=MemberState.LEFT,
    )
    assert left
    assert left[0].orphan_code == "CONT_ORPHAN_LEFT"
    assert left[0].decision == "ABORT"
    assert orch.machine.load(continuity_id).state == ContinuityStateName.ABORTED

    # REJOIN pending — cannot silent ACTIVE; resume blocked
    # Terminal ABORTED → resume forbidden
    resume = orch.resume_after_restart(
        continuity_id,
        member_state=MemberState.REJOIN,
        idempotency_key="idem:resume-rejoin",
    )
    assert resume.abort_code == "CONT_RESUME_FORBIDDEN_TERMINAL"

    # Silent drop forbidden
    drops = orch.notify_member_churn(
        goal_id=goal_id,
        continuity_id=continuity_id,
        new_state=MemberState.LEFT,
        allow_silent_drop=True,
    )
    assert drops[0].orphan_code == "CONT_ORPHAN_DROP_FORBIDDEN"

    kinds = [e.kind for e in orch.ledger.chain(goal_id)]
    assert kinds.count("orphan") >= 2
    assert orch.ledger.verify(goal_id)

    # New invoke while LEFT must not ALLOW
    env_left = sample_envelope(
        member_state=MemberState.LEFT,
        goal_id="goal:orphan000000099",
        continuity_id="cont:orphan000000099",
    )
    rcpt_left = orch.invoke(env_left, idempotency_key="idem:left-gate")
    assert rcpt_left.decision == "ABORT"
    assert rcpt_left.orphan_code == "CONT_ORPHAN_LEFT"


def test_t_cont_b_idempotency_no_double_invoke():
    """T-cont-b: same key+payload → replay; different payload → conflict; no double-invoke."""
    orch = ContinuityOrchestrator()
    env = sample_envelope(
        goal_id="goal:idem000000000001",
        continuity_id="cont:idem000000000001",
        prompt_body="same-prompt",
    )
    r1 = orch.invoke(env, idempotency_key="idem:dup-1")
    assert r1.decision == "ALLOW"
    assert orch.invoke_count == 1

    r2 = orch.invoke(env, idempotency_key="idem:dup-1")
    assert r2.invoke_id == r1.invoke_id
    assert orch.invoke_count == 1  # no double-invoke

    env_conflict = sample_envelope(
        goal_id="goal:idem000000000001",
        continuity_id="cont:idem000000000001",
        prompt_body="different-prompt",
        request_id="req:conflict",
    )
    r3 = orch.invoke(env_conflict, idempotency_key="idem:dup-1")
    assert r3.decision == "ABORT"
    assert r3.abort_code == "CONT_IDEMPOTENCY_CONFLICT"
    assert orch.invoke_count == 1


def test_t_cont_c_timeout_resume_gates():
    """T-cont-c: hard timeout; resume terminal; live; dual_primary; N>2; missing key."""
    orch = ContinuityOrchestrator(hard_timeout=10, soft_timeout=5)
    goal_id = "goal:timeout00000001"
    continuity_id = "cont:timeout00000001"
    env = sample_envelope(goal_id=goal_id, continuity_id=continuity_id)
    orch.begin_invoke(env, idempotency_key="idem:to-1")
    orch.advance_time(6)
    soft = orch.check_timeouts(goal_id=goal_id, continuity_id=continuity_id)
    assert soft and soft[0].abort_code == "CONT_TIMEOUT_SOFT"
    assert soft[0].decision == "BLOCKED"

    orch.advance_time(10)
    hard = orch.check_timeouts(goal_id=goal_id, continuity_id=continuity_id)
    assert hard and hard[0].abort_code == "CONT_TIMEOUT_HARD"
    assert orch.machine.load(continuity_id).state == ContinuityStateName.FAILED

    # resume on terminal forbidden
    r_term = orch.resume_after_restart(continuity_id, idempotency_key="idem:resume-term")
    assert r_term.abort_code == "CONT_RESUME_FORBIDDEN_TERMINAL"

    # live=True
    env_live = sample_envelope(
        goal_id="goal:live000000000001",
        continuity_id="cont:live000000000001",
        live_api_enabled=True,
    )
    r_live = orch.invoke(env_live, idempotency_key="idem:live")
    assert r_live.abort_code == "CONT_LIVE_DISABLED"

    # dual_primary
    env_fence = sample_envelope(
        goal_id="goal:fence0000000001",
        continuity_id="cont:fence0000000001",
        dual_primary=1,
    )
    r_fence = orch.invoke(env_fence, idempotency_key="idem:fence")
    assert r_fence.abort_code == "FENCE"

    # N>2
    env_n = sample_envelope(
        goal_id="goal:ngt2000000000001",
        continuity_id="cont:ngt2000000000001",
        n_members=3,
    )
    r_n = orch.invoke(env_n, idempotency_key="idem:n")
    assert r_n.abort_code == "CONT_N_GT2_REFUSED"

    # missing idempotency
    env_m = sample_envelope(
        goal_id="goal:missing000000001",
        continuity_id="cont:missing000000001",
    )
    r_m = orch.invoke(env_m, idempotency_key="")
    assert r_m.abort_code == "CONT_SCHEMA_INVALID"


def test_resume_after_restart_happy():
    orch = ContinuityOrchestrator()
    goal_id = "goal:resume0000000001"
    continuity_id = "cont:resume0000000001"
    env = sample_envelope(goal_id=goal_id, continuity_id=continuity_id)
    r1 = orch.invoke(env, idempotency_key="idem:pre-resume")
    assert r1.decision == "ALLOW"
    # Simulate restart: new orchestrator cannot — same instance rehydrates from registry+ledger
    assert orch.ledger.verify(goal_id)
    r2 = orch.resume_after_restart(continuity_id, idempotency_key="idem:post-resume")
    assert r2.decision == "ALLOW"
    assert r2.continuity_state in {
        ContinuityStateName.RUNNING.value,
        ContinuityStateName.RESUMING.value,
    }
    kinds = [e.kind for e in orch.ledger.chain(goal_id)]
    assert "resume" in kinds


def test_council_paste_and_package_present():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    assert PKG.is_file()
    paste = PASTE.read_text(encoding="utf-8")
    assert "CYCLE: 64" in paste
    assert "CP-0068" in paste
    assert "LAST_SEALED" in paste
    assert "CP-0067" in paste
    assert "live=DISABLED" in paste or "live=DISABLED" in paste.lower()
    assert "await_deepseek" in paste
    # no consciousness product claim
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
