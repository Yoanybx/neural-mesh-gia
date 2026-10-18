from __future__ import annotations

import argparse
import sys
import json
import subprocess
from pathlib import Path

from .benchmark.runner import run_twin_basic
from .checkpoint import CheckpointManager
from .git_audit import audit_git
from .obsidian import ObsidianSync
from .safety import ensure_default_policy, safety_status
from .status_snapshot import (
    format_obs_m2m,
    load_peers_json,
    merge_peer_summaries,
    parse_peers_json,
    snapshot,
    snapshot_to_json,
)
from .twin.events import FaultEvent
from .twin.faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
)
from .twin.schema import Topology, Workload
from .twin.simulator import DigitalTwin, TwinTask
from .twin.storage import load_faults

from .cram.observability import cmd_trace
from .cram.cli_ops import cmd_fsck, cmd_get, cmd_put, cmd_verify
from .cram.durability_cli import (
    cmd_durability_check,
    cmd_partition_test,
    cmd_recovery_trace,
)
from .cram.consistency_cli import (
    cmd_consistency_check,
    cmd_history,
    cmd_recovery_test,
)
from .router import (
    CapabilityAwareStrategy,
    CapabilityRegistry,
    CognitiveRouterR0,
    DecisionLog,
    DecisionStore,
    NodeCapability,
    RoundRobinStrategy,
    TaskSpec,
    candidates_from_topology,
    explain_decision,
    replay_from_store,
)
from .router.capabilities import DEFAULT_CAP_TTL_MS
import time as _time
from .network.ops import (
    cmd_fabric_diagnose,
    cmd_fabric_reconnect,
    cmd_fabric_status,
)
from .identity import (
    cmd_id_attest,
    cmd_id_revoke,
    cmd_id_rotate,
    cmd_id_status,
    cmd_id_tier,
)
from .recovery import (
    cmd_recover_rebuild,
    cmd_recover_restore,
    cmd_recover_snapshot,
    cmd_recover_status,
)
from .fence import (
    cmd_fence_demote,
    cmd_fence_probe,
    cmd_fence_reelect,
    cmd_fence_status,
)
from .obs import (
    cmd_obs_schema,
    cmd_obs_telemetry,
    cmd_obs_validate,
)
from .packaging.distribution import (
    cmd_dist_distribute,
    cmd_dist_pin_prior,
    cmd_dist_schema,
    cmd_dist_verify,
)

from .minority import (
    cmd_minority_halt,
    cmd_minority_probe,
    cmd_minority_status,
)
from .clock import (
    cmd_clock_join_check,
    cmd_clock_probe,
    cmd_clock_status,
)
from .packaging.parity import (
    cmd_parity_build_check,
    cmd_parity_check,
    cmd_parity_status,
)
from .cram.replica_cli import (
    cmd_replica_connect,
    cmd_replica_create,
    cmd_replica_promote,
    cmd_replica_repair,
    cmd_replica_serve,
    cmd_replica_status,
    cmd_replica_verify,
    cmd_replica_verify_consistency,
)


