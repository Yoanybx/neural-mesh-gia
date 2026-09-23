"""Local CA + mTLS contexts (stdlib ssl + openssl subprocess bootstrap)."""

from __future__ import annotations

import os
import ssl
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class CertBootstrapError(RuntimeError):
    """Failed to generate or load local CA / leaf certs."""


@dataclass(frozen=True)
class NodeCertPaths:
    node_id: str
    ca_cert: Path
    cert: Path
    key: Path


@dataclass(frozen=True)
class LocalCA:
    """Filesystem layout for a local CA and issued leafs."""

    root: Path
    ca_cert: Path
    ca_key: Path

    @classmethod
    def create(cls, root: str | Path, *, days: int = 3650) -> "LocalCA":
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        ca_cert = root / "ca.crt"
        ca_key = root / "ca.key"
        if not ca_cert.exists() or not ca_key.exists():
            _openssl(
                [
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(ca_key),
                    "-out",
                    str(ca_cert),
                    "-days",
                    str(days),
                    "-subj",
                    "/CN=neural-mesh-local-ca",
                ]
            )
            os.chmod(ca_key, 0o600)
        return cls(root=root, ca_cert=ca_cert, ca_key=ca_key)

    def issue_node(
        self, node_id: str, *, days: int = 825, force: bool = False
    ) -> NodeCertPaths:
        """Issue (or rotate) a leaf cert with CN/SAN = node_id."""
        node_dir = self.root / "nodes" / node_id
        node_dir.mkdir(parents=True, exist_ok=True)
        cert = node_dir / "node.crt"
        key = node_dir / "node.key"
        if cert.exists() and key.exists() and not force:
            return NodeCertPaths(
                node_id=node_id, ca_cert=self.ca_cert, cert=cert, key=key
            )

        csr = node_dir / "node.csr"
        ext = node_dir / "node.ext"
        # SAN DNS + CN both carry node_id for identity checks.
        ext.write_text(
            "subjectAltName=DNS:{nid},DNS:localhost,IP:127.0.0.1\n"
            "extendedKeyUsage=serverAuth,clientAuth\n"
            "basicConstraints=CA:FALSE\n".format(nid=node_id),
            encoding="utf-8",
        )
        _openssl(
            [
                "req",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(key),
                "-out",
                str(csr),
                "-subj",
                f"/CN={node_id}",
            ]
        )
        _openssl(
            [
                "x509",
                "-req",
                "-in",
                str(csr),
                "-CA",
                str(self.ca_cert),
                "-CAkey",
                str(self.ca_key),
                "-CAcreateserial",
                "-out",
                str(cert),
                "-days",
                str(days),
                "-extfile",
                str(ext),
            ]
        )
        os.chmod(key, 0o600)
        try:
            csr.unlink()
        except OSError:
            pass
        return NodeCertPaths(
            node_id=node_id, ca_cert=self.ca_cert, cert=cert, key=key
        )

    def rotate_node(self, node_id: str, *, days: int = 825) -> NodeCertPaths:
        return self.issue_node(node_id, days=days, force=True)


def _openssl(args: list[str]) -> None:
    cmd = ["openssl", *args]
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CertBootstrapError("openssl not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise CertBootstrapError(
            f"openssl failed: {exc.stderr or exc.stdout or exc}"
        ) from exc


def build_ssl_context(
    paths: NodeCertPaths,
    *,
    server_side: bool,
    check_hostname: bool = False,
) -> ssl.SSLContext:
    """Build an mTLS SSLContext trusting only the local CA."""
    if server_side:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    else:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # We verify peer cert against CA; node_id checked separately via CN/SAN.
        ctx.check_hostname = bool(check_hostname)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_verify_locations(cafile=str(paths.ca_cert))
    ctx.load_cert_chain(certfile=str(paths.cert), keyfile=str(paths.key))
    return ctx


def peer_identities(ssl_sock: ssl.SSLSocket) -> list[str]:
    """Return CN + DNS SANs from the peer certificate."""
    cert = ssl_sock.getpeercert()
    if not cert:
        return []
    ids: list[str] = []
    # subject = ((('commonName', 'node-01'),), ...)
    for rdn in cert.get("subject", ()):
        for attr in rdn:
            if not isinstance(attr, (tuple, list)) or len(attr) < 2:
                continue
            k, v = attr[0], attr[1]
            if k == "commonName" and v:
                ids.append(str(v))
    # subjectAltName = (('DNS', 'node-01'), ('DNS', 'localhost'), ...)
    for san in cert.get("subjectAltName", ()):
        if not isinstance(san, (tuple, list)) or len(san) < 2:
            continue
        typ, value = san[0], san[1]
        if typ == "DNS" and value:
            ids.append(str(value))
    # Preserve order, unique
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def verify_peer_identity(ssl_sock: ssl.SSLSocket, expected_node_id: str) -> str:
    """Fail-closed: expected node_id must appear in peer CN/SAN."""
    ids = peer_identities(ssl_sock)
    if expected_node_id not in ids:
        from .errors import FabricTLSError

        raise FabricTLSError(
            f"peer identity mismatch: expected {expected_node_id}, got {ids}",
            peer=expected_node_id,
        )
    return expected_node_id


def issue_foreign_ca_leaf(
    node_id: str, dest_dir: str | Path, *, days: int = 30
) -> NodeCertPaths:
    """Issue a leaf under a *different* CA (for rejection tests)."""
    dest = Path(dest_dir)
    with tempfile.TemporaryDirectory() as td:
        foreign = LocalCA.create(Path(td) / "foreign-ca")
        paths = foreign.issue_node(node_id, days=days)
        dest.mkdir(parents=True, exist_ok=True)
        ca_cert = dest / "ca.crt"
        cert = dest / "node.crt"
        key = dest / "node.key"
        ca_cert.write_bytes(paths.ca_cert.read_bytes())
        cert.write_bytes(paths.cert.read_bytes())
        key.write_bytes(paths.key.read_bytes())
        os.chmod(key, 0o600)
        return NodeCertPaths(
            node_id=node_id, ca_cert=ca_cert, cert=cert, key=key
        )


def bootstrap_pair(
    root: str | Path, node_ids: Iterable[str]
) -> tuple[LocalCA, dict[str, NodeCertPaths]]:
    ca = LocalCA.create(root)
    leaves = {nid: ca.issue_node(nid) for nid in node_ids}
    return ca, leaves


__all__ = [
    "CertBootstrapError",
    "LocalCA",
    "NodeCertPaths",
    "bootstrap_pair",
    "build_ssl_context",
    "issue_foreign_ca_leaf",
    "peer_identities",
    "verify_peer_identity",
]
