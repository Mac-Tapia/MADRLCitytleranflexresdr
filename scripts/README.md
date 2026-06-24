# scripts/ — orquestación PowerShell del entrenamiento CityLearn v3 MADRL

Fase 4 del plan de reorganización (`docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`)
propone regrupar estos `.ps1` en `scripts/{training,monitoring,setup}/`.

**Esta subdivisión NO se ejecutó** en esta pasada porque:

1. Hay un entrenamiento activo (`status: running`,
   `outputs/citylearn_v3_madrl_full_20260613_010234`) lanzado a partir de
   estos mismos scripts.
2. Todos resuelven `$ProjectRoot` vía `$PSScriptRoot` con un único `..`
   (asumen que están exactamente un nivel bajo la raíz del repo). Moverlos
   a una subcarpeta (`scripts/training/...`) rompe esa resolución
   (`..` apuntaría a `scripts/`, no a la raíz) y requiere editar cada script
   y cualquier proceso/atajo que los invoque por ruta.
3. `training_launcher_window.ps1` / `training_resume_window.ps1` pueden
   estar referenciados desde accesos directos o tareas programadas fuera
   del repo.

Lo que sí se ejecutó (Fase 1): los `.bat` sueltos de la raíz se movieron a
`scripts/legacy_bat/`.

## Categorización propuesta para una migración futura (con el entrenamiento detenido)

- **training/**: `run_citylearn_v3_full_training_visible.ps1`,
  `training_launcher_window.ps1`, `training_resume_window.ps1`
- **monitoring/**: `monitor_citylearn_training_visible.ps1`
- **setup/**: `activate_citylearn_v3.ps1`, `verify_project_context.ps1`

Pasos para migrar de forma segura:

1. Esperar a que el entrenamiento activo termine (o se detenga
   limpiamente) y confirmar `status != running` en
   `outputs/*/official_full_status.json`.
2. Mover los `.ps1` a sus subcarpetas.
3. En cada script movido, ajustar `$ProjectRoot = (Resolve-Path (Join-Path
   $PSScriptRoot "..")).Path` a `"..\\.."` (un nivel adicional).
4. Actualizar `docs/workflow_manifest.json` (`workflow.training.launcher`,
   `workflow.training.wrapper`, `workflow.monitoring.*`) y cualquier acceso
   directo/tarea programada de Windows que invoque estos scripts por ruta
   absoluta.
5. Relanzar un dry-run corto para confirmar que `$ProjectRoot` resuelve
   correctamente antes de lanzar el entrenamiento completo.
