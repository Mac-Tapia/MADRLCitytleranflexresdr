# Tareas — SPEC-005

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-005.2:** Pareto puro — `uc3m/domain/pareto.py`
- [x] **FR-005.3:** Diseño de sensibilidad y dry-run — `uc3m/application/sensitivity.py, data/audits/weight_sensitivity.json`
- [ ] **FR-005.4:** Configuración de campaña 4×3 multisemilla — `configs/experiments/madrl_4x3_multiseed.yaml`
- [ ] **FR-005.4:** Ejecutar campaña de horizonte completo (requiere aprobación de cómputo) — `outputs/<campaña>`
- [x] **FR-005.5 (herramienta, 2026-11-08):** Informe estadístico multisemilla. `pipeline analyze` (`uc3m/application/evaluation/fresh_analysis.py`) calcula, por semillas, Friedman y Wilcoxon pareado, con Holm dentro de cada familia, y un intervalo percentil de la media (semilla 7001, 10 000 remuestreos, 95 %), además de media e IQM. `tools/eval/build_campaign_statistical_report.py` no calcula nada: lee ese análisis con `read_verified_analysis` y separa `descriptive_leader` de `inferential_decision`, sin superioridad si el omnibus no es significativo tras Holm; falla cerrado (código 2) si no hay análisis registrado, si este o un intento ya no verifican, si está incompleto o con menos de 2 semillas. Verificado solo con KPI sintéticos: `tests/fresh_training/test_fresh_statistical_report.py`, `tests/unit/application/test_campaign_statistical_report.py`.
- [ ] **FR-005.5 (informe real):** Ejecutar `pipeline analyze` y la herramienta sobre la campaña nueva verificada (bloqueado por FR-005.4). `confirm` tiene 12 semillas (1001 a 1012); Holm corrige dentro de cada familia, no entre familias.
- [x] **FR-005.6 (contrato, 2026-11-01):** Prueba de aceptación de la regla existente — `tests/acceptance/test_model_selection.py` (máxima media de hipervolumen, desempate por menor varianza, rechazo de campaña incompleta, cadena sintética catálogo → corrida no verificada → rechazo).
- [ ] **FR-005.6 (pendiente):** Ejecutar `pipeline.select_model` sobre la evaluación de `confirm` en `validation_2024` de una campaña real. Ya verifica el análisis con `read_verified_analysis`, rechaza cualquier otra partición, construye el mapa `evaluation` desde el catálogo (`selection_evaluation`) y solo nombra ganador inferencial si gana en los tres ejes (`selection_inference`). `select_best_model` sigue sin verificar corridas por sí mismo, así que la única vía es `pipeline.select_model`; un empate total se resuelve por identificador de algoritmo. Verificado solo con KPI sintéticos: `tests/fresh_training/test_fresh_statistical_report.py`.

**Aceptación:** `python -m pytest -q tests/contract/multiobjective tests/contract/training tests/acceptance`
