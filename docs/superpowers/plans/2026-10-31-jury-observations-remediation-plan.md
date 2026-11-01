# Jury Observations Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Every conclusion must be backed by a primary paper, indexed article, master/doctoral thesis, or a project artifact with explicit provenance.

**Goal:** Levantar las observaciones del jurado sin inflar la evidencia: corregir contradicciones documentales de inmediato y ejecutar por separado las validaciones que requieren nuevos experimentos.

**Architecture:** `JuryObservation` enlaza observación, evidencia, estado, corrección y prueba. La tesis consume decisiones estadísticas desde artefactos canónicos; no codifica conclusiones manuales. Las observaciones documentales y experimentales usan puertas distintas.

**Tech Stack:** Python 3.9, pytest, python-docx, Markdown, JSON/YAML, SciPy, rliable o implementación abierta equivalente, PowerShell y renderizado local abierto.

**Source audit:** `docs/audits/MATRIZ_LEVANTAMIENTO_OBSERVACIONES_JURADO_2026-10-31.md`

**Spec Kit slice:** `SPEC-009 — Levantamiento de observaciones del jurado`.

## Global Constraints

- El DOCX del jurado es entrada de solo lectura.
- No cambiar “una semilla” por “multisemilla” sin ejecuciones independientes verificadas.
- No usar episodios correlacionados como sustitutos de semillas.
- No reincorporar HAPPO a HE/HG hasta disponer de KPI-gains finales comparables.
- No declarar seguridad, privacidad, escalabilidad, piloto o TRL superior como implementados si solo se discuten.
- Toda herramienta requerida será abierta y ejecutable localmente; no usar servicios de pago o suscripción.
- Antes de cada edición u operación Git, ejecutar `scripts/verify_project_context.ps1`.

### Task 1: Formalizar SPEC-009 y el manifiesto de observaciones

**Files:**
- Create: `specs/009-jury-observations/spec.md`
- Create: `specs/009-jury-observations/plan.md`
- Create: `specs/009-jury-observations/tasks.md`
- Create: `data/audits/jury_observations_manifest.json`
- Test: `tests/acceptance/test_jury_observations_manifest.py`

- [ ] Escribir prueba que exige ID, severidad, fuente, estado, evidencia, acción, responsable y criterio de cierre.
- [ ] Registrar J-01–J-17 sin marcar como resuelto un requisito experimental pendiente.
- [ ] Verificar que la suma por estado coincide con el informe Markdown.

### Task 2: Establecer una única verdad estadística para PE/OE/HE

**Files:**
- Modify: `tools/eval/run_problem_objective_hypothesis_statistical_analysis.py`
- Modify: `tools/thesis/thesis_doctoral_sections.py`
- Modify: `docs/tesis_capitulos/Capitulo_5_Resultados.md`
- Modify: `docs/tesis_capitulos/Capitulo_6_Conclusiones.md`
- Test: `tests/thesis/test_hypothesis_decision_consistency.py`

- [ ] Hacer fallar la prueba ante “superior”, “demuestra” o “mejor estadísticamente” cuando `p >= alpha`.
- [ ] Generar el texto de OE.1–OE.3 desde `decisiones_problemas_objetivos_hipotesis.csv`.
- [ ] Separar en campos distintos `descriptive_leader` e `inferential_decision`.
- [ ] Verificar en ambos Word: HE10/HE20/HE30 no rechazadas y líderes rotulados “descriptivos de esta corrida”.

### Task 3: Resolver la contradicción HAPPO 49/50

**Files:**
- Modify: `tools/eval/run_complete_drive_kpi_objective_analysis.py`
- Modify: `tools/thesis/update_word_quantitative_50episodes.py`
- Modify: `docs/tesis_capitulos/Capitulo_3_Metodologia.md`
- Modify: `docs/tesis_capitulos/Capitulo_5_Resultados.md`
- Test: `tests/acceptance/test_happo_coverage_contract.py`

- [ ] Definir `episodic_curve_coverage`, `final_kpi_coverage` e `inferential_eligibility` como campos separados.
- [ ] Aceptar la unión 49 históricos + 1 post-resume solo para descripción si su procedencia e índice son válidos.
- [ ] Mantener `inferential_eligibility=false` mientras falten KPI-gains homogéneos.
- [ ] Regenerar KPI-gains HAPPO o rotular el diseño inferencial efectivo como 3×3.

### Task 4: Separar los tres ejes ejecutados de UC3M

**Files:**
- Modify: `docs/tesis_capitulos/Capitulo_2_Marco_Teorico.md` if present
- Modify: `docs/tesis_capitulos/Capitulo_3_Metodologia.md`
- Modify: `tools/thesis/thesis_doctoral_sections.py`
- Test: `tests/thesis/test_executed_vs_future_axes.py`

- [ ] Registrar E1–E3 como `executed=true` y los ejes auxiliares UC3M como `executed=false`.
- [ ] Mover el detalle no ejecutado a extensión arquitectónica/trabajo futuro.
- [ ] Prohibir frases que atribuyan resultados experimentales a siete ejes.

