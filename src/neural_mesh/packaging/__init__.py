"""Mesh Packaging: Single-Node Bundle (CP-0024 / Cycle 20).

Capability packaging for a reproducible single-node tarball + manifest.
Does **not** change tags, SLOs, consensus, Raft, or N>2.
"""

from .manifest import (
    SCHEMA_ID,
    BundleManifest,
    PytestSummary,
    manifest_to_dict,
    manifest_to_json,
)
from .bundle import (
    DEFAULT_BUNDLE_NAME,
    DEFAULT_ENTRYPOINT,
    build_bundle,
    verify_bundle,
    collect_bundle_files,
    load_manifest,
    sha256_file,
    sha256_bytes,
)

__all__ = [
    "SCHEMA_ID",
    "BundleManifest",
    "PytestSummary",
    "manifest_to_dict",
    "manifest_to_json",
    "DEFAULT_BUNDLE_NAME",
    "DEFAULT_ENTRYPOINT",
    "build_bundle",
    "verify_bundle",
    "collect_bundle_files",
    "load_manifest",
    "sha256_file",
    "sha256_bytes",
]
