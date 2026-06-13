# Registro de cambios: reorganizacion del proyecto y politica de paralelismo MADRL

**Fecha:** 2026-06-13
**Proyecto:** `MADRLCitytleranflexresdr`
**Alcance:** Consolida (a) el resultado de la reorganizacion documental/estructural ejecutada en `docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md` (Fases 0-8, completas) y (b) el analisis de factibilidad de entrenamiento paralelo E1/E2/E3 por algoritmo realizado el 2026-06-13, junto con la decision tomada.

## 1. Resumen de la reorganizacion aplicada (Fases 0-8)

Todas las tareas #1-#15 del plan en `ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md` quedaron completadas. Cambios estructurales visibles en el arbol del proyecto:

- `docs/` reorganizado en subcarpetas tematicas: `docs/architecture/`, `docs/audits/`, `docs/decisions/`, `docs/thesis/`, `docs/contributions/<submodulo>/` (con `CHANGES.md` y `bibliografia.bib` por submodulo modificado).
- `docs/00_INDEX.md` creado como punto de entrada a toda la documentacion.
- Archivos previamente sueltos en `docs/` (informes, planes de tesis, diagramas) migrados a sus subcarpetas correspondientes; las rutas antiguas (`docs/ARQUITECTURA_*.md`, `docs/INFORME_*.md`, `docs/PLAN_TESIS_*`, `docs/JUSTIFICACION_*.md`, `docs/*.png/.pdf`, `docs/Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx`, `docs/dataset_construction_pipeline.md`, `docs/APORTES_*`) quedan eliminadas de la raiz de `docs/` y disponibles en `docs/architecture/`, `docs/audits/`, `docs/decisions/` o `docs/thesis/` segun corresponda.
- `agent-skills/` y `deploy/` agregados como nuevas carpetas de soporte (skills locales del repositorio y artefactos de despliegue Docker/AWS, Fase 8).
- `docs/workflow_manifest.json` (schema_version 2) actualizado como manifiesto canonico maquina-legible del flujo dataset -> entrenamiento -> comparacion -> evidencia de tesis.
- Scripts batch redundantes en la raiz (`monitor_citylearn_training_visible.bat`, `relanzar_entrenamiento_madrl.bat`, `run_citylearn_training_live_visible.bat`) y `diagnostico_dataset.py` duplicado consolidados/removidos de la raiz a favor de sus equivalentes en `scripts/`/`CityLearn/scripts/`.
- `.github/ISSUE_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/ci.yml`, `.gitignore`, `.vscode/settings.json` y `.vscode/extensions.json` actualizados para reflejar la nueva estructura de carpetas y las rutas de documentacion vigentes.
- `README.md`, `ESTRATEGIA_3PILARES_MADRL.md`, `agent-skills/madrl-citylearn-thesis-plan/SKILL.md`, `docs/architecture/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` y `docs/thesis/PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md` actualizados con las rutas y el estado vigente.
- Verificacion final (tarea #15): estructura `docs/` confirmada por carpeta tematica, `workflow_manifest.json` valido, README y AGENTS.md consistentes con el arbol actual.

Detalle completo, justificacion y matriz de decisiones por fase: ver `docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`.

## 2. Analisis de paralelismo E1/E2/E3 por algoritmo (2026-06-13)

Se evaluo si los 12 jobs (4 algoritmos x 3 escenarios) pueden correr con mas paralelismo del actual en la GPU local (RTX 4060 Laptop, 8,188 MiB VRAM, ~6,700 MiB utilizables tras `GpuVramReserveGib=1.5`).

### 2.1 Configuracion vigente (confirmada en archivos)

- `scripts/run_citylearn_v3_full_training_visible.ps1`: `ParallelScenarios=$true`, `MaxConcurrentScenarioJobs=2`, `MaxConcurrentHeavyJobs=1`, `TorchThreads=12`, `GpuProfile="local4060_fast"`, `GpuVramReserveGib=1.5`, `LiveOutput=$false` por defecto.
- `CityLearn/configs/citylearn_v3_madrl_training.json`: `official_training.execution="sequential"` (orden de etapas por algoritmo: HAPPO -> MASAC -> MATD3 -> MAAC), `torch_threads=8` a nivel global, pero el `cli.torch_threads=12` explicito en el bloque `algorithms.HAPPO` (los demas algoritmos heredan el valor del launcher, 12).

### 2.2 Estimacion de consumo por job

| Algoritmo | VRAM aprox./job | RAM aprox./job | Categoria |
| --------- | ---------------: | --------------: | --------- |
| HAPPO | ~300 MiB | ~1.9 GB | ligero (on-policy) |
| MATD3 | ~300 MiB | ~2.0 GB | ligero (off-policy determinista) |
| MASAC | ~500 MiB | ~3.5 GB | pesado (replay + QMIX) |
| MAAC | ~450 MiB | ~3.0 GB | pesado (replay + atencion) |

### 2.3 Hallazgo nuevo: sobre-suscripcion de hilos CPU

Con `torch_threads=12` por proceso:

- 2 jobs concurrentes (politica actual) -> 24 hilos solicitados.
- 3 jobs concurrentes (E1+E2+E3 simultaneos) -> 36 hilos solicitados.

Las CPU tipicas que acompanan una RTX 4060 Laptop tienen entre 14 y 24 hilos de hardware. 36 hilos solicitados sobre ese rango produce sobre-suscripcion de CPU (contencion de scheduler, throughput por hilo degradado), ademas de que en escenarios pesados (MASAC/MAAC) el VRAM en picos de batch (~1.35-1.5 GB acumulados) y RAM (~9-10.5 GB) quedan ajustados o en riesgo de OOM con 3 jobs simultaneos.

### 2.4 Decision

**Se mantiene la configuracion actual sin cambios:**

```text
ParallelScenarios=true
MaxConcurrentScenarioJobs=2   (HAPPO, MATD3)
MaxConcurrentHeavyJobs=1      (MASAC, MAAC)
TorchThreads=12
GpuProfile=local4060_fast
GpuVramReserveGib=1.5
LiveOutput=false (modo visible por defecto)
```

Justificacion: 2 escenarios concurrentes para HAPPO/MATD3 y 1 para MASAC/MAAC es el optimo validado para el hardware local (RTX 4060 Laptop 8 GB + CPU companion tipica). Subir a 3 escenarios concurrentes simultaneos es VRAM-factible para HAPPO/MATD3 pero queda limitado por sobre-suscripcion de hilos CPU (36 vs ~14-24 disponibles) y, para MASAC/MAAC, ademas por riesgo de OOM de VRAM/RAM en picos de batch. Una variante de 3 paralelos con `torch_threads` reducido (~4 por job) fue identificada como opcion futura pero **no se implementa**; el comportamiento por defecto del launcher permanece sin modificaciones.

Esta decision no afecta ninguna otra corrida de entrenamiento activa fuera de este proyecto (`D:\MADRLCitytleranflexresdr`); no se modifico ningun proceso en ejecucion.

## 3. Archivos actualizados como parte de este registro

- `docs/decisions/REGISTRO_CAMBIOS_REORGANIZACION_Y_POLITICA_PARALELISMO_2026-06-13.md` (este archivo, nuevo)
- `docs/00_INDEX.md` (referencia agregada en `decisions/`)

## 4. Referencias

- `docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md` — plan y ejecucion de la reorganizacion (Fases 0-8).
- `docs/decisions/JUSTIFICACION_DISENO_EXPERIMENTAL_ESCENARIOS_PARALELO.md` — fundamento academico de E1/E2/E3 como experimentos independientes.
- `docs/audits/INFORME_OPTIMIZACION_CITYLEARN_MADRL_VRAM.md` — politica de VRAM vigente (`MaxConcurrentScenarioJobs=2`, `MaxConcurrentHeavyJobs=1`).
- `scripts/run_citylearn_v3_full_training_visible.ps1` — parametros por defecto del launcher.
- `CityLearn/configs/citylearn_v3_madrl_training.json` — configuracion canonica de entrenamiento (`official_training`, `algorithms.*.cli`).
