"""Phase 4 Network Fabric v0 + mTLS (Cycle 11)."""

from .errors import (
    ConnectionDrop,
    FabricError,
    FabricTLSError,
    InvalidSession,
    MessageCorruption,
    NetworkTimeout,
    PlaintextForbidden,
)
from .fabric import DispatchResult, NetworkFabric, default_tls_endpoint
from .endpoint import ExecutionEndpoint
from .protocol import (
    REQUIRED_MESSAGE_TYPES,
    FabricMessage,
    MessageType,
    make_ack,
    make_error,
)
from .session import NodeEndpoint, NodeSession
from .tls import (
    CertBootstrapError,
    LocalCA,
    NodeCertPaths,
    bootstrap_pair,
    build_ssl_context,
    issue_foreign_ca_leaf,
    peer_identities,
    verify_peer_identity,
)
from .transport import (
    MAX_FRAME_BYTES,
    FrameStream,
    TransportMode,
    accept_tls,
    connect_tls,
    connect_unix,
    listen_tcp,
    listen_unix,
)
from .witness import PrimaryWitness

__all__ = [
    "CertBootstrapError",
    "ConnectionDrop",
    "DispatchResult",
    "ExecutionEndpoint",
    "FabricError",
    "FabricMessage",
    "FabricTLSError",
    "FrameStream",
    "InvalidSession",
    "LocalCA",
    "MAX_FRAME_BYTES",
    "MessageCorruption",
    "MessageType",
    "NetworkFabric",
    "NetworkTimeout",
    "NodeCertPaths",
    "NodeEndpoint",
    "NodeSession",
    "PlaintextForbidden",
    "PrimaryWitness",
    "REQUIRED_MESSAGE_TYPES",
    "TransportMode",
    "accept_tls",
    "bootstrap_pair",
    "build_ssl_context",
    "connect_tls",
    "connect_unix",
    "default_tls_endpoint",
    "issue_foreign_ca_leaf",
    "listen_tcp",
    "listen_unix",
    "make_ack",
    "make_error",
    "peer_identities",
    "verify_peer_identity",
]
