# Tareas — SPEC-004

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-004.1:** Identidad y especificación — `uc3m/domain/experiments.py`
- [x] **FR-004.2:** Manifiesto de evidencia — `uc3m/domain/evidence.py`
- [x] **FR-004.3:** Preflight — `uc3m/application/training/preflight.py`
- [~] **FR-004.4, sustituido (2026-11-06):** la continuidad exacta no aplica a la campaña vigente. El plan aprobado decide que todo intento empieza en el episodio 0, que no se reanuda y que no se suman intentos parciales ([remediacion_integrada.md](../../docs/plans/remediacion_integrada.md), sección de principios; [entrenamiento.md](../../docs/plans/entrenamiento.md): *"una futura reanudación requerirá otro contrato"*). Por eso no se crea `test_resume_trajectory_parity.py`, ni se declara una igualdad de trayectoria que no existe.
  - **Lo que sí rige (SPEC-015 FR-015.5):** los 4 lanzadores guardan `training_state.pt` junto a sus pesos, con los optimizadores que declara `native.yaml` (los mismos que se observan actualizándose), sus momentos y el RNG de torch, CUDA, numpy y python. No guardan la réplica.
  - **Uso del estado:** inferencia, auditoría y respaldo. Lo verifican `tests/fresh_training/test_real_learning.py::test_every_launcher_saves_its_training_state` y `tests/contract/test_resume_state_parity.py`.
  - **Para reanudar en el futuro** haría falta un contrato nuevo, con réplica persistida y una prueba de igualdad por algoritmo.
- [ ] **FR-004.5:** Manifiesto de runs históricos — `data/audits/historical_runs_manifest.json`

**Aceptación:** `python -m pytest -q tests/unit/domain tests/contract/training`
