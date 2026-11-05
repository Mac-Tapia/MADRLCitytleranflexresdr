# Diagnóstico mecánico por carpeta y módulo

Generado por `generar_diagnostico.py`. Leer hasta el final no equivale a revisar: la columna *vigente* solo cuenta archivos revisados cuyo SHA-256 no ha cambiado desde la revisión.

## Carpetas

| Ruta | Archivos | Líneas | EOF | Vigente | Caducada | Pendiente | Sin lote | Señales |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `(raiz)` | 14 | 656 | 13 | 8 | 0 | 3 | 3 | — |
| `.claude` | 5 | 101 | 5 | 5 | 0 | 0 | 0 | — |
| `.github` | 3 | 184 | 3 | 2 | 0 | 1 | 0 | — |
| `.specify` | 1 | 39 | 1 | 1 | 0 | 0 | 0 | — |
| `.vscode` | 3 | 177 | 3 | 3 | 0 | 0 | 0 | — |
| `configs` | 12 | 1585 | 12 | 11 | 0 | 0 | 1 | — |
| `data` | 461 | 2642845 | 461 | 0 | 0 | 0 | 24 | — |
| `deploy` | 30 | 2089 | 30 | 27 | 0 | 2 | 1 | except_pass 1, marcador 1, sin_prueba 2 |
| `docs` | 326 | 325503 | 326 | 0 | 0 | 73 | 28 | duplicado 1, marcador 3 |
| `examples_madrl_v3` | 7 | 5193 | 7 | 7 | 0 | 0 | 0 | sin_consumidor 1, sin_prueba 1 |
| `external` | 127 | 13224 | 119 | 0 | 0 | 0 | 0 | marcador 1, modulo_grande 1, ruff 11, vacio 22 |
| `governance` | 5 | 624 | 5 | 5 | 0 | 0 | 0 | — |
| `outputs` | 1 | 20 | 1 | 0 | 0 | 0 | 0 | — |
| `scripts` | 19 | 2375 | 19 | 0 | 0 | 19 | 0 | modulo_grande 1, sin_prueba 1 |
| `specs` | 40 | 1078 | 40 | 0 | 0 | 40 | 0 | — |
| `tests` | 157 | 19239 | 157 | 99 | 4 | 40 | 14 | except_pass 2, vacio 5 |
| `tools` | 226 | 62400 | 226 | 0 | 0 | 220 | 6 | duplicado 8, except_pass 10, modulo_grande 14, ruff 33, sin_consumidor 3, sin_prueba 120 |
| `uc3m` | 112 | 18780 | 112 | 73 | 6 | 32 | 1 | duplicado 2, except_pass 3, modulo_grande 3, sin_prueba 6, vacio 2 |

## Módulos

