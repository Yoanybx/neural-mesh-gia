"""Safety policy gate (Acceptance Part X)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_POLICY: dict[str, Any] = {
    "allow_network_actions": False,
    "allow_physical_actions": False,
    "require_human_approval": True,
}


@dataclass
class SafetyStatus:
    policy_path: str
    policy: dict[str, Any]
    status: str  # SAFE | UNSAFE | MISSING

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_path": self.policy_path,
            "policy": self.policy,
            "status": self.status,
        }


def policy_path(root: Path) -> Path:
    return root / ".project_state" / "SAFETY_POLICY.json"


def ensure_default_policy(root: Path) -> Path:
    path = policy_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            json.dumps(DEFAULT_POLICY, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return path


def load_policy(root: Path) -> dict[str, Any]:
    path = policy_path(root)
    if not path.exists():
        return dict(DEFAULT_POLICY)
    return json.loads(path.read_text(encoding="utf-8"))


def safety_status(root: Path) -> SafetyStatus:
    path = policy_path(root)
    if not path.exists():
        return SafetyStatus(policy_path=str(path), policy=dict(DEFAULT_POLICY), status="MISSING")
    policy = load_policy(root)
    # SAFE iff network/physical actions denied (default harden posture).
    safe = (
        policy.get("allow_network_actions") is False
        and policy.get("allow_physical_actions") is False
    )
    return SafetyStatus(
        policy_path=str(path),
        policy=policy,
        status="SAFE" if safe else "UNSAFE",
    )
