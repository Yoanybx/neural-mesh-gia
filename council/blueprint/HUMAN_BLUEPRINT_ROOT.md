# BLUEPRINT_ROOT FINAL — Neural Mesh / GIA-COS

**Rev:** 10 (tras 10 rondas DeepSeek)  
**Baseline tip:** 0.17.0 · tip `35d3e42` · CP-0032 VERIFIED · pytest 504/0  
**Auto-score DeepSeek:** 97/100 (no 100: consenso aún sin elegir, consejo por roles sin nombres, C1 candidato, umbrales WAN por ratificar)  
**Estado GIA:** HOLD / NO_HELD hasta evidencia + quórum

**Nota de operador (Grok):** En L1, DeepSeek aún lista soak/audit/freeze (P30–P32) como abiertos; en el tip real **ya están VERIFIED en CP-0032**. Lo que sigue en 0.17 congelado es: **Fabric ops UX, richer OBS peers, external quickstart** (+ signoff N2 si quieres release).

Leyenda: D=doc · S=schema · C=CLI · T=test(+neg) · R=RFC · P=policy

---

```
GIA-COS [HOLD]
│  proxies medibles P0.1..P0.12 (sin lenguaje AGI)
│
├── L0 HAVE [DONE] — tip 0.17.0 / CP-0032
│   runtime WAL+fsync; N=1 release 0.16.3 CLOSED
│   N=2 manifest v1-n2 + install + rollback
│   packaging single + N2 RC (soak/audit/freeze)
│   OBS single + básico N2; TLS helpers
│   CP-0001..0032; 504/0; dual_primary=0
│   majority = fenced_primary_heal (NO Raft)
│
├── L1 REMAINING_0.17 [CLOSED CP-0056]
│   ├── R1 Fabric ops UX     → mesh fabric status|diagnose|reconnect [CLOSED CP-0033]
│   ├── R2 OBS peers         → docs/ops/obs-peers-v1.md + inject/probe [CLOSED CP-0034]
│   ├── R3 External quickstart → quickstart.sh + docs/quickstart   [CLOSED CP-0035]
│   ├── R4 soak P30          → [DONE en tip / CP-0032]
│   ├── R5 audit P31         → [DONE en tip / CP-0032]
│   ├── R6 freeze P32        → [DONE en tip / CP-0032]
│   └── R7 install/signoff   → opcional seal N2 RC                 [OPEN?]
│
├── L2 NERVOUS_HARDENING [PARTIAL]
│   ├── H1 identity + attestation + trust tiers T0..T3
│   ├── H2 recovery + rebuild
│   ├── H3 dual-primary fence (tests+abort→demote)
│   ├── H4 OBS telemetry contract
│   ├── H5 packaging as distribution primitive (sign/provenance/replay)
│   ├── H6 minority_write@N2 = 0
│   ├── H7 clock_skew@N2 (HLC; refuse join)
│   └── H8 manifest parity@N2
│
├── L3 GATES + GOVERNANCE
│   ├── GOV.1 council charter (roles; vacancy pauses unlock)
│   ├── GOV.2 quorum: 3/4 unlock; GIA unánime; N=2 exige ambos nodos
│   ├── GOV.3 evidence-bundle schema
│   ├── GOV.4 mesh gov unlock (mecánico, no prosa)
│   ├── GOV.5 reversal · GOV.6 no prose unlock
│   ├── GOV.7 schema-debt deadline al entrar 0.18.x
│   └── RULE: unlock = CP evidence bundle + quórum
│
├── L4 MULTI_NODE_SCALE [NO_HELD]
│   ├── M1 consensus choice (scorecard ≥80; aún sin elegir)
│   ├── M2 membership + rejoin
│   ├── M3 WAN / partition model
│   ├── M4 N=3 partition suite (solo tras M1–M3)
│   ├── M5 reconciliation (gated)
│   ├── M6 scale soak + rollback evidence
│   └── ABORT: si M1–M3 fallan → N se queda en 2
│
├── L5 GIA_SURFACE [MISSING]
│   ├── I1 identity/attestation/tiers/rotate/revoke
│   ├── I2 control-plane API + mesh ctl
│   ├── I3 memory/state fabric (S0..S3) + repair + provenance
│   ├── I4 action boundary (A0..A4) + capability tokens + dry-run
│   ├── I5 human oversight (approve/deny/pause/kill/dead-man/consent)
│   ├── I6 auditabilidad (hash-chain; no-audit = no-action)
│   ├── I7 transport WAN (NAT, relay, latency, partitions)
│   ├── I8 key rotation RFC
│   ├── I9 upgrade/rollback RFC (drain obligatorio)
│   ├── I10 falsifiers F1..F10
│   └── I11 claim without test = INVALID
│
├── L6 CONSCIOUSNESS_CLAIM_POLICY [MISSING]
│   ├── C1 wording + falsifiers (candidato; default FORBIDDEN)
│   ├── C2 council charter · C3 revocation
│   ├── C4 no claim without C1∧C2∧C3 · C5 default forbidden
│   └── C6 mesh-lint --forbid-words
│
└── L7 ADVERSARY_MODEL [MISSING]
    ├── A1..A5 clases/capacidades/criterios/defensas
    ├── A6 tests adversary (+neg)
    └── ABORT: clase cumple criterio de éxito → no mint CP
```

