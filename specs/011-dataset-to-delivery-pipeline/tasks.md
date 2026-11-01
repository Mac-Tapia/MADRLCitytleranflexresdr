# Tareas — SPEC-011

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-011.1:** Orquestador de dataset existente — `tools/dataset/orchestrate_citylearn_dataset.py`
- [x] **FR-011.2:** Verificador de dataset listo — `tools/dataset/check_training_dataset_ready.py`
- [x] **FR-011.1:** Inventario: los 21 scripts de `tools/dataset/` son etapas del orquestador (11, en orden) o soporte documentado en su README; los sueltos ya se retiraron el 2026-07-29. El reporte de destilación se escribía y leía en `tools/dataset_docs/`, ruta abandonada desde el 2026-07-29, lo que dejaba el chequeo en BLOCKED; ahora ambos usan `tools/dataset/dataset_docs/` y una prueba lo fija — `tests/contract/test_dataset_pipeline_paths.py`
- [ ] **FR-011.4:** Subcomandos por etapa en la CLI y lanzadores `.bat/.ps1` que deleguen en ella; hoy `scripts/LANZAR_ENTRENAMIENTO_V4.bat` llama a los scripts de CityLearn sin pasar por el candado — `uc3m/application/training/cli.py`
- [x] **FR-011.5:** Candado dataset → entrenamiento: el chequeo registra `dataset_digest` (schema y todos los CSV referenciados) y `cli.py`/`colab.py` se niegan a ejecutar si el manifiesto no está `ready` o el dataset cambió después; un byte distinto bloquea hasta revalidar — `uc3m/application/training/dataset_gate.py, tests/unit/application/test_dataset_gate.py`
- [ ] **FR-011.6:** Humo end-to-end — `tests/acceptance/test_pipeline_smoke.py`

**Aceptación:** `python -m pytest -q tests/acceptance/test_pipeline_smoke.py`
