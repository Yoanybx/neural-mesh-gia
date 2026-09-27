# Council Agreement — Cycle 63 / CP-0067

**Capability:** perf_hotspot_and_improvement_design  
**Scope:** Hotspot analysis from CP-0066 microbenches; ranked experimental measurable improvement designs (I1..I7); optional A/B benches behind MESH_PERF_EXPERIMENTAL (default OFF); honest local only (no world-fastest / ranking claims); M1=NO_CONSENSUS_YET; package 0.18.0 held; continuity design remains queued  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0067  
**Authority:** Continuous-loop after DeepSeek C61-62 NEXT Option 1

## Deliverables

- docs/design/MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md
- docs/capabilities/MESH_PERF_HOTSPOT_AND_IMPROVEMENT.md
- packaging mesh_perf_hotspot (analyze_hotspots + designs + experimental A/B)
- tests/test_mesh_perf_hotspot_cycle63.py
- CP-0067 VERIFIED
- PASTE with LAST_SEALED (CP-0066 / tip 0778d32)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS. No false ranking claims. No live LLM. No pkg0190. No v0.19 tag. v0.18.0 untouched. live=DISABLED. M1=NO_CONSENSUS_YET. No production default perf patches.
