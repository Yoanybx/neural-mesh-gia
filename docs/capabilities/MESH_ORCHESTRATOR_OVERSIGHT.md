# Mesh Orchestrator Oversight (I5)

**Capability:** `MESH_ORCHESTRATOR_OVERSIGHT`  
**Cycle / Checkpoint:** 65 / CP-0069  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** Human oversight hooks approve/deny/pause/resume/kill/deadman/consent-revoke
against orchestrator decisions; A0..A4 boundary; dead-man T_dead + auto-DRAIN;
quorum-human for A4; compose ContinuityOrchestrator (CP-0068) + OrchestratorRouter
(CP-0064); RefuseTransport / HUMAN_ABORT (CP-0058); mock OversightPlane only;
live=DISABLED; no train; NOT consciousness; NOT GIA

## Gates

| Gate | Meaning |
|------|---------|
| Design present | `docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md` |
| Dead-man policy | `docs/oversight/deadman-v1.md` |
| Schema stub | `docs/schema/oversight/orchestrator_v0.md` |
| Compose continuity | acts on ContinuityState / InFlightTracker (CP-0068) |
| Compose routing | binds judge engine_ids (CP-0064) |
| Safety case | RefuseTransport on kill; live=DISABLED |
| Helpers + neg | packaging `orchestrator_oversight`; T-ovs-a/b/c |
| Substrate | human-in-the-loop control — NOT consciousness / NOT L_GIA |
| M1 orthogonal | NO_CONSENSUS_YET |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/live |

## Preferred next

`await_deepseek` (C65 oversight sealed; ranked follow-on = hold, or perf A/B only if operator ACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
