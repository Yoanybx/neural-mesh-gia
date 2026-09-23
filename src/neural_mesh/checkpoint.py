from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .models import Checkpoint, ProjectState, utc_now


class CheckpointManager:
    """Atomic, auditable checkpoint manager for Neural Mesh continuity."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.state_dir = self.root / ".project_state"
        self.cp_dir = self.root / "snapshots"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.cp_dir.mkdir(parents=True, exist_ok=True)

    def _atomic_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def load_state(self) -> ProjectState:
        p = self.state_dir / "CHECKPOINT.json"
        if not p.exists():
            return ProjectState()
        return ProjectState.model_validate_json(p.read_text(encoding="utf-8"))

    def save_state(self, state: ProjectState):
        state.last_updated = utc_now()
        self._atomic_json(self.state_dir / "CHECKPOINT.json", state.model_dump(mode="json"))

    def _canonical_bytes(self, path: Path) -> bytes:
        """Bytes used for integrity hashing.

        For checkpoint.json, exclude manifest_sha256 so the hash can be stored
        inside the same document without a circular dependency.
        """
        if path.name == "checkpoint.json":
            data = json.loads(path.read_text(encoding="utf-8"))
            data["manifest_sha256"] = None
            return json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        return path.read_bytes()

    def _manifest(self, paths: list[Path]) -> str:
        h = hashlib.sha256()
        for p in sorted(paths, key=lambda x: str(x)):
            if p.exists() and p.is_file():
                rel = str(p.relative_to(self.root))
                h.update(rel.encode("utf-8"))
                h.update(self._canonical_bytes(p))
        return h.hexdigest()

    def _next_id(self) -> str:
        existing = list(self.cp_dir.glob("CP-*"))
        n = 1
        if existing:
            nums = []
            for p in existing:
                parts = p.name.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    nums.append(int(parts[1]))
            if nums:
                n = max(nums) + 1
        return f"CP-{n:04d}"

    def create(
        self,
        phase: int,
        module: str,
        reason: str,
        next_action: str,
        git_commit: str | None = None,
        changed_files: list[str] | None = None,
        tests: dict | None = None,
        evidence: list[str] | None = None,
        status: str | None = None,
        cram_root_hash: str | None = None,
        cram_objects: list[str] | None = None,
    ) -> Checkpoint:
        state = self.load_state()
        cid = self._next_id()
        cp = Checkpoint(
            checkpoint_id=cid,
            project_version=state.project_version,
            phase=phase,
            module=module,
            reason=reason,
            next_action=next_action,
            git_commit=git_commit,
            changed_files=changed_files or [],
            tests=tests or {},
            evidence=evidence or [],
            cram_root_hash=cram_root_hash,
            cram_objects=list(cram_objects or []),
        )
        if status is not None:
            from .models import Status

            cp.status = Status(status)

        folder = self.cp_dir / cid
        folder.mkdir(parents=True, exist_ok=False)

        # Update project state docs + CHECKPOINT.json before sealing the snapshot.
        self._write_state_docs(state, cp)
        state.last_checkpoint = cid
        state.current_phase = phase
        state.current_module = module
        state.next_action = next_action
        state.git_commit = git_commit
        state.modified_files = changed_files or []
        if tests:
            state.test_summary = tests
        if status is not None:
            from .models import Status

            state.status = Status(status)
        self.save_state(state)

        # Freeze a copy of project state inside the snapshot so historical
        # verify does not depend on later global state mutations.
        frozen_state = folder / "CHECKPOINT.json"
        frozen_state.write_bytes((self.state_dir / "CHECKPOINT.json").read_bytes())

        cp_path = folder / "checkpoint.json"
        cp.manifest_sha256 = None
        cp_path.write_text(cp.model_dump_json(indent=2), encoding="utf-8")

        manifest = self._manifest([cp_path, frozen_state])
        cp.manifest_sha256 = manifest
        cp_path.write_text(cp.model_dump_json(indent=2), encoding="utf-8")
        (folder / "manifest.sha256").write_text(
            f"{manifest}  checkpoint.json\n", encoding="utf-8"
        )
        return cp

    def _write_state_docs(self, state, cp):
        self.state_dir.mkdir(exist_ok=True)
        (self.state_dir / "CURRENT_STATE.md").write_text(
            f"# CURRENT PROJECT STATE\n\nPhase: {cp.phase}\nModule: {cp.module}\n"
            f"Status: {cp.status.value}\nLast checkpoint: {cp.checkpoint_id}\n"
            f"Next action: {cp.next_action}\nGit: {cp.git_commit or 'unknown'}\n"
            f"Safety: {cp.safety_status}\nUpdated: {utc_now()}\n",
            encoding="utf-8",
        )
        (self.state_dir / "NEXT_ACTION.md").write_text(
            f"# NEXT ACTION\n\n## Priority\nP0\n\n## Action\n{cp.next_action}\n"
            f"\n## Status\nREADY\n\n## Checkpoint\n{cp.checkpoint_id}\n",
            encoding="utf-8",
        )
        (self.state_dir / "CHECKPOINT.md").write_text(
            f"# {cp.checkpoint_id}\n\nPhase: {cp.phase}\nModule: {cp.module}\n"
            f"Reason: {cp.reason}\nNext: {cp.next_action}\nTests: {cp.tests}\n",
            encoding="utf-8",
        )

    def latest(self) -> Checkpoint | None:
        files = sorted(self.cp_dir.glob("CP-*/checkpoint.json"))
        if not files:
            return None
        return Checkpoint.model_validate_json(files[-1].read_text(encoding="utf-8"))

    def list_ids(self) -> list[str]:
        return [p.parent.name for p in sorted(self.cp_dir.glob("CP-*/checkpoint.json"))]

    def verify(self, cid: str) -> bool:
        p = self.cp_dir / cid
        cp = p / "checkpoint.json"
        mf = p / "manifest.sha256"
        frozen = p / "CHECKPOINT.json"
        if not cp.exists() or not mf.exists():
            return False
        recorded = mf.read_text(encoding="utf-8").split()[0]
        # Prefer frozen snapshot state; fall back to live state for legacy layouts.
        state_path = frozen if frozen.exists() else self.state_dir / "CHECKPOINT.json"
        current = self._manifest([cp, state_path])
        return recorded == current
