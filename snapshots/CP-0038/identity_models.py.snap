"""Identity + trust-tier models (Cycle 34 / CP-0038 / H1).

Schema: mesh.identity/v1
Policy: docs/policy/trust-tiers-v1.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


SCHEMA_ID = "mesh.identity/v1"
SCHEMA_STORE = "mesh.identity.store/v1"


class TrustTier(IntEnum):
    """Trust tiers T0..T3 (see docs/policy/trust-tiers-v1.md)."""

    T0 = 0  # untrusted / revoked / unknown
    T1 = 1  # provisional (TOFU first-seen)
    T2 = 2  # attested under local CA
    T3 = 3  # pinned / operator-confirmed


TIER_NAMES = {t: f"T{t.value}" for t in TrustTier}
TIER_MIN = TrustTier.T0
TIER_MAX = TrustTier.T3


class IdentityError(RuntimeError):
    """Base identity / attestation error (fail-closed)."""

    code: str = "IDENTITY_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class IdentityMismatch(IdentityError):
    code = "IDENTITY_MISMATCH"


class IdentityAttestationFailed(IdentityError):
    code = "IDENTITY_ATTESTATION_FAILED"


class IdentityTierError(IdentityError):
    code = "IDENTITY_TIER_ERROR"


class IdentityRevoked(IdentityError):
    code = "IDENTITY_REVOKED"


class IdentityPinnedOnlyAbort(IdentityError):
    """ABORT→pinned-only: only pinned fingerprints are accepted."""

    code = "IDENTITY_PINNED_ONLY"


class IdentityPlaintextForbidden(IdentityError):
    code = "IDENTITY_PLAINTEXT_FORBIDDEN"


def parse_tier(value: int | str | TrustTier) -> TrustTier:
    """Parse tier from int, 'T2', 't2', or TrustTier. Bounds T0..T3."""
    if isinstance(value, TrustTier):
        return value
    if isinstance(value, int):
        if value < TIER_MIN or value > TIER_MAX:
            raise IdentityTierError(
                f"tier out of bounds: {value} (allowed T0..T3)",
                code="IDENTITY_TIER_BOUNDS",
            )
        return TrustTier(value)
    s = str(value).strip().upper()
    if s.startswith("T") and s[1:].isdigit():
        return parse_tier(int(s[1:]))
    if s.isdigit():
        return parse_tier(int(s))
    raise IdentityTierError(
        f"invalid tier: {value!r} (allowed T0..T3)",
        code="IDENTITY_TIER_BOUNDS",
    )


@dataclass
class NodeIdentityRecord:
    """Persisted node identity record (mesh.identity/v1)."""

    node_id: str
    cert_fingerprint: str = ""
    cert_path: str = ""
    key_path: str = ""
    ca_cert_path: str = ""
    tier: int = int(TrustTier.T0)
    revoked: bool = False
    pinned: bool = False
    pinned_fingerprint: str = ""
    revoked_fingerprints: list[str] = field(default_factory=list)
    prior_fingerprints: list[str] = field(default_factory=list)
    attested_at: str | None = None
    updated_at: str | None = None
    notes: str = ""
    schema: str = SCHEMA_ID
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0

    def trust_tier(self) -> TrustTier:
        return parse_tier(self.tier)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tier_name"] = TIER_NAMES[self.trust_tier()]
        d["dual_primary"] = 0
        d["vault_acme_required"] = 0
        d["plaintext_fallback"] = 0
        d["schema"] = SCHEMA_ID
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeIdentityRecord":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        rec = cls(**kwargs)
        # normalize tier
        rec.tier = int(parse_tier(rec.tier))
        rec.dual_primary = 0
        rec.vault_acme_required = 0
        rec.plaintext_fallback = 0
        rec.schema = SCHEMA_ID
        return rec


@dataclass
class AttestationResult:
    """Result of a local-CA attestation attempt."""

    ok: bool
    node_id: str
    cert_fingerprint: str = ""
    identities: list[str] = field(default_factory=list)
    tier: int = int(TrustTier.T0)
    tier_name: str = "T0"
    ca_verified: bool = False
    error: str | None = None
    error_code: str | None = None
    pinned_only: bool = False
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IdentityStatus:
    """Operator-facing identity status snapshot."""

    node_id: str
    record: dict[str, Any] | None
    pinned_only: bool
    store_path: str
    fabric_root: str
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    schema: str = SCHEMA_ID
    ok: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "TrustTier",
    "TIER_NAMES",
    "TIER_MIN",
    "TIER_MAX",
    "IdentityError",
    "IdentityMismatch",
    "IdentityAttestationFailed",
    "IdentityTierError",
    "IdentityRevoked",
    "IdentityPinnedOnlyAbort",
    "IdentityPlaintextForbidden",
    "parse_tier",
    "NodeIdentityRecord",
    "AttestationResult",
    "IdentityStatus",
]
