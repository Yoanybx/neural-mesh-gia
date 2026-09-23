"""Manifest + archive reproducibility helpers (CP-0025 / P10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .bundle import build_bundle, sha256_file
from .manifest import BundleManifest, manifest_to_json

__all__ = ["ReproResult", "repro_check"]


@dataclass
class ReproResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    sha_a: str | None = None
    sha_b: str | None = None
    manifest_a: BundleManifest | None = None
    manifest_b: BundleManifest | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "sha_a": self.sha_a,
            "sha_b": self.sha_b,
            "equal": self.ok and self.sha_a == self.sha_b,
        }


def repro_check(
    root: Path | str,
    out_dir: Path | str,
    *,
    name: str | None = None,
    ver: str | None = None,
    tip: str | None = None,
    cp_range: str | None = None,
    pytest: Mapping[str, int] | None = None,
    entrypoint: str = "mesh",
) -> ReproResult:
    """Build the same bundle twice into sibling dirs; compare bundle_sha256."""
    from .bundle import DEFAULT_BUNDLE_NAME

    result = ReproResult()
    root = Path(root)
    out_dir = Path(out_dir)
    out_a = out_dir / "repro_a"
    out_b = out_dir / "repro_b"
    kwargs = dict(
        name=name or DEFAULT_BUNDLE_NAME,
        ver=ver,
        tip=tip,
        cp_range=cp_range,
        pytest=pytest,
        entrypoint=entrypoint,
        freeze=True,
    )
    m1 = build_bundle(root, out_a, **kwargs)
    m2 = build_bundle(root, out_b, **kwargs)
    result.manifest_a = m1
    result.manifest_b = m2
    result.sha_a = m1.bundle_sha256
    result.sha_b = m2.bundle_sha256
    if m1.bundle_sha256 != m2.bundle_sha256:
        result.fail(
            f"bundle_sha256 mismatch: {m1.bundle_sha256} != {m2.bundle_sha256}"
        )
    if manifest_to_json(m1) != manifest_to_json(m2):
        result.fail("manifest JSON mismatch between repro builds")
    tar_a = out_a / f"{m1.name}-{m1.ver}.tar.gz"
    tar_b = out_b / f"{m2.name}-{m2.ver}.tar.gz"
    if sha256_file(tar_a) != sha256_file(tar_b):
        result.fail("archive file sha256 mismatch")
    return result
