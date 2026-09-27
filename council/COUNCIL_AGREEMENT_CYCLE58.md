# Council Agreement — Cycle 58 / CP-0062

**Capability:** agent_shell_extended_scenarios  
**Scope:** Extend CP-0053 shell spike — multi-turn bounded workload; safety-probe matrix; ABORT variants; receipt chain under M2 churn; optional compose with CP-0061 L_judge×M2 mocks; live=DISABLED  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0062  
**Authority:** DeepSeek C57 Option 1 (SP4 spike bias; ranked pick)

## Deliverables

- docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md
- MESH_AGENT_SHELL_EXTENDED
- packaging `agent_shell_extended` (MockAgentShellAdapter + ShellMembershipBridge)
- tests: multi-turn; probe matrix; churn chain verify; T-shell-a/b/c; optional L_judge compose
- CP-0062 VERIFIED
- PASTE with LAST_SEALED (SP1)
- PREFERRED_NEXT=`0.19_design_set_signoff_v2`

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS/settlement. No live LLM/API keys. No pkg0190. v0.18.0 untouched. live=DISABLED.
