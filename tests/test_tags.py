"""Cycle 17 — CP-0021 floor checkpoint tag invariant / 0.14.3."""

from __future__ import annotations

from pathlib import Path

import pytest

from neural_mesh.tags import (
    FLOOR_CHECKPOINT_PREFIX,
    FloorCheckpointTagError,
    is_floor_checkpoint_tag,
    make_floor_checkpoint_tag,
    parse_floor_checkpoint_tag,
    validate_one_checkpoint_tag_per_floor,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def checkpoint_every_floor_fixture():
    """Floor fixture: floors 0..2 each with exactly one CHECKPOINT@floor:<n>."""
    floors = [0, 1, 2]
    tags = [make_floor_checkpoint_tag(n) for n in floors] + [
        "unrelated:label",
        "env:test",
    ]
    return floors, tags


def test_checkpoint_every_floor_schema_documented():
    p = ROOT / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "CHECKPOINT@floor:<n>" in text or "CHECKPOINT@floor:" in text
    assert "SCHEMA-GATED" in text or "schema" in text.lower()
    assert "CP-0021" in text
    assert "validate_one_checkpoint_tag_per_floor" in text
    assert "EXPLICIT DEBT" in text or "SLO" in text
    assert "No Raft" in text or "NOT Raft" in text or "No Raft/Paxos" in text


def test_checkpoint_every_floor_make_parse_roundtrip():
    for n in (0, 1, 7, 42):
        tag = make_floor_checkpoint_tag(n)
        assert tag == f"CHECKPOINT@floor:{n}"
        assert is_floor_checkpoint_tag(tag)
        assert parse_floor_checkpoint_tag(tag) == n


def test_checkpoint_every_floor_invalid_tag_rejected():
    for bad in (
        "",
        "CHECKPOINT@floor:",
        "CHECKPOINT@floor:-1",
        "CHECKPOINT@floor:1a",
        "checkpoint@floor:1",
        "CHECKPOINT@FLOOR:1",
        "CHECKPOINT@floor: 1",
        "OTHER@floor:1",
    ):
        assert not is_floor_checkpoint_tag(bad)
        with pytest.raises(FloorCheckpointTagError):
            parse_floor_checkpoint_tag(bad)


def test_checkpoint_every_floor_make_rejects_negative():
    with pytest.raises(FloorCheckpointTagError):
        make_floor_checkpoint_tag(-1)


def test_checkpoint_every_floor_validator_ok(checkpoint_every_floor_fixture):
    floors, tags = checkpoint_every_floor_fixture
    result = validate_one_checkpoint_tag_per_floor(tags, floors)
    assert result["ok"] is True
    assert result["count"] == len(floors)
    assert result["schema"] == f"{FLOOR_CHECKPOINT_PREFIX}<n>"
    for n in floors:
        assert result["floors"][n] == make_floor_checkpoint_tag(n)


def test_checkpoint_every_floor_missing_rejected(checkpoint_every_floor_fixture):
    floors, tags = checkpoint_every_floor_fixture
    # Drop floor 1 tag
    tags = [t for t in tags if t != "CHECKPOINT@floor:1"]
    with pytest.raises(FloorCheckpointTagError, match="missing"):
        validate_one_checkpoint_tag_per_floor(tags, floors)


def test_checkpoint_every_floor_duplicate_rejected(checkpoint_every_floor_fixture):
    floors, tags = checkpoint_every_floor_fixture
    tags = list(tags) + ["CHECKPOINT@floor:0"]
    with pytest.raises(FloorCheckpointTagError, match="duplicate"):
        validate_one_checkpoint_tag_per_floor(tags, floors)


def test_checkpoint_every_floor_primary_floor_zero():
    """Primary EVERY overlay floor is floor 0 per debt schema."""
    tags = ["CHECKPOINT@floor:0"]
    result = validate_one_checkpoint_tag_per_floor(tags, floors=[0])
    assert result["ok"] is True
    assert result["floors"][0] == "CHECKPOINT@floor:0"


def test_checkpoint_every_floor_version_0143():
    from neural_mesh import __version__

    parts = [int(x) for x in __version__.split(".")[:3]]
    assert parts >= [0, 14, 3]


def test_checkpoint_every_floor_council_agreement():
    p = ROOT / "council" / "COUNCIL_AGREEMENT_CYCLE17.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "CP-0021" in text
    assert "0.14.3" in text
    assert "CHECKPOINT@floor" in text or "floor checkpoint" in text.lower()
