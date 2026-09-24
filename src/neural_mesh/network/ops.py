"""Fabric ops UX — status / diagnose / reconnect (Cycle 29 / CP-0033).

Operator ergonomics around existing TLS fabric helpers. Fail-closed on TLS
errors; never silent plaintext fallback. No Vault/ACME hard requirement.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import FabricError, FabricTLSError, PlaintextForbidden
from .protocol import FabricMessage, MessageType
from .session import NodeEndpoint, NodeSession
from .tls import NodeCertPaths
from .transport import TransportMode


SCHEMA_STATUS = "mesh.fabric.status/v1"
SCHEMA_DIAGNOSE = "mesh.fabric.diagnose/v1"
SCHEMA_RECONNECT = "mesh.fabric.reconnect/v1"


@dataclass
class PeerProbe:
    """Per-peer probe result from status / diagnose / reconnect."""

    node_id: str
    mode: str
    host: str = "127.0.0.1"
    port: int = 0
    reachable: bool = False
    tls_ok: bool | None = None
    heartbeat_ok: bool | None = None
    latency_ms: float | None = None
    peer_identity: str | None = None
    error: str | None = None
    error_code: str | None = None
    plaintext_attempted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FabricStatusReport:
    """Operator-facing fabric status snapshot."""

    schema: str = SCHEMA_STATUS
    local_node_id: str = ""
    tls_required: bool = True
    cert_ok: bool = False
    ca_cert_present: bool = False
    leaf_cert_present: bool = False
    leaf_key_present: bool = False
    ca_cert: str | None = None
    leaf_cert: str | None = None
    leaf_key: str | None = None
    endpoints_configured: int = 0
    peers: list[PeerProbe] = field(default_factory=list)
    ok: bool = False
    dual_primary: int = 0
    plaintext_fallback: int = 0
    vault_acme_required: bool = False
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class FabricDiagnoseReport:
    """Richer diagnose output with recommendations."""

    schema: str = SCHEMA_DIAGNOSE
    status: FabricStatusReport = field(default_factory=FabricStatusReport)
    recommendations: list[str] = field(default_factory=list)
    fail_closed: bool = True
    plaintext_fallback: int = 0
    dual_primary: int = 0
    ok: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status.to_dict(),
            "recommendations": list(self.recommendations),
            "fail_closed": self.fail_closed,
            "plaintext_fallback": self.plaintext_fallback,
            "dual_primary": self.dual_primary,
            "ok": self.ok,
            "issues": list(self.status.issues),
        }


@dataclass
class FabricReconnectResult:
    """Result of a safe TLS reconnect attempt for one or more peers."""

    schema: str = SCHEMA_RECONNECT
    local_node_id: str = ""
    results: list[PeerProbe] = field(default_factory=list)
    ok: bool = False
    dual_primary: int = 0
    plaintext_fallback: int = 0
    plaintext_attempted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "local_node_id": self.local_node_id,
            "results": [p.to_dict() for p in self.results],
            "ok": self.ok,
            "dual_primary": self.dual_primary,
            "plaintext_fallback": self.plaintext_fallback,
            "plaintext_attempted": self.plaintext_attempted,
        }


def load_endpoints_json(path: str | Path) -> dict[str, NodeEndpoint]:
    """Load endpoints from JSON.

    Accepted shapes:
      {"peers": [{"node_id", "host", "port", "mode"?}, ...]}
      {"endpoints": {...same...}}
      [{"node_id", ...}, ...]
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items = raw.get("peers") or raw.get("endpoints") or []
        if isinstance(items, dict):
            items = [
                {"node_id": k, **(v if isinstance(v, dict) else {})}
                for k, v in items.items()
            ]
    elif isinstance(raw, list):
        items = raw
    else:
        raise ValueError(f"unsupported endpoints JSON shape: {type(raw)}")
    out: dict[str, NodeEndpoint] = {}
    for item in items:
        nid = str(item["node_id"])
        mode_s = str(item.get("mode") or TransportMode.TLS.value)
        mode = TransportMode(mode_s)
        out[nid] = NodeEndpoint(
            node_id=nid,
            mode=mode,
            host=str(item.get("host") or "127.0.0.1"),
            port=int(item.get("port") or 0),
            unix_path=item.get("unix_path"),
        )
    return out


def resolve_cert_paths(
    fabric_root: str | Path, local_node_id: str
) -> NodeCertPaths | None:
    """Resolve NodeCertPaths from a LocalCA layout under fabric_root."""
    root = Path(fabric_root)
    ca_cert = root / "ca.crt"
    cert = root / "nodes" / local_node_id / "node.crt"
    key = root / "nodes" / local_node_id / "node.key"
    if ca_cert.is_file() and cert.is_file() and key.is_file():
        return NodeCertPaths(
            node_id=local_node_id, ca_cert=ca_cert, cert=cert, key=key
        )
    return None


