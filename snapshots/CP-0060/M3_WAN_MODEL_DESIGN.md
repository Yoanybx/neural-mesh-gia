# M3 WAN Latency / Partition + HLC — Design-Only Model

**Status:** DESIGN MATURED (no WAN runtime; no N>2 topology)  
**Cycle / Checkpoint:** 56 / CP-0060  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `M3_WAN_model_DESIGN` (0.19_SCOPE_FROZEN theme D / blueprint L4 M3)  
**Authority:** DeepSeek C55 NEXT Preferred (`M3_WAN_model_DESIGN`)  
**Prior pointer:** `M3_WAN_PARTITION_HLC_POINTER.md` (CP-0050) — superseded for design content; kept as historical stub  
**Target docs (later):** `docs/wan/partition-v1.md`, `docs/wan/latency-bands-v1.md`  
**ABORT rule:** M1..M3 fail review → N stays 2  
**Runtime:** Raft / N>2 / multi-primary / M4+ remain **NO_HELD**

---

## 1. Intent

Produce a **ratifiable WAN latency + partition + HLC ordering model** that:

1. Defines RTT latency bands, jitter/loss envelopes, and a design-time `P_partition`.
2. Requires **HLC** for cross-site event ordering (`wall_clock_as_authority = 0`).
3. Classifies partitions: **split / heal / flip-flop / cascade**.
4. **Composes with M2** membership actors (ACTIVE peers under N≤2) and stays
   **orthogonal to M1** (`NO_CONSENSUS_YET`).
5. Remains **design-first** (DeepSeek SP4 caveat): real WAN cannot be spiked
   without runtime N>2, which is NO_HELD.

This CP does **not** implement WAN transport, does **not** open N>2, and does
**not** claim world-scale deployment.

---

## 2. Latency bands (RTT)

Canonical design bands for peer RTT (one-way ≈ RTT/2 for modeling notes only):

| Band | ID | RTT range (ms) | Ops posture (design) |
|------|----|----------------|----------------------|
| Low | `RTT_lo` | `0 ≤ rtt < 50` | LAN / metro; heal windows short |
| Mid | `RTT_mid` | `50 ≤ rtt < 200` | Regional WAN; default planning band |
| High | `RTT_hi` | `200 ≤ rtt < 1000` | Intercontinental; widen heal / probe |
| Extreme | `RTT_x` | `rtt ≥ 1000` | Design-only stress; ABORT soft if used as prod default |

**Invariant:** band assignment is **diagnostic**, never write-authority. Ordering
authority remains HLC (see §5).

Helpers expose `classify_rtt(rtt_ms) → LatencyBand`.

---

## 3. Jitter and loss envelopes

| Metric | Symbol | Design defaults (ratifiable later) | Notes |
|--------|--------|-------------------------------------|-------|
| Jitter (p95 of \|ΔRTT\|) | `J` | lo≤5 ms; mid≤20 ms; hi≤50 ms | Excess jitter → band escalate advisory |
| Loss rate | `L` | lo≤0.1%; mid≤1%; hi≤3% | Sustained above envelope → partition suspect |
| Probe interval | `T_probe` | lo 1s; mid 2s; hi 5s | Design; not a live scheduler |
| Heal window | `T_heal` | lo 5s; mid 15s; hi 45s | Time to declare heal after path restore |

**ABORT / refuse codes (design):**

| Code | Meaning |
|------|---------|
| `WAN_BAND_EXTREME_DEFAULT` | Attempt to set RTT_x as production default |
| `WAN_LOSS_ENVELOPE_EXCEEDED` | Sustained loss above band envelope (suspect) |
| `WAN_JITTER_ENVELOPE_EXCEEDED` | Sustained jitter above band envelope |
| `WAN_WALL_CLOCK_AS_AUTHORITY` | Any claim that wall clock orders events |
| `WAN_N_GT2_REFUSED` | Model applied to N>2 runtime claim |
| `WAN_P_PARTITION_INVALID` | P_partition outside [0,1] |
| `WAN_CLASS_UNKNOWN` | Unknown partition class label |
| `WAN_HLC_ORDER_VIOLATION` | Event order claimed from wall / non-HLC |

---

## 4. P_partition (design probability)

`P_partition ∈ [0, 1]` is a **scenario parameter**, not a measured SLA claim.

| Label | Suggested range | Use |
|-------|-----------------|-----|
| `P_rare` | `[0, 0.01)` | Nominal N=2 soak narrative |
| `P_occasional` | `[0.01, 0.05)` | Regional flap planning |
| `P_elevated` | `[0.05, 0.20)` | Chaos / adversarial drill (design) |
| `P_hostile` | `[0.20, 1.0]` | Stress class; never a prod target |

**Invariant:** publishing `P_partition` does **not** unlock N>2 or Raft. It only
feeds partition-class scenario tables and future T-M3 matrix descriptors.

