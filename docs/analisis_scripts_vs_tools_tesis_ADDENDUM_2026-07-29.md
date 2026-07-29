# Addendum — reorg `tools/dataset/` (2026-07-29)

**Estado del archivo principal:** `docs/analisis_scripts_vs_tools_tesis.md`
**actualizado** en esta pasada (ya no bloqueado). Las rutas de dataset apuntan a
`tools/dataset/` y la seccion 12 documenta los dominios
(`dataset/`, `eval/`, `colab/`, `drive/`, `training/`, `ops/`, `figures/`, `thesis/`).

Detalle de la reorganizacion: `docs/analisis_reorganizacion_tools_dataset.md`.

## Reemplazos de ruta (referencia)

| Antes (raiz `tools/`) | Despues |
|------------------------|---------|
| `tools/generate_iquitos_dataset.py` | `tools/dataset/generate_iquitos_dataset.py` |
| `tools/fix_solar_pvlib.py` | `tools/dataset/fix_solar_pvlib.py` |
| `tools/orchestrate_citylearn_dataset.py` | `tools/dataset/orchestrate_citylearn_dataset.py` |
| `tools/distill_building_loads.py` | `tools/dataset/distill_building_loads.py` |
| `tools/check_training_dataset_ready.py` | `tools/dataset/check_training_dataset_ready.py` (shim en raiz por CityLearn launcher) |
| `tools/verify_solar.py` | `tools/dataset/verify_solar.py` |
| `tools/dimension_ev_chargers.py` | `tools/dataset/dimension_ev_chargers.py` |
| `tools/size_bess_optimal.py` | `tools/dataset/size_bess_optimal.py` |
| `tools/audit_der_sizing.py` | `tools/dataset/audit_der_sizing.py` |
| `tools/audit_training_dataset_provenance.py` | `tools/dataset/audit_training_dataset_provenance.py` |
| `tools/fix_schema_cooling.py` | `tools/dataset/fix_schema_cooling.py` |