### Task 5: Ejecutar campaña multisemilla confirmatoria

**Files:**
- Modify: `scripts/launch_citylearn_v3_multiseed_campaign.ps1`
- Modify: `tools/eval/aggregate_multiseed_seed_kpis.py`
- Create: `configs/experiments/madrl_4x3_multiseed.yaml`
- Create: `tools/eval/build_rliable_report.py`
- Test: `tests/integration/test_multiseed_campaign_manifest.py`

- [ ] Pre-registrar semillas, algoritmos, escenarios, presupuesto y regla de interrupción.
- [ ] Ejecutar 10–20 semillas cuando existan recursos; nunca ocultar semillas fallidas.
- [ ] Calcular mediana, IQM, IC bootstrap, perfil de rendimiento y probabilidad de mejora.
- [ ] Repetir HE/HG usando la semilla como unidad independiente y registrar cualquier cambio de conclusión.

### Task 6: Añadir introducción, aporte y reproducibilidad

**Files:**
- Modify: `docs/tesis_capitulos/Capitulo_1_Introduccion.md`
- Modify: `docs/tesis_capitulos/Capitulo_6_Conclusiones.md`
- Create: `docs/tesis_capitulos/Anexo_Reproducibilidad.md`
- Test: `tests/thesis/test_intro_contribution_reproducibility.py`

- [ ] Crear una introducción general breve, sin duplicar el planteamiento.
- [ ] Unificar el aporte: integración y evaluación estandarizada para el SEAI Iquitos, dataset/pipeline y extensión experimental; no novedad algorítmica.
- [ ] Incluir URL del repositorio, commit, licencia, entorno, datos, submódulos y comandos reproducibles.

### Task 7: Documentar datos faltantes, leakage y sesgo de simulación

**Files:**
- Create: `docs/research/data_quality_and_validity_matrix.yaml`
- Modify: `docs/tesis_capitulos/Capitulo_3_Metodologia.md`
- Modify: `docs/tesis_capitulos/Capitulo_5_Resultados.md`
- Test: `tests/thesis/test_data_validity_controls.py`

- [ ] Inventariar por variable la ausencia y su tratamiento; ninguna imputación implícita.
- [ ] Registrar cortes temporales y `fit_scope` de transformaciones para impedir fuga de futuro.
- [ ] Añadir amenazas de simulación: clima, ocupación, tarifa, red, equipos y comportamiento humano.

### Task 8: Añadir seguridad, privacidad y operación segura

**Files:**
- Create: `docs/thesis/SECURITY_PRIVACY_DEPLOYMENT.md`
- Create: `docs/operations/MADRL_DEPLOYMENT_RUNBOOK.md`
- Modify: capítulos 4 y 7 mediante sus fuentes canónicas
- Test: `tests/thesis/test_security_privacy_claims.py`

- [ ] Modelar amenazas sobre observación, acción, recompensa, checkpoint, API y enlace OT/IT.
- [ ] Definir minimización de datos, autenticación, cifrado, integridad, auditoría y respuesta.
- [ ] Definir fallback RBC, límites de acción, rollback, monitoreo de deriva y responsables.
- [ ] Rotular todo como requisito de futuro despliegue hasta contar con evidencia ejecutada.

### Task 9: Evaluar escalabilidad, economía y madurez

**Files:**
- Create: `tools/eval/benchmark_scalability.py`
- Create: `tools/eval/analyze_deployment_economics.py`
- Create: `docs/thesis/TRL_TRANSFER_ROADMAP.md`
- Test: `tests/eval/test_scalability_and_economics_contracts.py`

- [ ] Medir tiempo, memoria, latencia y KPI en tamaños de comunidad factibles.
- [ ] Separar costo energético simulado de CAPEX/OPEX e indicar moneda, año y fuente.
- [ ] Mantener TRL 4 y definir evidencia requerida para TRL 5–6.

### Task 10: Regenerar los Word y emitir respuesta final

**Files:**
- Modify: los dos DOCX canónicos definidos por `docs/workflow_manifest.json`
- Create: `docs/audits/RESPUESTA_OBSERVACIONES_JURADO.md`
- Create: `data/audits/jury_observations_acceptance.json`
- Test: `tests/acceptance/test_jury_response_acceptance.py`

- [ ] Parchear desde fuentes canónicas, no mediante búsquedas ambiguas.
- [ ] Reabrir, validar estructura, renderizar todas las páginas y revisar visualmente.
- [ ] Generar tabla “observación → corrección → página → evidencia”.
- [ ] Mantener como `pending_experiment` todo ítem no ejecutado.
- [ ] Cerrar solo cuando el manifiesto y ambos Word sean coherentes.

## Acceptance Gate

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_jury_observations_gates.ps1
```

Expected: código `0`; cero contradicciones HE, cero mezcla UC3M/experimento, HAPPO correctamente clasificado, referencias verificables y estados experimentales no inflados.
