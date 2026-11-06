# Tareas — SPEC-003

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-003.3:** Módulos de entrenamiento extraídos — `uc3m/application/training/*.py`
- [x] **FR-003.1:** LearnerPort y ArtifactStore — `uc3m/ports/learner.py, uc3m/ports/artifact_store.py`
- [x] **FR-003.1:** `SimulatorPort` sin numpy y los tres puertos `runtime_checkable` y exportados; `ExperimentTrackerPort` aplazado hasta tener consumidor (ADR) — `uc3m/ports/*.py, docs/decisions/simulator.md`
- [x] **FR-003.2:** Conformidad verificada de `NativeBackend` con `LearnerPort` y de `LocalArtifactStore` con `ArtifactStore` — `tests/contract/test_ports_contract.py`
- [ ] **FR-003.4:** TrainingReportBuilder, tablas y FigureRenderer — `uc3m/application/evaluation/tables.py, uc3m/adapters/matplotlib_figures.py`
- [x] **FR-003.5 (2026-11-06, SPEC-015 FR-015.4):** el adaptador `uc3m/adapters/process_tree.py` lanza cada intento como un árbol de procesos cancelable, usando solo la biblioteca estándar.
  - **Lado del padre:** cada hijo es líder de su grupo de procesos (sesión nueva en POSIX, grupo nuevo en Windows) y queda registrado. `cancel_all` termina cada árbol, nietos incluidos, y rechaza lanzamientos posteriores. `cancellation_scope` liga SIGINT, SIGTERM y SIGBREAK de la CLI a esa cancelación, y la CLI informa `cancelled` con el código 130.
  - **Lado del hijo:** `native_entrypoint` vigila al padre en un hilo. Si el padre muere, aunque sea por una terminación forzada o por cerrar una celda de Colab, el hijo termina su propio árbol.
    - En POSIX usa una tubería propia (`pass_fds`) cuyo extremo de escritura solo tiene el padre.
    - En Windows abre el proceso padre y espera con `WaitForSingleObject`.
    - El stdin del hijo es `DEVNULL`.
  - **Defecto reproducido antes del arreglo:** con `subprocess.run`, el hijo seguía vivo 5 s después de matar al lanzador.
  - **Error de la primera versión, corregido:** vigilaba stdin. En Windows, un hilo bloqueado leyendo una tubería congela cualquier otro uso de ese handle, incluso lanzar un subproceso que lo herede, y HAPPO se quedó detenido al arrancar con 0 de CPU. Se reprodujo con una prueba que quedó en rojo y se corrigió.
  - **Verificación final:** pasan 124 pruebas, incluidos los entrenamientos cortos reales de los 4 algoritmos por la CLI (`test_real_learning.py`), en 19 min 36 s.
  - **Pruebas:** 7 en Windows y 5 en Linux (WSL, Python 3.12); el CI corre las 5 de procesos en Ubuntu 24.04 con Python 3.9.
  - **Reanudación:** el relanzamiento crea un intento nuevo desde cero y conserva el interrumpido. — `tests/integration/test_training_interruption.py`
  - **Limitación:** `NativeBackend` (`uc3m/adapters/algorithms/native.py`) también usa `run_child`, pero lanza el script nativo directamente. Ese hijo no vigila al padre: se cancela si el padre lo cancela, pero no si el padre muere. La CLI, la única vía de entrenamiento, sí cubre ambos casos.
- [x] **FR-003.6:** Prueba de arquitectura: el dominio no importa infraestructura ni capas externas, y la aplicación solo llega a adaptadores desde `cli.py`/`colab.py`; `finite_kpis` se movió del adaptador al dominio para cumplirla — `tests/contract/test_import_architecture.py, uc3m/domain/evidence.py`
- [ ] **FR-003:** El manifiesto real de la puerta es `data/audits/modular_training_acceptance.json` (escrito por `tools/ops/audit_modular_training.py`); no se crea un segundo `orchestration_acceptance.json`. Cierre pendiente de FR-003.4 (FR-003.5 hecho el 2026-11-06) — `scripts/quality/run_orchestration_gates.ps1`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_orchestration_gates.ps1`