class FabricOps:
    """Operator helpers: status, diagnose, reconnect around NetworkFabric TLS."""

    def __init__(
        self,
        local_node_id: str,
        cert_paths: NodeCertPaths | None = None,
        *,
        endpoints: dict[str, NodeEndpoint] | None = None,
        tls_required: bool = True,
        fabric_root: str | Path | None = None,
    ):
        self.local_node_id = str(local_node_id)
        self.tls_required = bool(tls_required)
        self.fabric_root = Path(fabric_root) if fabric_root else None
        if cert_paths is None and self.fabric_root is not None:
            cert_paths = resolve_cert_paths(self.fabric_root, self.local_node_id)
        self.cert_paths = cert_paths
        self.endpoints: dict[str, NodeEndpoint] = dict(endpoints or {})

    @classmethod
    def from_fabric_root(
        cls,
        fabric_root: str | Path,
        local_node_id: str,
        *,
        tls_required: bool = True,
        endpoints_path: str | Path | None = None,
    ) -> "FabricOps":
        root = Path(fabric_root)
        endpoints: dict[str, NodeEndpoint] = {}
        ep_path = Path(endpoints_path) if endpoints_path else root / "endpoints.json"
        if ep_path.is_file():
            endpoints = load_endpoints_json(ep_path)
        return cls(
            local_node_id,
            resolve_cert_paths(root, local_node_id),
            endpoints=endpoints,
            tls_required=tls_required,
            fabric_root=root,
        )

    def register(self, endpoint: NodeEndpoint) -> None:
        self.endpoints[endpoint.node_id] = endpoint

    def _cert_fields(self) -> dict[str, Any]:
        cp = self.cert_paths
        if cp is None:
            return {
                "cert_ok": False,
                "ca_cert_present": False,
                "leaf_cert_present": False,
                "leaf_key_present": False,
                "ca_cert": None,
                "leaf_cert": None,
                "leaf_key": None,
            }
        ca_ok = Path(cp.ca_cert).is_file()
        cert_ok = Path(cp.cert).is_file()
        key_ok = Path(cp.key).is_file()
        return {
            "cert_ok": ca_ok and cert_ok and key_ok,
            "ca_cert_present": ca_ok,
            "leaf_cert_present": cert_ok,
            "leaf_key_present": key_ok,
            "ca_cert": str(cp.ca_cert),
            "leaf_cert": str(cp.cert),
            "leaf_key": str(cp.key),
        }

    def _probe_peer(self, ep: NodeEndpoint) -> PeerProbe:
        """TLS heartbeat probe. Fail-closed; never plaintext fallback."""
        probe = PeerProbe(
            node_id=ep.node_id,
            mode=str(ep.mode.value if isinstance(ep.mode, TransportMode) else ep.mode),
            host=ep.host,
            port=int(ep.port),
            plaintext_attempted=False,
        )
        mode = TransportMode(ep.mode)
        if self.tls_required and mode != TransportMode.TLS:
            probe.error = (
                f"refusing mode={mode.value}: TLS required (no plaintext fallback)"
            )
            probe.error_code = PlaintextForbidden.code
            probe.tls_ok = False
            return probe
        if mode == TransportMode.TLS and self.cert_paths is None:
            probe.error = "TLS mode requires cert_paths"
            probe.error_code = "INVALID_SESSION"
            probe.tls_ok = False
            return probe

        session = NodeSession(
            self.local_node_id,
            cert_paths=self.cert_paths,
            tls_required=self.tls_required,
        )
        t0 = time.perf_counter()
        try:
            session.connect(ep)
            probe.tls_ok = True
            probe.reachable = True
            probe.peer_identity = session.peer_node_id
            msg = FabricMessage(
                MessageType.HEARTBEAT,
                from_node=self.local_node_id,
                to_node=ep.node_id,
                payload={},
            )
            resp = session.request(msg)
            probe.latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            probe.heartbeat_ok = resp.type == MessageType.ACK and bool(
                (resp.payload or {}).get("pong", True)
            )
            if not probe.heartbeat_ok:
                probe.error = "heartbeat nack or unexpected response"
                probe.error_code = "FABRIC_ERROR"
        except PlaintextForbidden as exc:
            probe.plaintext_attempted = False
            probe.tls_ok = False
            probe.error = str(exc)
            probe.error_code = getattr(exc, "code", PlaintextForbidden.code)
        except FabricTLSError as exc:
            probe.tls_ok = False
            probe.error = str(exc)
            probe.error_code = getattr(exc, "code", FabricTLSError.code)
        except FabricError as exc:
            probe.tls_ok = False if mode == TransportMode.TLS else probe.tls_ok
            probe.error = str(exc)
            probe.error_code = getattr(exc, "code", "FABRIC_ERROR")
        except Exception as exc:  # noqa: BLE001 — surface unexpected as error
            probe.tls_ok = False
            probe.error = str(exc)
            probe.error_code = "FABRIC_ERROR"
        finally:
            session.close()
        return probe

    def status(self, *, probe: bool = True) -> FabricStatusReport:
        fields = self._cert_fields()
        issues: list[str] = []
        if not fields["cert_ok"]:
            issues.append("local leaf/CA cert material missing or incomplete")
        peers: list[PeerProbe] = []
        if probe:
            for ep in self.endpoints.values():
                peers.append(self._probe_peer(ep))
        else:
            for ep in self.endpoints.values():
                peers.append(
                    PeerProbe(
                        node_id=ep.node_id,
                        mode=str(
                            ep.mode.value
                            if isinstance(ep.mode, TransportMode)
                            else ep.mode
                        ),
                        host=ep.host,
                        port=int(ep.port),
                    )
                )
        for p in peers:
            if p.error:
                issues.append(f"{p.node_id}: {p.error_code or 'ERROR'}: {p.error}")
        all_peers_ok = all(
            (p.reachable and p.tls_ok and (p.heartbeat_ok is not False))
            for p in peers
        ) if peers and probe else True
        ok = bool(fields["cert_ok"]) and (all_peers_ok if probe else True)
        if self.tls_required and not fields["cert_ok"]:
            ok = False
        return FabricStatusReport(
            local_node_id=self.local_node_id,
            tls_required=self.tls_required,
            endpoints_configured=len(self.endpoints),
            peers=peers,
            ok=ok,
            dual_primary=0,
            plaintext_fallback=0,
            vault_acme_required=False,
            issues=issues,
            **fields,
        )

    def diagnose(self, *, probe: bool = True) -> FabricDiagnoseReport:
        st = self.status(probe=probe)
        recs: list[str] = []
        if not st.cert_ok:
            recs.append(
                "Bootstrap local CA leafs via LocalCA.create/issue_node "
                "(no Vault/ACME required)"
            )
        if not st.ca_cert_present:
            recs.append("Ensure ca.crt exists under fabric root")
        if not st.leaf_cert_present or not st.leaf_key_present:
            recs.append(
                f"Issue leaf for local_node_id={self.local_node_id} under nodes/"
            )
        for p in st.peers:
            if p.error_code == PlaintextForbidden.code:
                recs.append(
                    f"{p.node_id}: keep mode=tls; plaintext/unix is forbidden "
                    "when tls_required"
                )
            elif p.error_code == FabricTLSError.code:
                recs.append(
                    f"{p.node_id}: fix TLS (CA trust / identity / handshake); "
                    "fail-closed — do not fall back to plaintext"
                )
            elif p.error_code == "CONNECTION_DROP" or (
                p.error and "connect" in (p.error or "").lower()
            ):
                recs.append(
                    f"{p.node_id}: peer unreachable — start ExecutionEndpoint "
                    "or check host/port"
                )
            elif p.error:
                recs.append(f"{p.node_id}: inspect error_code={p.error_code}")
        if st.ok and not recs:
            recs.append("fabric healthy: certs present; peer probes ok (TLS)")
        return FabricDiagnoseReport(
            status=st,
            recommendations=recs,
            fail_closed=True,
            plaintext_fallback=0,
            dual_primary=0,
            ok=st.ok,
        )

    def reconnect(
        self,
        node_id: str | None = None,
        *,
        attempts: int = 2,
    ) -> FabricReconnectResult:
        """Safe reconnect of sessions via TLS heartbeat.

        Never attempts plaintext / unix fallback. TLS errors fail closed.
        """
        if attempts < 1:
            attempts = 1
        targets: list[NodeEndpoint]
        if node_id is not None:
            ep = self.endpoints.get(node_id)
            if ep is None:
                bad = PeerProbe(
                    node_id=node_id,
                    mode=TransportMode.TLS.value,
                    error=f"no endpoint for {node_id}",
                    error_code="INVALID_SESSION",
                    tls_ok=False,
                    plaintext_attempted=False,
                )
                return FabricReconnectResult(
                    local_node_id=self.local_node_id,
                    results=[bad],
                    ok=False,
                    dual_primary=0,
                    plaintext_fallback=0,
                    plaintext_attempted=False,
                )
            targets = [ep]
        else:
            targets = list(self.endpoints.values())

        results: list[PeerProbe] = []
        for ep in targets:
            last: PeerProbe | None = None
            for _ in range(attempts):
                last = self._probe_peer(ep)
                if last.reachable and last.tls_ok and last.heartbeat_ok:
                    break
                # Fail-closed: do not retry with a different (plaintext) mode.
                if last.error_code in (
                    PlaintextForbidden.code,
                    FabricTLSError.code,
                ):
                    break
            assert last is not None
            results.append(last)

        ok = bool(results) and all(
            r.reachable and r.tls_ok and r.heartbeat_ok for r in results
        )
        return FabricReconnectResult(
            local_node_id=self.local_node_id,
            results=results,
            ok=ok,
            dual_primary=0,
            plaintext_fallback=0,
            plaintext_attempted=False,
        )


