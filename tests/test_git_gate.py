"""P3 mesh audit git dirty-tree gate."""

import subprocess
from pathlib import Path

from neural_mesh.git_audit import audit_git


def _git(cwd: Path, *args: str):
    subprocess.check_call(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_git_audit_pass_on_clean_repo(tmp_path: Path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README").write_text("x" + chr(10), encoding="utf-8")
    _git(tmp_path, "add", "README")
    _git(tmp_path, "commit", "-m", "init")
    result = audit_git(tmp_path)
    assert result.ok
    assert result.status_line == "GIT STATUS: PASS"
    assert result.branch
    assert result.commit
    assert result.modified == []
    assert result.untracked == []


def test_git_audit_fail_on_dirty(tmp_path: Path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README").write_text("x" + chr(10), encoding="utf-8")
    _git(tmp_path, "add", "README")
    _git(tmp_path, "commit", "-m", "init")
    (tmp_path / "README").write_text("dirty" + chr(10), encoding="utf-8")
    (tmp_path / "new.txt").write_text("u" + chr(10), encoding="utf-8")
    result = audit_git(tmp_path)
    assert not result.ok
    assert result.status_line == "GIT STATUS: FAIL"
    assert any("README" in m for m in result.modified)
    assert any("new.txt" in u for u in result.untracked)
