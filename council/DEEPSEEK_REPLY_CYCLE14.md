VERDICT: PASS_WITH_GAPS
CONFIDENCE: HIGH
EVIDENCE: CP-0001..0018=VERIFIED; CP-0018=VERIFIED; PYTEST=328/0; AUDIT=PASS; DUAL_PRIMARY=0; PLAINTEXT_FB=0; STALE_REJECT_PCT=100; DUP_IDEM_PCT=100; MINORITY_WRITES=0
SLO_GAPS: recovery=2.13>2=GAP(stretch); checkpoint_durable=0.80>0.1=GAP
SLO_MET: checkpoint_parity=0.09<=0.1=MET; conflict_classify=0.0003<=0.1=MET
DONE: P0_doc,P1_WAL_fsync_crash,P2_partition_suite,P3_compaction,P4_CLI,P5_bench,P6_seal
RELEASE: HOLD_P7_checkpoint_durable
NEXT: P7_checkpoint_durable_tune<=0.1; P8_recovery_stretch<=2; rebench_P99; rerun_PYTEST+AUDIT; keep NO_HELD unchanged
NOTE: majority=fenced_primary_heal_NOT_Raft; no Raft/N>2/multi-primary/ML/R2/R3/plaintext/Vault-ACME-req/GIA
