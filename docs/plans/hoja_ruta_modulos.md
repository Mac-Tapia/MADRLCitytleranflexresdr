# Hoja de ruta por módulos hasta el entrenamiento

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Revisión:** 2026-11-06 · **Fuente de pendientes:** [STATUS](../../specs/STATUS.md) y [remediación integrada](remediacion_integrada.md)

## Regla del propietario (2026-11-06)

Los módulos se implementan y cierran uno por uno. **No se entrena hasta que el proyecto esté completo**: todos los specs sin pendientes y la arquitectura terminada. La autorización de `pilot` dada ese día queda aplazada hasta el módulo final; `authorized_stages` sigue vacío.

Un módulo se cierra con spec, pruebas en rojo y luego en verde, puerta `-Scope Repository` aprobada sobre su commit, CI en verde, registros actualizados y publicación.

## Módulos

| Módulo | Alcance | Specs y tareas | Estado |
|---|---|---|---|
| 1. Tarifas oficiales | PDF PBA, contraste, factura con cargo por potencia | SPEC-013 | Cerrado |
| 2. Dataset físico y reconexión | `iquitos_v5`, FV/carga, integridad, S9 | SPEC-014 | Cerrado |
| 3. Contrato de algoritmos y recursos | Capacidad de MASAC con las dimensiones de `iquitos_v5` y reformulación de su búfer (D05); requisitos derivados del contrato y no fijos; conformidad de `NativeBackend` y cancelación de hijos; `save_training_state` en los 4 lanzadores; descomposición de la recompensa en los registros | SPEC-002, SPEC-003, SPEC-004, D03, D05 | En curso |
| 4. Estadística y selección | IQM con 3 semillas, `decide_oe_winner` sin Kruskal-Wallis, `select_best_model` sin significancia ni estado de corridas; verdad estadística única | SPEC-005 (defectos), SPEC-009 (documental) | Pendiente |
| 5. Flujo y herramientas | Subcomandos por etapa en la CLI; 30 herramientas obsoletas; 16 que requieren decisión del propietario | SPEC-011 | Pendiente |
| 6. Artefactos e higiene | Reglas de `.gitignore` de FR-008.4; ramas `codex/*`/`cursor/*`, duplicados y prueba de higiene integral | SPEC-008, SPEC-012 | Pendiente |
| 7. Agentes, skills y licencias | Invocación real, eficiencia, migración de 4 skills, hook heredado; pedidos de licencia | SPEC-007, SPEC-001 | Pendiente |
| 8. Entrenamiento y evaluación | Piloto, HPO, confirmación y sensibilidad en Colab; entrenar sin B01; D04; prueba real de Colab y copia fuera de la máquina; observaciones experimentales del jurado; tesis (SPEC-006) | SPEC-005, SPEC-006, SPEC-008, SPEC-009, SPEC-013, SPEC-014 | Último |

## Decisiones del propietario que siguen abiertas

| Decisión | Módulo | Recomendación |
|---|---|---|
| D04, recompensar la factura | 8 | No cambiar la recompensa para el piloto; la factura queda como KPI |
| Supuestos económicos sin fuente (CAPEX FV, tasa de descuento) | 8 | Verificar con IRENA y la tasa social del MEF antes de la tesis final |
| Retirar `iquitos_v1` (D01) | 8 | Conservarlo hasta tener el piloto |
| 16 herramientas que requieren decisión | 5 | Se proponen una por una en el módulo 5 |
| Publicar los pedidos de licencia | 7 | Publicarlos; no inventar licencias |

## Decisiones tomadas el 2026-11-06

- El piloto se ejecutará en Colab A100 cuando llegue el módulo 8.
- MASAC se reformula antes de entrenar (D05). Reducir solo el búfer no basta: el búfer muestrea con reemplazo (`external/MARL/src/common/replay_buffer.py:58`), así que el crítico se actualiza sobre 32 episodios aunque el búfer guarde menos, y eso fija la VRAM.
