"""Mesh identity + attestation + trust tiers (Cycle 34 / CP-0038 / H1).

Schema: mesh.identity/v1
Policy: docs/policy/trust-tiers-v1.md
CLI: mesh id status|attest|tier|rotate|revoke
"""

from .models import (
    SCHEMA_ID,
    SCHEMA_STORE,
    AttestationResult,
    IdentityAttestationFailed,
    IdentityError,
    IdentityMismatch,
    IdentityPinnedOnlyAbort,
    IdentityPlaintextForbidden,
    IdentityRevoked,
    IdentityStatus,
    IdentityTierError,
    NodeIdentityRecord,
    TrustTier,
    parse_tier,
)
from .service import (
    IdentityService,
    cert_fingerprint,
    cert_identities,
    resolve_leaf_paths,
    verify_cert_against_ca,
)
from .store import IdentityStore
from .cli_ops import (
    cmd_id_attest,
    cmd_id_revoke,
    cmd_id_rotate,
    cmd_id_status,
    cmd_id_tier,
)

__all__ = [
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "AttestationResult",
    "IdentityAttestationFailed",
    "IdentityError",
    "IdentityMismatch",
    "IdentityPinnedOnlyAbort",
    "IdentityPlaintextForbidden",
    "IdentityRevoked",
    "IdentityService",
    "IdentityStatus",
    "IdentityStore",
    "IdentityTierError",
    "NodeIdentityRecord",
    "TrustTier",
    "cert_fingerprint",
    "cert_identities",
    "cmd_id_attest",
    "cmd_id_revoke",
    "cmd_id_rotate",
    "cmd_id_status",
    "cmd_id_tier",
    "parse_tier",
    "resolve_leaf_paths",
    "verify_cert_against_ca",
]
