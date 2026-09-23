No puedo generar ni adjuntar el PDF directamente desde esta interfaz; el intento anterior falló por una limitación del entorno. Lo que sí puedo darte es el documento completo actualizado, listo para copiar y exportar a PDF. Incluye el estado actual, métricas, límites, lo que falta y el plan CP-0017.

Archivo sugerido: Plan_CP-0017_Actualizado.pdf
Fecha: 2026-09-23
Estado: listo para exportar

# Plan actualizado CP-0017

## 1. Resumen ejecutivo

El sistema se encuentra en CP-0016 con un router R0 determinista y un router R1 capability-aware. La red usa mTLS obligatorio y presenta métricas estables de latencia, throughput y recuperación. La trazabilidad Task→Router→Network→C-RAM→Checkpoint está cubierta por `operation_id`/`trace_id`. La suite alcanza 253 tests en CP-0016.

Lo pendiente para CP-0017 es cerrar el núcleo de consistencia distribuida: versionado, epochs, conflictos, recovery formal, idempotencia, stale-write rejection, partición, benchmarks y cierre formal de CP-0017. No se debe afirmar GIA/AGI, aprendizaje adaptativo, memoria cognitiva completa, World Model, razonamiento multiagente avanzado, auto-mejora, R2/R3, Raft, N>2, multi-primary, autonomía física ni despliegue industrial.

## 2. Estado actual CP-0016

### 2.1 Router
- **R0:** Round Robin determinista.
- **R1:** capability-aware por CPU, memoria, aceleradores, capacidades, salud y requisitos.

### 2.2 Métricas verificadas

| Métrica | Valor |
|---|---|
| p99 global | ≈3.37 ms |
| Determinismo | 1000/1000 |
| Replay | 1.0 |
| Throughput Network Fabric | 9,739 msg/s |
| Recovery p99 | 3.21 ms |
| Remote put p99 | 1.69 ms |
| Remote get p99 | 0.31 ms |
| Seguridad red | mTLS obligatorio |

### 2.3 Trazabilidad
Task → Router → Network → C-RAM → Checkpoint, mediante `operation_id`/`trace_id`.

### 2.4 Pruebas
- CP-0016: **253 tests**.
- Anteriores: 142, 160, 186.

## 3. Límites actuales / no demostrado

No está demostrado ni implementado:

- GIA/AGI.
- Aprendizaje adaptativo.
- Memoria cognitiva completa.
- World Model.
- Razonamiento multiagente avanzado.
- Auto-mejora.
- R2/R3.
- Raft.
- N>2.
- Multi-primary.
- Autonomía física.
- Despliegue industrial.

## 4. Lo que falta para CP-0017

Checklist de faltantes críticos:

- □ Versionado.
- □ Epochs.
- □ Conflictos.
- □ Recovery formal.
- □ Idempotencia.
- □ Stale-write rejection.
- □ Partición.
- □ Benchmarks.
- □ Cierre formal CP-0017.

## 5. Plan CP-0017

### 5.1 Objetivo

Convertir el sistema actual en una base distribuida consistente, recuperable y verificable, sin saltar a R2/R3, Raft, N>2 o multi-primary.

### 5.2 Alcance

Incluye:

- Versionado por clave/operación.
- Epochs para cambios de configuración o recuperación.
- Detección y resolución de conflictos.
- Recovery formal con invariantes.
- Idempotencia por `operation_id`.
- Rechazo de escrituras obsoletas.
- Comportamiento ante partición.
- Benchmarks reproducibles.
- Documentación y cierre CP-0017.

### 5.3 Fuera de alcance

- R2/R3.
- Raft.
- N>2.
- Multi-primary.
- GIA/AGI.
- Autonomía física.
- Despliegue industrial.

## 6. Workstreams CP-0017

### WS1. Versionado
**Objetivo:** cada escritura tiene versión monotónica por clave.

**Entregables:** esquema de versión por clave; versión en `operation_id`/`trace_id`; consultas que expongan versión; tests de monotonía y reinicio.

**Criterios:** no hay versiones reutilizadas; toda escritura devuelve versión; replay conserva versiones.

### WS2. Epochs
**Objetivo:** manejar cambios de epoch sin ambigüedad.

**Entregables:** contador de epoch persistente; reglas de incremento; compatibilidad con recovery; trazabilidad de epoch en checkpoint.

