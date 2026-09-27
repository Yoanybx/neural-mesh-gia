# Council Agreement — Cycle 64 / CP-0068

**Capability:** orchestrator_continuity_design  
**Scope:** Durable goals + evidence/audit ledger + continuity state machine; in-flight/orphan policy across LEFT/REJOIN; invocation idempotency; resume after restart; timeout bounds; ABORT propagation; compose with CP-0064 judge routing; CP-0067 receipt_hash_chain budget note; substrate memory NOT consciousness; mock ContinuityOrchestrator + T-cont-a/b/c; package 0.18.0 held  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0068  
**Authority:** Continuous-loop after DeepSeek C63 NEXT Option 1

## Deliverables

- docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md
- docs/schema/continuity/orchestrator_v0.md
- docs/capabilities/MESH_ORCHESTRATOR_CONTINUITY.md
- packaging orchestrator_continuity (registry/ledger/machine/inflight/orchestrator)
- tests/test_orchestrator_continuity_cycle64.py
- CP-0068 VERIFIED
- PASTE with LAST_SEALED (CP-0067 / tip fe6b81d)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS. No consciousness claims. No live LLM. No pkg0190. No v0.19 tag. v0.18.0 untouched. live=DISABLED. M1=NO_CONSENSUS_YET. MESH_PERF_EXPERIMENTAL stays OFF. Oversight-hooks refinement remains queued.
