"""Tests for Cycle 56 / CP-0060: M3 WAN model design (mock).

Markers: m3_wan_model_cycle56
Design-only; no N>2 runtime; no Raft; dual_primary=0; wall_clock_as_authority=0.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m3_wan_model import (
    ABORT_CODES,
    CYCLE,
    JITTER_ENVELOPE_MS,
    LOSS_ENVELOPE_PCT,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_HLC,
    SCHEMA_WAN,
    SEAL_CP,
    HlcStamp,
    LatencyBand,
    PartitionClass,
    PPartitionLabel,
    WanError,
    WanModel,
    classify_p_partition,
    classify_rtt,
    compare_hlc_tuple,
)

pytestmark = [pytest.mark.m3_wan_model_cycle56]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "fabric" / "M3_WAN_MODEL_DESIGN.md"
POINTER = REPO / "docs" / "design" / "fabric" / "M3_WAN_PARTITION_HLC_POINTER.md"
CAP = REPO / "docs" / "capabilities" / "MESH_M3_WAN_MODEL_DESIGN.md"
SCHEMA = REPO / "docs" / "schema" / "wan" / "v0.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE56.md"
PASTE = REPO / "council" / "PASTE_CYCLE56_M2M.md"
SP2_NOTE = REPO / "docs" / "planning" / "NOTE_L1_ALIAS_VS_NO_HELD_R2_R3.md"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0060"
    assert PRIOR_CP == "CP-0059"
    assert CYCLE == 56
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_WAN == "mesh.wan.model/v0"
    assert SCHEMA_HLC == "mesh.clock.hlc/v1"
    assert N_CAP == 2


def test_design_doc_bands_classes_hlc():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0060" in text
    assert "DESIGN" in text
    for band in ("RTT_lo", "RTT_mid", "RTT_hi"):
        assert band in text
    for cls in ("split", "heal", "flip-flop", "cascade", "SPLIT", "HEAL", "FLIP_FLOP", "CASCADE"):
        # design uses both prose and IDs
        pass
    assert "SPLIT" in text and "HEAL" in text
    assert "FLIP_FLOP" in text and "CASCADE" in text
    assert "P_partition" in text or "P_partition" in text
    assert "HLC" in text
    assert "wall_clock_as_authority" in text
    assert "NO_HELD" in text
    assert "jitter" in text.lower()
    assert "loss" in text.lower()
    assert "no N>2" in text or "N>2" in text
    assert "M2" in text


def test_pointer_schema_capability():
    assert POINTER.is_file()
    ptext = POINTER.read_text(encoding="utf-8")
    assert "M3_WAN_MODEL_DESIGN.md" in ptext
    assert "SUPERSEDED" in ptext or "design matured" in ptext.lower()
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.wan.model/v0" in stext
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0060" in ctext
    assert "NO_HELD" in ctext


def test_classify_rtt_bands():
    assert classify_rtt(0) == LatencyBand.RTT_lo
    assert classify_rtt(49.9) == LatencyBand.RTT_lo
    assert classify_rtt(50) == LatencyBand.RTT_mid
    assert classify_rtt(199) == LatencyBand.RTT_mid
    assert classify_rtt(200) == LatencyBand.RTT_hi
    assert classify_rtt(999) == LatencyBand.RTT_hi
    assert classify_rtt(1000) == LatencyBand.RTT_x


def test_classify_p_partition():
    assert classify_p_partition(0.0) == PPartitionLabel.P_rare
    assert classify_p_partition(0.009) == PPartitionLabel.P_rare
    assert classify_p_partition(0.01) == PPartitionLabel.P_occasional
    assert classify_p_partition(0.04) == PPartitionLabel.P_occasional
    assert classify_p_partition(0.05) == PPartitionLabel.P_elevated
    assert classify_p_partition(0.19) == PPartitionLabel.P_elevated
    assert classify_p_partition(0.20) == PPartitionLabel.P_hostile
    assert classify_p_partition(1.0) == PPartitionLabel.P_hostile
    with pytest.raises(WanError) as ei:
        classify_p_partition(1.1)
    assert ei.value.code == "WAN_P_PARTITION_INVALID"
    with pytest.raises(WanError) as ei2:
        classify_p_partition(-0.01)
    assert ei2.value.code == "WAN_P_PARTITION_INVALID"


def test_compare_hlc_ignores_wall():
    a = HlcStamp(logical=1, counter=0, wall_ms=9999)
    b = HlcStamp(logical=1, counter=1, wall_ms=0)
    assert compare_hlc_tuple(a, b) == -1
    assert compare_hlc_tuple(b, a) == 1
    c = HlcStamp(logical=1, counter=1, wall_ms=12345)
    assert compare_hlc_tuple(b, c) == 0


def test_t_m3a_partition_matrix_happy():
    m = WanModel()
    m.set_rtt(80)
    assert m.record.band == LatencyBand.RTT_mid
    m.set_p_partition(0.02)
    assert m.record.p_label == PPartitionLabel.P_occasional
    m.set_envelopes(jitter_ms=10, loss_pct=0.5)
    m.stamp_hlc(1, 0, wall_ms=100)
    m.path_loss()
    assert m.record.partition_class == PartitionClass.SPLIT
    assert m.record.dual_primary == 0
    h1 = HlcStamp(logical=1, counter=0)
    m.stamp_hlc(1, 1, wall_ms=200)
    assert compare_hlc_tuple(h1, m.record.hlc) == -1
    m.path_ok()
    assert m.record.partition_class == PartitionClass.HEAL
    m.path_ok()
    assert m.record.partition_class == PartitionClass.STABLE
    d = m.record.to_dict()
    assert d["dual_primary"] == 0
    assert d["wall_clock_as_authority"] == 0
    assert d["n_cap"] == 2
    assert d["schema"] == SCHEMA_WAN


def test_t_m3a_neg_wall_as_authority():
    m = WanModel()
    with pytest.raises(WanError) as ei:
        m.claim_wall_as_authority()
    assert ei.value.code == "WAN_WALL_CLOCK_AS_AUTHORITY"


def test_t_m3a_neg_hlc_order_violation():
    m = WanModel()
    with pytest.raises(WanError) as ei:
        m.order_by_wall(100, 200)
    assert ei.value.code == "WAN_HLC_ORDER_VIOLATION"


def test_t_m3a_neg_n_gt2():
    m = WanModel(n_members=3)
    with pytest.raises(WanError) as ei:
        m.path_loss()
    assert ei.value.code == "WAN_N_GT2_REFUSED"


def test_t_m3a_neg_invalid_p():
    m = WanModel()
    with pytest.raises(WanError) as ei:
        m.set_p_partition(2.0)
    assert ei.value.code == "WAN_P_PARTITION_INVALID"


def test_t_m3a_neg_unknown_class():
    m = WanModel()
    with pytest.raises(WanError) as ei:
        m.set_class("QUORUM_WITNESS")
    assert ei.value.code == "WAN_CLASS_UNKNOWN"


def test_t_m3a_neg_extreme_default():
    m = WanModel()
    with pytest.raises(WanError) as ei:
        m.set_rtt(1500, as_prod_default=True)
    assert ei.value.code == "WAN_BAND_EXTREME_DEFAULT"


def test_t_m3a_neg_envelopes():
    m = WanModel()
    m.set_rtt(30)  # lo
    with pytest.raises(WanError) as ei:
        m.set_envelopes(jitter_ms=JITTER_ENVELOPE_MS[LatencyBand.RTT_lo] + 1, loss_pct=0)
    assert ei.value.code == "WAN_JITTER_ENVELOPE_EXCEEDED"
    with pytest.raises(WanError) as ei2:
        m.set_envelopes(jitter_ms=0, loss_pct=LOSS_ENVELOPE_PCT[LatencyBand.RTT_lo] + 0.1)
    assert ei2.value.code == "WAN_LOSS_ENVELOPE_EXCEEDED"


def test_t_m3b_flip_flop_bound():
    m = WanModel()
    m.path_loss()
    m.path_ok()
    m.path_loss()
    m.path_ok()
    m.path_loss()  # flap_count triggers FLIP_FLOP
    assert m.record.partition_class == PartitionClass.FLIP_FLOP
    assert m.record.dual_primary == 0
    m.path_ok()
    assert m.record.partition_class == PartitionClass.HEAL
    assert m.record.dual_primary == 0


def test_t_m3b_neg_cascade_witness():
    m = WanModel()
    m.path_loss()
    m.cascade_fault()
    assert m.record.partition_class == PartitionClass.CASCADE
    assert m.record.dual_primary == 0
    with pytest.raises(WanError) as ei:
        m.invent_witness_n3()
    assert ei.value.code == "WAN_N_GT2_REFUSED"


def test_abort_codes_documented():
    text = DESIGN.read_text(encoding="utf-8") + SCHEMA.read_text(encoding="utf-8")
    for code in ABORT_CODES:
        assert code in text, code


def test_no_gia_raft_runtime_claims():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "we unlocked raft" not in low
    assert "n>2 is live" not in low
    assert "agi achieved" not in low
    assert "does **not** implement" in text or "no WAN runtime" in text


def test_no_live_secrets_in_docs():
    for path in (DESIGN, SCHEMA, CAP):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name


def test_council_paste_sp_ack():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "SP1" in ptext and "ACK" in ptext
    assert "SP2" in ptext
    assert "SP3" in ptext and "ACK_WITH_FENCE" in ptext
    assert "SP4" in ptext and "ACK_WITH_CAVEAT" in ptext
    assert "M3_WAN" in ptext or "M3_WAN_model" in ptext
    assert "PREFERRED_NEXT" in ptext


def test_sp2_alias_note_and_blueprint():
    assert SP2_NOTE.is_file()
    ntext = SP2_NOTE.read_text(encoding="utf-8")
    assert "L1-OBS-peers" in ntext
    assert "L1-quickstart" in ntext
    assert "NO_HELD" in ntext
    # Blueprint display aliases present; NO_HELD R2/R3 list unchanged
    for bp in (
        REPO / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT.md",
        REPO / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT_READABLE.md",
        REPO / "council" / "blueprint" / "HUMAN_BLUEPRINT_ROOT.md",
    ):
        btext = bp.read_text(encoding="utf-8")
        assert "L1-OBS-peers" in btext or "L1-OBS-peers" in btext
        assert "L1-quickstart" in btext
        assert "UNLOCKABLE_NO_HELD" in btext or "NO_HELD" in btext
        # product ML tracks still named R2, R3 in NO_HELD list
        assert "R2" in btext and "R3" in btext


def test_tags_untouched():
    assert subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode == 0


def test_record_invariants():
    m = WanModel()
    m.set_rtt(10)
    m.set_p_partition(0)
    d = m.record.to_dict()
    assert d["dual_primary"] == 0
    assert d["wall_clock_as_authority"] == 0
    assert d["n_cap"] == 2
    assert d["hlc"]["wall_clock_as_authority"] == 0
