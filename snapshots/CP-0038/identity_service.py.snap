"""Identity service: attest / tier / rotate / revoke / pinned-only abort.

Builds on ``neural_mesh.network.tls`` LocalCA leafs (CN/SAN = node_id).
No Vault/ACME required. Fail-closed. dual_primary hard 0.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from neural_mesh.network.tls import LocalCA, NodeCertPaths, CertBootstrapError

from .models import (
    SCHEMA_ID,
    AttestationResult,
    IdentityAttestationFailed,
    IdentityError,
    IdentityMismatch,
    IdentityPinnedOnlyAbort,
    IdentityRevoked,
    IdentityStatus,
    IdentityTierError,
    NodeIdentityRecord,
    TrustTier,
    parse_tier,
)
from .store import IdentityStore, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cert_fingerprint(cert_path: str | Path) -> str:
    """SHA-256 hex fingerprint of leaf cert PEM bytes."""
    data = Path(cert_path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def _openssl_text(cert_path: Path) -> str:
    try:
        proc = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-noout", "-subject", "-ext", "subjectAltName"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise IdentityAttestationFailed("openssl not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise IdentityAttestationFailed(
            f"openssl failed reading cert: {exc.stderr or exc.stdout or exc}"
        ) from exc
    return (proc.stdout or "") + (proc.stderr or "")


def cert_identities(cert_path: str | Path) -> list[str]:
    """Extract CN + DNS SANs from a PEM leaf (openssl)."""
    text = _openssl_text(Path(cert_path))
    ids: list[str] = []
    # subject=CN = node-01  OR  subject= /CN=node-01
    for m in re.finditer(r"(?:/CN=|CN\s*=\s*)([^/\n,]+)", text):
        v = m.group(1).strip()
        if v:
            ids.append(v)
    for m in re.finditer(r"DNS:([^,\s]+)", text):
        v = m.group(1).strip()
        if v:
            ids.append(v)
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def verify_cert_against_ca(cert_path: Path, ca_cert: Path) -> bool:
    """openssl verify -CAfile; fail-closed on error."""
    try:
        proc = subprocess.run(
            ["openssl", "verify", "-CAfile", str(ca_cert), str(cert_path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise IdentityAttestationFailed("openssl not found on PATH") from exc
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0 and "OK" in out


def resolve_leaf_paths(fabric_root: str | Path, node_id: str) -> NodeCertPaths:
    root = Path(fabric_root)
    ca_cert = root / "ca.crt"
    node_dir = root / "nodes" / node_id
    return NodeCertPaths(
        node_id=node_id,
        ca_cert=ca_cert,
        cert=node_dir / "node.crt",
        key=node_dir / "node.key",
    )


class IdentityService:
    """H1 identity + attestation + trust tiers around a LocalCA fabric root."""

    def __init__(
        self,
        fabric_root: str | Path,
        *,
        store_root: str | Path | None = None,
        node_id: str | None = None,
    ):
        self.fabric_root = Path(fabric_root)
        sr = Path(store_root) if store_root else self.fabric_root / "identity"
        self.store = IdentityStore(sr)
        self.local_node_id = node_id

    # --- status ---

    def status(self, node_id: str | None = None) -> IdentityStatus:
        nid = node_id or self.local_node_id
        if not nid:
            raise IdentityError("node_id required for status")
        rec = self.store.load(nid)
        issues: list[str] = []
        paths = resolve_leaf_paths(self.fabric_root, nid)
        if not paths.cert.is_file():
            issues.append("missing_leaf_cert")
        if not paths.key.is_file():
            issues.append("missing_leaf_key")
        if not paths.ca_cert.is_file():
            issues.append("missing_ca_cert")
        if rec and rec.revoked:
            issues.append("revoked")
        if self.store.pinned_only:
            issues.append("pinned_only_abort")
        ok = not any(
            x in issues
            for x in ("missing_leaf_cert", "missing_leaf_key", "missing_ca_cert", "revoked")
        )
        return IdentityStatus(
            node_id=nid,
            record=rec.to_dict() if rec else None,
            pinned_only=self.store.pinned_only,
            store_path=str(self.store.root),
            fabric_root=str(self.fabric_root),
            dual_primary=0,
            vault_acme_required=0,
            plaintext_fallback=0,
            schema=SCHEMA_ID,
            ok=ok,
            issues=issues,
        )

    # --- attest ---

    def attest(
        self,
        node_id: str,
        *,
        expected_node_id: str | None = None,
        mode: str | None = "tls",
        allow_upgrade: bool = True,
    ) -> AttestationResult:
        """Fail-closed local-CA attestation. Mismatch → reject (+ optional pinned-only)."""
        require_no_plaintext(mode)
        expected = expected_node_id or node_id
        paths = resolve_leaf_paths(self.fabric_root, node_id)

        if not paths.cert.is_file() or not paths.key.is_file():
            self._maybe_abort_pinned(f"missing cert/key for {node_id}")
            return AttestationResult(
                ok=False,
                node_id=node_id,
                error="missing leaf cert or key",
                error_code="IDENTITY_ATTESTATION_FAILED",
                pinned_only=self.store.pinned_only,
            )

        if not paths.ca_cert.is_file():
            self._maybe_abort_pinned(f"missing CA for {node_id}")
            return AttestationResult(
                ok=False,
                node_id=node_id,
                error="missing local CA cert",
                error_code="IDENTITY_ATTESTATION_FAILED",
                pinned_only=self.store.pinned_only,
            )

        existing = self.store.load(node_id)
        if existing and existing.revoked:
            raise IdentityRevoked(f"identity revoked: {node_id}")

        try:
            ids = cert_identities(paths.cert)
            fp = cert_fingerprint(paths.cert)
            ca_ok = verify_cert_against_ca(paths.cert, paths.ca_cert)
        except IdentityAttestationFailed as exc:
            self._maybe_abort_pinned(str(exc))
            return AttestationResult(
                ok=False,
                node_id=node_id,
                error=str(exc),
                error_code=exc.code,
                pinned_only=self.store.pinned_only,
            )

        if expected not in ids:
            self._maybe_abort_pinned(
                f"peer identity mismatch: expected {expected}, got {ids}"
            )
            raise IdentityMismatch(
                f"peer identity mismatch: expected {expected}, got {ids}"
            )

        if not ca_ok:
            self._maybe_abort_pinned(f"CA verify failed for {node_id}")
            raise IdentityAttestationFailed(
                f"leaf not signed by local CA: {node_id}"
            )

        # pinned-only: only accept pinned fingerprints
        if self.store.pinned_only:
            pinned_ok = False
            if existing and existing.pinned and existing.pinned_fingerprint:
                pinned_ok = fp == existing.pinned_fingerprint
            if not pinned_ok:
                # also allow any record with matching pinned_fingerprint across store
                for rec in self.store.all_records():
                    if rec.pinned and rec.pinned_fingerprint == fp and rec.node_id == node_id:
                        pinned_ok = True
                        break
            if not pinned_ok:
                raise IdentityPinnedOnlyAbort(
                    f"pinned-only abort: fingerprint not in pin set for {node_id}"
                )

        # revoked fingerprint check
        if existing and fp in (existing.revoked_fingerprints or []):
            raise IdentityRevoked(
                f"fingerprint revoked for {node_id}: {fp[:16]}..."
            )

        now = _utcnow()
        if existing is None:
            rec = NodeIdentityRecord(
                node_id=node_id,
                cert_fingerprint=fp,
                cert_path=str(paths.cert),
                key_path=str(paths.key),
                ca_cert_path=str(paths.ca_cert),
                tier=int(TrustTier.T2) if allow_upgrade else int(TrustTier.T1),
                attested_at=now,
                updated_at=now,
            )
        else:
            prior = list(existing.prior_fingerprints or [])
            if existing.cert_fingerprint and existing.cert_fingerprint != fp:
                if existing.cert_fingerprint not in prior:
                    prior.append(existing.cert_fingerprint)
            tier = existing.trust_tier()
            # attestation promotes to at least T2 (never silent downgrade)
            if allow_upgrade and tier < TrustTier.T2:
                tier = TrustTier.T2
            rec = NodeIdentityRecord(
                node_id=node_id,
                cert_fingerprint=fp,
                cert_path=str(paths.cert),
                key_path=str(paths.key),
                ca_cert_path=str(paths.ca_cert),
                tier=int(tier),
                revoked=False,
                pinned=existing.pinned,
                pinned_fingerprint=existing.pinned_fingerprint
                or (fp if existing.pinned else ""),
                revoked_fingerprints=list(existing.revoked_fingerprints or []),
                prior_fingerprints=prior,
                attested_at=now,
                updated_at=now,
                notes=existing.notes,
            )
        self.store.save(rec)
        return AttestationResult(
            ok=True,
            node_id=node_id,
            cert_fingerprint=fp,
            identities=ids,
            tier=rec.tier,
            tier_name=f"T{rec.tier}",
            ca_verified=True,
            pinned_only=self.store.pinned_only,
        )

    def _maybe_abort_pinned(self, reason: str) -> None:
        """On attestation abort path, enter pinned-only mode (H1 ABORT)."""
        self.store.enter_pinned_only(reason)

    # --- tiers ---

    def get_tier(self, node_id: str) -> TrustTier:
        rec = self.store.load(node_id)
        if rec is None:
            return TrustTier.T0
        return rec.trust_tier()

    def set_tier(
        self,
        node_id: str,
        tier: int | str | TrustTier,
        *,
        reason: str = "",
        pin: bool = False,
    ) -> NodeIdentityRecord:
        """Assign tier with bounds. Upgrade to T3 requires pin; no silent escalate past attested."""
        target = parse_tier(tier)
        rec = self.store.load(node_id)
        if rec is None:
            # create provisional record at requested tier only if T0/T1
            if target > TrustTier.T1 and not pin:
                raise IdentityTierError(
                    "cannot assign >T1 without existing attested record "
                    "(attest first, or pin=True for T3)",
                )
            paths = resolve_leaf_paths(self.fabric_root, node_id)
            fp = ""
            if paths.cert.is_file():
                fp = cert_fingerprint(paths.cert)
            rec = NodeIdentityRecord(
                node_id=node_id,
                cert_fingerprint=fp,
                cert_path=str(paths.cert) if paths.cert.is_file() else "",
                key_path=str(paths.key) if paths.key.is_file() else "",
                ca_cert_path=str(paths.ca_cert) if paths.ca_cert.is_file() else "",
                tier=int(target),
                updated_at=_utcnow(),
                notes=reason,
            )
        else:
            current = rec.trust_tier()
            # upgrades above T2 require pin (T3) or prior attestation path
            if target > current:
                if target == TrustTier.T3:
                    if not pin and not rec.pinned:
                        raise IdentityTierError(
                            "upgrade to T3 requires pin=True (operator pin)",
                        )
                elif target >= TrustTier.T2 and not rec.attested_at and not rec.cert_fingerprint:
                    raise IdentityTierError(
                        "upgrade to T2+ requires attestation first",
                    )
            # downgrade T3→T2→T1→T0 always allowed (P-10)
            rec.tier = int(target)
            rec.updated_at = _utcnow()
            if reason:
                rec.notes = reason
        if target == TrustTier.T3 or pin:
            rec.pinned = True
            if rec.cert_fingerprint:
                rec.pinned_fingerprint = rec.cert_fingerprint
            elif pin:
                paths = resolve_leaf_paths(self.fabric_root, node_id)
                if paths.cert.is_file():
                    rec.cert_fingerprint = cert_fingerprint(paths.cert)
                    rec.pinned_fingerprint = rec.cert_fingerprint
        if target < TrustTier.T3 and not pin:
            # downgrade from T3 clears pin flag but keeps pinned_fingerprint history
            if rec.trust_tier() < TrustTier.T3:
                rec.pinned = False
        self.store.save(rec)
        return rec

    def downgrade(
        self, node_id: str, *, reason: str = "downgrade"
    ) -> NodeIdentityRecord:
        """Explicit one-step downgrade T3→T2→T1→T0 (P-10)."""
        rec = self.store.load(node_id)
        if rec is None:
            raise IdentityError(f"no identity record for {node_id}")
        current = rec.trust_tier()
        if current == TrustTier.T0:
            return rec
        return self.set_tier(node_id, TrustTier(int(current) - 1), reason=reason)

    # --- rotate / revoke ---

    def rotate(
        self, node_id: str, *, days: int = 825, keep_tier: bool = True
    ) -> NodeIdentityRecord:
        """Rotate leaf under local CA. Does **not** silent-downgrade identity.

        Prior fingerprint is retained in ``prior_fingerprints``. Tier kept if
        ``keep_tier`` and re-attest succeeds; otherwise stays at prior tier
        until operator downgrade (never silent).
        """
        if not (self.fabric_root / "ca.crt").is_file():
            raise IdentityAttestationFailed(
                "local CA missing; cannot rotate (Vault/ACME not required — bootstrap LocalCA)"
            )
        try:
            ca = LocalCA.create(self.fabric_root)
            paths = ca.rotate_node(node_id, days=days)
        except CertBootstrapError as exc:
            raise IdentityAttestationFailed(str(exc)) from exc

        existing = self.store.load(node_id)
        new_fp = cert_fingerprint(paths.cert)
        prior: list[str] = []
        tier = TrustTier.T2
        pinned = False
        pinned_fp = ""
        revoked_fps: list[str] = []
        if existing:
            prior = list(existing.prior_fingerprints or [])
            if existing.cert_fingerprint and existing.cert_fingerprint != new_fp:
                if existing.cert_fingerprint not in prior:
                    prior.append(existing.cert_fingerprint)
            tier = existing.trust_tier() if keep_tier else TrustTier.T2
            # never silent-downgrade: keep_tier preserves tier
            pinned = existing.pinned
            pinned_fp = existing.pinned_fingerprint
            revoked_fps = list(existing.revoked_fingerprints or [])
            # if was pinned, update pin to new fingerprint (explicit rotation)
            if pinned:
                pinned_fp = new_fp

        # verify new cert identities
        ids = cert_identities(paths.cert)
        if node_id not in ids:
            raise IdentityMismatch(
                f"rotated cert identity mismatch: expected {node_id}, got {ids}"
            )
        if not verify_cert_against_ca(paths.cert, paths.ca_cert):
            raise IdentityAttestationFailed("rotated leaf failed CA verify")

        now = _utcnow()
        rec = NodeIdentityRecord(
            node_id=node_id,
            cert_fingerprint=new_fp,
            cert_path=str(paths.cert),
            key_path=str(paths.key),
            ca_cert_path=str(paths.ca_cert),
            tier=int(tier),
            revoked=False,
            pinned=pinned,
            pinned_fingerprint=pinned_fp,
            revoked_fingerprints=revoked_fps,
            prior_fingerprints=prior,
            attested_at=now,
            updated_at=now,
            notes="rotated",
        )
        self.store.save(rec)
        return rec

    def revoke(
        self, node_id: str, *, reason: str = "revoked"
    ) -> NodeIdentityRecord:
        """Revoke identity: mark revoked, force T0, record fingerprint.

        Does not silent-downgrade without recording — revocation is explicit.
        """
        rec = self.store.load(node_id)
        paths = resolve_leaf_paths(self.fabric_root, node_id)
        fp = ""
        if paths.cert.is_file():
            fp = cert_fingerprint(paths.cert)
        if rec is None:
            rec = NodeIdentityRecord(
                node_id=node_id,
                cert_fingerprint=fp,
                cert_path=str(paths.cert) if paths.cert.is_file() else "",
                key_path=str(paths.key) if paths.key.is_file() else "",
                ca_cert_path=str(paths.ca_cert) if paths.ca_cert.is_file() else "",
            )
        revoked_fps = list(rec.revoked_fingerprints or [])
        if rec.cert_fingerprint and rec.cert_fingerprint not in revoked_fps:
            revoked_fps.append(rec.cert_fingerprint)
        if fp and fp not in revoked_fps:
            revoked_fps.append(fp)
        rec.revoked = True
        rec.tier = int(TrustTier.T0)
        rec.pinned = False
        rec.revoked_fingerprints = revoked_fps
        rec.updated_at = _utcnow()
        rec.notes = reason
        self.store.save(rec)
        # revocation of a peer can trigger pinned-only abort for safety
        self.store.enter_pinned_only(f"revoke:{node_id}:{reason}")
        return rec

    def enter_pinned_only(self, reason: str) -> dict[str, Any]:
        return self.store.enter_pinned_only(reason)

    def clear_pinned_only(self) -> dict[str, Any]:
        return self.store.clear_pinned_only()


__all__ = [
    "IdentityService",
    "cert_fingerprint",
    "cert_identities",
    "verify_cert_against_ca",
    "resolve_leaf_paths",
]
