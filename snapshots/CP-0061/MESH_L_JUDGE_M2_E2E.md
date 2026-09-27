# Mesh L_judge × M2 Membership E2E (Mock)

**Capability:** `MESH_L_JUDGE_M2_E2E`  
**Cycle / Checkpoint:** 57 / CP-0061  
**Version:** package **0.18.0** held  
**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Scope:** Compose L_judge MIX mock with M2 MembershipSM; ABORT + receipt chain; no live API

## Gates

| Gate | Meaning |
|------|---------|
| Design note | `docs/design/L_JUDGE_M2_E2E_SPIKE.md` |
| Bridge helpers | packaging `l_judge_m2_e2e` |
| Happy path | JOINING→ATTESTING→ACTIVE(T2\|T3) + mock judgments |
| Mid-judgment | DRAINING / LEFT / REJOIN cancel in-flight |
| Neg tests | T-M2-judge-a / T-M2-judge-b / T-M2-judge-c |
| live | DISABLED (no keys, no WAN, no frontier) |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/SaaS |

## Preferred next

`await_deepseek` (C57 Option1 sealed; Option2 agent_shell_extended or Option3 0.19 design-set signoff_v2 per DeepSeek)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
