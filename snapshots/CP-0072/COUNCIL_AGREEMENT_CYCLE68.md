# Council Agreement — Cycle 68 / CP-0072

**Capability:** d2_m1_consensus_candidate_reresearch  
**Scope:** Design/docs-only M1 consensus candidate re-research under C67 axes (safety 30 / liveness 15 / fence-compat 15 / no-Raft 10 / WAN 15 / adversary-resistance 10 / complexity 5); C5 FQ-ED custom sketch; compose D1 consensus draft (CP-0071); decision **NO_CONSENSUS_YET** (closest C5=78<80); live=DISABLED; M1=NO_CONSENSUS_YET; pkg0190 NOT_OPENED; MESH_PERF_EXPERIMENTAL=OFF; no Raft default; no runtime N>2; no GIA/train/SaaS  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0072  
**Authority:** DeepSeek C67 VERDICT PASS; NEXT=D2; COUNCIL_AGREEMENT_D4 LOCKED (F10)

## Deliverables

- docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md (F2 confirmed; D1 exit PASS/gaps noted)
- docs/design/fabric/M1_CONSENSUS_RERESEARCH.md
- MESH_D2_M1_CONSENSUS_RERESEARCH + d2_m1_consensus_reresearch helpers
- docs/schema/membership/m1_reresearch_v0.md
- dist/releases/d2-m1-reresearch/D2_M1_RERESEARCH.json
- CP-0072 VERIFIED
- PASTE with LAST_SEALED (tip=c6e824a cp=CP-0071)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS/settlement. No live LLM/API keys. No pkg0190. No v0.19 tag. v0.18.0 untouched. live=DISABLED. MESH_PERF_EXPERIMENTAL=OFF. Does not silently default M1 to Raft. Does not start D3 without separate ACK.
