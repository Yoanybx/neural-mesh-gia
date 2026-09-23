"""Persistence helpers for twin JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import FaultEvent


def load_json(path: str | Path) -> dict[str, Any] | list[Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_faults(path: str | Path) -> list[FaultEvent]:
    data = load_json(path)
    if isinstance(data, dict):
        items = data.get("faults", [])
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"unsupported faults JSON shape in {path}")
    return [FaultEvent.from_dict(item) for item in items]


def save_faults(path: str | Path, faults: list[FaultEvent]) -> None:
    save_json(path, {"faults": [f.to_dict() for f in faults]})


def faults_hash(faults: list[FaultEvent]) -> str:
    import hashlib

    payload = [f.to_dict() for f in sorted(
        faults, key=lambda e: (e.tick, e.fault_type, e.target_id, e.event_id)
    )]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()
