# Consejo acordado — Ciclo 5 (ChatGPT ∩ DeepSeek ∩ Grok)

**Fecha:** 2026-09-23 America/New_York (EDT)

## Veredicto Ciclo 4
| Voz | Veredicto |
|-----|-----------|
| ChatGPT | Diseñó/aprobó C-RAM Core P0–P4 (ejecutado) |
| DeepSeek | **APROBADO CON CAMBIOS** (foundation OK; recovery_time STUB + N=1 “RECOVERABLE” engañoso + falta corrupción/errores tipados) |
| Grok Bot | **APROBADO CON CAMBIOS MENORES** (misma dirección; exigir CLI, corrupción, NodeUnavailable vs ObjectMissing, hashing canónico) |

**Acuerdo:** Ciclo 4 se acepta como foundation. No se rechaza el rumbo. Los cambios van al **Ciclo 5**, no a reescribir CAS.

## Rumbo Ciclo 5 (acordado)
**Opción 2 DeepSeek** (prerequisito de réplica): hooks twin→C-RAM + **recovery_time real** + errores tipados + CLI + corrupción + bench + **solo interfaz** réplica N=2.

ChatGPT había listado réplica lite / hooks / recovery_time como opciones. DeepSeek prioriza hooks+métrica **antes** de réplica. Grok coincide. **Réplica real = Ciclo 6+.** Phase 3 Router = bloqueado hasta SLO.

### P0–P7 (aceptación)
- P0 recovery_time instrumentado (no STUB); 0 skips por STUB
- P1 NODE_LOSS → locate; si no resuelve ⇒ ERROR (no RECOVERABLE optimista)
- P2 NodeUnavailable vs ObjectMissing + tests
- P3 CLI `mesh cram put|get|verify|fsck` exit codes 0/2/3
- P4 Test corrupción blob + durabilidad
- P5 Bench N=100 faults → p50/p99 en checkpoint (meta p99 < 150ms o documentar baseline realista del hardware del box)
- P6 Doc/firma interfaz réplica N=2 **sin** implementar
- P7 audit + **CP-0009 VERIFIED**; pytest ≥62

## NO hacer
Réplica/consenso activos, ML, memoria neuronal distribuida, Phase 3 Router, reescritura CAS, dashboards cosméticos.

## Criterio de cierre consejo
Tras Ciclo 5: postear status a ChatGPT + DeepSeek; si ambos APROBADO (o APROBADO CON CAMBIOS menores), abrir Ciclo 6 réplica N=2.

## Ratificación ChatGPT (2026-09-23)
**A) Confirmado** con ajustes:
- P1: locate válido → OK; sin ruta → ERROR; no RECOVERABLE sin prueba; tests `test_node_loss_unresolved_returns_error`, `test_node_loss_resolved_returns_location`
- P3 exit codes: 0=PASS, 2=integrity failure, 3=missing/unavailable; `mesh cram fsck --json`

Estado: **ACUERDO CERRADO** pendiente solo eco DeepSeek (no bloqueante si no veta).

## Ratificación DeepSeek (2026-09-23)
**(A) CONFIRMO** — matices no bloqueantes:
- Exit codes: 0 PASS, 2 integrity, 3 missing/unavailable, 1 generic CLI; fsck --json `fsck_schema: 1`
- Extra test: `test_node_loss_locate_raises_on_stale_topology`

**Consejo 100% cerrado.** Implementación Ciclo 5 en curso → CP-0009.
