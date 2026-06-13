# tools/ — scripts del pipeline de dataset, auditoría y reportes

Fase 6 del plan de reorganización (`docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`)
propone subdividir `tools/` en `dataset/`, `audit/` y `reports/`. **Esta
subdivisión física NO se ejecutó** en esta pasada: los scripts tienen
imports cruzados directos (`from size_bess_optimal import ...`,
`from generate_iquitos_dataset import ...`, etc.) y `orchestrate_citylearn_dataset.py`
invoca a más de 10 scripts hermanos vía subprocess con rutas relativas
`tools/<script>.py`. Mover físicamente estos archivos mientras hay un
entrenamiento activo y sin poder ejecutar el pipeline completo de dataset
para validar cada import roto es de alto riesgo y bajo beneficio inmediato
— por eso se mantiene como **trabajo pendiente, no bloqueante**.

Categorización propuesta para una futura migración (con ventana de
validación completa del pipeline de dataset):

## dataset/ (generación y transformación del dataset)
`buildingcsv_inputs.py`, `calibrate_buildings.py`, `clean_dataset_orphans.py`,
`dimension_ev_chargers.py`, `distill_building_loads.py`, `fix_and_validate.py`,
`fix_schema_cooling.py`, `fix_solar_pvlib.py`, `generate_b01_billing.py`,
`generate_iquitos_dataset.py`, `rebuild_per_building_profiles.py`,
`size_bess_optimal.py`, `sync_controlled_machines.py`

## audit/ (auditorías y validaciones)
`audit_citylearn_csv_integrity.py`, `audit_der_sizing.py`,
`audit_training_dataset_provenance.py`, `verify_ev_sessions.py`,
`verify_solar.py`, `verify_training_optimization.py`,
`verify_artifact_layout.py`

## reports/ (análisis y reportes — ya iniciado en Fase 1)
`analyze_support_files.py`, `dataset_report.py`, `deep_dataset_analysis.py`,
`evaluate_dataset.py`, `evaluate_iquitos_citylearn_v3_dataset.py`,
`diagnostico_dataset.py` (movido desde raíz), `ver_metricas_madrl.py`
(movido desde raíz)

## raíz de tools/ (orquestación canónica, rutas fijadas en `docs/workflow_manifest.json`)
`orchestrate_citylearn_dataset.py`, `check_training_dataset_ready.py`,
`verify_workflow_integrity.py`, `dataset_docs/`

## Migración futura recomendada
1. Ejecutar el pipeline completo de dataset (`orchestrate_citylearn_dataset.py`)
   en un entorno sin entrenamiento activo para tener una corrida de
   referencia "antes".
2. Mover archivos por subcarpeta y convertir los imports cruzados
   (`from size_bess_optimal import ...`) a imports relativos de paquete
   (`from .size_bess_optimal import ...` + `__init__.py` en cada subcarpeta)
   o a imports absolutos (`from tools.dataset.size_bess_optimal import ...`).
2. Actualizar las rutas `tools/<script>.py` hardcodeadas en
   `orchestrate_citylearn_dataset.py`, `verify_workflow_integrity.py` y
   `docs/workflow_manifest.json`.
3. Re-ejecutar el pipeline y comparar artefactos con la corrida "antes".
