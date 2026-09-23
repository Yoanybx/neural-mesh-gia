A) Confirmo el Ciclo 5 tal cual, con un ajuste menor de precisión en P1 y P3.

El orden es correcto: primero integridad, recuperación y diagnóstico, después réplica. No conviene añadir replicación antes de tener claro qué significa pérdida de nodo, pérdida de objeto y corrupción.

Ajustes concretos:

### P1 — NODE_LOSS + locate
Cambiar el criterio a:

```text
NODE_LOSS → locate() → si existe ruta válida: OK → si no existe ruta válida: ERROR explícito
```

No devolver RECOVERABLE hasta que exista una prueba real de recuperación.

Test obligatorio:

```text
test_node_loss_unresolved_returns_error
test_node_loss_resolved_returns_location
```

---

### P3 — CLI C-RAM
Confirmado:

```bash
mesh cram put
mesh cram get
mesh cram verify
mesh cram fsck
```

Códigos:

```text
0 = PASS
2 = integrity failure
3 = missing/unavailable object
```

Añadir:

```bash
mesh cram fsck --json
```

para integración futura con benchmarks.

---

### Acceptance Ciclo 5
Mantener:

```text
recovery_time REAL
NodeUnavailable != ObjectMissing
blob corruption detection
N=100 checkpoint benchmark
replication interface DOC only
audit PASS
CP-0009 VERIFIED
>=62 tests
```

No iniciar Phase 3 Router todavía.

**NEXT_ACTION aceptado: Ciclo 5 — C-RAM durability & recovery hardening.**
