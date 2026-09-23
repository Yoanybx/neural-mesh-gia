"""Release tag + archive for single-node RC (CP-0028 / P19).

- Optional local annotated git tag (v0.16.3 or release-0.16.3 if taken).
- Never edit git config; one-shot -c user.name/email only; never push.
- Build release archive under dist/releases/0.16.3/:
  bundle tarball + manifest + SIGNOFF.json + SHA256SUMS + final audit copy.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .bundle import FIXED_MTIME, build_bundle, sha256_file
from .manifest import FREEZE_CHANNEL
from .release_checklist import NO_HELD_DEFAULT, GateResult
from .release_signoff import RELEASE_VERSION, SEAL_CP, DEFAULT_SIGNER

__all__ = [
    "TAG_AUTHOR_NAME",
    "TAG_AUTHOR_EMAIL",
    "ArchiveResult",
    "run_release_tag_archive",
    "preferred_tag_name",
    "create_annotated_tag",
]

TAG_AUTHOR_NAME = "Joan A Barrios Cruz"
TAG_AUTHOR_EMAIL = "yoanybx@users.noreply.github.com"


@dataclass
class ArchiveResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    tag_name: str | None = None
    tag_created: bool = False
    archive_dir: str | None = None
    tarball: str | None = None
    manifest_path: str | None = None
    signoff_path: str | None = None
    sha256sums_path: str | None = None
    audit_copy: str | None = None
    release_archive: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.gates.append(GateResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "version": self.version,
            "tip": self.tip,
            "tag_name": self.tag_name,
            "tag_created": self.tag_created,
            "archive_dir": self.archive_dir,
            "tarball": self.tarball,
            "manifest_path": self.manifest_path,
            "signoff_path": self.signoff_path,
            "sha256sums_path": self.sha256sums_path,
            "audit_copy": self.audit_copy,
            "release_archive": self.release_archive,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "freeze": FREEZE_CHANNEL,
            "cp": SEAL_CP,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def preferred_tag_name(root: Path, version: str = RELEASE_VERSION) -> str:
    """Return vX.Y.Z, or release-X.Y.Z if vX.Y.Z already exists."""
    primary = f"v{version}"
    alt = f"release-{version}"
    if _tag_exists(root, primary):
        return alt
    return primary


def _tag_exists(root: Path, name: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{name}"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _git_clean(root: Path) -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    # Allow untracked dist/ noise? Require clean for tag — empty porcelain.
    return proc.stdout.strip() == ""


def _git_tip(root: Path, override: str | None = None) -> str:
    if override:
        return override
    proc = subprocess.run(
        ["git", "rev-parse", "--short=7", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return "unknown"


def create_annotated_tag(
    root: Path,
    tag_name: str,
    *,
    message: str | None = None,
    force: bool = False,
) -> tuple[bool, str]:
    """Create local annotated tag with one-shot author. Never edits git config."""
    if _tag_exists(root, tag_name) and not force:
        return False, f"tag already exists: {tag_name}"
    msg = message or (
        f"Neural Mesh / GIA-COS {tag_name}: single-node RC release closeout "
        f"(Cycle 24 / {SEAL_CP}; freeze {FREEZE_CHANNEL}; signer {DEFAULT_SIGNER})"
    )
    cmd = [
        "git",
        "-c",
        f"user.name={TAG_AUTHOR_NAME}",
        "-c",
        f"user.email={TAG_AUTHOR_EMAIL}",
        "tag",
    ]
    if force:
        cmd.append("-f")
    cmd.extend(["-a", tag_name, "-m", msg])
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "tag failed").strip()
    return True, f"created {tag_name}"


def _write_sha256sums(archive_dir: Path, files: list[Path]) -> Path:
    lines: list[str] = []
    for p in files:
        if p.is_file():
            digest = sha256_file(p)
            lines.append(f"{digest}  {p.name}\n")
    out = archive_dir / "SHA256SUMS"
    out.write_text("".join(lines), encoding="utf-8")
    return out


def _copy_if_exists(src: Path, dest: Path) -> Path | None:
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return dest
    return None


def _bundle_release_tarball(archive_dir: Path, version: str) -> Path:
    """Pack the release dir contents into a nested release archive (deterministic mtime)."""
    out_tar = archive_dir / f"neural-mesh-gia-release-{version}.tar.gz"
    # Collect files currently in archive_dir (excluding the release tar itself)
    members = sorted(
        [
            p
            for p in archive_dir.iterdir()
            if p.is_file() and p.name != out_tar.name
        ],
        key=lambda p: p.name,
    )
    import gzip
    import io

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for p in members:
            info = tarfile.TarInfo(name=f"release-{version}/{p.name}")
            data = p.read_bytes()
            info.size = len(data)
            info.mtime = FIXED_MTIME
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
    raw = buf.getvalue()
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=open(out_tar, "wb"), mtime=FIXED_MTIME
    ) as gz:
        gz.write(raw)
    return out_tar


def run_release_tag_archive(
    root: Path | str,
    *,
    version: str = RELEASE_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    create_tag: bool = False,
    require_clean: bool = True,
    require_signoff: bool = True,
    tag_name: str | None = None,
    tag_fn: Callable[..., tuple[bool, str]] | None = None,
    skip_bundle: bool = False,
    force_fail: str | None = None,
) -> ArchiveResult:
    """Build dist/releases/<ver>/ archive; optionally create local annotated tag."""
    root = Path(root).resolve()
    result = ArchiveResult(version=version)
    archive_dir = Path(out_dir) if out_dir else (root / "dist" / "releases" / version)
    archive_dir.mkdir(parents=True, exist_ok=True)
    result.archive_dir = str(archive_dir)
    result.tip = _git_tip(root, tip)

    # --- signoff present ---
    signoff = archive_dir / "SIGNOFF.json"
    alt_signoff = root / ".project_state" / f"RELEASE_SIGNOFF_{version}.json"
    if force_fail == "signoff_present":
        result.add("signoff_present", False, "forced fail")
    else:
        if not signoff.is_file() and alt_signoff.is_file():
            shutil.copy2(alt_signoff, signoff)
        ok = signoff.is_file()
        if ok:
            try:
                data = json.loads(signoff.read_text(encoding="utf-8"))
                ok = bool(data.get("ok")) if require_signoff else True
                detail = f"ok={data.get('ok')} ver={data.get('ver')}"
            except (OSError, json.JSONDecodeError) as exc:
                ok = False
                detail = str(exc)
        else:
            detail = "SIGNOFF.json missing"
        result.add("signoff_present", ok, detail)
        if signoff.is_file():
            result.signoff_path = str(signoff)

    # --- build / copy bundle ---
    if force_fail == "bundle":
        result.add("bundle", False, "forced fail")
    elif skip_bundle:
        result.add("bundle", True, "skipped")
    else:
        built = build_bundle(
            root,
            archive_dir,
            tip=result.tip or "relarch",
            ver=version,
            freeze=True,
        )
        tar = archive_dir / f"{built.name}-{built.ver}.tar.gz"
        man = archive_dir / f"{built.name}-{built.ver}.manifest.json"
        result.tarball = str(tar) if tar.is_file() else None
        result.manifest_path = str(man) if man.is_file() else None
        result.add(
            "bundle",
            tar.is_file() and man.is_file(),
            f"tar={tar.name if tar.is_file() else None} "
            f"manifest={man.name if man.is_file() else None}",
        )

    # --- copy final audit if available ---
    audit_candidates = [
        root / "dist" / "final_audit" / "final_release_audit.json",
        archive_dir / "audit" / "final_release_audit.json",
        root / "snapshots" / "CP-0027" / "final_release_audit.json",
    ]
    audit_dest = archive_dir / "final_release_audit.json"
    copied = None
    for c in audit_candidates:
        copied = _copy_if_exists(c, audit_dest)
        if copied:
            break
    result.audit_copy = str(copied) if copied else None
    result.add(
        "audit_copy",
        True,  # optional — always soft-pass
        f"copied={copied is not None}",
    )

    # --- SHA256SUMS for artifacts currently present ---
    sum_files = [
        p
        for p in sorted(archive_dir.iterdir(), key=lambda x: x.name)
        if p.is_file()
        and p.name != "SHA256SUMS"
        and not p.name.startswith("neural-mesh-gia-release-")
    ]
    sha_path = _write_sha256sums(archive_dir, sum_files)
    result.sha256sums_path = str(sha_path)
    result.add("sha256sums", sha_path.is_file(), sha_path.name)

    # --- nested release archive ---
    try:
        rel_tar = _bundle_release_tarball(archive_dir, version)
        result.release_archive = str(rel_tar)
        # Refresh SHA256SUMS to include release tarball
        all_files = [
            p
            for p in sorted(archive_dir.iterdir(), key=lambda x: x.name)
            if p.is_file() and p.name != "SHA256SUMS"
        ]
        sha_path = _write_sha256sums(archive_dir, all_files)
        result.sha256sums_path = str(sha_path)
        result.add("release_archive", rel_tar.is_file(), rel_tar.name)
    except OSError as exc:
        result.add("release_archive", False, str(exc))

    # --- optional tag ---
    name = tag_name or preferred_tag_name(root, version)
    result.tag_name = name
    if create_tag:
        if force_fail == "tag":
            result.add("tag", False, "forced fail")
        else:
            clean = True
            if require_clean:
                clean = _git_clean(root)
            if not clean:
                result.add("tag", False, "working tree not clean; refuse tag")
            else:
                fn = tag_fn or create_annotated_tag
                ok, detail = fn(root, name)
                result.tag_created = ok
                result.add("tag", ok, detail)
                # Write archive marker even when tag mocked
                marker = archive_dir / "TAG_MARKER.json"
                marker.write_text(
                    json.dumps(
                        {
                            "tag": name,
                            "created": ok,
                            "tip": result.tip,
                            "ver": version,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
    else:
        # Always leave an archive marker noting tag intent
        marker = archive_dir / "TAG_MARKER.json"
        exists = _tag_exists(root, name) if (root / ".git").exists() else False
        marker.write_text(
            json.dumps(
                {
                    "tag": name,
                    "created": False,
                    "exists": exists,
                    "tip": result.tip,
                    "ver": version,
                    "note": "tag not requested (--tag to create when clean)",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result.add("tag", True, f"skipped exists={exists} name={name}")

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]
    result.summary = {
        "cycle": 24,
        "cp": SEAL_CP,
        "ver": version,
        "tip": result.tip,
        "tag": result.tag_name,
        "tag_created": result.tag_created,
        "archive_dir": result.archive_dir,
    }
    # Write ARCHIVE_MANIFEST.json
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(result.to_json(), encoding="utf-8")
    return result
