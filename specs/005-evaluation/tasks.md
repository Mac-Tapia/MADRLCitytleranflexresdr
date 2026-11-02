# Tareas — SPEC-005

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-005.2:** Pareto puro — `uc3m/domain/pareto.py`
- [x] **FR-005.3:** Diseño de sensibilidad y dry-run — `uc3m/application/sensitivity.py, data/audits/weight_sensitivity.json`
- [ ] **FR-005.4:** Configuración de campaña 4×3 multisemilla — `configs/experiments/madrl_4x3_multiseed.yaml`
- [ ] **FR-005.4:** Ejecutar campaña de horizonte completo (requiere aprobación de cómputo) — `outputs/<campaña>`
- [x] **FR-005.5 (herramienta, 2026-11-01):** Informe estadístico multisemilla — `tools/eval/build_campaign_statistical_report.py` (sustituye al previsto `build_rliable_report.py`; solo numpy/scipy, sin rliable). Media, IQM (`trim_mean` 25 %), IC bootstrap percentil del IQM (semillas remuestreadas por estrato algoritmo×escenario, `BOOTSTRAP_SEED=20211206`, 10 000 remuestreos, 95 %), Kruskal-Wallis + Dunn-Holm reutilizados de `uc3m/multicriteria/stats_tests.py`; `descriptive_leader` separado de `inferential_decision`, sin superioridad si p ≥ α; falla cerrado (código 2) ante tratamientos/semillas faltantes, corridas no verificadas o incompletas, KPI orientado ausente o < 2 semillas. Verificado solo con fixtures sintéticos: `tests/unit/application/test_campaign_statistical_report.py`.
- [ ] **FR-005.5 (informe real):** Ejecutar la herramienta sobre la campaña nueva verificada (bloqueado por FR-005.4). Con 3 semillas el IC 95 % es el rango muestral y los p-valores son asintóticos; sin corrección entre KPI/escenarios.
- [x] **FR-005.6 (contrato, 2026-11-01):** Prueba de aceptación de la regla existente — `tests/acceptance/test_model_selection.py` (máxima media de hipervolumen, desempate por menor varianza, rechazo de campaña incompleta, cadena sintética catálogo → corrida no verificada → rechazo).
- [ ] **FR-005.6 (pendiente):** `select_best_model` no verifica corridas por sí mismo (confía en `campaign_complete`), no modela separación entrenamiento/evaluación (fuga no comprobable), no exige significancia antes de nombrar el mejor modelo y no define el empate total (depende del orden de entrada); falta el constructor de producción del mapa `evaluation` desde el catálogo.

**Aceptación:** `python -m pytest -q tests/contract/multiobjective tests/contract/training tests/acceptance`
