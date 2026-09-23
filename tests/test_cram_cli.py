"""P3 CLI mesh cram put|get|verify|fsck — exit 0 PASS, 2 corrupt, 3 missing."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]


def _run(args: list[str], *, cwd: Path, input_bytes: bytes | None = None):
    return subprocess.run(
        MESH + args,
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
    )


def test_cram_put_get_verify_ok(tmp_path: Path):
    r = _run(["cram", "put", "--root", str(tmp_path), "hello-cram"], cwd=ROOT)
    assert r.returncode == 0, r.stderr
    key = r.stdout.decode().strip()
    assert len(key) == 64

    g = _run(["cram", "get", "--root", str(tmp_path), key], cwd=ROOT)
    assert g.returncode == 0
    assert b"hello-cram" in g.stdout

    v = _run(["cram", "verify", "--root", str(tmp_path), key], cwd=ROOT)
    assert v.returncode == 0
    assert b"OK" in v.stdout


def test_cram_verify_missing_exit_3(tmp_path: Path):
    r = _run(["cram", "verify", "--root", str(tmp_path), "0" * 64], cwd=ROOT)
    assert r.returncode == 3
    assert b"MISSING" in r.stderr


def test_cram_verify_corrupt_exit_2(tmp_path: Path):
    r = _run(["cram", "put", "--root", str(tmp_path), "intact"], cwd=ROOT)
    key = r.stdout.decode().strip()
    blob = tmp_path / ".cram" / key[:2] / key[2:]
    blob.write_bytes(b"tampered-bytes")
    v = _run(["cram", "verify", "--root", str(tmp_path), key], cwd=ROOT)
    assert v.returncode == 2
    assert b"CORRUPT" in v.stderr


def test_cram_get_missing_exit_3(tmp_path: Path):
    r = _run(["cram", "get", "--root", str(tmp_path), "b" * 64], cwd=ROOT)
    assert r.returncode == 3


def test_cram_fsck_json_and_corrupt(tmp_path: Path):
    r = _run(["cram", "put", "--root", str(tmp_path), "fsck-me"], cwd=ROOT)
    key = r.stdout.decode().strip()
    ok = _run(["cram", "fsck", "--root", str(tmp_path), "--json"], cwd=ROOT)
    assert ok.returncode == 0
    report = json.loads(ok.stdout.decode())
    assert report["fsck_schema"] == 1
    assert report["status"] == "OK"
    assert key in report["ok"]

    (tmp_path / ".cram" / key[:2] / key[2:]).write_bytes(b"x")
    bad = _run(["cram", "fsck", "--root", str(tmp_path), "--json"], cwd=ROOT)
    assert bad.returncode == 2
    report2 = json.loads(bad.stdout.decode())
    assert key in report2["corrupt"]