def format_status_human(report: FabricStatusReport) -> str:
    lines = [
        f"fabric status local={report.local_node_id} ok={report.ok} "
        f"tls_required={report.tls_required}",
        f"  cert_ok={report.cert_ok} ca={report.ca_cert_present} "
        f"leaf={report.leaf_cert_present} key={report.leaf_key_present}",
        f"  endpoints={report.endpoints_configured} "
        f"dual_primary={report.dual_primary} "
        f"plaintext_fallback={report.plaintext_fallback}",
    ]
    for p in report.peers:
        lines.append(
            f"  peer {p.node_id} mode={p.mode} "
            f"{p.host}:{p.port} reachable={p.reachable} tls_ok={p.tls_ok} "
            f"hb={p.heartbeat_ok} lat_ms={p.latency_ms} "
            f"err={p.error_code or '-'}"
        )
    for issue in report.issues:
        lines.append(f"  issue: {issue}")
    return "\n".join(lines)


def format_diagnose_human(report: FabricDiagnoseReport) -> str:
    lines = [format_status_human(report.status), "recommendations:"]
    for r in report.recommendations:
        lines.append(f"  - {r}")
    lines.append(
        f"fail_closed={report.fail_closed} "
        f"plaintext_fallback={report.plaintext_fallback} "
        f"dual_primary={report.dual_primary}"
    )
    return "\n".join(lines)