| Ruta | Archivos | Líneas | EOF | Vigente | Caducada | Pendiente | Sin lote | Señales |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `.` | 14 | 656 | 13 | 8 | 0 | 3 | 3 | — |
| `.claude` | 2 | 69 | 2 | 2 | 0 | 0 | 0 | — |
| `.claude/agents` | 3 | 32 | 3 | 3 | 0 | 0 | 0 | — |
| `.github` | 2 | 66 | 2 | 2 | 0 | 0 | 0 | — |
| `.github/workflows` | 1 | 118 | 1 | 0 | 0 | 1 | 0 | — |
| `.specify/memory` | 1 | 39 | 1 | 1 | 0 | 0 | 0 | — |
| `.vscode` | 3 | 177 | 3 | 3 | 0 | 0 | 0 | — |
| `configs` | 2 | 50 | 2 | 2 | 0 | 0 | 0 | — |
| `configs/algorithms` | 1 | 71 | 1 | 1 | 0 | 0 | 0 | — |
| `configs/dataset` | 5 | 1228 | 5 | 4 | 0 | 0 | 1 | — |
| `configs/evaluation` | 1 | 159 | 1 | 1 | 0 | 0 | 0 | — |
| `configs/experiments` | 3 | 77 | 3 | 3 | 0 | 0 | 0 | — |
| `data/audits` | 10 | 5604 | 10 | 0 | 0 | 0 | 10 | — |
| `data/campaigns/iquitos_v1` | 6 | 33995 | 6 | 0 | 0 | 0 | 0 | — |
| `data/campaigns/iquitos_v2` | 6 | 25349 | 6 | 0 | 0 | 0 | 0 | — |
| `data/campaigns/iquitos_v3` | 6 | 26613 | 6 | 0 | 0 | 0 | 0 | — |
| `data/campaigns/iquitos_v4` | 6 | 26639 | 6 | 0 | 0 | 0 | 0 | — |
| `data/dataset_audit` | 14 | 11617 | 14 | 0 | 0 | 0 | 14 | — |
| `data/maintenance/gates` | 9 | 149 | 9 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/github_readiness` | 1 | 56 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/historicos` | 5 | 3126 | 5 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01` | 11 | 0 | 11 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01` | 7 | 1606 | 7 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded` | 1 | 1271 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves` | 1 | 952 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit` | 3 | 14436 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B01` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B01_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B01_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B01_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B02` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B02_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B02_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B02_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B03` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B03_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B03_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B03_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B04` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B04_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B04_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B04_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B05` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B05_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B05_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B05_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B06` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B06_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B06_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B06_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B07` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B07_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B07_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B07_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B08` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B08_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B08_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B08_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B09` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B09_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B09_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B09_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B10` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B10_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B10_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B10_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B11` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B11_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B11_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B11_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B12` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B12_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B12_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B12_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B13` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B13_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B13_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B13_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B14` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B14_capex0.70` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B14_capex1.30` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/audit/microgrids_runs/B14_nodemand` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/dataset` | 57 | 1396856 | 57 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/raw/buildingcsv` | 18 | 1013489 | 18 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/raw/fx` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/raw/osinergmin` | 42 | 35410 | 42 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/raw/thesis` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/D01/discarded/iquitos_v4_uncontrolled_battery_curves/raw/weather` | 6 | 3 | 6 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I00` | 1 | 559 | 1 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I01` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I06` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I07` | 5 | 32 | 5 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I08` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I09` | 4 | 0 | 4 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I10` | 5 | 0 | 5 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I11` | 2 | 222 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I12` | 9 | 78 | 9 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I13` | 20 | 157 | 20 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I13/incident_s3` | 3 | 48 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I13/r008_before` | 2 | 183 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/integracion/c20261101i01/I15` | 5 | 131 | 5 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/layout` | 3 | 122 | 3 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/names` | 10 | 9183 | 10 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/remediacion/c20261101a/P00` | 2 | 701 | 2 | 0 | 0 | 0 | 0 | — |
| `data/maintenance/repository_layout` | 5 | 34257 | 5 | 0 | 0 | 0 | 0 | — |
| `deploy` | 5 | 231 | 5 | 4 | 0 | 0 | 1 | — |
| `deploy/aws` | 1 | 109 | 1 | 1 | 0 | 0 | 0 | — |
| `deploy/aws/iac` | 3 | 0 | 3 | 3 | 0 | 0 | 0 | — |
| `deploy/dashboard` | 3 | 136 | 3 | 3 | 0 | 0 | 0 | — |
| `deploy/edge` | 1 | 89 | 1 | 1 | 0 | 0 | 0 | — |
| `deploy/inference` | 6 | 751 | 6 | 4 | 0 | 2 | 0 | except_pass 1, sin_prueba 1 |
| `deploy/k8s` | 7 | 441 | 7 | 7 | 0 | 0 | 0 | — |
| `deploy/plant_adapter` | 4 | 332 | 4 | 4 | 0 | 0 | 0 | marcador 1, sin_prueba 1 |
| `docs` | 15 | 2834 | 15 | 0 | 0 | 11 | 4 | marcador 1 |
| `docs/architecture` | 23 | 2736 | 23 | 0 | 0 | 10 | 13 | — |
| `docs/architecture/_refs` | 1 | 0 | 1 | 0 | 0 | 0 | 1 | — |
| `docs/audits` | 20 | 1705 | 20 | 0 | 0 | 0 | 0 | — |
| `docs/audits/addendum_auditoria_20261101` | 7 | 3873 | 7 | 0 | 0 | 0 | 0 | — |
| `docs/audits/architecture_thesis_20261101` | 52 | 22706 | 52 | 0 | 0 | 0 | 0 | — |
| `docs/audits/architecture_thesis_20261101/layout` | 5 | 42752 | 5 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101` | 52 | 104485 | 52 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/configs/experiments` | 1 | 38 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m` | 1 | 40 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/algorithms` | 1 | 384 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/application/dataset` | 1 | 103 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/application/evaluation` | 4 | 506 | 4 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/application/thesis` | 1 | 45 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/application/training` | 2 | 95 | 2 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/data/adapters` | 2 | 219 | 2 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/domain` | 1 | 252 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/multicriteria` | 1 | 1900 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/presentation` | 1 | 68 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/inspection_cut/uc3m/reward` | 1 | 222 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/deep_20261101/recheck` | 8 | 10454 | 8 | 0 | 0 | 0 | 0 | — |
| `docs/audits/diagnostico_20261102` | 1 | 274 | 1 | 0 | 0 | 0 | 0 | — |
| `docs/audits/ejecucion_remediacion_20261101` | 25 | 93028 | 25 | 0 | 0 | 0 | 0 | — |
| `docs/audits/integracion_auditorias_20261101` | 15 | 18532 | 15 | 0 | 0 | 0 | 0 | — |
| `docs/audits/revision_semantica_20261102` | 5 | 1038 | 5 | 0 | 0 | 0 | 0 | — |
| `docs/audits/word` | 18 | 1243 | 18 | 0 | 0 | 0 | 0 | — |
| `docs/chapters` | 12 | 2378 | 12 | 0 | 0 | 12 | 0 | — |
| `docs/contributions/CityLearn` | 2 | 232 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/HARL` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/MAAC` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/MARL` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/MARLlib` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/MATD3implementation` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/MicroGrids` | 2 | 58 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/evcc` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/contributions/prosumpy` | 2 | 55 | 2 | 0 | 0 | 1 | 1 | — |
| `docs/decisions` | 7 | 1202 | 7 | 0 | 0 | 7 | 0 | — |
| `docs/design` | 2 | 721 | 2 | 0 | 0 | 2 | 0 | — |
| `docs/failures` | 1 | 17 | 1 | 0 | 0 | 1 | 0 | — |
| `docs/history` | 2 | 885 | 2 | 0 | 0 | 2 | 0 | — |
| `docs/plans` | 16 | 9750 | 16 | 0 | 0 | 16 | 0 | marcador 2 |
| `docs/research` | 2 | 83 | 2 | 0 | 0 | 2 | 0 | — |
| `docs/thesis` | 2 | 260 | 2 | 0 | 0 | 1 | 1 | duplicado 1 |
| `examples_madrl_v3` | 7 | 5193 | 7 | 7 | 0 | 0 | 0 | sin_consumidor 1, sin_prueba 1 |
| `external` | 10 | 100 | 2 | 0 | 0 | 0 | 0 | — |
| `external/off-policy` | 6 | 655 | 6 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/.github/ISSUE_TEMPLATE` | 3 | 68 | 3 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy` | 2 | 207 | 2 | 0 | 0 | 0 | 0 | marcador 1 |
| `external/off-policy/offpolicy/algorithms` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/base` | 4 | 109 | 4 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/maddpg` | 2 | 435 | 2 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/algorithms/maddpg/algorithm` | 3 | 248 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/matd3` | 2 | 6 | 2 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/matd3/algorithm` | 3 | 16 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/mqmix` | 2 | 251 | 2 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/algorithms/mqmix/algorithm` | 4 | 303 | 4 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/mvdn` | 2 | 7 | 2 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/algorithms/mvdn/algorithm` | 3 | 41 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/qmix` | 2 | 232 | 2 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/algorithms/qmix/algorithm` | 4 | 367 | 4 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/r_maddpg` | 2 | 580 | 2 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/r_maddpg/algorithm` | 3 | 310 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/r_matd3` | 2 | 8 | 2 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/r_matd3/algorithm` | 3 | 16 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/algorithms/utils` | 3 | 172 | 3 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/algorithms/vdn` | 2 | 8 | 2 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/algorithms/vdn/algorithm` | 3 | 45 | 3 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/envs` | 2 | 507 | 2 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/envs/mpe` | 7 | 1292 | 7 | 0 | 0 | 0 | 0 | ruff 1, vacio 1 |
| `external/off-policy/offpolicy/envs/mpe/scenarios` | 10 | 1322 | 10 | 0 | 0 | 0 | 0 | ruff 2 |
| `external/off-policy/offpolicy/envs/starcraft2` | 4 | 2164 | 4 | 0 | 0 | 0 | 0 | modulo_grande 1, ruff 1, vacio 1 |
| `external/off-policy/offpolicy/runner/mlp` | 3 | 892 | 3 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/runner/rnn` | 3 | 816 | 3 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/scripts` | 16 | 179 | 16 | 0 | 0 | 0 | 0 | vacio 1 |
| `external/off-policy/offpolicy/scripts/sweep_config` | 2 | 101 | 2 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/scripts/train` | 2 | 384 | 2 | 0 | 0 | 0 | 0 | — |
| `external/off-policy/offpolicy/utils` | 7 | 1383 | 7 | 0 | 0 | 0 | 0 | ruff 2, vacio 1 |
| `governance` | 5 | 624 | 5 | 5 | 0 | 0 | 0 | — |
| `outputs` | 1 | 20 | 1 | 0 | 0 | 0 | 0 | — |
| `scripts` | 10 | 1576 | 10 | 0 | 0 | 10 | 0 | modulo_grande 1, sin_prueba 1 |
| `scripts/maintenance` | 3 | 508 | 3 | 0 | 0 | 3 | 0 | — |
| `scripts/quality` | 5 | 250 | 5 | 0 | 0 | 5 | 0 | — |
| `scripts/skills` | 1 | 41 | 1 | 0 | 0 | 1 | 0 | — |
| `specs` | 1 | 160 | 1 | 0 | 0 | 1 | 0 | — |
| `specs/000-foundation` | 3 | 66 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/001-provenance` | 3 | 73 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/002-objectives` | 3 | 71 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/003-orchestration` | 3 | 72 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/004-manifests` | 3 | 67 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/005-evaluation` | 3 | 71 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/006-evidence` | 3 | 67 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/007-agents` | 3 | 43 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/008-artifacts` | 3 | 66 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/009-jury` | 3 | 68 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/010-panel` | 3 | 99 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/011-pipeline` | 3 | 82 | 3 | 0 | 0 | 3 | 0 | — |
| `specs/012-hygiene` | 3 | 73 | 3 | 0 | 0 | 3 | 0 | — |
| `tests` | 2 | 30 | 2 | 2 | 0 | 0 | 0 | vacio 1 |
| `tests/acceptance` | 4 | 248 | 4 | 4 | 0 | 0 | 0 | vacio 1 |
| `tests/citylearn_v3` | 3 | 72 | 3 | 3 | 0 | 0 | 0 | vacio 1 |
| `tests/contract` | 10 | 729 | 10 | 10 | 0 | 0 | 0 | except_pass 1 |
| `tests/contract/multiobjective` | 2 | 166 | 2 | 2 | 0 | 0 | 0 | — |
| `tests/contract/training` | 4 | 106 | 4 | 4 | 0 | 0 | 0 | — |
| `tests/fresh_training` | 62 | 8703 | 62 | 28 | 2 | 30 | 2 | vacio 1 |
| `tests/integration` | 4 | 353 | 4 | 4 | 0 | 0 | 0 | — |
| `tests/ops` | 9 | 1150 | 9 | 6 | 0 | 3 | 0 | — |
| `tests/remediation` | 17 | 2677 | 17 | 0 | 0 | 5 | 12 | — |
| `tests/skills` | 1 | 102 | 1 | 1 | 0 | 0 | 0 | — |
| `tests/uc3m` | 16 | 2904 | 16 | 13 | 2 | 1 | 0 | except_pass 1, vacio 1 |
| `tests/unit/adapters` | 1 | 57 | 1 | 1 | 0 | 0 | 0 | — |
| `tests/unit/application` | 7 | 669 | 7 | 7 | 0 | 0 | 0 | — |
| `tests/unit/application/training` | 8 | 256 | 8 | 8 | 0 | 0 | 0 | — |
| `tests/unit/domain` | 5 | 478 | 5 | 5 | 0 | 0 | 0 | — |
| `tests/unit/evaluation` | 1 | 449 | 1 | 0 | 0 | 1 | 0 | — |
| `tests/unit/governance` | 1 | 90 | 1 | 1 | 0 | 0 | 0 | — |
| `tools` | 2 | 64 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/colab` | 2 | 722 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/dataset` | 26 | 13149 | 26 | 0 | 0 | 25 | 1 | modulo_grande 5, sin_consumidor 2, sin_prueba 13 |
| `tools/dataset/dataset_docs` | 2 | 645 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/drive` | 7 | 974 | 7 | 0 | 0 | 7 | 0 | ruff 1, sin_prueba 7 |
| `tools/eval` | 21 | 8803 | 21 | 0 | 0 | 21 | 0 | modulo_grande 2, ruff 2, sin_prueba 14 |
| `tools/figures` | 6 | 1671 | 6 | 0 | 0 | 6 | 0 | except_pass 2, ruff 1, sin_prueba 5 |
| `tools/ops` | 14 | 4153 | 14 | 0 | 0 | 14 | 0 | modulo_grande 1, sin_prueba 3 |
| `tools/skills` | 3 | 417 | 3 | 0 | 0 | 3 | 0 | — |
| `tools/skills/architecture-patterns` | 2 | 185 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/architecture-patterns/references` | 2 | 735 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/docker-build-strategies` | 3 | 389 | 3 | 0 | 0 | 3 | 0 | duplicado 1 |
| `tools/skills/docker-build-strategies/agents` | 1 | 6 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/docker-build-strategies/assets` | 4 | 68 | 4 | 0 | 0 | 0 | 4 | — |
| `tools/skills/docker-build-strategies/checks` | 1 | 155 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/docker-build-strategies/references` | 2 | 360 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/docker-build-strategies/scripts` | 1 | 34 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/docker-compose-patterns` | 3 | 394 | 3 | 0 | 0 | 3 | 0 | duplicado 1 |
| `tools/skills/docker-compose-patterns/agents` | 1 | 6 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/docker-compose-patterns/assets` | 3 | 272 | 3 | 0 | 0 | 3 | 0 | — |
| `tools/skills/docker-compose-patterns/checks` | 1 | 90 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/docker-compose-patterns/references` | 2 | 275 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/docker-compose-patterns/scripts` | 1 | 23 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/fastapi-templates` | 2 | 177 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/fastapi-templates/references` | 1 | 430 | 1 | 0 | 0 | 1 | 0 | — |
| `tools/skills/frontend-design` | 2 | 248 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/harness-engineering` | 2 | 248 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/madrl-agent-coordination` | 2 | 37 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/madrl-experiment-evidence-audit` | 2 | 35 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/madrl-scientific-literature-audit` | 2 | 33 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/madrl-spec-conformance` | 2 | 36 | 2 | 0 | 0 | 2 | 0 | duplicado 1 |
| `tools/skills/notebooklm-mcp` | 8 | 437 | 8 | 0 | 0 | 7 | 1 | sin_prueba 1 |
| `tools/skills/notebooklm-mcp/scripts` | 11 | 2136 | 11 | 0 | 0 | 11 | 0 | except_pass 5, ruff 6, sin_prueba 8 |
| `tools/skills/task-coordination-strategies` | 2 | 184 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/task-coordination-strategies/references` | 2 | 195 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/webapp-testing` | 2 | 300 | 2 | 0 | 0 | 2 | 0 | — |
| `tools/skills/webapp-testing/examples` | 3 | 108 | 3 | 0 | 0 | 3 | 0 | ruff 1, sin_prueba 3 |
| `tools/skills/webapp-testing/scripts` | 1 | 106 | 1 | 0 | 0 | 1 | 0 | sin_prueba 1 |
| `tools/thesis` | 59 | 20076 | 59 | 0 | 0 | 59 | 0 | except_pass 3, modulo_grande 5, ruff 19, sin_prueba 53 |
| `tools/training` | 13 | 4024 | 13 | 0 | 0 | 13 | 0 | modulo_grande 1, ruff 3, sin_consumidor 1, sin_prueba 12 |
| `uc3m` | 1 | 40 | 1 | 1 | 0 | 0 | 0 | duplicado 1 |
| `uc3m/adapters` | 2 | 106 | 2 | 2 | 0 | 0 | 0 | — |
| `uc3m/adapters/algorithms` | 5 | 650 | 5 | 4 | 0 | 1 | 0 | — |
| `uc3m/adapters/citylearn` | 6 | 1135 | 6 | 3 | 2 | 1 | 0 | modulo_grande 1, vacio 1 |
| `uc3m/algorithms` | 2 | 404 | 2 | 2 | 0 | 0 | 0 | — |
| `uc3m/application` | 4 | 567 | 4 | 3 | 0 | 1 | 0 | — |
| `uc3m/application/artifacts` | 3 | 344 | 3 | 3 | 0 | 0 | 0 | — |
| `uc3m/application/dataset` | 4 | 789 | 4 | 2 | 0 | 2 | 0 | — |
| `uc3m/application/evaluation` | 13 | 1843 | 13 | 5 | 0 | 8 | 0 | sin_prueba 1 |
| `uc3m/application/thesis` | 2 | 90 | 2 | 2 | 0 | 0 | 0 | vacio 1 |
| `uc3m/application/training` | 24 | 4001 | 24 | 13 | 0 | 10 | 1 | duplicado 1, except_pass 1, modulo_grande 1, sin_prueba 2 |
| `uc3m/data` | 4 | 203 | 4 | 4 | 0 | 0 | 0 | — |
| `uc3m/data/adapters` | 4 | 528 | 4 | 3 | 0 | 1 | 0 | sin_prueba 2 |
| `uc3m/domain` | 7 | 1031 | 7 | 6 | 0 | 1 | 0 | — |
| `uc3m/env` | 4 | 769 | 4 | 2 | 2 | 0 | 0 | except_pass 1 |
| `uc3m/geography` | 2 | 414 | 2 | 1 | 0 | 1 | 0 | — |
| `uc3m/governance` | 3 | 205 | 3 | 3 | 0 | 0 | 0 | — |
| `uc3m/kpis` | 2 | 436 | 2 | 1 | 1 | 0 | 0 | — |
| `uc3m/multicriteria` | 10 | 4102 | 10 | 5 | 0 | 5 | 0 | except_pass 1, modulo_grande 1 |
| `uc3m/ports` | 4 | 73 | 4 | 4 | 0 | 0 | 0 | sin_prueba 1 |
| `uc3m/presentation` | 2 | 112 | 2 | 1 | 0 | 1 | 0 | — |
| `uc3m/reward` | 4 | 938 | 4 | 3 | 1 | 0 | 0 | — |
