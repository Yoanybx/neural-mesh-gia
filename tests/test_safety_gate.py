"""P3 safety policy gate."""

import json
from pathlib import Path

from neural_mesh.safety import (
    DEFAULT_POLICY,
    ensure_default_policy,
    safety_status,
)


def test_ensure_and_status_safe(tmp_path: Path):
    path = ensure_default_policy(tmp_path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["allow_network_actions"] is False
    assert data["allow_physical_actions"] is False
    assert data["require_human_approval"] is True
    st = safety_status(tmp_path)
    assert st.status == "SAFE"
    assert st.policy == DEFAULT_POLICY


def test_unsafe_when_network_allowed(tmp_path: Path):
    path = ensure_default_policy(tmp_path)
    payload = {
        "allow_network_actions": True,
        "allow_physical_actions": False,
        "require_human_approval": True,
    }
    path.write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")
    st = safety_status(tmp_path)
    assert st.status == "UNSAFE"


def test_missing_policy_status(tmp_path: Path):
    st = safety_status(tmp_path)
    assert st.status == "MISSING"
