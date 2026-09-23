# Grok Bot assessment — Cycle 4 C-RAM plan (ChatGPT)

**Veredicto:** APROBADO CON CAMBIOS MENORES

## Alineación
El plan de ChatGPT es correcto para el codebook Phase 2: CAS + integridad + checkpoint + fault recovery antes de réplica/consenso. Encaja con “no fake LOC” y con el twin ya endurecido.

## Riesgos
1. Romper verify de CP-0001..0007 si se muta el schema Checkpoint de forma incompatible.
2. Confundir “placement locality” con “datos viven solo en un nodo” sin réplica → NODE_LOSS test debe recuperar desde store durable del proceso, no desde RAM del nodo simulado.
3. Inflar object_type MEMORY hacia memoria cognitiva prematura.
4. Meter hashing no canónico (orden de metadata) y perder reproducibilidad.
5. Acceptance ≥40 tests con tests débiles/duplicados.

## Mejoras concretas que yo exigiría
1. Canonical JSON/bytes hashing: metadata sorted; put idempotent (same content → same hash).
2. Checkpoint: campos `cram_*` **opcionales** o en evidence dict separado para no invalidar históricos.
3. NODE_LOSS: distinguir `NodeUnavailable` vs `ObjectMissing`; recovery path documentado (reload from `.cram` + checkpoint refs).
4. CLI mínima: `mesh cram put|get|verify` para auditoría humana.
5. Un test de corrupción de blob en disco (verify=false) además de NODE_LOSS.

## NEXT_ACTION acordable (si DeepSeek no objeta fuerte)
P0 CAS + hashing canónico
P1 CRAMObject model
P2 Placement determinista
P3 Checkpoint evidence opcional cram_root_hash/cram_objects
P4 NODE_LOSS recoverable + blob corruption verify
P5 CLI cram put/get/verify
Tests list ChatGPT + test_cram_corruption.py
Target: ≥40 tests, CP-0008 VERIFIED, audit PASS

## NO hacer
Réplica, consenso, ML, memoria neuronal distribuida, auto-organización.