---

## 5. HLC ordering (required)

Cross-site / cross-peer event ordering **MUST** use HLC:

- Schema: `mesh.clock.hlc/v1` (H7 / CP-0044) — `(logical, counter)`; `wall_ms` advisory.
- Invariant: **`wall_clock_as_authority = 0`** (P-02 / PERMANENT_NO_HELD).
- Compare: `compare_hlc(a,b)` on `(logical, counter)` only.
- Membership (M2) transitions that carry receipts SHOULD stamp HLC, not wall.

**WAN model rule:** partition class transitions and heal declarations are ordered
by HLC on each node’s local receipt chain. Wall delta may trip H7 skew refuse-join
but **never** establishes happened-before.

---

## 6. Partition classes

Actors: M2 **ACTIVE** members under **N≤2** (typically primary/secondary). No
third voting member. Majority story remains **fenced_primary_heal_NOT_Raft**.

| Class | ID | Meaning | Expected fence posture |
|-------|----|---------|------------------------|
| **split** | `SPLIT` | Path loss between ACTIVE peers; both sides may still be locally up | H6 minority-write halt; dual_primary=0; no silent multi-primary |
| **heal** | `HEAL` | Path restored within `T_heal`; anti-entropy / rejoin receipts | Resume only after fence clear; HLC-ordered catch-up |
| **flip-flop** | `FLIP_FLOP` | Rapid split↔heal oscillation (RTT/jitter envelope stress) | Bound flaps; refuse thrash-promote; OBS marks unstable |
| **cascade** | `CASCADE` | Split plus secondary fault (disk/process) while partitioned | Prefer safe LEFT/DRAIN path; no N>2 witness invent |

### Class transition sketch (design)

```
STABLE --(path_loss)--> SPLIT --(path_ok ∧ within T_heal)--> HEAL --> STABLE
SPLIT  --(oscillate)--> FLIP_FLOP --(settle ∨ operator)--> HEAL|SPLIT
SPLIT  --(+node_fault)--> CASCADE --(drain/rejoin M2)--> HEAL|LEFT
```

### Negative / ABORT descriptors

| ID | Case | Expect |
|----|------|--------|
| T-M3a | `partition_matrix` happy | SPLIT→HEAL with HLC order; dual_primary=0 |
| T-M3a-neg-1 | wall used as order authority | `WAN_WALL_CLOCK_AS_AUTHORITY` / `WAN_HLC_ORDER_VIOLATION` |
| T-M3a-neg-2 | N>2 partition claim | `WAN_N_GT2_REFUSED` |
| T-M3a-neg-3 | invalid P_partition | `WAN_P_PARTITION_INVALID` |
| T-M3a-neg-4 | unknown class | `WAN_CLASS_UNKNOWN` |
| T-M3b | `flip_flop_bound` | FLIP_FLOP does not promote dual_primary |
| T-M3b-neg | cascade invents witness | refused; N stays ≤2 |

Runtime partition_suite (M4) remains **NO_HELD**. Helpers in
`neural_mesh.packaging.m3_wan_model` are **pattern mocks** only.

---

## 7. Composition with M1 / M2 / H7

| Item | Relation |
|------|----------|
| **M2** | Provides ACTIVE actor set; REJOIN after CASCADE/LEFT uses M2 SM |
| **M1** | Unchanged **NO_CONSENSUS_YET**; WAN/HLC axis now has a draft model |
| **H3** | dual_primary=0 under SPLIT/FLIP_FLOP |
| **H6** | minority write halt under SPLIT |
| **H7** | clock skew refuse-join; HLC ordering authority |

---

## 8. Record sketch (design schema)

See `docs/schema/wan/v0.md` (`mesh.wan.model/v0`).

Minimal fields: `schema`, `rtt_ms`, `band`, `jitter_ms`, `loss_pct`,
`p_partition`, `partition_class`, `hlc`, `dual_primary=0`, `n_cap=2`,
`wall_clock_as_authority=0`, `abort_code`.

---

## 9. Non-goals

- Implementing WAN transport / relay / NAT traversal runtime
- Opening N>2 topology or Raft/Paxos
- World-scale deployment claims or SLO chase
- Spiking real multi-site WAN (requires N>2 — NO_HELD; SP4 design-first)
- GIA / train / SaaS / economy
- Changing H7 HLC semantics

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## Related

- `docs/design/fabric/M3_WAN_PARTITION_HLC_POINTER.md` (historical stub)
- `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md` (CP-0059)
- `docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md` / `M1_SCORECARD_MATURATION.md`
- `docs/schema/clock_skew/v1.md` (`mesh.clock.hlc/v1`)
- `docs/planning/0.19_SCOPE_FROZEN.md`
- `council/DEEPSEEK_REPLY_CYCLE55.md` (Preferred NEXT + SP4 M3 design-first)
