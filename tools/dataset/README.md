# tools/dataset/ — creación del dataset CityLearn Iquitos

Carpeta **única** para generación, sincronización DER, auditoría y gate
del dataset `citylearn_iquitos_2023_2025`. No mezclar aquí scripts de
tesis, KPIs Drive, Colab ni entrenamiento.

## Entrada canónica

```powershell
.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\orchestrate_citylearn_dataset.py `
  --dataset-dir CityLearn\data\datasets\citylearn_iquitos_2023_2025
```

Gate final (también lo ejecuta el orquestador):

```powershell
.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\check_training_dataset_ready.py `
  --manifest-out data\dataset_audit\training_dataset_ready_manifest.json
```

Integridad del workflow (fuera de esta carpeta):

```powershell
.venv39-citylearn-v3\Scripts\python.exe -B tools\ops\verify_workflow_integrity.py `
  --manifest-out data\dataset_audit\workflow_integrity_manifest.json
```

## Orden del pipeline (orchestrate)

1. `generate_iquitos_dataset.py` — base (edificios, weather, pricing, carbon, schema)
2. `distill_building_loads.py` — cargas reales + costos desde `buildingcsv`
3. `fix_solar_pvlib.py` — PV pvlib/TMY
4. `dimension_ev_chargers.py` — cargadores EV
5. `sync_controlled_machines.py` — Washing_Machine_X
6. `fix_schema_cooling.py` — safety_factor cooling
7. `size_bess_optimal.py --write` — BESS
8. `audit_der_sizing.py` / `audit_training_dataset_provenance.py`
9. `clean_dataset_orphans.py` / `audit_citylearn_csv_integrity.py`
10. `evaluate_dataset.py` / `deep_dataset_analysis.py`
11. `check_training_dataset_ready.py` — gate pre-MADRL

## Soporte y reportes auxiliares (no etapas del orquestador)

| Script | Rol |
|--------|-----|
| `buildingcsv_inputs.py` | Biblioteca de inventario/mediciones (importada por varios) |
| `generate_b01_billing.py` | Genera `buildingcsv/B_01.csv` desde Excel |
| `verify_solar.py` | Verificación read-only PV |
| `verify_ev_sessions.py` | Diagnóstico sesiones EV |
| `evaluate_iquitos_citylearn_v3_dataset.py` | Informe formal Mode3/V2G → MD/JSON |

Documentación auxiliar: `dataset_docs/`.

Stubs históricos (`calibrate_buildings.py`, `diagnostico_dataset.py`, etc.) fueron
**eliminados** en auditoría 2026-07-29; usar solo los scripts listados arriba.
Ver `docs/AUDITORIA_TOOLS_2026-07-29.md`.
