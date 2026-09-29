# NORTH STAR RECALIBRATION — Neural Mesh / GIA

**Fecha:** 2026-09-26 America/New_York (EDT)  
**Autor:** Grok Bot (docs) · **Confirmado por operador:** Yoan  
**Estado:** PROPUESTA DE CONSEJO (pendiente ACK M2M) — **no** unlock  
**Baseline tip (referencia):** 0.18.0 · tip feature `5b72056` · CP-0044 VERIFIED · H1..H7 DONE · NEXT = H8

---

## Norte / North Star

| ES | EN |
|----|----|
| **Sistema de razonamiento suprahumano** (aspiracional). | **Suprahuman reasoning system** (aspirational). |
| No es claim actual. No es AGI. No es conciencia. | Not a present claim. Not AGI. Not consciousness. |
| Es la brújula a largo plazo; el trabajo diario es evidencia + capas. | Long-term compass; daily work is evidence + layers. |

**Regla dura:** no inventar unlocks NO_HELD ni afirmar AGI/conciencia **ahora**.

---

## Capas / Layer plan

```
L_nervous  →  L_judge  →  L_GIA
   (ahora)      (MIX)      (NO_HELD)
```

| Capa | Qué es | Estado |
|------|--------|--------|
| **L_nervous** | Sistema nervioso verificable: H1..H8 @N2 (scope 0.18) | **En curso.** H1..H7 DONE; **H8 manifest_parity** = NEXT; luego signoff 0.18 |
| **L_judge** | Juicio MIX: Neural Mesh como control/OBS + LLM externo (p.ej. DeepSeek-70B) como motor de juicio | **Diseño / intención.** **DO_NOT_TRAIN_70B_NOW.** Path **B MIX** |
| **L_GIA** | Superficie GIA / claims | **NO_HELD** hasta evidencia + GOV (quórum + bundle). Sin prosa unlock |

### Claridad explícita

- **Neural Mesh ≠ LLM.** Mesh = identidad, fence, recovery, OBS, packaging, parity, audit. LLM = razonamiento/juicio semántico.
- **Terminar H8 no crea un cerebro suprahumano solo.** H8 cierra el endurecimiento nervioso @N2; no es AGI ni L_GIA.
- Completar L_nervous es **necesario pero no suficiente** para el norte aspiracional.

## Puntero de producto: Mesh más allá de Cursor (DESIGN_ONLY)

La barra aspiracional de producto es **mejor que Cursor**, no “tipo Cursor” ni un
clon de Cursor: Mesh aporta orquestación, auditoría/ledger y refusal alrededor
de una UX de agent-shell. El track por etapas está en
`docs/planning/BLUEPRINT_AGENT_SHELL_BEYOND_CURSOR_TRACK.md`.

- **Cerca:** bus MCP-lite + jueces L_judge gratis (Gemini/DeepSeek) bajo la
  autorización F4 LIVE existente; advisory, no Mesh SoT.
- **Medio:** superficie agent-shell con herramientas orquestadas, ledger visible
  y refuse/abort explícito.
- **Lejos:** GIA / self-building agent; **NO_HELD** hasta consejo + evidence
  bundle y gates existentes.

Esto actualiza la intención de producto, no el código ni el estado LIVE: no abre
GIA, self-mod auto-loop, nuevas credenciales, proveedores, permisos o NO_HELD.

---

## Aparcamientos / PARKED

| Tema | Estado | Nota |
|------|--------|------|
| **SaaS** | **PARKED** | Producto multi-empresa / revenue SaaS aparcado. No es NEXT. |
| **Economía tokenless** (fiat/crypto/IOU/settlement/peering market) | **PARKED** | Ver `NOTE_M2M_TOKENLESS_ECONOMY.md`. Fuera de H1..H8. |
| **Entrenar 70B propio** | **DO_NOT_TRAIN_70B_NOW** | Usar LLM existente vía MIX (B). TRAIN_LATER solo con gap medido. |

---

## Qué cambia / What changes

| Cambia | Detalle |
|--------|---------|
| Norte explícito | De “PC-then-SaaS monitor” como brújula dominante → **razonamiento suprahumano** (aspiracional) como norte. |
| SaaS | Pasa a **PARKED** (no camino inmediato a revenue). |
| Juicio | Confirma **B MIX**: Mesh + LLM-as-judge (DeepSeek-70B u otro); **sin** train 70B ahora. |
| Capas nombradas | L_nervous → L_judge → L_GIA (GIA sigue NO_HELD). |

## Qué se mantiene / What stays

| Se mantiene | Detalle |
|-------------|---------|
| **H8 + signoff 0.18** | Continuar. PREFERRED_NEXT = `0.18_H8_manifest_parity`. |
| Scope 0.18 frozen | H1..H8 @N2; mismos NON-GOALS. |
| **NO_HELD** | Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, **GIA**, SLO_chase, tag_schema, EVERY_fsync — **sin cambio**. |
| GIA HOLD | Unlock solo con evidence-bundle + quórum GOV — no por este doc. |
| Economía tokenless | PARKED (sin código de ledger/IOU). |
| Tags | v0.17.0 / v0.16.3 intactos. |
| Política de conciencia | C1..C6 / default FORBIDDEN — sin claim. |

---

## Próximo trabajo real (sin inventar capas)

1. Ejecutar / sellar **H8** `0.18_H8_manifest_parity` (ABORT→reject build).
2. Signoff / cierre de track H* 0.18 según gates existentes.
3. **No** train 70B. **No** SaaS push. **No** economía. **No** unlock GIA.
4. L_judge: solo diseño/integración futura bajo control Mesh — **después** de nervioso cerrado y con alcance explícito (no este commit).

---

## Enlaces

- Blueprint: `council/blueprint/HUMAN_BLUEPRINT_ROOT.md` (puntero a este doc)
- Scope: `council/SCOPE_0.18_FROZEN.md`
- Economía PARKED: `council/NOTE_M2M_TOKENLESS_ECONOMY.md`
- Paste M2M: `council/PASTE_NORTH_STAR_RECALIBRATION_M2M.md`
- Acuerdo borrador: `council/COUNCIL_AGREEMENT_NORTH_STAR.md`

---

*Fin. Este documento recalibra intención; no modifica código H8; no desbloquea GIA.*
