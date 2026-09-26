"""Distribute / verify / pin-prior for mesh.bundle/v1 (Cycle 38 / CP-0042 / H5).

ABORT→pin prior on schema, signature, replay, toolchain, or invariant breach.
Does not reopen 0.16.3 / 0.17.0 tags or frozen release archives.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .models import (
    DIST_CHANNEL,
    FROZEN_CHANNELS,
    LOCAL_KEY_ID,
    LOCAL_KEY_MATERIAL,
    LOCAL_SIGN_ALG,
    PRIOR_PIN_DEFAULT_LABEL,
    PRIOR_PIN_DEFAULT_VER,
    REQUIRED_TOP_FIELDS,
    SCHEMA_ID,
    SOURCE_MANIFEST_SCHEMA,
    DistAbortPinPrior,
    DistFrozenChannel,
    DistInvariantBreach,
    DistN2Only,
    DistPlaintextForbidden,
    DistPriorPin,
    DistProvenanceStep,
    DistReplayDetected,
    DistSchemaMismatch,
    DistSignature,
    DistSignatureInvalid,
    DistToolchain,
    DistToolchainMismatch,
    DistributionDocument,
    schema_descriptor,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_no_plaintext(mode: str | None = None) -> None:
    if mode and str(mode).lower() in ("plaintext", "plain", "cleartext"):
        raise DistPlaintextForbidden(
            f"plaintext mode forbidden for packaging distribution: {mode!r}"
        )


def require_n2_bound(*, n_nodes: int | None = None, claim_raft: bool = False) -> None:
    if claim_raft or (n_nodes is not None and n_nodes > 2):
        raise DistN2Only("packaging distribution refuses Raft / N>2")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_payload(doc: DistributionDocument | Mapping[str, Any]) -> bytes:
    """Canonical JSON for signing (signature.value stripped)."""
    if isinstance(doc, DistributionDocument):
        d = doc.to_dict()
    else:
        d = dict(doc)
    sig = dict(d.get("signature") or {})
    sig["value"] = ""
    d["signature"] = sig
    # Hard zeros in signed payload
    d["dual_primary"] = 0
    d["plaintext_fallback"] = 0
    d["vault_acme_required"] = 0
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_document(
    doc: DistributionDocument,
    *,
    key_material: bytes = LOCAL_KEY_MATERIAL,
    key_id: str = LOCAL_KEY_ID,
) -> DistSignature:
    payload = _canonical_payload(doc)
    value = hmac.new(key_material, payload, hashlib.sha256).hexdigest()
    return DistSignature(alg=LOCAL_SIGN_ALG, key_id=key_id, value=value)


def verify_signature(
    doc: DistributionDocument | Mapping[str, Any],
    *,
    key_material: bytes = LOCAL_KEY_MATERIAL,
) -> None:
    d = doc if isinstance(doc, DistributionDocument) else DistributionDocument.from_dict(dict(doc))
    sig = d.signature
    if sig.alg != LOCAL_SIGN_ALG:
        raise DistSignatureInvalid(f"unsupported signature alg: {sig.alg!r}")
    if sig.key_id != LOCAL_KEY_ID:
        raise DistSignatureInvalid(f"unknown signature key_id: {sig.key_id!r}")
    expected = sign_document(d, key_material=key_material, key_id=sig.key_id).value
    if not sig.value or not hmac.compare_digest(sig.value, expected):
        raise DistSignatureInvalid("signature mismatch (ABORT→pin prior)")


def compute_toolchain_pin(
    *,
    compiler: str | None = None,
    libc: str | None = None,
    locale: str | None = None,
) -> DistToolchain:
    """P-09: pin compiler+libc+locale → pin_hash."""
    comp = compiler or f"cpython-{sys.version_info.major}.{sys.version_info.minor}"
    lib = libc or (platform.libc_ver()[0] or "host")
    loc = locale or os.environ.get("LC_ALL") or os.environ.get("LANG") or "C.UTF-8"
    raw = f"{comp}|{lib}|{loc}|{SCHEMA_ID}".encode("utf-8")
    return DistToolchain(compiler=comp, libc=lib, locale=loc, pin_hash=_sha256_hex(raw))


def _read_repo_meta(repo: Path) -> dict[str, Any]:
    ver = "0.18.0"
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("version"):
                # version = "0.18.0"
                parts = line.split("=", 1)
                if len(parts) == 2:
                    ver = parts[1].strip().strip('"').strip("'")
                break
    cp_tip = "CP-0042"
    cp_path = repo / ".project_state" / "CHECKPOINT.json"
    if cp_path.is_file():
        try:
            state = json.loads(cp_path.read_text(encoding="utf-8"))
            cp_tip = str(state.get("last_checkpoint") or cp_tip)
            if state.get("version"):
                ver = str(state.get("version") or ver)
        except (OSError, json.JSONDecodeError):
            pass
    tip = None
    try:
        tip = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(repo),
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
            or None
        )
    except (OSError, subprocess.CalledProcessError):
        tip = None
    return {"ver": ver, "cp_tip": cp_tip, "tip": tip}


def _bundle_id(ver: str, channel: str, nonce: str) -> str:
    raw = f"{ver}|{channel}|{nonce}|{SCHEMA_ID}".encode("utf-8")
    return f"bundle-{_sha256_hex(raw)[:20]}"


def _replay_registry_path(root: Path) -> Path:
    return root / ".project_state" / "dist_replay_registry.json"


def _load_replay_registry(root: Path) -> set[str]:
    path = _replay_registry_path(root)
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("nonces") or [])
    except (OSError, json.JSONDecodeError, TypeError):
        return set()


def _save_replay_registry(root: Path, nonces: set[str]) -> None:
    path = _replay_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "mesh.bundle.replay_registry/v1", "nonces": sorted(nonces)}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prior_pin_path(root: Path) -> Path:
    return root / ".project_state" / "DIST_PRIOR_PIN.json"


def check_channel(channel: str) -> None:
    if channel in FROZEN_CHANNELS or channel.startswith("0.16.") or channel in (
        "0.17.0",
        "0.17.x",
        "0.17.x-n2",
    ):
        # Allow reading frozen as prior pin target, but refuse distribute onto them.
        raise DistFrozenChannel(
            f"refuse distribute onto frozen channel {channel!r}; "
            f"use {DIST_CHANNEL} (do not reopen 0.16.3 / 0.17.0)"
        )


def distribute(
    repo: str | Path,
    *,
    out_dir: str | Path | None = None,
    name: str = "neural-mesh-gia-dist",
    channel: str = DIST_CHANNEL,
    cycle: int = 38,
    parent: DistributionDocument | Mapping[str, Any] | None = None,
    files: Sequence[str] | None = None,
    mode: str | None = None,
    n_nodes: int | None = None,
    claim_raft: bool = False,
    register_replay: bool = True,
    toolchain: DistToolchain | None = None,
    cp_tip: str | None = None,
    ver: str | None = None,
) -> DistributionDocument:
    """Mint a mesh.bundle/v1 distribution document (T-H5a) with sign+provenance+replay+toolchain."""
    require_no_plaintext(mode)
    require_n2_bound(n_nodes=n_nodes, claim_raft=claim_raft)
    if channel != DIST_CHANNEL:
        check_channel(channel)

    root = Path(repo).resolve()
    meta = _read_repo_meta(root)
    ver_s = ver or str(meta["ver"] or "0.18.0")
    if not ver_s.startswith("0.18."):
        raise DistInvariantBreach(
            f"H5 distribution is for 0.18.x only; got ver={ver_s!r} "
            "(do not reopen 0.16.3 / 0.17.0)"
        )
    cp = cp_tip or str(meta["cp_tip"] or "CP-0042")
    tip = meta.get("tip")
    nonce = secrets.token_hex(16)
    tc = toolchain or compute_toolchain_pin()
    if not tc.pin_hash:
        tc = compute_toolchain_pin(compiler=tc.compiler, libc=tc.libc, locale=tc.locale)

    file_list = list(files or ["pyproject.toml", "src/neural_mesh/packaging/distribution"])
    checksums: dict[str, str] = {}
    for rel in file_list:
        p = root / rel
        if p.is_file():
            checksums[rel] = _sha256_hex(p.read_bytes())
        elif p.is_dir():
            # Directory marker hash from sorted file digests
            digests: list[str] = []
            for fp in sorted(p.rglob("*")):
                if fp.is_file() and "__pycache__" not in fp.parts:
                    digests.append(_sha256_hex(fp.read_bytes()))
            checksums[rel + "/"] = _sha256_hex("\n".join(digests).encode("utf-8"))

    bid = _bundle_id(ver_s, channel, nonce)
    body = json.dumps(
        {"bundle_id": bid, "checksums": checksums, "toolchain": tc.to_dict()},
        sort_keys=True,
    ).encode("utf-8")
    bundle_sha = _sha256_hex(body)

    provenance: list[DistProvenanceStep] = []
    if parent is not None:
        pdata = parent if isinstance(parent, DistributionDocument) else DistributionDocument.from_dict(dict(parent))
        provenance.append(
            DistProvenanceStep(
                parent_bundle_id=pdata.bundle_id,
                parent_sha256=pdata.bundle_sha256,
                step="derive",
                at=_utc_now(),
            )
        )
    else:
        provenance.append(
            DistProvenanceStep(
                parent_bundle_id=None,
                parent_sha256=None,
                step="mint",
                at=_utc_now(),
            )
        )

    doc = DistributionDocument(
        schema=SCHEMA_ID,
        bundle_id=bid,
        ver=ver_s,
        channel=channel,
        name=name,
        tip=tip,
        cp_tip=cp,
        cp_range=f"CP-0001..{cp.replace('CP-', '')}" if cp.startswith("CP-") else "CP-0001..0042",
        entrypoint="mesh",
        checksums=checksums,
        bundle_sha256=bundle_sha,
        provenance=provenance,
        replay_nonce=nonce,
        replay_seen=False,
        toolchain=tc,
        revoked=False,
        prior_pin=None,
        dual_primary=0,
        plaintext_fallback=0,
        vault_acme_required=0,
        invariants_ok=True,
        abort_pin_prior=False,
        source_manifest_schema=SOURCE_MANIFEST_SCHEMA,
        cycle=cycle,
        created_utc=_utc_now(),
        files=file_list,
    )
    doc.signature = sign_document(doc)

    # Replay registry stores *consumed* nonces only (H5.c). Mint does not consume.
    if register_replay:
        seen = _load_replay_registry(root)
        if nonce in seen:
            raise DistReplayDetected(f"replay nonce already consumed: {nonce}")

    # Write artifact under dist/releases/0.18.0/ (never into 0.16.3 / 0.17.0)
    dest_root = Path(out_dir) if out_dir else (root / "dist" / "releases" / ver_s)
    if "0.16.3" in dest_root.parts or "0.17.0" in dest_root.parts:
        raise DistFrozenChannel(
            f"refuse write into frozen release dir {dest_root}; use dist/releases/{ver_s}"
        )
    dest_root.mkdir(parents=True, exist_ok=True)
    out_path = dest_root / f"{name}-{ver_s}.bundle.json"
    out_path.write_text(document_to_json(doc), encoding="utf-8")
    sums_path = dest_root / "DIST_SHA256SUMS"
    line = f"{doc.bundle_sha256}  {out_path.name}\n"
    prev = sums_path.read_text(encoding="utf-8") if sums_path.is_file() else ""
    if line not in prev:
        sums_path.write_text(prev + line, encoding="utf-8")
    return doc


def validate_dict(
    data: Mapping[str, Any],
    *,
    abort_on_breach: bool = True,
    check_sig: bool = True,
    expected_toolchain: DistToolchain | None = None,
    replay_registry: set[str] | None = None,
) -> DistributionDocument:
    """Fail-closed schema + invariant validation (T-H5d/e/c)."""
    if not isinstance(data, Mapping):
        raise DistSchemaMismatch("distribution document must be a mapping")
    schema = data.get("schema")
    if schema != SCHEMA_ID:
        err = DistSchemaMismatch(f"expected schema {SCHEMA_ID}, got {schema!r}")
        if abort_on_breach:
            raise DistAbortPinPrior(str(err), code=err.code)
        raise err
    for field in REQUIRED_TOP_FIELDS:
        if field not in data:
            err = DistSchemaMismatch(f"missing required field: {field}")
            if abort_on_breach:
                raise DistAbortPinPrior(str(err), code=err.code)
            raise err

    doc = DistributionDocument.from_dict(dict(data))

    breaches: list[str] = []
    if doc.dual_primary != 0 or int(data.get("dual_primary", 0) or 0) != 0:
        breaches.append("dual_primary!=0")
    if doc.plaintext_fallback != 0 or int(data.get("plaintext_fallback", 0) or 0) != 0:
        breaches.append("plaintext_fallback!=0")
    if doc.vault_acme_required != 0 or int(data.get("vault_acme_required", 0) or 0) != 0:
        breaches.append("vault_acme_required!=0")
    if doc.channel in FROZEN_CHANNELS:
        breaches.append(f"frozen_channel={doc.channel}")
    if doc.revoked:
        breaches.append("revoked")
    if not doc.replay_nonce:
        breaches.append("empty_replay_nonce")
    if not doc.provenance:
        breaches.append("empty_provenance")
    if not doc.toolchain.pin_hash:
        breaches.append("empty_toolchain_pin")

    if expected_toolchain is not None:
        if doc.toolchain.pin_hash != expected_toolchain.pin_hash:
            err = DistToolchainMismatch(
                f"toolchain pin mismatch: got {doc.toolchain.pin_hash[:12]}… "
                f"expected {expected_toolchain.pin_hash[:12]}…"
            )
            if abort_on_breach:
                raise DistAbortPinPrior(str(err), code=err.code)
            raise err

    if replay_registry is not None and doc.replay_nonce in replay_registry and doc.replay_seen:
        err = DistReplayDetected(f"replay guard fired for nonce {doc.replay_nonce}")
        if abort_on_breach:
            raise DistAbortPinPrior(str(err), code=err.code)
        raise err

    if check_sig:
        try:
            verify_signature(doc)
        except DistSignatureInvalid as exc:
            if abort_on_breach:
                raise DistAbortPinPrior(str(exc), code=exc.code) from exc
            raise

    if breaches:
        doc.invariants_ok = False
        doc.abort_pin_prior = True
        err = DistInvariantBreach("invariant breach: " + ", ".join(breaches))
        if abort_on_breach:
            raise DistAbortPinPrior(str(err), code=err.code)
        raise err

    doc.invariants_ok = True
    doc.abort_pin_prior = False
    return doc


def verify_distribution(
    source: str | Path | Mapping[str, Any] | DistributionDocument,
    *,
    repo: str | Path | None = None,
    abort_on_breach: bool = True,
    mark_replay_seen: bool = False,
) -> DistributionDocument:
    """Verify a distribution document or JSON path (T-H5d + T-H5c)."""
    if isinstance(source, DistributionDocument):
        data = source.to_dict()
    elif isinstance(source, Mapping):
        data = dict(source)
    else:
        path = Path(source)
        data = json.loads(path.read_text(encoding="utf-8"))

    root = Path(repo).resolve() if repo else None
    registry = _load_replay_registry(root) if root is not None else set()

    nonce = str(data.get("replay_nonce") or "")
    # Consumed nonce presented again → replay (even without mark flag)
    if nonce and nonce in registry:
        err = DistReplayDetected(f"bundle replay detected for nonce {nonce}")
        if abort_on_breach:
            raise DistAbortPinPrior(str(err), code=err.code)
        raise err

    tc = None
    if root is not None:
        tc = compute_toolchain_pin()

    doc = validate_dict(
        data,
        abort_on_breach=abort_on_breach,
        check_sig=True,
        expected_toolchain=None,
        replay_registry=None,
    )
    _ = tc

    if mark_replay_seen and root is not None:
        seen = _load_replay_registry(root)
        if doc.replay_nonce in seen:
            doc.replay_seen = True
            err = DistReplayDetected(f"replay guard: nonce already consumed {doc.replay_nonce}")
            if abort_on_breach:
                raise DistAbortPinPrior(str(err), code=err.code)
            raise err
        seen.add(doc.replay_nonce)
        _save_replay_registry(root, seen)
        doc.replay_seen = True
    return doc


def detect_replay(nonce: str, registry: set[str] | Sequence[str]) -> None:
    """T-H5c: raise if nonce already present in registry."""
    if nonce in set(registry):
        raise DistReplayDetected(f"replay nonce collision: {nonce}")


def pin_prior(
    repo: str | Path,
    *,
    reason: str,
    ver: str = PRIOR_PIN_DEFAULT_VER,
    bundle_id: str = "",
    sha256: str = "",
    label: str = PRIOR_PIN_DEFAULT_LABEL,
    from_doc: DistributionDocument | Mapping[str, Any] | None = None,
) -> DistPriorPin:
    """ABORT→pin prior: record prior known-good; never retag v0.16.3/v0.17.0 (T-H5f)."""
    root = Path(repo).resolve()
    if from_doc is not None:
        d = from_doc if isinstance(from_doc, DistributionDocument) else DistributionDocument.from_dict(dict(from_doc))
        # Pin *prior* of the failed doc — prefer explicit prior_pin or default 0.17.0
        if d.prior_pin is not None:
            pin = d.prior_pin
        else:
            pin = DistPriorPin(ver=ver, bundle_id=bundle_id or "prior-frozen", sha256=sha256, label=label)
    else:
        pin = DistPriorPin(
            ver=ver,
            bundle_id=bundle_id or "prior-frozen",
            sha256=sha256,
            label=label,
        )
    # Guard: never claim we retagged
    payload = {
        "ok": True,
        "abort_pin_prior": True,
        "reason": reason,
        "prior_pin": pin.to_dict(),
        "retag": False,
        "tags_untouched": ["v0.16.3", "v0.17.0"],
        "channel_frozen": True,
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
        "schema": SCHEMA_ID,
        "at": _utc_now(),
    }
    path = _prior_pin_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return pin


def load_prior_pin(repo: str | Path) -> dict[str, Any] | None:
    path = _prior_pin_path(Path(repo))
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def document_to_json(doc: DistributionDocument, *, indent: int = 2) -> str:
    return json.dumps(doc.to_dict(), indent=indent, sort_keys=True) + "\n"


def format_dist_m2m(doc: DistributionDocument) -> str:
    return (
        f"DIST: schema={doc.schema} ver={doc.ver} channel={doc.channel} "
        f"bundle_id={doc.bundle_id} cp={doc.cp_tip} "
        f"sha={doc.bundle_sha256[:12]} nonce={doc.replay_nonce[:8]} "
        f"toolchain={doc.toolchain.pin_hash[:12]} "
        f"dual_primary={doc.dual_primary} abort_pin_prior={int(doc.abort_pin_prior)} "
        f"invariants_ok={int(doc.invariants_ok)} revoked={int(doc.revoked)}"
    )


# Re-export descriptor for CLI
__all__ = [
    "check_channel",
    "compute_toolchain_pin",
    "detect_replay",
    "distribute",
    "document_to_json",
    "format_dist_m2m",
    "load_prior_pin",
    "pin_prior",
    "require_n2_bound",
    "require_no_plaintext",
    "schema_descriptor",
    "sign_document",
    "validate_dict",
    "verify_distribution",
    "verify_signature",
]
