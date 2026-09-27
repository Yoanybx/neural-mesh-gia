# Council Agreement — Cycle 57 / CP-0061

**Capability:** L_judge_mock_e2e_with_M2_SM  
**Scope:** Compose existing L_judge MIX mock (CP-0052) with M2 MembershipSM (CP-0059) end-to-end; ABORT paths; hash-chained receipts; neg tests T-M2-judge-a/b/c; live=DISABLED  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0061  
**Authority:** DeepSeek C56 Option 1 (SP4 spike bias; ranked pick)

## Deliverables

- docs/design/L_JUDGE_M2_E2E_SPIKE.md
- MESH_L_JUDGE_M2_E2E
- packaging `l_judge_m2_e2e` bridge (MembershipSM × MockLJudgePort)
- tests: happy JOINING→ATTESTING→ACTIVE(T2|T3); DRAINING mid-judgment; LEFT/REJOIN inflight; T-M2-judge-a/b/c
- CP-0061 VERIFIED
- PASTE with LAST_SEALED (SP1)
- PREFERRED_NEXT=`await_deepseek`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS. No real WAN. No live LLM/API keys. No pkg0190. v0.18.0 untouched. live=DISABLED.
