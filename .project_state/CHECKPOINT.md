# CP-0018

Phase: 5
Module: phase5c-durability-partition
Reason: Cycle 14 Phase 5C: Durability & Adversarial Partition Hardening — WAL/fsync policy, crash invariants (kill -9 mid-write/append/checkpoint), N=2 partition suite (minority=0, dual-primary=0, heal reconcile), safe snapshot compaction, CLI durability/partition/recovery-trace, bench crash+partition+reconnect, CP-0018
Next: DeepSeek review of Cycle 14 / CP-0018 (ChatGPT catch-up). Still blocked: Raft, N>2, multi-primary, ML/R2/R3, silent plaintext fallback.
Tests: {'passed': 328, 'failed': 0}