def _git_commit(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _load_twin(
    *,
    topology: str | None,
    workload: str | None,
    faults: str | None,
    seed: int,
) -> DigitalTwin:
    if topology:
        raw = json.loads(Path(topology).read_text(encoding="utf-8"))
        if "tasks" in raw or "faults" in raw:
            twin = DigitalTwin.from_topology_dict(raw)
        else:
            topo = Topology.from_dict(raw)
            wl = Workload.load(workload) if workload else Workload()
            twin = DigitalTwin.from_parts(topo, wl, seed=seed)
        twin.seed = int(seed)
    else:
        twin = DigitalTwin.build_demo(seed=seed)
        if workload:
            wl = Workload.load(workload)
            twin.tasks = []
            for t in wl.tasks:
                twin.add_task(
                    TwinTask(
                        task_id=t.task_id,
                        cpu_need=t.cpu_need,
                        duration_ticks=t.duration_ticks,
                        earliest_start=t.earliest_start,
                        preferred_capabilities=tuple(t.preferred_capabilities),
                    )
                )
    if faults:
        for f in load_faults(faults):
            twin.inject_fault(f)
    return twin


def _build_router_strategy(a, cands, root):
    """Build strategy + capability registry from CLI args."""
    strat = getattr(a, "strategy", "rr") or "rr"
    cap_root = getattr(a, "cap_store", None)
    registry = CapabilityRegistry(cap_root) if cap_root else CapabilityRegistry()
    now_ms = int(_time.time() * 1000)
    # Seed registry from candidates so capability strategy has advertisements.
    for i, c in enumerate(cands):
        if registry.get(c.node_id) is None:
            cap = NodeCapability(
                node_id=c.node_id,
                cpu=int(c.cpu),
                memory=int(c.memory),
                accelerators=tuple(x for x in c.capabilities if x != "compute"),
                supported_tasks=tuple(c.capabilities) or ("compute",),
                health=1.0,
                advertised_at_ms=now_ms,
                ttl_ms=DEFAULT_CAP_TTL_MS,
            )
            registry.upsert(
                cap,
                op_id=f"cli-seed-{c.node_id}-{now_ms}-{i}",
                epoch=0,
                trace_id=f"cli-seed-{c.node_id}",
            )
    if strat == "capability":
        return CapabilityAwareStrategy(registry), registry
    return RoundRobinStrategy(index=int(getattr(a, "seed", 0))), registry


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="mesh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("resume")
    status_p = sub.add_parser("status")
    status_p.add_argument(
        "--snapshot",
        action="store_true",
        help="Print read-only mesh observability status snapshot (JSON)",
    )
    status_p.add_argument(
        "--json",
        action="store_true",
        help="JSON output (default for --snapshot)",
    )
    status_p.add_argument(
        "--m2m",
        action="store_true",
        help="With --snapshot: print compact OBS: one-liner for council STATUS",
    )
    status_p.add_argument(
        "--node-id",
        default=None,
        help="Override snapshot node_id (default: local)",
    )
    status_p.add_argument(
        "--peers-file",
        default=None,
        help="With --snapshot: inject peer summaries from JSON file (read-only)",
    )
    status_p.add_argument(
        "--peers-json",
        default=None,
        help="With --snapshot: inject peer summaries from JSON string (read-only)",
    )
    status_p.add_argument(
        "--probe-peer",
        action="append",
        default=None,
        dest="probe_peers",
        help=(
            "With --snapshot: optional RO TLS heartbeat probe of peer id "
            "(repeatable, max 2). Requires --fabric-root. Fail-closed; no writes."
        ),
    )
    status_p.add_argument(
        "--fabric-root",
        default=None,
        help="Fabric root for --probe-peer (LocalCA layout)",
    )
    status_p.add_argument(
        "--endpoints",
        default=None,
        help="Optional endpoints.json for --probe-peer",
    )
    sub.add_parser("agent-context")

    cp = sub.add_parser("checkpoint")
    cps = cp.add_subparsers(dest="op", required=True)
    c = cps.add_parser("create")
    c.add_argument("--phase", type=int, default=0)
    c.add_argument("--module", default="unknown")
    c.add_argument("--reason", default="manual")
    c.add_argument("--next", dest="next_action", required=True)
    c.add_argument("--evidence", action="append", default=[])
    c.add_argument("--tests-passed", type=int, default=None)
    c.add_argument("--tests-failed", type=int, default=None)
    c.add_argument("--status", default=None)
    c = cps.add_parser("verify")
    c.add_argument("id")
    cps.add_parser("latest")
    cps.add_parser("list")

    twin = sub.add_parser("twin")
    twins = twin.add_subparsers(dest="op", required=True)

    run_p = twins.add_parser("run", help="Run twin simulation (demo or JSON inputs)")
    run_p.add_argument("--seed", type=int, default=42)
    run_p.add_argument("--ticks", type=int, default=20)
    run_p.add_argument("--topology", type=str, default=None)
    run_p.add_argument("--workload", type=str, default=None)
    run_p.add_argument("--faults", type=str, default=None)
    run_p.add_argument("--fault", action="append", default=[], metavar="SPEC")
    run_p.add_argument("--json", action="store_true")
    run_p.add_argument("--summary", action="store_true")

    top_p = twins.add_parser("topology", help="Save/load demo or file topology")
    tops = top_p.add_subparsers(dest="top_op", required=True)
    save_p = tops.add_parser("save")
    save_p.add_argument("path")
    save_p.add_argument("--seed", type=int, default=42)
    save_p.add_argument("--from", dest="from_path", default=None)
    save_p.add_argument(
        "--schema", choices=("legacy", "chatgpt"), default="legacy"
    )
    load_p = tops.add_parser("load")
    load_p.add_argument("path")
    load_p.add_argument("--json", action="store_true")

    bench_p = twins.add_parser("bench", help="Benchmark schedule latency / utilization")
    bench_p.add_argument("--seed", type=int, default=42)
    bench_p.add_argument("--ticks", type=int, default=20)
    bench_p.add_argument("--topology", type=str, default=None)
    bench_p.add_argument("--workload", type=str, default=None)
    bench_p.add_argument("--faults", type=str, default=None)
    bench_p.add_argument("--fault", action="append", default=[])
    bench_p.add_argument("--json", action="store_true")

    bench_cmd = sub.add_parser("benchmark")
    bench_subs = bench_cmd.add_subparsers(dest="op", required=True)
    br = bench_subs.add_parser("run")
    br.add_argument("suite", choices=("twin-basic",))
    br.add_argument("--seed", type=int, default=42)
    br.add_argument("--ticks", type=int, default=20)
    br.add_argument("--json", action="store_true")

    audit_cmd = sub.add_parser("audit")
    audit_subs = audit_cmd.add_subparsers(dest="op", required=True)
    audit_subs.add_parser("git")

    safety_cmd = sub.add_parser("safety")
    safety_subs = safety_cmd.add_subparsers(dest="op", required=True)
    safety_subs.add_parser("status")


    cram_cmd = sub.add_parser("cram", help="C-RAM put/get/verify/fsck")
    cram_subs = cram_cmd.add_subparsers(dest="op", required=True)
    cram_put = cram_subs.add_parser("put", help="Store content; print content hash")
    cram_put.add_argument("--root", type=str, default=None)
    cram_put.add_argument(
        "--file", type=str, default=None, help="Read bytes from file (default: stdin)"
    )
    cram_put.add_argument("data", nargs="?", default=None, help="Literal string payload")
    cram_get = cram_subs.add_parser("get", help="Fetch object bytes by key")
    cram_get.add_argument("key")
    cram_get.add_argument("--root", type=str, default=None)
    cram_ver = cram_subs.add_parser("verify", help="Verify blob integrity")
    cram_ver.add_argument("key")
    cram_ver.add_argument("--root", type=str, default=None)
    cram_fsck = cram_subs.add_parser("fsck", help="Filesystem check; report orphans/corrupt")
    cram_fsck.add_argument("--root", type=str, default=None)
    cram_fsck.add_argument("--json", action="store_true")

    cram_trace = cram_subs.add_parser(
        "trace", help="Reconstruct Task→Router→Network→C-RAM→Checkpoint for operation_id"
    )
    cram_trace.add_argument("operation_id")
    cram_trace.add_argument("--root", type=str, default=None)

    # Phase 5B — consistency / recovery / history
    cram_cons = cram_subs.add_parser(
        "consistency", help="C-RAM consistency check (Phase 5B)"
    )
    cons_subs = cram_cons.add_subparsers(dest="consistency_op", required=True)
    cc = cons_subs.add_parser("check", help="Check object consistency / dual-primary")
    cc.add_argument("object")
    cc.add_argument("--root", type=str, default=None)
    cc.add_argument("--topology", type=str, default=None)
    cc.add_argument("--seed", type=int, default=42)

    cram_rec = cram_subs.add_parser(
        "recovery", help="C-RAM formal recovery protocol (Phase 5B)"
    )
    rec_subs = cram_rec.add_subparsers(dest="recovery_op", required=True)
    rt = rec_subs.add_parser("test", help="Run recovery FSM test (DETECT→…→RESUME)")
    rt.add_argument("object", nargs="?", default=None, help="Object hash (or use --put)")
    rt.add_argument("--put", type=str, default=None, help="Seed literal bytes then recover")
    rt.add_argument("--reason", type=str, default="primary_unavailable")
    rt.add_argument("--root", type=str, default=None)
    rt.add_argument("--topology", type=str, default=None)
    rt.add_argument("--seed", type=int, default=42)

    cram_hist = cram_subs.add_parser(
        "history", help="Show version/conflict/replication history for object"
    )
    cram_hist.add_argument("object")
    cram_hist.add_argument("--root", type=str, default=None)
    cram_hist.add_argument("--topology", type=str, default=None)
    cram_hist.add_argument("--seed", type=int, default=42)

    # Phase 5C — durability / partition / recovery trace
    cram_dur = cram_subs.add_parser(
        "durability", help="C-RAM durability / WAL / crash invariants (Phase 5C)"
    )
    dur_subs = cram_dur.add_subparsers(dest="durability_op", required=True)
    dc = dur_subs.add_parser("check", help="WAL/fsync + crash-invariant report")
    dc.add_argument("--root", type=str, default=None)

    cram_part = cram_subs.add_parser(
        "partition", help="N=2 adversarial partition suite (Phase 5C)"
    )
    part_subs = cram_part.add_subparsers(dest="partition_op", required=True)
    pt = part_subs.add_parser("test", help="Run partition suite (minority=0, dual=0, heal)")
    pt.add_argument("--root", type=str, default=None)

    # Extend recovery with trace subcommand (keep existing test)
    rt_trace = rec_subs.add_parser(
        "trace", help="Trace WAL + recovery evidence (Phase 5C)"
    )
    rt_trace.add_argument("object", nargs="?", default=None)
    rt_trace.add_argument("--root", type=str, default=None)

    cram_repl = cram_subs.add_parser("replica", help="C-RAM N=2 controlled replica ops")
    repl_subs = cram_repl.add_subparsers(dest="replica_op", required=True)
    rc = repl_subs.add_parser("create", help="Create+sync replica (hash or --put)")
    rc.add_argument("hash", nargs="?", default=None)
    rc.add_argument("--put", type=str, default=None, help="Literal bytes to put_replicated")
    rc.add_argument("--file", type=str, default=None, help="File bytes to put_replicated")
    rc.add_argument("--root", type=str, default=None)
    rc.add_argument("--topology", type=str, default=None)
    rc.add_argument("--seed", type=int, default=42)
    rs = repl_subs.add_parser("status", help="Replica status JSON")
    rs.add_argument("hash")
    rs.add_argument("--root", type=str, default=None)
    rs.add_argument("--topology", type=str, default=None)
    rs.add_argument("--seed", type=int, default=42)
    rv = repl_subs.add_parser("verify", help="Verify replica integrity")
    rv.add_argument("hash")
    rv.add_argument("--root", type=str, default=None)
    rv.add_argument("--topology", type=str, default=None)
    rv.add_argument("--seed", type=int, default=42)
    rr = repl_subs.add_parser("repair", help="Repair / re-sync replica")
    rr.add_argument("hash")
    rr.add_argument("--root", type=str, default=None)
    rr.add_argument("--topology", type=str, default=None)
    rr.add_argument("--seed", type=int, default=42)
    rp = repl_subs.add_parser("promote", help="Promote secondary with fencing")
    rp.add_argument("hash")
    rp.add_argument("--node", type=str, default=None)
    rp.add_argument("--root", type=str, default=None)
    rp.add_argument("--topology", type=str, default=None)
    rp.add_argument("--seed", type=int, default=42)
    rvc = repl_subs.add_parser(
        "verify-consistency", help="Merkle-diff consistency (optional --repair)"
    )
    rvc.add_argument("hash")
    rvc.add_argument("--repair", action="store_true")
    rvc.add_argument("--root", type=str, default=None)
    rvc.add_argument("--topology", type=str, default=None)
    rvc.add_argument("--seed", type=int, default=42)

    rserve = repl_subs.add_parser(
        "serve", help="Out-of-process secondary over Unix socket (Cycle 7)"
    )
    rserve.add_argument("--socket", type=str, required=True, help="Unix socket path")
    rserve.add_argument("--root", type=str, default=None)
    rserve.add_argument("--node-id", type=str, default="node-02")
    rserve.add_argument("--ready-file", type=str, default=None)

    rconn = repl_subs.add_parser(
        "connect", help="Connect to replica serve (--socket)"
    )
    rconn.add_argument("--socket", type=str, required=True)
    rconn.add_argument("--root", type=str, default=None)
    rconn.add_argument("--put", type=str, default=None, help="Literal bytes to PUT")
    rconn.add_argument("--file", type=str, default=None, help="File bytes to PUT")
    rconn.add_argument("--get", type=str, default=None, help="GET content hash")
    rconn.add_argument("--ping", action="store_true")


    fabric_cmd = sub.add_parser(
        "fabric", help="TLS fabric ops UX: status / diagnose / reconnect"
    )
    fabric_subs = fabric_cmd.add_subparsers(dest="fabric_op", required=True)
    fstat = fabric_subs.add_parser("status", help="Local fabric status (certs + peer probes)")
    fstat.add_argument("--fabric-root", type=str, required=True, help="LocalCA / fabric root")
    fstat.add_argument("--node-id", type=str, required=True, help="Local node_id (leaf CN)")
    fstat.add_argument("--endpoints", type=str, default=None, help="endpoints.json path")
    fstat.add_argument("--json", action="store_true", help="JSON output")
    fstat.add_argument("--no-probe", action="store_true", help="Skip live peer probes")
    fstat.add_argument(
        "--tls-required",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require TLS (default true; no plaintext fallback)",
    )
    fdiag = fabric_subs.add_parser("diagnose", help="Diagnose fabric certs / peers")
    fdiag.add_argument("--fabric-root", type=str, required=True)
    fdiag.add_argument("--node-id", type=str, required=True)
    fdiag.add_argument("--endpoints", type=str, default=None)
    fdiag.add_argument("--json", action="store_true")
    fdiag.add_argument("--no-probe", action="store_true")
    fdiag.add_argument(
        "--tls-required",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    frec = fabric_subs.add_parser(
        "reconnect", help="Safe TLS reconnect of sessions (fail-closed)"
    )
    frec.add_argument("--fabric-root", type=str, required=True)
    frec.add_argument("--node-id", type=str, required=True)
    frec.add_argument("--peer", type=str, default=None, help="Peer node_id (default: all)")
    frec.add_argument("--endpoints", type=str, default=None)
    frec.add_argument("--json", action="store_true")
    frec.add_argument("--attempts", type=int, default=2)
    frec.add_argument(
        "--tls-required",
        action=argparse.BooleanOptionalAction,
        default=True,
    )


    id_cmd = sub.add_parser(
        "id", help="Identity + attestation + trust tiers (H1): status/attest/tier/rotate/revoke"
    )
    id_subs = id_cmd.add_subparsers(dest="id_op", required=True)
    id_stat = id_subs.add_parser("status", help="Show local identity record + pinned-only state")
    id_stat.add_argument("--fabric-root", type=str, required=True, help="LocalCA / fabric root")
    id_stat.add_argument("--node-id", type=str, required=True)
    id_stat.add_argument("--json", action="store_true")
    id_att = id_subs.add_parser("attest", help="Attest leaf under local CA (fail-closed)")
    id_att.add_argument("--fabric-root", type=str, required=True)
    id_att.add_argument("--node-id", type=str, required=True)
    id_att.add_argument("--expected", type=str, default=None, help="Expected node_id (default: --node-id)")
    id_att.add_argument("--mode", type=str, default="tls", help="Transport mode (tls only; plaintext forbidden)")
    id_att.add_argument("--json", action="store_true")
    id_tier = id_subs.add_parser("tier", help="Read/assign/downgrade trust tier T0..T3")
    id_tier.add_argument("--fabric-root", type=str, required=True)
    id_tier.add_argument("--node-id", type=str, required=True)
    id_tier.add_argument("--set", dest="tier_set", type=str, default=None, help="Set tier T0..T3")
    id_tier.add_argument("--pin", action="store_true", help="Operator pin (required for T3 upgrade)")
    id_tier.add_argument("--downgrade", action="store_true", help="One-step downgrade T3→…→T0")
    id_tier.add_argument("--reason", type=str, default="")
    id_tier.add_argument("--json", action="store_true")
    id_rot = id_subs.add_parser("rotate", help="Rotate leaf cert (no silent identity downgrade)")
    id_rot.add_argument("--fabric-root", type=str, required=True)
    id_rot.add_argument("--node-id", type=str, required=True)
    id_rot.add_argument("--days", type=int, default=825)
    id_rot.add_argument("--no-keep-tier", action="store_true", help="Do not preserve prior tier")
    id_rot.add_argument("--json", action="store_true")
    id_rev = id_subs.add_parser("revoke", help="Revoke identity (force T0 + pinned-only abort)")
    id_rev.add_argument("--fabric-root", type=str, required=True)
    id_rev.add_argument("--node-id", type=str, required=True)
    id_rev.add_argument("--reason", type=str, default="revoked")
    id_rev.add_argument("--json", action="store_true")

    recover_cmd = sub.add_parser(
        "recover",
        help="Recovery + rebuild (H2): status/snapshot/restore/rebuild; ABORT→snapshot restore",
    )
    recover_subs = recover_cmd.add_subparsers(dest="recover_op", required=True)
    rec_stat = recover_subs.add_parser("status", help="Show durable/WAL/abort_restore status")
    rec_stat.add_argument("--data-root", type=str, required=True, help="Recovery data root")
    rec_stat.add_argument("--json", action="store_true")
    rec_snap = recover_subs.add_parser(
        "snapshot", help="Create / list / verify content-hashed recovery snapshot"
    )
    rec_snap.add_argument("--data-root", type=str, required=True)
    rec_snap.add_argument("--reason", type=str, default="manual")
    rec_snap.add_argument("--list", dest="snap_list", action="store_true")
    rec_snap.add_argument("--verify", type=str, default=None, help="Verify SNAP-id integrity")
    rec_snap.add_argument("--json", action="store_true")
    rec_rest = recover_subs.add_parser(
        "restore", help="Restore durable state from verified snapshot (fail-closed)"
    )
    rec_rest.add_argument("--data-root", type=str, required=True)
    rec_rest.add_argument("--snapshot", type=str, default=None, help="SNAP-id (default: last_good)")
    rec_rest.add_argument(
        "--mode", type=str, default="local", help="Transport mode (local only; plaintext forbidden)"
    )
    rec_rest.add_argument("--json", action="store_true")
    rec_reb = recover_subs.add_parser(
        "rebuild", help="Rebuild from last good snapshot + WAL; ABORT→snapshot restore"
    )
    rec_reb.add_argument("--data-root", type=str, required=True)
    rec_reb.add_argument("--snapshot", type=str, default=None)
    rec_reb.add_argument("--mode", type=str, default="local")
    rec_reb.add_argument("--json", action="store_true")

    fence_cmd = sub.add_parser(
        "fence",
        help="Dual-primary fence (H3): status/probe/demote/reelect; ABORT→demote+re-elect @N2",
    )
    fence_subs = fence_cmd.add_subparsers(dest="fence_op", required=True)
    fen_stat = fence_subs.add_parser("status", help="Show fence epoch/roles/abort status")
    fen_stat.add_argument("--data-root", type=str, required=True, help="Fence data root")
    fen_stat.add_argument("--json", action="store_true")
    fen_probe = fence_subs.add_parser(
        "probe", help="Probe dual-primary @N2; ABORT→demote+re-elect when auto-fence"
    )
    fen_probe.add_argument("--data-root", type=str, required=True)
    fen_probe.add_argument(
        "--no-auto-fence",
        dest="auto_fence",
        action="store_false",
        help="Detect only; enter abort without demote+re-elect",
    )
    fen_probe.set_defaults(auto_fence=True)
    fen_probe.add_argument("--preferred", type=str, default=None, help="Preferred primary node id")
    fen_probe.add_argument(
        "--mode", type=str, default="local", help="Transport mode (local only; plaintext forbidden)"
    )
    fen_probe.add_argument("--json", action="store_true")
    fen_dem = fence_subs.add_parser("demote", help="Demote a primary contender")
    fen_dem.add_argument("--data-root", type=str, required=True)
    fen_dem.add_argument("--node-id", type=str, required=True)
    fen_dem.add_argument("--mode", type=str, default="local")
    fen_dem.add_argument("--json", action="store_true")
    fen_ree = fence_subs.add_parser("reelect", help="Re-elect sole writable primary @N2")
    fen_ree.add_argument("--data-root", type=str, required=True)
    fen_ree.add_argument("--preferred", type=str, default=None)
    fen_ree.add_argument("--mode", type=str, default="local")
    fen_ree.add_argument("--json", action="store_true")

    minority_cmd = sub.add_parser(
        "minority",
        help="Minority-write safety (H6): status/probe/halt; ABORT→halt writes @N2",
    )
    minority_subs = minority_cmd.add_subparsers(dest="minority_op", required=True)
    min_stat = minority_subs.add_parser("status", help="Show minority-write / halt status")
    min_stat.add_argument("--data-root", type=str, required=True, help="Minority data root")
    min_stat.add_argument("--json", action="store_true")
    min_probe = minority_subs.add_parser(
        "probe", help="Probe minority-write @N2; ABORT→halt writes when auto-halt"
    )
    min_probe.add_argument("--data-root", type=str, required=True)
    min_probe.add_argument(
        "--no-auto-halt",
        dest="auto_halt",
        action="store_false",
        help="Detect only; enter abort without auto halt clear",
    )
    min_probe.set_defaults(auto_halt=True)
    min_probe.add_argument(
        "--mode", type=str, default="local", help="Transport mode (local only; plaintext forbidden)"
    )
    min_probe.add_argument("--json", action="store_true")
    min_halt = minority_subs.add_parser("halt", help="ABORT→halt writes (refuse further writes)")
    min_halt.add_argument("--data-root", type=str, required=True)
    min_halt.add_argument("--reason", type=str, default="operator halt")
    min_halt.add_argument("--mode", type=str, default="local")
    min_halt.add_argument("--json", action="store_true")

    clock_cmd = sub.add_parser(
        "clock",
        help="Clock-skew join fence (H7): status/probe/join-check; ABORT→refuse join @N2",
    )
    clock_subs = clock_cmd.add_subparsers(dest="clock_op", required=True)
    clk_stat = clock_subs.add_parser("status", help="Show clock-skew / refuse-join status")
    clk_stat.add_argument("--data-root", type=str, required=True, help="Clock data root")
    clk_stat.add_argument("--json", action="store_true")
    clk_probe = clock_subs.add_parser(
        "probe", help="Probe clock-skew @N2; ABORT→refuse join when auto-refuse"
    )
    clk_probe.add_argument("--data-root", type=str, required=True)
    clk_probe.add_argument(
        "--no-auto-refuse",
        dest="auto_refuse",
        action="store_false",
        help="Detect only; enter abort without auto refuse clear",
    )
    clk_probe.set_defaults(auto_refuse=True)
    clk_probe.add_argument(
        "--mode", type=str, default="local", help="Transport mode (local only; plaintext forbidden)"
    )
    clk_probe.add_argument("--json", action="store_true")
    clk_join = clock_subs.add_parser(
        "join-check", help="Check join; ABORT→refuse join on excess skew"
    )
    clk_join.add_argument("--data-root", type=str, required=True)
    clk_join.add_argument("--node-id", type=str, required=True, help="Joining node id")
    clk_join.add_argument("--peer-wall-ms", type=int, default=None, help="Peer wall ms (diagnostic)")
    clk_join.add_argument("--local-wall-ms", type=int, default=None, help="Local wall ms (diagnostic)")
    clk_join.add_argument(
        "--no-auto-refuse",
        dest="auto_refuse",
        action="store_false",
    )
    clk_join.set_defaults(auto_refuse=True)
    clk_join.add_argument("--mode", type=str, default="local")
    clk_join.add_argument("--json", action="store_true")

    parity_cmd = sub.add_parser(
        "parity",
        help="Manifest parity @N2 (H8): status/check/build-check; ABORT→reject build",
    )
    parity_subs = parity_cmd.add_subparsers(dest="parity_op", required=True)
    par_stat = parity_subs.add_parser("status", help="Show manifest-parity / reject-build status")
    par_stat.add_argument("--data-root", type=str, required=True, help="Parity data root")
    par_stat.add_argument("--json", action="store_true")
    par_check = parity_subs.add_parser(
        "check", help="Check recorded N2 builds; ABORT→reject build on mismatch"
    )
    par_check.add_argument("--data-root", type=str, required=True)
    par_check.add_argument(
        "--no-auto-reject",
        dest="auto_reject",
        action="store_false",
        help="Detect only; enter abort without auto reject clear",
    )
    par_check.set_defaults(auto_reject=True)
    par_check.add_argument(
        "--mode", type=str, default="local", help="Transport mode (local only; plaintext forbidden)"
    )
    par_check.add_argument("--json", action="store_true")
    par_build = parity_subs.add_parser(
        "build-check",
        help="Concurrent build byte-equality @N2 (or compare two manifest files)",
    )
    par_build.add_argument("--data-root", type=str, required=True)
    par_build.add_argument("--manifest-a", type=str, default=None, help="Left manifest JSON path")
    par_build.add_argument("--manifest-b", type=str, default=None, help="Right manifest JSON path")
    par_build.add_argument(
        "--no-auto-reject",
        dest="auto_reject",
        action="store_false",
    )
    par_build.set_defaults(auto_reject=True)
    par_build.add_argument("--mode", type=str, default="local")
    par_build.add_argument("--json", action="store_true")

    obs_cmd = sub.add_parser(
        "obs",
        help="OBS telemetry contract (H4): telemetry/validate/schema; ABORT→block CP mint",
    )
    obs_subs = obs_cmd.add_subparsers(dest="obs_op", required=True)
    obs_tel = obs_subs.add_parser(
        "telemetry", help="Emit mesh.obs/v1 from local status snapshot"
    )
    obs_tel.add_argument("--repo", type=str, default=".", help="Repo root for snapshot")
    obs_tel.add_argument("--node-id", type=str, default="local")
    obs_tel.add_argument(
        "--cadence",
        type=str,
        default="10s",
        choices=["1s", "10s", "60s"],
        help="Cadence tier 1s/10s/60s",
    )
    obs_tel.add_argument(
        "--packaging",
        type=str,
        default="0.18-H4-obs-telemetry",
        help="Packaging label embedded in contract",
    )
    obs_tel.add_argument("--cycle", type=int, default=None, help="Override cycle int")
    obs_tel.add_argument(
        "--mode", type=str, default="local", help="Transport mode (plaintext forbidden)"
    )
    obs_tel.add_argument("--json", action="store_true", default=True)
    obs_tel.add_argument(
        "--m2m", action="store_true", help="Compact OBS telemetry one-liner"
    )
    obs_tel.add_argument(
        "--text", action="store_true", help="Human text instead of JSON"
    )
    obs_val = obs_subs.add_parser(
        "validate", help="Validate mesh.obs/v1 JSON; ABORT→block CP on breach"
    )
    obs_val.add_argument(
        "--file",
        type=str,
        default=None,
        help="Telemetry JSON path (default: stdin / -)",
    )
    obs_val.add_argument(
        "--stdin",
        action="store_true",
        help="Read telemetry JSON from stdin",
    )
    obs_sch = obs_subs.add_parser("schema", help="Print active mesh.obs/v1 descriptor")
    obs_sch.add_argument("--json", action="store_true", default=True)
    obs_sch.add_argument("--text", action="store_true")

    dist_cmd = sub.add_parser(
        "dist",
        help="Packaging distribution (H5): distribute/verify/pin-prior; ABORT→pin prior",
    )
    dist_subs = dist_cmd.add_subparsers(dest="dist_op", required=True)
    dist_dist = dist_subs.add_parser(
        "distribute", help="Mint mesh.bundle/v1 under dist/releases/0.18.x"
    )
    dist_dist.add_argument("--repo", type=str, default=".", help="Repo root")
    dist_dist.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output dir (default: dist/releases/<ver>)",
    )
    dist_dist.add_argument("--name", type=str, default="neural-mesh-gia-dist")
    dist_dist.add_argument("--channel", type=str, default="0.18.x")
    dist_dist.add_argument("--cycle", type=int, default=38)
    dist_dist.add_argument(
        "--mode", type=str, default="local", help="Transport mode (plaintext forbidden)"
    )
    dist_dist.add_argument("--json", action="store_true", default=True)
    dist_dist.add_argument("--m2m", action="store_true", help="Compact DIST one-liner")
    dist_dist.add_argument("--text", action="store_true", help="Human text instead of JSON")
    dist_ver = dist_subs.add_parser(
        "verify", help="Verify mesh.bundle/v1 JSON; ABORT→pin prior on breach"
    )
    dist_ver.add_argument(
        "--file", type=str, default=None, help="Distribution JSON path (default: stdin / -)"
    )
    dist_ver.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    dist_ver.add_argument("--repo", type=str, default=".", help="Repo for replay registry")
    dist_ver.add_argument(
        "--mark-replay-seen",
        action="store_true",
        help="Consume nonce into replay registry (second consume aborts)",
    )
    dist_pin = dist_subs.add_parser(
        "pin-prior", help="ABORT→pin prior known-good; never retag v0.16.3/v0.17.0"
    )
    dist_pin.add_argument("--repo", type=str, default=".")
    dist_pin.add_argument("--reason", type=str, default="ABORT distribution breach")
    dist_pin.add_argument("--ver", type=str, default="0.17.0", help="Prior version label")
    dist_pin.add_argument("--json", action="store_true", default=True)
    dist_pin.add_argument("--text", action="store_true")
    dist_sch = dist_subs.add_parser("schema", help="Print active mesh.bundle/v1 descriptor")
    dist_sch.add_argument("--json", action="store_true", default=True)
    dist_sch.add_argument("--text", action="store_true")

    router_cmd = sub.add_parser("router", help="Cognitive Router R0/R1 (Phase 3)")
    router_subs = router_cmd.add_subparsers(dest="op", required=True)
    rex = router_subs.add_parser("explain", help="Explain last/logged decision for task_id")
    rex.add_argument("task_id")
    rex.add_argument("--log", type=str, default=None, help="Decision JSONL path")
    rex.add_argument("--topology", type=str, default=None)
    rex.add_argument("--seed", type=int, default=0)
    rex.add_argument(
        "--requires-network", action="store_true", help="Simulate network-requiring task"
    )
    rex.add_argument(
        "--capability", action="append", default=[], help="Required capability (repeatable)"
    )
    rex.add_argument(
        "--strategy",
        choices=("rr", "capability"),
        default="rr",
        help="Routing strategy when live-routing for explain",
    )
    rex.add_argument("--cap-store", type=str, default=None)
    rroute = router_subs.add_parser("route", help="Route a TaskSpec (demo/topology)")
    rroute.add_argument("task_id")
    rroute.add_argument("--topology", type=str, default=None)
    rroute.add_argument("--seed", type=int, default=0)
    rroute.add_argument("--capability", action="append", default=[])
    rroute.add_argument("--requires-network", action="store_true")
    rroute.add_argument("--requires-physical", action="store_true")
    rroute.add_argument("--log", type=str, default=None)
    rroute.add_argument("--json", action="store_true")
    rroute.add_argument("--store", type=str, default=None, help="C-RAM DecisionStore root")
    rroute.add_argument(
        "--strategy",
        choices=("rr", "capability"),
        default="rr",
        help="Routing strategy: rr (R0) or capability (R1)",
    )
    rroute.add_argument(
        "--cap-store",
        type=str,
        default=None,
        help="C-RAM CapabilityRegistry root (R1)",
    )
    rreplay = router_subs.add_parser(
        "replay", help="Replay RouteDecision by trace_id (byte-identical)"
    )
    rreplay.add_argument("trace_id")
    rreplay.add_argument("--store", type=str, required=True, help="C-RAM DecisionStore root")
    rreplay.add_argument("--json", action="store_true")

    mino_cmd = sub.add_parser("minogan", help="Minogan.ai scorer (CP-0088): local loopback service")
    mino_subs = mino_cmd.add_subparsers(dest="mino_op", required=True)
    mino_srv = mino_subs.add_parser("serve", help="Serve POST /v1/score + GET /health on loopback")
    mino_srv.add_argument("--host", type=str, default="127.0.0.1", help="Loopback only")
    mino_srv.add_argument("--port", type=int, default=8787)
    mino_srv.add_argument("--memory-root", type=str, required=True, help="AgentMemory root dir")
    mino_srv.add_argument(
        "--tokens-file",
        type=str,
        default=None,
        help="JSON {tenants:{org:[sha256:..]}} outside the repo (else $MESH_MINOGAN_TOKENS_FILE / $MESH_MINOGAN_TOKENS)",
    )
    mino_subs.add_parser("hash-token", help="Read a token on stdin; print sha256:<hex> for the tokens file")

    a = parser.parse_args(argv)
    if a.cmd == "minogan":
        if a.mino_op == "hash-token":
            from .minogan.service import hash_token

            print(hash_token(sys.stdin.readline().strip()))
            return
        from .minogan.service import serve

        serve(a.memory_root, host=a.host, port=a.port, tokens_file=a.tokens_file)
        return
    root = Path.cwd()
    mgr = CheckpointManager(root)

    if a.cmd == "init":
        mgr.save_state(mgr.load_state())
        ObsidianSync(root).bootstrap()
        ensure_default_policy(root)
        print("initialized")
    elif a.cmd == "status":
        if getattr(a, "snapshot", False):
            injected = []
            peers_file = getattr(a, "peers_file", None)
            peers_json = getattr(a, "peers_json", None)
            if peers_file:
                injected = merge_peer_summaries(injected, load_peers_json(peers_file))
            if peers_json:
                injected = merge_peer_summaries(injected, parse_peers_json(peers_json))
            probe_ids = getattr(a, "probe_peers", None) or []
            if probe_ids:
                from .obs_peers import MAX_OBS_PEER_PROBES, probe_peers_readonly

                if len(probe_ids) > MAX_OBS_PEER_PROBES:
                    raise SystemExit(
                        f"--probe-peer refuses N>{MAX_OBS_PEER_PROBES} "
                        "(no Raft / N>2 / multi-primary)"
                    )
                fabric_root = getattr(a, "fabric_root", None)
                if not fabric_root:
                    raise SystemExit("--probe-peer requires --fabric-root")
                local_id = getattr(a, "node_id", None) or "local"
                probed = probe_peers_readonly(
                    local_node_id=local_id,
                    peers=list(probe_ids),
                    fabric_root=fabric_root,
                    endpoints_path=getattr(a, "endpoints", None),
                )
                injected = merge_peer_summaries(injected, probed)
            snap = snapshot(
                root,
                node_id=getattr(a, "node_id", None),
                peers=injected or None,
            )
            if getattr(a, "m2m", False):
                print(format_obs_m2m(snap))
            else:
                # --json is default for snapshot; keep flag for explicit callers
                print(snapshot_to_json(snap), end="")
        else:
            print(mgr.load_state().model_dump_json(indent=2))
    elif a.cmd == "resume":
        s = mgr.load_state()
        print("NEURAL MESH RECOVERY")
        print(s.model_dump_json(indent=2))
        na = root / ".project_state" / "NEXT_ACTION.md"
        if na.exists():
            print("--- NEXT_ACTION ---")
            print(na.read_text(encoding="utf-8"))
    elif a.cmd == "agent-context":
        s = mgr.load_state()
        p = root / ".agent_context.md"
        p.write_text(
            "# AGENT CONTEXT\n\nRead .project_state/CURRENT_STATE.md, "
            ".project_state/NEXT_ACTION.md, .project_state/CHECKPOINT.json and "
            ".project_state/DECISIONS.md before changing code.\n\n"
            + s.model_dump_json(indent=2),
            encoding="utf-8",
        )
        print(p)
    elif a.cmd == "checkpoint":
        if a.op == "create":
            tests = {}
            if a.tests_passed is not None:
                tests["passed"] = a.tests_passed
            if a.tests_failed is not None:
                tests["failed"] = a.tests_failed
            cp_obj = mgr.create(
                a.phase,
                a.module,
                a.reason,
                a.next_action,
                git_commit=_git_commit(root),
                tests=tests or None,
                evidence=a.evidence,
                status=a.status,
            )
            ObsidianSync(root).record_checkpoint(cp_obj)
            print(cp_obj.checkpoint_id)
        elif a.op == "verify":
            print("VERIFIED" if mgr.verify(a.id) else "FAILED")
        elif a.op == "latest":
            latest = mgr.latest()
            print(latest.model_dump_json(indent=2) if latest else "NONE")
        elif a.op == "list":
            print("\n".join(mgr.list_ids()))
    elif a.cmd == "audit":
        if a.op == "git":
            result = audit_git(root)
            print(result.status_line)
            print(f"branch: {result.branch}")
            print(f"commit: {result.commit}")
            print(f"modified: {len(result.modified)}")
            for p in result.modified:
                print(f"  M {p}")
            print(f"untracked: {len(result.untracked)}")
            for p in result.untracked:
                print(f"  ? {p}")
            if result.error:
                print(f"error: {result.error}")
            raise SystemExit(0 if result.ok else 1)
    elif a.cmd == "safety":
        if a.op == "status":
            ensure_default_policy(root)
            st = safety_status(root)
            print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
            print(f"SAFETY: {st.status}")
    elif a.cmd == "benchmark":
        if a.op == "run" and a.suite == "twin-basic":
            result = run_twin_basic(
                root,
                seed=a.seed,
                ticks=a.ticks,
                git_commit=_git_commit(root),
            )
            if a.json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(
                    f"experiment_id={result.experiment_id} "
                    f"duration_ms={result.duration_ms}"
                )
                print(f"artifacts={','.join(result.artifacts)}")
                print(
                    f"topology_hash={result.metrics.get('topology_hash')} "
                    f"checkpoint_id={result.metrics.get('checkpoint_id')}"
                )

    elif a.cmd == "cram":
        root = Path(a.root) if getattr(a, "root", None) else root
        if a.op == "put":
            if a.file:
                content = Path(a.file).read_bytes()
            elif a.data is not None:
                content = a.data.encode("utf-8")
            else:
                content = sys.stdin.buffer.read()
            raise SystemExit(cmd_put(content, root=root))
        elif a.op == "get":
            raise SystemExit(cmd_get(a.key, root=root))
        elif a.op == "verify":
            raise SystemExit(cmd_verify(a.key, root=root))
        elif a.op == "fsck":
            raise SystemExit(cmd_fsck(root=root, as_json=bool(a.json)))
        elif a.op == "trace":
            raise SystemExit(cmd_trace(a.operation_id, root=root))
        elif a.op == "consistency":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            if a.consistency_op == "check":
                raise SystemExit(
                    cmd_consistency_check(
                        a.object,
                        root=rroot,
                        topology_path=getattr(a, "topology", None),
                        seed=int(getattr(a, "seed", 42)),
                    )
                )
        elif a.op == "recovery":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            if a.recovery_op == "test":
                raise SystemExit(
                    cmd_recovery_test(
                        root=rroot,
                        object_id=getattr(a, "object", None),
                        put=getattr(a, "put", None),
                        reason=getattr(a, "reason", "primary_unavailable"),
                        topology_path=getattr(a, "topology", None),
                        seed=int(getattr(a, "seed", 42)),
                    )
                )
            elif a.recovery_op == "trace":
                raise SystemExit(
                    cmd_recovery_trace(
                        root=rroot,
                        object_id=getattr(a, "object", None),
                    )
                )
        elif a.op == "history":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            raise SystemExit(
                cmd_history(
                    a.object,
                    root=rroot,
                    topology_path=getattr(a, "topology", None),
                    seed=int(getattr(a, "seed", 42)),
                )
            )
        elif a.op == "durability":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            if a.durability_op == "check":
                raise SystemExit(cmd_durability_check(root=rroot))
        elif a.op == "partition":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            if a.partition_op == "test":
                raise SystemExit(cmd_partition_test(root=rroot))
        elif a.op == "replica":
            rroot = Path(a.root) if getattr(a, "root", None) else root
            topo = getattr(a, "topology", None)
            seed = int(getattr(a, "seed", 42))
            if a.replica_op == "create":
                content = None
                if getattr(a, "file", None):
                    content = Path(a.file).read_bytes()
                elif getattr(a, "put", None) is not None:
                    content = a.put.encode("utf-8")
                raise SystemExit(
                    cmd_replica_create(
                        a.hash,
                        content=content,
                        root=rroot,
                        topology_path=topo,
                        seed=seed,
                    )
                )
            elif a.replica_op == "status":
                raise SystemExit(
                    cmd_replica_status(
                        a.hash, root=rroot, topology_path=topo, seed=seed
                    )
                )
            elif a.replica_op == "verify":
                raise SystemExit(
                    cmd_replica_verify(
                        a.hash, root=rroot, topology_path=topo, seed=seed
                    )
                )
            elif a.replica_op == "repair":
                raise SystemExit(
                    cmd_replica_repair(
                        a.hash, root=rroot, topology_path=topo, seed=seed
                    )
                )
            elif a.replica_op == "promote":
                raise SystemExit(
                    cmd_replica_promote(
                        a.hash,
                        root=rroot,
                        node_id=getattr(a, "node", None),
                        topology_path=topo,
                        seed=seed,
                    )
                )
            elif a.replica_op == "verify-consistency":
                raise SystemExit(
                    cmd_replica_verify_consistency(
                        a.hash,
                        root=rroot,
                        topology_path=topo,
                        seed=seed,
                        repair=bool(getattr(a, "repair", False)),
                    )
                )
            elif a.replica_op == "serve":
                raise SystemExit(
                    cmd_replica_serve(
                        root=rroot,
                        socket=a.socket,
                        node_id=getattr(a, "node_id", "node-02"),
                        ready_file=getattr(a, "ready_file", None),
                    )
                )
            elif a.replica_op == "connect":
                content = None
                if getattr(a, "file", None):
                    content = Path(a.file).read_bytes()
                elif getattr(a, "put", None) is not None:
                    content = a.put.encode("utf-8")
                raise SystemExit(
                    cmd_replica_connect(
                        root=rroot,
                        socket=a.socket,
                        put=content,
                        get_hash=getattr(a, "get", None),
                        ping=bool(getattr(a, "ping", False)),
                    )
                )

    elif a.cmd == "fabric":
        fr = a.fabric_root
        nid = a.node_id
        eps = getattr(a, "endpoints", None)
        as_json = bool(getattr(a, "json", False))
        tls_req = bool(getattr(a, "tls_required", True))
        if a.fabric_op == "status":
            raise SystemExit(
                cmd_fabric_status(
                    fabric_root=fr,
                    node_id=nid,
                    endpoints=eps,
                    as_json=as_json,
                    probe=not bool(getattr(a, "no_probe", False)),
                    tls_required=tls_req,
                )
            )
        elif a.fabric_op == "diagnose":
            raise SystemExit(
                cmd_fabric_diagnose(
                    fabric_root=fr,
                    node_id=nid,
                    endpoints=eps,
                    as_json=as_json,
                    probe=not bool(getattr(a, "no_probe", False)),
                    tls_required=tls_req,
                )
            )
        elif a.fabric_op == "reconnect":
            raise SystemExit(
                cmd_fabric_reconnect(
                    fabric_root=fr,
                    node_id=nid,
                    peer=getattr(a, "peer", None),
                    endpoints=eps,
                    as_json=as_json,
                    attempts=int(getattr(a, "attempts", 2)),
                    tls_required=tls_req,
                )
            )


    elif a.cmd == "id":
        fr = a.fabric_root
        nid = a.node_id
        as_json = bool(getattr(a, "json", False))
        if a.id_op == "status":
            raise SystemExit(cmd_id_status(fabric_root=fr, node_id=nid, as_json=as_json))
        elif a.id_op == "attest":
            raise SystemExit(
                cmd_id_attest(
                    fabric_root=fr,
                    node_id=nid,
                    expected=getattr(a, "expected", None),
                    as_json=as_json,
                    mode=str(getattr(a, "mode", "tls")),
                )
            )
        elif a.id_op == "tier":
            raise SystemExit(
                cmd_id_tier(
                    fabric_root=fr,
                    node_id=nid,
                    tier=getattr(a, "tier_set", None),
                    pin=bool(getattr(a, "pin", False)),
                    downgrade=bool(getattr(a, "downgrade", False)),
                    reason=str(getattr(a, "reason", "") or ""),
                    as_json=as_json,
                )
            )
        elif a.id_op == "rotate":
            raise SystemExit(
                cmd_id_rotate(
                    fabric_root=fr,
                    node_id=nid,
                    days=int(getattr(a, "days", 825)),
                    keep_tier=not bool(getattr(a, "no_keep_tier", False)),
                    as_json=as_json,
                )
            )
        elif a.id_op == "revoke":
            raise SystemExit(
                cmd_id_revoke(
                    fabric_root=fr,
                    node_id=nid,
                    reason=str(getattr(a, "reason", "revoked") or "revoked"),
                    as_json=as_json,
                )
            )

    elif a.cmd == "recover":
        dr = a.data_root
        as_json = bool(getattr(a, "json", False))
        if a.recover_op == "status":
            raise SystemExit(cmd_recover_status(data_root=dr, as_json=as_json))
        elif a.recover_op == "snapshot":
            raise SystemExit(
                cmd_recover_snapshot(
                    data_root=dr,
                    reason=str(getattr(a, "reason", "manual") or "manual"),
                    list_only=bool(getattr(a, "snap_list", False)),
                    verify=getattr(a, "verify", None),
                    as_json=as_json,
                )
            )
        elif a.recover_op == "restore":
            raise SystemExit(
                cmd_recover_restore(
                    data_root=dr,
                    snapshot_id=getattr(a, "snapshot", None),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.recover_op == "rebuild":
            raise SystemExit(
                cmd_recover_rebuild(
                    data_root=dr,
                    snapshot_id=getattr(a, "snapshot", None),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )

    elif a.cmd == "fence":
        dr = a.data_root
        as_json = bool(getattr(a, "json", False))
        if a.fence_op == "status":
            raise SystemExit(cmd_fence_status(data_root=dr, as_json=as_json))
        elif a.fence_op == "probe":
            raise SystemExit(
                cmd_fence_probe(
                    data_root=dr,
                    auto_fence=bool(getattr(a, "auto_fence", True)),
                    preferred=getattr(a, "preferred", None),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.fence_op == "demote":
            raise SystemExit(
                cmd_fence_demote(
                    data_root=dr,
                    node_id=str(a.node_id),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.fence_op == "reelect":
            raise SystemExit(
                cmd_fence_reelect(
                    data_root=dr,
                    preferred=getattr(a, "preferred", None),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )

    elif a.cmd == "minority":
        dr = a.data_root
        as_json = bool(getattr(a, "json", False))
        if a.minority_op == "status":
            raise SystemExit(cmd_minority_status(data_root=dr, as_json=as_json))
        elif a.minority_op == "probe":
            raise SystemExit(
                cmd_minority_probe(
                    data_root=dr,
                    auto_halt=bool(getattr(a, "auto_halt", True)),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.minority_op == "halt":
            raise SystemExit(
                cmd_minority_halt(
                    data_root=dr,
                    reason=str(getattr(a, "reason", "operator halt") or "operator halt"),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )

    elif a.cmd == "clock":
        dr = a.data_root
        as_json = bool(getattr(a, "json", False))
        if a.clock_op == "status":
            raise SystemExit(cmd_clock_status(data_root=dr, as_json=as_json))
        elif a.clock_op == "probe":
            raise SystemExit(
                cmd_clock_probe(
                    data_root=dr,
                    auto_refuse=bool(getattr(a, "auto_refuse", True)),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.clock_op == "join-check":
            raise SystemExit(
                cmd_clock_join_check(
                    data_root=dr,
                    node_id=str(getattr(a, "node_id")),
                    peer_wall_ms=getattr(a, "peer_wall_ms", None),
                    local_wall_ms=getattr(a, "local_wall_ms", None),
                    mode=str(getattr(a, "mode", "local")),
                    auto_refuse=bool(getattr(a, "auto_refuse", True)),
                    as_json=as_json,
                )
            )

    elif a.cmd == "parity":
        dr = a.data_root
        as_json = bool(getattr(a, "json", False))
        if a.parity_op == "status":
            raise SystemExit(cmd_parity_status(data_root=dr, as_json=as_json))
        elif a.parity_op == "check":
            raise SystemExit(
                cmd_parity_check(
                    data_root=dr,
                    auto_reject=bool(getattr(a, "auto_reject", True)),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )
        elif a.parity_op == "build-check":
            raise SystemExit(
                cmd_parity_build_check(
                    data_root=dr,
                    manifest_a=getattr(a, "manifest_a", None),
                    manifest_b=getattr(a, "manifest_b", None),
                    auto_reject=bool(getattr(a, "auto_reject", True)),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                )
            )

    elif a.cmd == "obs":
        if a.obs_op == "telemetry":
            as_json = not bool(getattr(a, "text", False))
            raise SystemExit(
                cmd_obs_telemetry(
                    repo=getattr(a, "repo", ".") or ".",
                    node_id=str(getattr(a, "node_id", "local")),
                    cadence=str(getattr(a, "cadence", "10s")),
                    packaging=str(getattr(a, "packaging", "0.18-H4-obs-telemetry")),
                    as_json=as_json,
                    m2m=bool(getattr(a, "m2m", False)),
                    mode=str(getattr(a, "mode", "local")),
                    cycle=getattr(a, "cycle", None),
                )
            )
        elif a.obs_op == "validate":
            raise SystemExit(
                cmd_obs_validate(
                    file=getattr(a, "file", None),
                    use_stdin=bool(getattr(a, "stdin", False))
                    or getattr(a, "file", None) in (None, "-"),
                    abort_on_breach=True,
                )
            )
        elif a.obs_op == "schema":
            as_json = not bool(getattr(a, "text", False))
            raise SystemExit(cmd_obs_schema(as_json=as_json))

    elif a.cmd == "dist":
        if a.dist_op == "distribute":
            as_json = not bool(getattr(a, "text", False))
            raise SystemExit(
                cmd_dist_distribute(
                    repo=getattr(a, "repo", ".") or ".",
                    out_dir=getattr(a, "out_dir", None),
                    name=str(getattr(a, "name", "neural-mesh-gia-dist")),
                    channel=str(getattr(a, "channel", "0.18.x")),
                    cycle=int(getattr(a, "cycle", 38) or 38),
                    mode=str(getattr(a, "mode", "local")),
                    as_json=as_json,
                    m2m=bool(getattr(a, "m2m", False)),
                )
            )
        elif a.dist_op == "verify":
            raise SystemExit(
                cmd_dist_verify(
                    file=getattr(a, "file", None),
                    use_stdin=bool(getattr(a, "stdin", False))
                    or getattr(a, "file", None) in (None, "-"),
                    repo=getattr(a, "repo", ".") or ".",
                    abort_on_breach=True,
                    mark_replay_seen=bool(getattr(a, "mark_replay_seen", False)),
                )
            )
        elif a.dist_op == "pin-prior":
            as_json = not bool(getattr(a, "text", False))
            raise SystemExit(
                cmd_dist_pin_prior(
                    repo=getattr(a, "repo", ".") or ".",
                    reason=str(getattr(a, "reason", "ABORT distribution breach")),
                    ver=str(getattr(a, "ver", "0.17.0")),
                    as_json=as_json,
                )
            )
        elif a.dist_op == "schema":
            as_json = not bool(getattr(a, "text", False))
            raise SystemExit(cmd_dist_schema(as_json=as_json))

    elif a.cmd == "router":
        ensure_default_policy(root)
        caps = tuple(a.capability) if getattr(a, "capability", None) else ("compute",)
        if not caps:
            caps = ("compute",)
        if a.op == "route":
            if a.topology:
                topo = Topology.load(a.topology)
                cands = candidates_from_topology(topo)
            else:
                twin_obj = DigitalTwin.build_demo(seed=a.seed)
                cands = candidates_from_topology(twin_obj)
            log = DecisionLog(a.log) if a.log else DecisionLog()
            store = DecisionStore(a.store) if getattr(a, "store", None) else None
            strategy, registry = _build_router_strategy(a, cands, root)
            router = CognitiveRouterR0(
                cands,
                seed=int(a.seed),
                policy_root=root,
                decision_log=log,
                decision_store=store,
                strategy=strategy,
                capability_registry=registry,
            )
            task = TaskSpec(
                task_id=a.task_id,
                required_capabilities=caps,
                requires_network=bool(a.requires_network),
                requires_physical=bool(getattr(a, "requires_physical", False)),
            )
            decision = router.route(task)
            payload = explain_decision(decision)
            if a.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
            raise SystemExit(0 if decision.status.value == "ACCEPTED" else 3)
        elif a.op == "replay":
            store = DecisionStore(a.store)
            try:
                stored, recomputed = replay_from_store(store, a.trace_id)
            except KeyError as exc:
                print(json.dumps({"error": str(exc), "trace_id": a.trace_id}))
                raise SystemExit(3)
            identical = stored.canonical_bytes() == recomputed.canonical_bytes()
            payload = {
                "trace_id": a.trace_id,
                "byte_identical": identical,
                "stored": explain_decision(stored),
                "recomputed": explain_decision(recomputed),
                "stored_canonical_sha256": __import__("hashlib")
                .sha256(stored.canonical_bytes())
                .hexdigest(),
                "recomputed_canonical_sha256": __import__("hashlib")
                .sha256(recomputed.canonical_bytes())
                .hexdigest(),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            raise SystemExit(0 if identical else 1)
        elif a.op == "explain":
            # Prefer log lookup; else live-route once for explain.
            found = None
            if a.log and Path(a.log).exists():
                for row in DecisionLog(a.log).entries():
                    if row.get("task_id") == a.task_id:
                        found = row
            if found is not None:
                from neural_mesh.router.models import RouteDecision

                decision = RouteDecision.from_dict(found)
                print(json.dumps(explain_decision(decision), indent=2, sort_keys=True))
                raise SystemExit(0)
            if a.topology:
                topo = Topology.load(a.topology)
                cands = candidates_from_topology(topo)
            else:
                twin_obj = DigitalTwin.build_demo(seed=a.seed)
                cands = candidates_from_topology(twin_obj)
            strategy, registry = _build_router_strategy(a, cands, root)
            router = CognitiveRouterR0(
                cands,
                seed=int(a.seed),
                policy_root=root,
                strategy=strategy,
                capability_registry=registry,
            )
            task = TaskSpec(
                task_id=a.task_id,
                required_capabilities=caps,
                requires_network=bool(a.requires_network),
            )
            decision = router.route(task)
            print(json.dumps(explain_decision(decision), indent=2, sort_keys=True))
            raise SystemExit(0)

    elif a.cmd == "twin":
        if a.op == "topology":
            if a.top_op == "save":
                if a.from_path:
                    twin_obj = DigitalTwin.load_topology(a.from_path)
                else:
                    twin_obj = DigitalTwin.build_demo(seed=a.seed)
                if a.schema == "chatgpt":
                    twin_obj.to_topology_model().save(a.path)
                else:
                    twin_obj.save_topology(a.path)
                print(a.path)
            elif a.top_op == "load":
                raw = json.loads(Path(a.path).read_text(encoding="utf-8"))
                nodes = raw.get("nodes") or []
                legacy = (
                    "tasks" in raw
                    or "faults" in raw
                    or (nodes and "node_id" in nodes[0])
                )
                if legacy:
                    twin_obj = DigitalTwin.load_topology(a.path)
                    info = (
                        f"seed={twin_obj.seed} nodes={len(twin_obj.nodes)} "
                        f"links={len(twin_obj.links)} tasks={len(twin_obj.tasks)} "
                        f"faults={len(twin_obj.faults)}"
                    )
                    payload = twin_obj.to_topology_dict()
                else:
                    topo = Topology.load(a.path)
                    info = (
                        f"network_id={topo.network_id} seed={topo.seed} "
                        f"nodes={len(topo.nodes)} links={len(topo.links)} "
                        f"hash={topo.hash()}"
                    )
                    payload = topo.to_dict()
                if a.json:
                    print(json.dumps(payload, indent=2))
                else:
                    print(info)
        elif a.op in {"run", "bench"}:
            twin_obj = _load_twin(
                topology=a.topology,
                workload=getattr(a, "workload", None),
                faults=getattr(a, "faults", None),
                seed=a.seed,
            )
            for spec in a.fault:
                twin_obj.inject_fault(_parse_fault(spec, seed=a.seed))
            report = twin_obj.run(ticks=a.ticks)
            if a.op == "bench" or a.json:
                if a.json:
                    print(json.dumps(report.to_dict(), indent=2))
                else:
                    m = report.metrics
                    assert m is not None
                    print(
                        f"seed={report.seed} ticks={report.ticks} digest={report.digest}"
                    )
                    print(
                        f"makespan={m.makespan} mean_wait={m.mean_wait_ticks:.3f} "
                        f"mean_latency={m.mean_latency_ticks:.3f} "
                        f"utilization={m.utilization:.3f}"
                    )
                    print(
                        f"scheduled={m.scheduled_count} failed={m.failed_count} "
                        f"unscheduled={m.unscheduled_count} "
                        f"pkt_drop_rate={m.packet_drop_rate:.3f} "
                        f"({m.packets_dropped}/{m.packets_sent})"
                    )
            elif getattr(a, "summary", False):
                print(json.dumps(report.run_summary(), indent=2, sort_keys=True))
            else:
                s = report.run_summary()
                print(
                    f"experiment_id={s['experiment_id']} seed={s['seed']} "
                    f"events_executed={s['events_executed']} "
                    f"nodes_alive={s['nodes_alive']} "
                    f"packets_sent={s['packets_sent']} "
                    f"packets_dropped={s['packets_dropped']} "
                    f"latency_avg={s['latency_avg']:.3f} "
                    f"checkpoint_id={s['checkpoint_id']}"
                )
                print(f"digest={report.digest}")
                for r in report.schedule:
                    print(
                        f"  {r.task_id} -> {r.node_id or '-'} "
                        f"[{r.start_tick},{r.end_tick}] {r.status}"
                    )


def _parse_fault(spec: str, seed: int = 0) -> FaultEvent:
    parts = spec.split(":")
    if not parts:
        raise SystemExit(f"invalid fault SPEC: {spec}")
    kind = parts[0].upper()
    if kind == FAULT_NODE_LOSS:
        if len(parts) < 3:
            raise SystemExit(
                "NODE_LOSS SPEC requires NODE_LOSS:node:at_tick[:duration]"
            )
        duration = int(parts[3]) if len(parts) > 3 else -1
        return FaultEvent.create(
            FAULT_NODE_LOSS,
            parts[1],
            at_tick=int(parts[2]),
            duration_ticks=duration,
            seed=seed,
        )
    if kind == FAULT_PACKET_DROP:
        if len(parts) < 4:
            raise SystemExit(
                "PACKET_DROP SPEC requires "
                "PACKET_DROP:src->dst:at_tick:rate[:duration]"
            )
        duration = int(parts[4]) if len(parts) > 4 else -1
        return FaultEvent.create(
            FAULT_PACKET_DROP,
            parts[1],
            at_tick=int(parts[2]),
            drop_rate=float(parts[3]),
            duration_ticks=duration,
            seed=seed,
        )
    if kind == FAULT_PACKET_DELAY:
        if len(parts) < 4:
            raise SystemExit(
                "PACKET_DELAY SPEC requires "
                "PACKET_DELAY:src->dst:at_tick:delay_ticks[:delay_ms]"
            )
        delay_ms = float(parts[4]) if len(parts) > 4 else 0.0
        return FaultEvent.create(
            FAULT_PACKET_DELAY,
            parts[1],
            at_tick=int(parts[2]),
            delay_ticks=int(parts[3]),
            delay_ms=delay_ms,
            seed=seed,
        )
    raise SystemExit(f"unsupported fault type: {kind}")


if __name__ == "__main__":
    main()
