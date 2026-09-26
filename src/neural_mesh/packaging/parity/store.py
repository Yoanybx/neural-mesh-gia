"""Filesystem manifest-parity store: pair, builds, abort/reject-build flags.

Layout under ``<data_root>/parity/``:

  parity_state.json
  builds.jsonl
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_STORE,
    BuildArtifact,
    ParityN2Only,
    ParityPlaintextForbidden,
    ToolchainPin,
)


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / cleartext as a parity transport claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        raise ParityPlaintextForbidden(
            f"plaintext mode forbidden for parity ops: {mode!r}"
        )


class ParityStore:
    """Persist N=2 pair + manifest-parity fence state under a data root."""

    MAX_NODES = 2

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.root = self.data_root / "parity"
        self.state_path = self.root / "parity_state.json"
        self.builds_path = self.root / "builds.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    def _atomic_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def _default_state(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_STORE,
            "pair": [],
            "parity_ok": False,
            "mismatch_pending": False,
            "pending_paths": [],
            "build_rejected": False,
            "abort_reject_build": False,
            "abort_reason": "",
            "dual_primary": 0,
            "minority_writes": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
            "check_count": 0,
            "reject_count": 0,
            "match_count": 0,
            "last_digest_a": "",
            "last_digest_b": "",
            "mismatch_paths": [],
            "toolchain": ToolchainPin().to_dict(),
            "builds": {},
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return self._default_state()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["dual_primary"] = 0
        data["minority_writes"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        if "pair" not in data or data["pair"] is None:
            data["pair"] = []
        if "pending_paths" not in data or data["pending_paths"] is None:
            data["pending_paths"] = []
        if "mismatch_paths" not in data or data["mismatch_paths"] is None:
            data["mismatch_paths"] = []
        if "builds" not in data or data["builds"] is None:
            data["builds"] = {}
        if "toolchain" not in data or data["toolchain"] is None:
            data["toolchain"] = ToolchainPin().to_dict()
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data["dual_primary"] = 0
        data["minority_writes"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        self._atomic_json(self.state_path, data)

    def state(self) -> dict[str, Any]:
        return self._read_state()

    @property
    def pair(self) -> list[str]:
        return list(self._read_state().get("pair") or [])

    @property
    def build_rejected(self) -> bool:
        return bool(self._read_state().get("build_rejected"))

    @property
    def abort_reject_build(self) -> bool:
        return bool(self._read_state().get("abort_reject_build"))

    def set_pair(self, nodes: list[str]) -> list[str]:
        nodes = [str(n) for n in nodes]
        if len(nodes) != 2:
            raise ParityN2Only(f"parity pair requires exactly 2 nodes; got {len(nodes)}")
        if len(set(nodes)) != 2:
            raise ParityN2Only("parity pair requires two distinct node ids")
        if len(nodes) > self.MAX_NODES:
            raise ParityN2Only("N>2 refused for manifest parity")
        st = self._read_state()
        st["pair"] = list(nodes)
        self._write_state(st)
        return list(nodes)

    def set_toolchain(self, tc: ToolchainPin | dict[str, Any]) -> dict[str, Any]:
        pin = tc if isinstance(tc, ToolchainPin) else ToolchainPin.from_dict(tc)
        st = self._read_state()
        st["toolchain"] = pin.to_dict()
        self._write_state(st)
        return pin.to_dict()

    def record_build(self, artifact: BuildArtifact) -> None:
        st = self._read_state()
        builds = dict(st.get("builds") or {})
        builds[artifact.side] = artifact.to_dict()
        st["builds"] = builds
        if artifact.side in ("a", st.get("pair", [None])[0] if st.get("pair") else "a"):
            st["last_digest_a"] = artifact.digest_sha256
        if artifact.side in ("b", st.get("pair", [None, None])[1] if st.get("pair") and len(st.get("pair") or []) > 1 else "b"):
            st["last_digest_b"] = artifact.digest_sha256
        # Also key by literal side labels a/b
        if artifact.side == "a":
            st["last_digest_a"] = artifact.digest_sha256
        elif artifact.side == "b":
            st["last_digest_b"] = artifact.digest_sha256
        self._write_state(st)
        with self.builds_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(artifact.to_dict(), sort_keys=True) + "\n")

    def get_builds(self) -> dict[str, dict[str, Any]]:
        return dict(self._read_state().get("builds") or {})

    def mark_pending(self, paths: list[str]) -> None:
        st = self._read_state()
        st["mismatch_pending"] = True
        st["pending_paths"] = list(paths)
        st["mismatch_paths"] = list(paths)
        st["parity_ok"] = False
        self._write_state(st)

    def clear_pending_detection(self) -> None:
        st = self._read_state()
        st["mismatch_pending"] = False
        st["pending_paths"] = []
        self._write_state(st)

    def mark_match(self, digest_a: str, digest_b: str) -> None:
        st = self._read_state()
        st["parity_ok"] = True
        st["mismatch_pending"] = False
        st["pending_paths"] = []
        st["mismatch_paths"] = []
        st["last_digest_a"] = digest_a
        st["last_digest_b"] = digest_b
        st["match_count"] = int(st.get("match_count") or 0) + 1
        st["check_count"] = int(st.get("check_count") or 0) + 1
        self._write_state(st)

    def bump_check(self) -> None:
        st = self._read_state()
        st["check_count"] = int(st.get("check_count") or 0) + 1
        self._write_state(st)

    def reject_build(self, reason: str) -> None:
        st = self._read_state()
        st["build_rejected"] = True
        st["abort_reject_build"] = True
        st["abort_reason"] = str(reason or "ABORT→reject build")
        st["parity_ok"] = False
        st["reject_count"] = int(st.get("reject_count") or 0) + 1
        self._write_state(st)

    def enter_abort(self, reason: str, *, paths: list[str] | None = None) -> None:
        st = self._read_state()
        st["abort_reject_build"] = True
        st["build_rejected"] = True
        st["abort_reason"] = str(reason or "ABORT→reject build")
        st["parity_ok"] = False
        if paths is not None:
            st["mismatch_paths"] = list(paths)
            st["pending_paths"] = list(paths)
            st["mismatch_pending"] = True
        st["reject_count"] = int(st.get("reject_count") or 0) + 1
        self._write_state(st)

    def list_builds_log(self) -> list[dict[str, Any]]:
        if not self.builds_path.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in self.builds_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
        return out


__all__ = [
    "ParityStore",
    "require_no_plaintext",
]
