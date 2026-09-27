# Council Agreement — Cycle 65 / CP-0069

**Capability:** oversight_hooks_design_refinement (I5 human oversight)  
**Scope:** Formalize approve/deny/pause/resume/kill/deadman/consent-revoke against orchestrator decisions; A0..A4 boundary at orchestrator; dead-man T_dead→auto-DRAIN (override logged); quorum-human for A4; compose ContinuityOrchestrator (CP-0068) + OrchestratorRouter (CP-0064); RefuseTransport/HUMAN_ABORT (CP-0058); mock OversightPlane + T-ovs-a/b/c; package 0.18.0 held  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0069  
**Authority:** Continuous-loop after DeepSeek C64 NEXT Option 1

## Deliverables

- docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md
- docs/oversight/deadman-v1.md
- docs/schema/oversight/orchestrator_v0.md
- docs/capabilities/MESH_ORCHESTRATOR_OVERSIGHT.md
- packaging orchestrator_oversight (plane/deadman/quorum/orchestrator)
- tests/test_orchestrator_oversight_cycle65.py
- CP-0069 VERIFIED
- PASTE with LAST_SEALED (CP-0068 / tip d8442c3)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS. No consciousness claims. No live LLM. No pkg0190. No v0.19 tag. v0.18.0 untouched. live=DISABLED. M1=NO_CONSENSUS_YET. MESH_PERF_EXPERIMENTAL stays OFF (perf A/B only if operator ACK).