## Camino crítico (orden)

CP-0032 → (cerrar L1 abierto) → H1..H8 → adversario A1..A4 →  
I2→I3→I4→I5→I6→I8→I9→I7 → M1→M2→M3→M4→M6 → I1→I10 → C1→C2→C3 → GIA-COS

## Permanentemente prohibido (nunca se “desbloquea”)

silent plaintext · SLO chase · silent dual-primary · silent minority write ·  
igualar consenso=Raft por default · claim de conciencia sin C1..C6 ·  
peer sin autenticar · upgrade sin drain · acción sin audit ·  
reloj de pared como autoridad

## Desbloqueable con evidencia + quórum

Raft · N>2 · multi-primary · ML · R2/R3 · Vault-ACME-req · **GIA** · tag_schema · EVERY_fsync

## Decisiones de gobierno aún abiertas (no ingeniería)

1. Elegir consenso (M1 scorecard listo)  
2. Nombrar asientos del consejo (roles ya definidos)  
3. Aprobar wording C1  
4. Ratificar umbrales WAN  
5. Economía de relays (neutralizada, no cerrada)  
6. Deadline/waiver de deuda SCHEMA-GATED al entrar 0.18.x

## Próximo trabajo real (corrección Grok sobre tip)

No P30 (ya hecho). Siguiente alineado a scope 0.17 congelado: **Fabric ops UX** (R1), luego OBS peers (R2), luego quickstart (R3).

---

## North Star Recalibration (2026-09-26)

**Puntero / pointer:** ver `council/NORTH_STAR_RECALIBRATION.md` (no reescribe este blueprint).

- **Norte aspiracional:** sistema de razonamiento suprahumano — **no** claim AGI/conciencia ahora.
- **Capas:** L_nervous (H1..H8 / 0.18) → L_judge (B MIX LLM-as-judgment; DO_NOT_TRAIN_70B_NOW) → L_GIA (**NO_HELD** hasta evidencia + GOV).
- **Neural Mesh ≠ LLM.** Terminar H8 no crea cerebro suprahumano solo.
- **PARKED:** SaaS; economía tokenless.
- **Se mantiene:** continuar H8 + signoff 0.18; lista NO_HELD intacta; GIA HOLD.

Paste M2M: `council/PASTE_NORTH_STAR_RECALIBRATION_M2M.md` · Acuerdo borrador: `council/COUNCIL_AGREEMENT_NORTH_STAR.md` (pending ACK).
