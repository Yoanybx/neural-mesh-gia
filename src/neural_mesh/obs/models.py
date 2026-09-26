"""OBS telemetry contract models (Cycle 37 / CP-0041 / H4).

Schema: mesh.obs/v1
Capability: docs/capabilities/MESH_OBS_TELEMETRY.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SCHEMA_ID = "mesh.obs/v1"
SCHEMA_SIGNALS = "mesh.obs.signals/v1"
SCHEMA_ADVERSARY = "mesh.obs.adversary/v1"
SCHEMA_WINDOW = "mesh.obs.window/v1"
SOURCE_SNAPSHOT_SCHEMA = "mesh.status.snapshot/v1"

CADENCE_TIERS = ("1s", "10s", "60s")
Cadence = Literal["1s", "10s", "60s"]

REQUIRED_TOP_FIELDS = (
    "schema",
    "node_id",
    "cycle",
    "ver",
    "cp_tip",
    "cp_range",
    "pytest",
    "signals",
    "adversary",
    "cadence",
    "window",
    "dual_primary",
    "plaintext_fallback",
    "vault_acme_required",
)


class ObsError(RuntimeError):
    """Base OBS telemetry error (fail-closed)."""

    code: str = "OBS_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class ObsSchemaMismatch(ObsError):
    """Wrong/missing schema or required field — fail-closed."""

    code = "OBS_SCHEMA_MISMATCH"


class ObsInvariantBreach(ObsError):
    """Contract invariant breached (dual_primary, plaintext, …)."""

    code = "OBS_INVARIANT_BREACH"


class ObsAbortBlockCp(ObsError):
    """ABORT→block CP mint on schema/invariant breach."""

    code = "OBS_ABORT_BLOCK_CP"


class ObsPlaintextForbidden(ObsError):
    code = "OBS_PLAINTEXT_FORBIDDEN"


class ObsN2Only(ObsError):
    """N>2 / Raft refused."""

    code = "OBS_N2_ONLY"


class ObsCadenceInvalid(ObsError):
    code = "OBS_CADENCE_INVALID"


@dataclass
class ObsSignals:
    """Versioned OBS signals (mesh.obs.signals/v1)."""

    recovery_p99: str = "SCHEMA-GATED"
    ckpt_durable: str = "MET"
    ckpt_parity: str = "MET"
    conflict_full: int = 0
    conflict_classify: int = 0
    minority_writes: int = 0
    dual_primary: int = 0
    cp_lag: int = 0
    schema: str = SCHEMA_SIGNALS

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dual_primary"] = 0
        d["minority_writes"] = 0
        d["schema"] = SCHEMA_SIGNALS
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ObsSignals":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        sig = cls(**kwargs)
        sig.dual_primary = 0
        sig.minority_writes = 0
        sig.schema = SCHEMA_SIGNALS
        for name in ("conflict_full", "conflict_classify", "cp_lag"):
            val = getattr(sig, name)
            if val is None:
                setattr(sig, name, 0)
            else:
                setattr(sig, name, int(val))
        return sig


@dataclass
class ObsAdversary:
    """Adversary signals (mesh.obs.adversary/v1)."""

    replay_attempts: int = 0
    auth_fails: int = 0
    tier_changes: int = 0
    schema: str = SCHEMA_ADVERSARY

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_ADVERSARY
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ObsAdversary":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        adv = cls(**kwargs)
        adv.schema = SCHEMA_ADVERSARY
        for name in ("replay_attempts", "auth_fails", "tier_changes"):
            val = getattr(adv, name)
            setattr(adv, name, 0 if val is None else int(val))
        return adv


@dataclass
class ObsWindow:
    """OBS window for CP-cites-OBS-window linkage."""

    window_id: str = ""
    started_at: str | None = None
    ended_at: str | None = None
    cadence: str = "10s"
    schema: str = SCHEMA_WINDOW

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA_WINDOW
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ObsWindow":
        data = dict(data or {})
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        win = cls(**kwargs)
        win.schema = SCHEMA_WINDOW
        return win


@dataclass
class TelemetryDocument:
    """Operator / council OBS telemetry document (mesh.obs/v1)."""

    node_id: str
    cycle: int
    ver: str
    cp_tip: str
    cp_range: str
    tip: str | None = None
    pytest: dict[str, int] = field(default_factory=lambda: {"passed": 0, "failed": 0})
    slo_state: dict[str, str] = field(default_factory=dict)
    debt_gates: list[dict[str, Any]] = field(default_factory=list)
    peers: list[dict[str, Any]] = field(default_factory=list)
    signals: ObsSignals = field(default_factory=ObsSignals)
    adversary: ObsAdversary = field(default_factory=ObsAdversary)
    cadence: str = "10s"
    window: ObsWindow = field(default_factory=ObsWindow)
    dual_primary: int = 0
    vault_acme_required: int = 0
    plaintext_fallback: int = 0
    invariants_ok: bool = True
    abort_block_cp: bool = False
    source_schema: str = SOURCE_SNAPSHOT_SCHEMA
    schema: str = SCHEMA_ID
    packaging: str = ""
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_ID,
            "node_id": self.node_id,
            "cycle": int(self.cycle),
            "ver": self.ver,
            "tip": self.tip,
            "cp_tip": self.cp_tip,
            "cp_range": self.cp_range,
            "pytest": {
                "passed": int((self.pytest or {}).get("passed", 0)),
                "failed": int((self.pytest or {}).get("failed", 0)),
            },
            "slo_state": dict(sorted((self.slo_state or {}).items())),
            "debt_gates": list(self.debt_gates or []),
            "peers": list(self.peers or []),
            "signals": self.signals.to_dict()
            if isinstance(self.signals, ObsSignals)
            else ObsSignals.from_dict(self.signals).to_dict(),  # type: ignore[arg-type]
            "adversary": self.adversary.to_dict()
            if isinstance(self.adversary, ObsAdversary)
            else ObsAdversary.from_dict(self.adversary).to_dict(),  # type: ignore[arg-type]
            "cadence": self.cadence,
            "window": self.window.to_dict()
            if isinstance(self.window, ObsWindow)
            else ObsWindow.from_dict(self.window).to_dict(),  # type: ignore[arg-type]
            "dual_primary": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
            "invariants_ok": bool(self.invariants_ok),
            "abort_block_cp": bool(self.abort_block_cp),
            "source_schema": self.source_schema or SOURCE_SNAPSHOT_SCHEMA,
            "packaging": self.packaging or "",
            "issues": list(self.issues or []),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TelemetryDocument":
        if not isinstance(data, dict):
            raise ObsSchemaMismatch("telemetry document must be an object")
        sig = ObsSignals.from_dict(data.get("signals") if isinstance(data.get("signals"), dict) else {})
        adv = ObsAdversary.from_dict(
            data.get("adversary") if isinstance(data.get("adversary"), dict) else {}
        )
        win = ObsWindow.from_dict(data.get("window") if isinstance(data.get("window"), dict) else {})
        pytest = data.get("pytest") or {}
        if not isinstance(pytest, dict):
            pytest = {"passed": 0, "failed": 0}
        return cls(
            node_id=str(data.get("node_id") or ""),
            cycle=int(data.get("cycle") or 0),
            ver=str(data.get("ver") or ""),
            tip=data.get("tip"),
            cp_tip=str(data.get("cp_tip") or ""),
            cp_range=str(data.get("cp_range") or ""),
            pytest={
                "passed": int(pytest.get("passed", 0)),
                "failed": int(pytest.get("failed", 0)),
            },
            slo_state=dict(data.get("slo_state") or {}),
            debt_gates=list(data.get("debt_gates") or []),
            peers=list(data.get("peers") or []),
            signals=sig,
            adversary=adv,
            cadence=str(data.get("cadence") or "10s"),
            window=win,
            dual_primary=0,
            vault_acme_required=0,
            plaintext_fallback=0,
            invariants_ok=bool(data.get("invariants_ok", True)),
            abort_block_cp=bool(data.get("abort_block_cp", False)),
            source_schema=str(data.get("source_schema") or SOURCE_SNAPSHOT_SCHEMA),
            schema=SCHEMA_ID,
            packaging=str(data.get("packaging") or ""),
            issues=list(data.get("issues") or []),
        )


def schema_descriptor() -> dict[str, Any]:
    """CLI / docs helper: active schema + required signals."""
    return {
        "schema": SCHEMA_ID,
        "signals_schema": SCHEMA_SIGNALS,
        "adversary_schema": SCHEMA_ADVERSARY,
        "window_schema": SCHEMA_WINDOW,
        "source_snapshot_schema": SOURCE_SNAPSHOT_SCHEMA,
        "cadence_tiers": list(CADENCE_TIERS),
        "required_fields": list(REQUIRED_TOP_FIELDS),
        "signals": [
            "recovery_p99",
            "ckpt_durable",
            "ckpt_parity",
            "conflict_full",
            "conflict_classify",
            "minority_writes",
            "dual_primary",
            "cp_lag",
        ],
        "adversary": ["replay_attempts", "auth_fails", "tier_changes"],
        "abort": "block_cp_mint",
        "dual_primary": 0,
        "vault_acme_required": 0,
        "plaintext_fallback": 0,
        "deprecation_note": (
            "mesh.status.snapshot/v1 remains ACTIVE for local snapshots; "
            "mesh.obs/v1 is the versioned telemetry contract track."
        ),
    }
