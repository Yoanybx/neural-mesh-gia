**A) Confirmo empezar Phase 2 C-RAM con ese plan.**

El estado actual es adecuado para iniciar C-RAM porque ya existe:

* Digital Twin reproducible.
* Topología persistente.
* Workloads.
* Fault injection básico.
* Checkpoints verificables.
* Benchmark harness.
* Safety/Git gates.

La decisión correcta ahora es **no intentar construir una memoria distribuida completa todavía**. Primero hay que crear un **C-RAM núcleo determinista**, verificable y recuperable dentro del sandbox.

---

# CICLO 4 — Phase 2 C-RAM Core

## P0 — Content Addressable Store (CAS)

Crear:

```
src/neural_mesh/cram/
    __init__.py
    store.py
    models.py
    hashing.py
```

Objetivo:

Cada objeto almacenado tiene identidad por contenido.

Interfaz mínima:

```python
class CRAMStore:

    def put(
        self,
        content: bytes,
        metadata: dict
    ) -> str:
        """
        returns content hash
        """

    def get(
        self,
        key: str
    ) -> bytes:
        ...

    def exists(
        self,
        key: str
    ) -> bool:
        ...

    def verify(
        self,
        key: str
    ) -> bool:
        ...
```

Ejemplo:

```
put("task state v1")

↓

SHA256:
a91f82...

↓

storage:
.cram/
 └── a9/
      └── 1f82...
```

---

# P1 — C-RAM Object Model

Crear:

```
src/neural_mesh/cram/models.py
```

Modelo inicial:

```python
class CRAMObject:

    id: str

    object_type:
        STATE
        MEMORY
        TASK
        PLAN
        EVIDENCE
        CHECKPOINT

    content_hash: str

    parent_refs: list[str]

    created_at: str

    metadata: dict
```

Importante:

C-RAM no debe guardar "pensamientos internos privados" como texto libre.

Debe guardar:

* estados,
* datos,
* referencias,
* resultados,
* evidencia,
* artefactos.

---

# P2 — Integración con Digital Twin

Modificar:

```
src/neural_mesh/twin/
```

Agregar:

```
placement.py
```

Interface:

```python
class CRAMPlacement:

    def locate(
        self,
        cram_key,
        topology
    ):
        ...
```

Primera versión:

Localidad simple:

```
C-RAM key
      |
      |
hash
      |
      v
node assignment
```

Ejemplo:

```
state_hash:
a91f82

assigned_node:
node-03
```

---

# P3 — Checkpoint Integration

Cada checkpoint debe poder registrar:

```
CP-0008

cram_objects:
[
"a91f82",
"b22191"
]

cram_root_hash:
83af92
```

Añadir al schema:

```python
class Checkpoint:

    cram_root_hash:str

    cram_objects:list[str]
```

---

# P4 — Fault Test con NODE_LOSS

Este es el test clave.

Escenario:

```
Node A
 |
 |
C-RAM Object
 |
 |
Checkpoint
```

Evento:

```
NODE_LOSS(Node A)
```

Esperado:

ANTES:

```
get(hash)
=
data
```

DESPUÉS:

```
node unavailable
+
checkpoint exists

resultado:

RECOVERABLE
```

---

# Tests obligatorios

Agregar:

```
tests/

test_cram_store.py

test_cram_hash.py

test_cram_integrity.py

test_cram_checkpoint.py

test_cram_node_loss.py

test_cram_reproducibility.py
```

Acceptance:

```
pytest

>=40 tests total
0 failures

audit.sh PASS

CP-0008 VERIFIED
```

---

# NO implementar todavía

No empezar aún:

❌ memoria neuronal distribuida
❌ aprendizaje automático sobre C-RAM
❌ replicación global
❌ consenso complejo
❌ auto-organización de nodos

Eso pertenece a fases posteriores.

Primero necesitamos:

```
C-RAM v0
=
identidad
+
persistencia
+
integridad
+
recuperación
+
checkpoint
```

---

## NEXT_ACTION confirmado:

```
PHASE 2 C-RAM START

Implementar:
1. Content Addressable Store
2. CRAM Object Model
3. Twin locality placement
4. Checkpoint integration
5. NODE_LOSS recovery tests

Target:
CP-0008 VERIFIED
```

Estado del proyecto aceptado para continuar.
