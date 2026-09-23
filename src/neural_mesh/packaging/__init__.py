"""Mesh Packaging: Single-Node Bundle (CP-0024 / Cycle 20; RC harden CP-0025).

Capability packaging for a reproducible single-node tarball + manifest.
Does **not** change tags, SLOs, consensus, Raft, or N>2.
"""

from .manifest import (
    SCHEMA_ID,
    FREEZE_CHANNEL,
    BundleManifest,
    FreezeInfo,
    PytestSummary,
    manifest_to_dict,
    manifest_to_json,
)
from .bundle import (
    DEFAULT_BUNDLE_NAME,
    DEFAULT_ENTRYPOINT,
    FIXED_MTIME,
    ARCHIVE_ROOT,
    build_bundle,
    verify_bundle,
    collect_bundle_files,
    load_manifest,
    sha256_file,
    sha256_bytes,
)
from .clean_smoke import CleanSmokeResult, clean_node_smoke, assert_extract_isolation
from .repro import ReproResult, repro_check

__all__ = [
    "SCHEMA_ID",
    "FREEZE_CHANNEL",
    "BundleManifest",
    "FreezeInfo",
    "PytestSummary",
    "manifest_to_dict",
    "manifest_to_json",
    "DEFAULT_BUNDLE_NAME",
    "DEFAULT_ENTRYPOINT",
    "FIXED_MTIME",
    "ARCHIVE_ROOT",
    "build_bundle",
    "verify_bundle",
    "collect_bundle_files",
    "load_manifest",
    "sha256_file",
    "sha256_bytes",
    "CleanSmokeResult",
    "clean_node_smoke",
    "assert_extract_isolation",
    "ReproResult",
    "repro_check",
]
