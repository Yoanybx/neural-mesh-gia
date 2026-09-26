"""Manifest-parity service: byte-equality @N2, toolchain pin, ABORT→reject build.

Fail-closed. Extends packaging/manifest_n2 core_parity — does not reopen
0.16.3 / 0.17.0 tags. No Raft. No N>2. No multi-primary. No Vault/ACME.
No plaintext. No GIA. No fiat/tokens. Economy PARKED.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from neural_mesh.packaging.bundle_n2 import CORE_PARITY_CANDIDATES, core_parity_checksums

from .models import (
    FROZEN_CHANNELS,
    PARITY_CHANNEL,
    SCHEMA_ID,
    BuildArtifact,
    ConcurrentBuildResult,
    ParityAbortRejectBuild,
    ParityCheckResult,
    ParityError,
    ParityFrozenChannel,
    ParityIncomplete,
    ParityMismatch,
    ParityN2Only,
    ParityStatus,
    ParityToolchainMismatch,
    ToolchainPin,
)
from .store import ParityStore, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_manifest_bytes(manifest: Mapping[str, Any] | bytes | str) -> bytes:
    """Canonical JSON bytes for byte-equality (stable key order; strip noise).

    Strips non-deterministic fields (created_utc) so concurrent builds from
    the same tip/ver compare on content digests only.
    """
    if isinstance(manifest, (bytes, bytearray)):
        raw = bytes(manifest)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Opaque bytes — digest as-is
            return raw
    elif isinstance(manifest, str):
        data = json.loads(manifest)
    else:
        data = dict(manifest)
    data = dict(data)
    data.pop("created_utc", None)
    # Hard zeros in compared payload
    data["dual_primary"] = 0
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def compute_toolchain_pin(
    *,
    compiler: str | None = None,
    libc: str | None = None,
    locale: str | None = None,
) -> ToolchainPin:
    """P-09: pin compiler+libc+locale → pin_hash."""
    comp = compiler or f"cpython-{sys.version_info.major}.{sys.version_info.minor}"
    lib = libc or platform.libc_ver()[0] or platform.system().lower() or "host"
    loc = locale or "C.UTF-8"
    material = f"{comp}|{lib}|{loc}".encode("utf-8")
    return ToolchainPin(
        compiler=comp,
        libc=lib,
        locale=loc,
        pin_hash=_sha256_hex(material),
    )


def compare_checksum_maps(
    a: Mapping[str, str],
    b: Mapping[str, str],
    *,
    paths: Sequence[str] | None = None,
) -> tuple[bool, list[str]]:
    """Byte-level path checksum equality; returns (ok, mismatch_paths)."""
    if paths is not None:
        keys = list(paths)
    else:
        keys = sorted(set(a.keys()) | set(b.keys()))
    mismatches: list[str] = []
    for rel in keys:
        va = a.get(rel)
        vb = b.get(rel)
        if va is None or vb is None:
            if va != vb:
                mismatches.append(rel)
            continue
        if va != vb:
            mismatches.append(rel)
    return (len(mismatches) == 0, mismatches)


class ParityService:
    """H8 manifest parity @N2 around a local data root (no Raft)."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.store = ParityStore(self.data_root)

    # --- bootstrap ---

    def bootstrap_pair(
        self,
        node_a: str,
        node_b: str,
        *,
        mode: str = "local",
        pin_toolchain: bool = True,
        channel: str = PARITY_CHANNEL,
    ) -> dict[str, Any]:
        """Register exactly two build sides; optionally pin toolchain (P-09)."""
        require_no_plaintext(mode)
        if channel in FROZEN_CHANNELS:
            raise ParityFrozenChannel(
                f"refuse reopen of frozen channel {channel!r} "
                "(0.16.3 / 0.17.0 untouched)"
            )
        if not node_a or not node_b:
            raise ParityError("both node_a and node_b required")
        if str(node_a) == str(node_b):
            raise ParityN2Only("pair requires two distinct node ids")
        pair = self.store.set_pair([str(node_a), str(node_b)])
        tc = compute_toolchain_pin() if pin_toolchain else ToolchainPin()
        if pin_toolchain:
            self.store.set_toolchain(tc)
        return {
            "schema": SCHEMA_ID,
            "pair": pair,
            "channel": channel,
            "toolchain": tc.to_dict(),
            "dual_primary": 0,
            "minority_writes": 0,
            "build_rejected": False,
            "parity_ok": False,
        }

    # --- record / check ---

    def record_build(
        self,
        side: str,
        manifest: Mapping[str, Any] | bytes | str,
        *,
        checksums: Mapping[str, str] | None = None,
        bundle_sha256: str | None = None,
        ver: str | None = None,
        tip: str | None = None,
        mode: str = "local",
    ) -> BuildArtifact:
        """Record one side of an N2 concurrent build for later parity check."""
        require_no_plaintext(mode)
        if self.store.build_rejected:
            raise ParityAbortRejectBuild(
                "build already rejected (ABORT→reject build); refuse record"
            )
        pair = self.store.pair
        if pair and side not in pair and side not in ("a", "b"):
            raise ParityN2Only(f"side {side!r} not in pair {pair} (use a/b or pair ids)")
        canon = canonical_manifest_bytes(manifest)
        digest = _sha256_hex(canon)
        if isinstance(manifest, Mapping):
            cs = dict(checksums or manifest.get("checksums") or {})
            bsha = bundle_sha256 or manifest.get("bundle_sha256")
            ver = ver or manifest.get("ver")
            tip = tip or manifest.get("tip")
        else:
            cs = dict(checksums or {})
            bsha = bundle_sha256
        tc = ToolchainPin.from_dict(self.store.state().get("toolchain"))
        art = BuildArtifact(
            side=str(side),
            digest_sha256=digest,
            canonical_bytes_len=len(canon),
            checksums=cs,
            bundle_sha256=str(bsha) if bsha else None,
            ver=str(ver) if ver else None,
            tip=str(tip) if tip else None,
            toolchain_pin_hash=tc.pin_hash or None,
            ts=_utcnow(),
        )
        self.store.record_build(art)
        return art

    def _sides(self) -> tuple[str, str]:
        pair = self.store.pair
        if pair and len(pair) == 2:
            return pair[0], pair[1]
        return "a", "b"

    def _resolve_builds(self) -> tuple[dict[str, Any], dict[str, Any]]:
        builds = self.store.get_builds()
        side_a, side_b = self._sides()
        a = builds.get(side_a) or builds.get("a")
        b = builds.get(side_b) or builds.get("b")
        if not a or not b:
            raise ParityIncomplete(
                f"both build sides required; have={sorted(builds.keys())}"
            )
        return a, b

    def detect_mismatch(self) -> tuple[bool, list[str], str, str]:
        """Return (detected, mismatch_paths, digest_a, digest_b)."""
        st = self.store.state()
        if st.get("mismatch_pending"):
            return (
                True,
                list(st.get("pending_paths") or st.get("mismatch_paths") or []),
                str(st.get("last_digest_a") or ""),
                str(st.get("last_digest_b") or ""),
            )
        try:
            a, b = self._resolve_builds()
        except ParityIncomplete:
            return False, [], "", ""
        da = str(a.get("digest_sha256") or "")
        db = str(b.get("digest_sha256") or "")
        paths: list[str] = []
        if da != db:
            paths.append("canonical_manifest")
        ok_cs, cs_paths = compare_checksum_maps(
            dict(a.get("checksums") or {}),
            dict(b.get("checksums") or {}),
        )
        if not ok_cs:
            paths.extend(cs_paths)
        ba = a.get("bundle_sha256")
        bb = b.get("bundle_sha256")
        if ba and bb and ba != bb:
            paths.append("bundle_sha256")
        # Live detect only if not already rejected
        if (
            paths
            and not st.get("build_rejected")
            and not st.get("abort_reject_build")
        ):
            return True, paths, da, db
        return False, paths if paths else [], da, db

    def status(self) -> ParityStatus:
        st = self.store.state()
        detected, paths, da, db = self.detect_mismatch()
        issues: list[str] = []
        if detected:
            issues.append("parity_mismatch")
        if st.get("build_rejected") or st.get("abort_reject_build"):
            issues.append("build_rejected")
        pair = list(st.get("pair") or [])
        if len(pair) > 2:
            issues.append("n_gt_2")
        # Live byte-equality (equal digests, no pending mismatch) counts as ok
        # even before an explicit check() marks parity_ok — mirrors clock status.
        live_equal = bool(da) and bool(db) and da == db and not detected
        parity_ok = (
            (bool(st.get("parity_ok")) or live_equal)
            and not detected
            and not st.get("build_rejected")
        )
        # ok = healthy fence: no mismatch, no reject, N<=2 (no builds yet is ok)
        ok = (not detected) and (not st.get("build_rejected")) and ("n_gt_2" not in issues)
        return ParityStatus(
            ok=ok,
            data_root=str(self.data_root),
            pair=pair,
            parity_ok=parity_ok,
            mismatch_detected=detected,
            build_rejected=bool(st.get("build_rejected")),
            abort_reject_build=bool(st.get("abort_reject_build")),
            abort_reason=str(st.get("abort_reason") or ""),
            toolchain=dict(st.get("toolchain") or {}),
            last_digest_a=da or str(st.get("last_digest_a") or ""),
            last_digest_b=db or str(st.get("last_digest_b") or ""),
            mismatch_paths=paths or list(st.get("mismatch_paths") or []),
            check_count=int(st.get("check_count") or 0),
            reject_count=int(st.get("reject_count") or 0),
            match_count=int(st.get("match_count") or 0),
            issues=issues,
        )

    def check(
        self,
        *,
        auto_reject: bool = True,
        mode: str = "local",
        expect_toolchain_pin: str | None = None,
    ) -> ParityCheckResult:
        """Compare recorded N2 builds. Mismatch → ABORT→reject build."""
        require_no_plaintext(mode)
        if self.store.build_rejected:
            st = self.store.state()
            self.store.bump_check()
            return ParityCheckResult(
                ok=False,
                outcome="rejected_abort",
                parity_ok=False,
                mismatch_detected=False,
                build_rejected=True,
                abort_reject_build=True,
                digest_a=str(st.get("last_digest_a") or ""),
                digest_b=str(st.get("last_digest_b") or ""),
                mismatch_paths=list(st.get("mismatch_paths") or []),
                toolchain_pin_hash=str(
                    (st.get("toolchain") or {}).get("pin_hash") or ""
                ),
                reason="build already rejected (ABORT→reject build)",
                error="build rejected (ABORT→reject build)",
                error_code="PARITY_ABORT_REJECT_BUILD",
                action="abort_reject_build",
            )

        try:
            a, b = self._resolve_builds()
        except ParityIncomplete as exc:
            self.store.bump_check()
            return ParityCheckResult(
                ok=False,
                outcome="incomplete",
                reason=str(exc),
                error=str(exc),
                error_code="PARITY_INCOMPLETE",
                action="none",
            )

        da = str(a.get("digest_sha256") or "")
        db = str(b.get("digest_sha256") or "")
        mismatches: list[str] = []
        if da != db:
            mismatches.append("canonical_manifest")
        ok_cs, cs_paths = compare_checksum_maps(
            dict(a.get("checksums") or {}),
            dict(b.get("checksums") or {}),
        )
        if not ok_cs:
            mismatches.extend(cs_paths)
        ba = a.get("bundle_sha256")
        bb = b.get("bundle_sha256")
        if ba and bb and ba != bb:
            mismatches.append("bundle_sha256")

        # Toolchain pin check (P-09)
        tc = ToolchainPin.from_dict(self.store.state().get("toolchain"))
        pin_hash = tc.pin_hash or ""
        if expect_toolchain_pin is not None and expect_toolchain_pin != pin_hash:
            raise ParityToolchainMismatch(
                f"toolchain pin mismatch: expected={expect_toolchain_pin} got={pin_hash}"
            )
        a_pin = a.get("toolchain_pin_hash")
        b_pin = b.get("toolchain_pin_hash")
        if a_pin and b_pin and a_pin != b_pin:
            mismatches.append("toolchain_pin")

        if not mismatches:
            self.store.mark_match(da, db)
            return ParityCheckResult(
                ok=True,
                outcome="matched",
                parity_ok=True,
                mismatch_detected=False,
                build_rejected=False,
                abort_reject_build=False,
                digest_a=da,
                digest_b=db,
                toolchain_pin_hash=pin_hash,
                reason="byte-equality under concurrent build @N2",
                action="none",
            )

        # Mismatch — never silently accept
        self.store.mark_pending(mismatches)
        if auto_reject:
            jr = self.abort_reject_build(
                reason=(
                    f"ABORT→reject build: parity mismatch paths={mismatches} "
                    f"digest_a={da[:12]} digest_b={db[:12]}"
                ),
                mode=mode,
            )
            return ParityCheckResult(
                ok=False,
                outcome="mismatch",
                parity_ok=False,
                mismatch_detected=False,  # consumed into reject
                build_rejected=jr.build_rejected,
                abort_reject_build=jr.abort_reject_build,
                digest_a=da,
                digest_b=db,
                mismatch_paths=mismatches,
                toolchain_pin_hash=pin_hash,
                reason="parity mismatch; ABORT→reject build",
                error="parity mismatch; ABORT→reject build",
                error_code="PARITY_MISMATCH",
                action="abort_reject_build",
            )

        self.store.enter_abort(
            f"parity mismatch paths={mismatches}; auto_reject=false",
            paths=mismatches,
        )
        self.store.bump_check()
        return ParityCheckResult(
            ok=False,
            outcome="mismatch",
            parity_ok=False,
            mismatch_detected=True,
            build_rejected=True,
            abort_reject_build=True,
            digest_a=da,
            digest_b=db,
            mismatch_paths=mismatches,
            toolchain_pin_hash=pin_hash,
            reason="parity mismatch unresolved; ABORT pending reject build",
            error="parity mismatch; ABORT pending reject build",
            error_code="PARITY_MISMATCH",
            action="abort_reject_build",
        )

    def abort_reject_build(
        self,
        *,
        reason: str = "ABORT→reject build",
        mode: str = "local",
    ) -> ParityCheckResult:
        """ABORT path: never silent accept under mismatch; reject the build."""
        require_no_plaintext(mode)
        detected_before, paths, da, db = self.detect_mismatch()
        self.store.reject_build(
            reason
            or (
                f"ABORT→reject build (detected={detected_before}, "
                f"paths={paths}, digest_a={da[:12]}, digest_b={db[:12]})"
            )
        )
        self.store.clear_pending_detection()
        st = self.store.state()
        return ParityCheckResult(
            ok=True,  # abort path itself succeeded
            outcome="rejected_abort",
            parity_ok=False,
            mismatch_detected=False,
            build_rejected=True,
            abort_reject_build=True,
            digest_a=da or str(st.get("last_digest_a") or ""),
            digest_b=db or str(st.get("last_digest_b") or ""),
            mismatch_paths=paths or list(st.get("mismatch_paths") or []),
            toolchain_pin_hash=str((st.get("toolchain") or {}).get("pin_hash") or ""),
            reason=str(reason or ""),
            action="abort_reject_build",
        )

    # --- concurrent build ---

    def concurrent_build_check(
        self,
        builder: Callable[[], Mapping[str, Any] | bytes | str],
        *,
        auto_reject: bool = True,
        mode: str = "local",
        workers: int = 2,
    ) -> ConcurrentBuildResult:
        """Run builder twice concurrently; require byte-equality; else reject.

        ``builder`` must be pure w.r.t. tip/ver content (deterministic).
        """
        require_no_plaintext(mode)
        if workers != 2:
            raise ParityN2Only(f"concurrent build requires workers=2 @N2; got {workers}")
        if self.store.build_rejected:
            raise ParityAbortRejectBuild(
                "build already rejected (ABORT→reject build); refuse concurrent build"
            )

        results: list[Mapping[str, Any] | bytes | str] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(builder), pool.submit(builder)]
            for fut in concurrent.futures.as_completed(futs):
                results.append(fut.result())
        if len(results) != 2:
            raise ParityError(f"expected 2 concurrent results; got {len(results)}")

        side_a, side_b = self._sides()
        art_a = self.record_build(side_a, results[0], mode=mode)
        art_b = self.record_build(side_b, results[1], mode=mode)
        check = self.check(auto_reject=auto_reject, mode=mode)
        return ConcurrentBuildResult(
            ok=check.ok,
            parity_ok=check.parity_ok,
            digest_a=art_a.digest_sha256,
            digest_b=art_b.digest_sha256,
            byte_equal=art_a.digest_sha256 == art_b.digest_sha256 and check.parity_ok,
            mismatch_paths=list(check.mismatch_paths),
            build_rejected=check.build_rejected,
            abort_reject_build=check.abort_reject_build,
            toolchain_pin_hash=check.toolchain_pin_hash,
            error=check.error,
            error_code=check.error_code,
        )

    def core_parity_vs_single(
        self,
        n2_checksums: Mapping[str, str],
        single_checksums: Mapping[str, str],
        *,
        paths: Sequence[str] | None = None,
        auto_reject: bool = True,
        mode: str = "local",
    ) -> ParityCheckResult:
        """Extend manifest_n2.core_parity_checksums with ABORT→reject build."""
        require_no_plaintext(mode)
        use_paths = list(paths) if paths is not None else list(CORE_PARITY_CANDIDATES)
        ok, errs = core_parity_checksums(
            n2_checksums, single_checksums, paths=use_paths
        )
        if ok:
            # Synthesize matched digests from shared core set
            material = json.dumps(
                {p: n2_checksums.get(p) for p in use_paths if p in n2_checksums},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            digest = _sha256_hex(material)
            self.store.mark_match(digest, digest)
            return ParityCheckResult(
                ok=True,
                outcome="matched",
                parity_ok=True,
                digest_a=digest,
                digest_b=digest,
                toolchain_pin_hash=str(
                    (self.store.state().get("toolchain") or {}).get("pin_hash") or ""
                ),
                reason="core_parity vs single-node matched",
                action="none",
            )
        paths_bad = [e.split(" for ")[-1].split(":")[0] for e in errs]
        # Fallback: use error strings as paths if parse odd
        if not paths_bad:
            paths_bad = list(errs)
        self.store.mark_pending(paths_bad)
        if auto_reject:
            self.abort_reject_build(
                reason=f"ABORT→reject build: core_parity mismatch {errs}",
                mode=mode,
            )
            return ParityCheckResult(
                ok=False,
                outcome="mismatch",
                parity_ok=False,
                build_rejected=True,
                abort_reject_build=True,
                mismatch_paths=paths_bad,
                reason="core_parity mismatch; ABORT→reject build",
                error="core_parity mismatch; ABORT→reject build",
                error_code="PARITY_MISMATCH",
                action="abort_reject_build",
            )
        self.store.enter_abort(
            f"core_parity mismatch; auto_reject=false: {errs}",
            paths=paths_bad,
        )
        return ParityCheckResult(
            ok=False,
            outcome="mismatch",
            parity_ok=False,
            mismatch_detected=True,
            build_rejected=True,
            abort_reject_build=True,
            mismatch_paths=paths_bad,
            reason="core_parity mismatch unresolved",
            error="core_parity mismatch",
            error_code="PARITY_MISMATCH",
            action="abort_reject_build",
        )


__all__ = [
    "ParityService",
    "canonical_manifest_bytes",
    "compare_checksum_maps",
    "compute_toolchain_pin",
    "require_no_plaintext",
    "core_parity_checksums",
    "CORE_PARITY_CANDIDATES",
]