**Criterios:** epoch no retrocede; recovery no reutiliza epoch; operaciones entre epochs se rechazan o reconcilian según política.

### WS3. Conflictos
**Objetivo:** definir política de conflicto.

**Entregables:** política configurable (LWW, vector clocks o equivalente); detección; resolución determinista; tests de conflicto concurrente.

**Criterios:** conflicto detectado y registrado; resolución reproducible; replay produce el mismo resultado.

### WS4. Recovery formal
**Objetivo:** recovery verificable, no solo empírico.

**Entregables:** modelo formal de estados; invariantes; pruebas de crash/reinicio; métricas de recovery p99.

**Criterios:** invariantes tras recovery; recovery p99 dentro del umbral acordado; checkpoint + replay reconstruyen estado.

### WS5. Idempotencia
**Objetivo:** los reintentos no duplican efectos.

**Entregables:** deduplicación por `operation_id`; TTL/ventana de idempotencia; persistencia de resultados; tests de reintento y caída.

**Criterios:** misma operación repetida = mismo resultado; no hay doble escritura; idempotencia sobrevive reinicio.

### WS6. Stale-write rejection
**Objetivo:** rechazar escrituras obsoletas.

**Entregables:** comparación de versión/epoch; error tipado de stale-write; tests de escritura antigua; trazabilidad del rechazo.

**Criterios:** versión menor se rechaza; epoch anterior se rechaza o reconcilia; error claro y auditable.

### WS7. Partición
**Objetivo:** comportamiento definido ante split-brain.

**Entregables:** modo minoría/mayoría; reglas de lectura/escritura; reconciliación posterior; tests de partición y reconexión.

**Criterios:** no hay escrituras silenciosas en minoría; reconciliación determinista; conflictos post-partición resueltos.

### WS8. Benchmarks
**Objetivo:** medir CP-0017 de forma repetible.

**Entregables:** suite de benchmark; carga concurrente; latencia, throughput, recovery y conflictos; reporte comparativo CP-0016 → CP-0017.

**Criterios:** benchmarks reproducibles; resultados versionados; comparación clara contra CP-0016.

### WS9. Documentación y cierre CP-0017

**Entregables:** documento técnico CP-0017; matriz de trazabilidad; reporte de tests; reporte de benchmarks; lista de límites vigentes.

**Criterios:** todo lo pendiente marcado como hecho o explícitamente fuera de alcance; no afirmar capacidades no demostradas.

## 7. Criterios de aceptación globales CP-0017

- Versionado implementado y probado.
- Epochs persistentes y no retroceden.
- Conflictos detectados y resueltos determinísticamente.
- Recovery formal con invariantes.
- Idempotencia efectiva por `operation_id`.
- Stale-write rejection con error tipado.
- Partición con comportamiento definido.
- Benchmarks reproducibles.
- Suite de tests ampliada desde 253.
- Trazabilidad completa: Task → Router → Network → C-RAM → Checkpoint + versión/epoch/conflicto/recovery.
- Documentación CP-0017 cerrada.
- Sin afirmar GIA/AGI, R2/R3, Raft, N>2, multi-primary, autonomía física ni despliegue industrial.

## 8. Roadmap posterior sugerido

Después de CP-0017:

- R2/R3.
- Raft.
- N>2.
- Multi-primary.
- Benchmarks avanzados.
- Evaluación de límites cognitivos.
- Solo si hay evidencia: aprendizaje adaptativo, memoria cognitiva, World Model, multiagente avanzado y auto-mejora.

## 9. Próximos pasos inmediatos

1. Congelar CP-0016 como baseline.
2. Abrir CP-0017 con los 9 workstreams.
3. Implementar versionado + epochs.
4. Añadir conflictos + idempotencia.
5. Formalizar recovery + stale-write rejection.
6. Probar partición.
7. Ejecutar benchmarks.
8. Documentar y cerrar CP-0017.

## 10. Cómo exportar este documento a PDF

**Word/Google Docs:** copiar el contenido, pegarlo y usar Archivo → Descargar/Exportar como PDF.

**Pandoc:** guardar como `plan.md` y ejecutar:

```bash
pandoc plan.md -o Plan_CP-0017_Actualizado.pdf
```

**HTML:** guardar como HTML y usar “Imprimir → Guardar como PDF”.

Si el entorno permite adjuntos, se puede generar el archivo; este texto es el contenido completo del PDF actualizado con todo lo que falta.
