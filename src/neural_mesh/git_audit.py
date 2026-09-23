"""Git dirty-tree gate — `mesh audit git`."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitAuditResult:
    ok: bool
    branch: str | None
    commit: str | None
    modified: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def status_line(self) -> str:
        return f"GIT STATUS: {'PASS' if self.ok else 'FAIL'}"

    def to_dict(self) -> dict:
        return {
            "status": "PASS" if self.ok else "FAIL",
            "branch": self.branch,
            "commit": self.commit,
            "modified": list(self.modified),
            "untracked": list(self.untracked),
            "error": self.error,
        }


def _run_git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


def audit_git(root: str | Path) -> GitAuditResult:
    root = Path(root)
    if not (root / ".git").exists():
        return GitAuditResult(
            ok=False,
            branch=None,
            commit=None,
            error="not a git repository",
        )
    try:
        branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
        commit = _run_git(root, "rev-parse", "HEAD")
        # Tracked modifications (staged + unstaged)
        modified_set: set[str] = set()
        for args in (
            ("diff", "--name-only"),
            ("diff", "--name-only", "--cached"),
        ):
            out = _run_git(root, *args)
            for line in out.splitlines():
                if line.strip():
                    modified_set.add(line.strip())
        untracked_out = _run_git(
            root, "ls-files", "--others", "--exclude-standard"
        )
        untracked = [ln.strip() for ln in untracked_out.splitlines() if ln.strip()]
        modified = sorted(modified_set)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return GitAuditResult(
            ok=False, branch=None, commit=None, error=str(exc)
        )

    ok = not modified and not untracked
    return GitAuditResult(
        ok=ok,
        branch=branch,
        commit=commit,
        modified=modified,
        untracked=untracked,
    )
