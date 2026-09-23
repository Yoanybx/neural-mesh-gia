Veredicto Ciclo 10

APROBADO. 186 passed, CP-0014 verde, determinismo 1000×=0, no-match fail-closed, TTL stale=0. R1 cerrado limpiamente.

NEXT → (A) Phase 4 Network Fabric + pago de TLS

Razón: R0+R1 están verificados, réplica OOP sólida, C-RAM estable. Phase 4 es el siguiente eslabón real y TLS es deuda con vencimiento 2026-12-31 — pagarla ahora evita arrastrarla a Phase 5+ donde el blast radius es mayor. No hay razón técnica para posponerla.

Riesgos a cerrar en P0
- Boundary de confianza indefinido: ¿qué es "nodo" en fabric? ¿mTLS entre procesos, hosts, o ambos?
- Identidad sin rotación: certs estáticos = deuda que envejece mal.
- Framing sobre TLS: renegociación, half-close, tamaño máximo — romper framing OOP si no se re-especifica.
- Fail-closed vs availability: TLS handshake fallido ⇒ ERROR tipado, no fallback plaintext silencioso.
- Compat: ¿fabric reemplaza AF_UNIX o convive? Debe quedar explícito.

Plan P0–P7
- P0 — Doc freeze: modelo de confianza, mTLS scope (proc/proc vs host/host), rotación de certs, framing sobre TLS, fail-closed, compat AF_UNIX↔TLS, no-plaintext-fallback.
- P1 — Transport TLS con mTLS sobre el framing existente (16MiB preservado).
- P2 — Identidad: cert por nodo, rotación documentada, rechazo de cert expirado/caído.
- P3 — Fabric registry: descubrimiento de nodos con identidad verificada (integrado con CapabilityRegistry).
- P4 — Fail-closed: handshake fallido ⇒ FABRIC_TLS_ERROR tipado; 0 plaintext fallback (test binario).
- P5 — Crash/partición sobre TLS: kill -9 mid-handshake, mid-frame, rejoin — dual-primary sigue 0.
- P6 — Bench: overhead TLS p99 sobre réplica y routing; comparación vs Ciclo 7 (6.75× baseline).
- P7 — Audit + CP-0015.

Criterio de aceptación
- 0 plaintext fallback en suite (pass/fail binario).
- mTLS handshake fallido ⇒ ERROR tipado, latencia p99 < 20 ms.
- Rotación de cert sin downtime: 0 decisiones/rutas perdidas en ventana de rotación.
- Dual writable primary = 0 sobre TLS (paridad con CP-0011).
- Overhead TLS p99 < 15× sobre baseline single-node.
- Suite ≥ 215 passed; audit PASS; CP-0015 VERIFIED.

Qué NO hacer en Ciclo 11
- No Phase 5 Cognitive/Memory distribuida.
- No N>2, no Raft, no consenso real.
- No ML, no adaptive.
- No PKI externa (Vault/ACME) — certs locales rotables, deuda explícita si aplica.
- No relajar fail-closed por disponibilidad.

Después (Ciclo 12): Phase 5 con CP-0015 verde y TLS deuda cerrada (no renovada).
