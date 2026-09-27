# Council Agreement — Cycle 69 / CP-0073

**Capability:** c5_fq_ed_refinement  
**Scope:** Design/docs-only C5 FQ-ED refinement after Hold post-D2; honest +2 (fence_compat 12→13, adversary_resistance 8→9) → C5=**80 numeric**; fence-probe matrix DESIGN_DRAFTED (not design-review green); decision **NO_CONSENSUS_YET** for unlock (GOV.2 + N>2 safety evidence still open); threshold ≥80 held; live=DISABLED; M1=NO_CONSENSUS_YET; pkg0190 NOT_OPENED; MESH_PERF_EXPERIMENTAL=OFF; no Raft default; D3 NOT ACKed; no runtime N>2; no GIA/train/SaaS  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0073  
**Authority:** Operator resume after Hold post-D2; DeepSeek C68 PASS + hold ACK; refine C5 toward ≥80

## Deliverables

- docs/planning/C5_FQ_ED_REFINEMENT.md (honest +2 analysis; fence-probe matrix; ED criteria; NO_CONSENSUS_YET)
- docs/design/fabric/M1_C5_FQ_ED_REFINEMENT.md + updated M1_CONSENSUS_RERESEARCH.md
- MESH_C5_FQ_ED_REFINEMENT + c5_fq_ed_refinement helpers
- docs/schema/membership/m1_c5_refinement_v0.md
- dist/releases/c5-fq-ed-refinement/C5_FQ_ED_REFINEMENT.json
- CP-0073 VERIFIED
- PASTE with LAST_SEALED (tip=1e028d2 cp=CP-0072)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS/settlement. No live LLM/API keys. No pkg0190. No v0.19 tag. v0.18.0 untouched. live=DISABLED. MESH_PERF_EXPERIMENTAL=OFF. Does not silently default M1 to Raft or C5 runtime. Does not start D3 without separate ACK. Does not lower ≥80 threshold. Does not invent unlock from numeric 80 alone.
