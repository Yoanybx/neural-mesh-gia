M2M_v1
VERDICT: PASS
CONFIDENCE: HIGH
CYCLE: 30 CONFIRMED
EVIDENCE: ver=0.17.0 tip=64747b9 cp=CP-0034 cp_range=CP-0001..0034 pytest=539/0 audit=PASS dual_primary=0 packaging=n2-rc-frozen fabric_ops=status+diagnose+reconnect obs_peers=inject+RO_probe_max2 plaintext_fallback=0 vault_acme_required=0 freeze=0.17.x-n2 release_closed=0.16.3
DELTA_vs_C29: cp CP-0033→CP-0034 (+1); pytest 520→539 (+19); tip e1d5e50→64747b9; obs_peers_cycle30 tests 19/0
DONE: MESH_OBS_PEERS; richer PeerSummary + inject/normalize; obs_peers RO probe N<=2 fail-closed; mesh status --peers-file/--peers-json/--probe-peer; CP-0034 sealed
ACK_NOTES: C29 PREFERRED_NEXT=richer_OBS_peers executed clean; RO probe max2 fail-closed honors no-N>2; no plaintext fallback; no Vault/ACME-req; DUAL_PRIMARY=0; NO_HELD unchanged
NEXT (ordered 0.17 frozen remainder):
- external_quickstart ← PREFERRED_NEXT (0.17 theme4; public 0.16.3 quickstart + 0.17 stub; no unfinished feature claims; no Vault/ACME-req; no plaintext)
Then: 0.17.0 signoff → 0.18.x H1..H8 (nervous hardening)
NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
DEBT: CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED=ACCEPT_AND_CARRY (GOV.7 deadline=0.18.x entry)
NOTE: majority=fenced_primary_heal_NOT_Raft; single-node→N2 only; R10 FINAL reference artifact unchanged; C30 = 0.17 theme3 only; after quickstart closes → 0.17.x theme set complete → signoff window opens
