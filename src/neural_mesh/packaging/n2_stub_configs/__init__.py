"""N=2 dual-node stub configs packaged with neural-mesh-gia-n2 bundles."""

from __future__ import annotations

from pathlib import Path

STUB_DIR = Path(__file__).resolve().parent
NODE_A_PRIMARY = STUB_DIR / "node_a_primary.json"
NODE_B_SECONDARY = STUB_DIR / "node_b_secondary.json"

__all__ = ["STUB_DIR", "NODE_A_PRIMARY", "NODE_B_SECONDARY"]
