"""Packaging distribution models (Cycle 38 / CP-0042 / H5).

Schema: mesh.bundle/v1
Capability: docs/capabilities/MESH_PACKAGING_DISTRIBUTION.md
ABORT→pin prior on schema/invariant/replay/signature breach.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_ID = "mesh.bundle/v1"
SCHEMA_TOOLCHAIN = "mesh.bundle.toolchain/v1"
SCHEMA_PROVENANCE = "mesh.bundle.provenance/v1"
SCHEMA_SIGNATURE = "mesh.bundle.signature/v1"
SCHEMA_PRIOR_PIN = "mesh.bundle.prior_pin/v1"
SOURCE_MANIFEST_SCHEMA = "mesh.bundle.manifest/v1"
SOURCE_MANIFEST_SCHEMA_N2 = "mesh.bundle.manifest/v1-n2"

# Distribution channel for 0.18.x — never reopen frozen RC archives.
DIST_CHANNEL = "0.18.x"
FROZEN_CHANNELS = frozenset({"0.16.3", "0.16.x", "0.17.0", "0.17.x-n2"})
PRIOR_PIN_DEFAULT_VER = "0.17.0"
PRIOR_PIN_DEFAULT_LABEL = "dist/releases/0.17.0"

LOCAL_SIGN_ALG = "hmac-sha256-local"
LOCAL_KEY_ID = "mesh-dist-local-v1"
# Local-only key material (NOT Vault/ACME). Deterministic for repro; fail-closed
# verify refuses unknown algs / key ids.
LOCAL_KEY_MATERIAL = b"neural-mesh-gia-dist-local-v1-NO-VAULT"

REQUIRED_TOP_FIELDS = (
    "schema",
    "bundle_id",
    "ver",
    "channel",
    "name",
    "cp_tip",
    "cp_range",
    "entrypoint",
    "checksums",
    "bundle_sha256",
    "signature",
    "provenance",
    "replay_nonce",
    "toolchain",
    "dual_primary",
    "plaintext_fallback",
    "vault_acme_required",
)


class DistError(RuntimeError):
    """Base packaging-distribution error (fail-closed)."""

    code: str = "DIST_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class DistSchemaMismatch(DistError):
    code = "DIST_SCHEMA_MISMATCH"


class DistInvariantBreach(DistError):
    code = "DIST_INVARIANT_BREACH"


class DistAbortPinPrior(DistError):
    """ABORT→pin prior on distribution breach."""

    code = "DIST_ABORT_PIN_PRIOR"


class DistReplayDetected(DistError):
    code = "DIST_REPLAY_DETECTED"


class DistSignatureInvalid(DistError):
    code = "DIST_SIGNATURE_INVALID"


class DistToolchainMismatch(DistError):
    code = "DIST_TOOLCHAIN_MISMATCH"


class DistFrozenChannel(DistError):
    """Refuse reopen of frozen 0.16.3 / 0.17.0 channels."""

    code = "DIST_FROZEN_CHANNEL"


class DistPlaintextForbidden(DistError):
    code = "DIST_PLAINTEXT_FORBIDDEN"


class DistN2Only(DistError):
    """N>2 / Raft refused for distribution."""

    code = "DIST_N2_ONLY"


@dataclass
class DistToolchain:
    """P-09 toolchain pin: compiler + libc + locale → pin_hash."""

    compiler: str = "cpython"
    libc: str = "host"
    locale: str = "C.UTF-8"
    pin_hash: str = ""
    schema: str = SCHEMA_TOOLCHAIN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_TOOLCHAIN
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DistToolchain":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        tc = cls(**kwargs)
        tc.schema = SCHEMA_TOOLCHAIN
        return tc


@dataclass
class DistSignature:
    """Signed-manifest envelope (local HMAC; no Vault/ACME required)."""

    alg: str = LOCAL_SIGN_ALG
    key_id: str = LOCAL_KEY_ID
    value: str = ""
    schema: str = SCHEMA_SIGNATURE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_SIGNATURE
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DistSignature":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        sig = cls(**kwargs)
        sig.schema = SCHEMA_SIGNATURE
        return sig


@dataclass
class DistProvenanceStep:
    """One link in the provenance chain (H5.b)."""

    parent_bundle_id: str | None = None
    parent_sha256: str | None = None
    step: str = "mint"
    at: str | None = None
    schema: str = SCHEMA_PROVENANCE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_PROVENANCE
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DistProvenanceStep":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        step = cls(**kwargs)
        step.schema = SCHEMA_PROVENANCE
        return step


@dataclass
class DistPriorPin:
    """Pinned prior known-good distribution (ABORT→pin prior target)."""

    ver: str = PRIOR_PIN_DEFAULT_VER
    bundle_id: str = ""
    sha256: str = ""
    label: str = PRIOR_PIN_DEFAULT_LABEL
    schema: str = SCHEMA_PRIOR_PIN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_PRIOR_PIN
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DistPriorPin":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        pin = cls(**kwargs)
        pin.schema = SCHEMA_PRIOR_PIN
        return pin


@dataclass
class DistributionDocument:
    """mesh.bundle/v1 distribution document (packaging as distribution primitive)."""

    schema: str = SCHEMA_ID
    bundle_id: str = ""
    ver: str = "0.18.0"
    channel: str = DIST_CHANNEL
    name: str = "neural-mesh-gia-dist"
    tip: str | None = None
    cp_tip: str = "CP-0042"
    cp_range: str = "CP-0001..0042"
    entrypoint: str = "mesh"
    checksums: dict[str, str] = field(default_factory=dict)
    bundle_sha256: str = ""
    signature: DistSignature = field(default_factory=DistSignature)
    provenance: list[DistProvenanceStep] = field(default_factory=list)
    replay_nonce: str = ""
    replay_seen: bool = False
    toolchain: DistToolchain = field(default_factory=DistToolchain)
    revoked: bool = False
    prior_pin: DistPriorPin | None = None
    dual_primary: int = 0
    plaintext_fallback: int = 0
    vault_acme_required: int = 0
    invariants_ok: bool = True
    abort_pin_prior: bool = False
    source_manifest_schema: str = SOURCE_MANIFEST_SCHEMA
    cycle: int = 38
    created_utc: str | None = None
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_ID,
            "bundle_id": self.bundle_id,
            "ver": self.ver,
            "channel": self.channel,
            "name": self.name,
            "tip": self.tip,
            "cp_tip": self.cp_tip,
            "cp_range": self.cp_range,
            "entrypoint": self.entrypoint,
            "checksums": dict(self.checksums),
            "bundle_sha256": self.bundle_sha256,
            "signature": self.signature.to_dict(),
            "provenance": [p.to_dict() for p in self.provenance],
            "replay_nonce": self.replay_nonce,
            "replay_seen": bool(self.replay_seen),
            "toolchain": self.toolchain.to_dict(),
            "revoked": bool(self.revoked),
            "prior_pin": self.prior_pin.to_dict() if self.prior_pin else None,
            "dual_primary": 0,
            "plaintext_fallback": 0,
            "vault_acme_required": 0,
            "invariants_ok": bool(self.invariants_ok),
            "abort_pin_prior": bool(self.abort_pin_prior),
            "source_manifest_schema": self.source_manifest_schema,
            "cycle": int(self.cycle),
            "created_utc": self.created_utc,
            "files": list(self.files),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DistributionDocument":
        data = dict(data)
        sig = DistSignature.from_dict(data.get("signature") if isinstance(data.get("signature"), dict) else {})
        tc = DistToolchain.from_dict(data.get("toolchain") if isinstance(data.get("toolchain"), dict) else {})
        prov_raw = data.get("provenance") or []
        provenance = [
            DistProvenanceStep.from_dict(p) if isinstance(p, dict) else DistProvenanceStep()
            for p in prov_raw
        ]
        prior = None
        if isinstance(data.get("prior_pin"), dict):
            prior = DistPriorPin.from_dict(data["prior_pin"])
        return cls(
            schema=str(data.get("schema") or SCHEMA_ID),
            bundle_id=str(data.get("bundle_id") or ""),
            ver=str(data.get("ver") or "0.18.0"),
            channel=str(data.get("channel") or DIST_CHANNEL),
            name=str(data.get("name") or "neural-mesh-gia-dist"),
            tip=data.get("tip"),
            cp_tip=str(data.get("cp_tip") or "CP-0042"),
            cp_range=str(data.get("cp_range") or "CP-0001..0042"),
            entrypoint=str(data.get("entrypoint") or "mesh"),
            checksums=dict(data.get("checksums") or {}),
            bundle_sha256=str(data.get("bundle_sha256") or ""),
            signature=sig,
            provenance=provenance,
            replay_nonce=str(data.get("replay_nonce") or ""),
            replay_seen=bool(data.get("replay_seen", False)),
            toolchain=tc,
            revoked=bool(data.get("revoked", False)),
            prior_pin=prior,
            dual_primary=0,
            plaintext_fallback=0,
            vault_acme_required=0,
            invariants_ok=bool(data.get("invariants_ok", True)),
            abort_pin_prior=bool(data.get("abort_pin_prior", False)),
            source_manifest_schema=str(
                data.get("source_manifest_schema") or SOURCE_MANIFEST_SCHEMA
            ),
            cycle=int(data.get("cycle") or 38),
            created_utc=data.get("created_utc"),
            files=list(data.get("files") or []),
        )


def schema_descriptor() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "channel": DIST_CHANNEL,
        "frozen_channels": sorted(FROZEN_CHANNELS),
        "toolchain_schema": SCHEMA_TOOLCHAIN,
        "provenance_schema": SCHEMA_PROVENANCE,
        "signature_schema": SCHEMA_SIGNATURE,
        "prior_pin_schema": SCHEMA_PRIOR_PIN,
        "source_manifest_schemas": [SOURCE_MANIFEST_SCHEMA, SOURCE_MANIFEST_SCHEMA_N2],
        "ops": ["distribute", "verify", "pin-prior", "schema"],
        "tests": ["T-H5a", "T-H5b", "T-H5c", "T-H5d", "T-H5e", "T-H5f"],
        "abort": "pin prior",
        "sign_alg": LOCAL_SIGN_ALG,
        "p09": "toolchain pin (compiler+libc+locale → pin_hash)",
        "deprecation_note": (
            "mesh.bundle.manifest/v1 and v1-n2 remain ACTIVE for single/N2 "
            "archive manifests; mesh.bundle/v1 is the distribution primitive "
            "(sign/provenance/replay/revocation). Do not reopen 0.16.3 / 0.17.0."
        ),
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