def format_reconnect_human(result: FabricReconnectResult) -> str:
    lines = [
        f"fabric reconnect local={result.local_node_id} ok={result.ok} "
        f"plaintext_attempted={result.plaintext_attempted} "
        f"plaintext_fallback={result.plaintext_fallback}"
    ]
    for p in result.results:
        lines.append(
            f"  {p.node_id}: reachable={p.reachable} tls_ok={p.tls_ok} "
            f"hb={p.heartbeat_ok} err={p.error_code or '-'}"
        )
    return "\n".join(lines)


def cmd_fabric_status(
    *,
    fabric_root: str | Path,
    node_id: str,
    endpoints: str | Path | None = None,
    as_json: bool = False,
    probe: bool = True,
    tls_required: bool = True,
) -> int:
    ops = FabricOps.from_fabric_root(
        fabric_root,
        node_id,
        tls_required=tls_required,
        endpoints_path=endpoints,
    )
    report = ops.status(probe=probe)
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_status_human(report))
    return 0 if report.ok else 1


def cmd_fabric_diagnose(
    *,
    fabric_root: str | Path,
    node_id: str,
    endpoints: str | Path | None = None,
    as_json: bool = False,
    probe: bool = True,
    tls_required: bool = True,
) -> int:
    ops = FabricOps.from_fabric_root(
        fabric_root,
        node_id,
        tls_required=tls_required,
        endpoints_path=endpoints,
    )
    report = ops.diagnose(probe=probe)
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_diagnose_human(report))
    return 0 if report.ok else 1


def cmd_fabric_reconnect(
    *,
    fabric_root: str | Path,
    node_id: str,
    peer: str | None = None,
    endpoints: str | Path | None = None,
    as_json: bool = False,
    attempts: int = 2,
    tls_required: bool = True,
) -> int:
    ops = FabricOps.from_fabric_root(
        fabric_root,
        node_id,
        tls_required=tls_required,
        endpoints_path=endpoints,
    )
    result = ops.reconnect(peer, attempts=attempts)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_reconnect_human(result))
    return 0 if result.ok else 1


__all__ = [
    "SCHEMA_DIAGNOSE",
    "SCHEMA_RECONNECT",
    "SCHEMA_STATUS",
    "FabricDiagnoseReport",
    "FabricOps",
    "FabricReconnectResult",
    "FabricStatusReport",
    "PeerProbe",
    "cmd_fabric_diagnose",
    "cmd_fabric_reconnect",
    "cmd_fabric_status",
    "format_diagnose_human",
    "format_reconnect_human",
    "format_status_human",
    "load_endpoints_json",
    "resolve_cert_paths",
]
