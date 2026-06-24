# Evaluacion final dataset Iquitos - CityLearn v3

Fecha UTC: `2026-06-15T04:44:21.264130+00:00`

## Resultado

- Estado global: `OK`.
- Edificios cargados: `17`.
- Edificios con tomas EV: `17`.
- Tomas/loadpoints Mode 3 CityLearn: `185`.
- Equipos fisicos Mode 3 doble toma: `96`.
- EV definidos en pool: `1850`.
- Potencia EV nominal simultanea: `749.4` kW.
- Tomas camioneta V2G bidireccional: `31` de `31`.
- Tomas no camioneta con V2G habilitado: `0`.
- Unidades fisicas con simultaneidad observada en ambas tomas: `89` de `89`.

## Carga CityLearn v3

| Escenario | Estado | Agentes | State dim | EV acciones | EV observaciones |
|---|---:|---:|---:|---:|---:|
| E1 | OK | 17 | 1856 | True | True |
| E2 | OK | 17 | 1856 | True | True |
| E3 | OK | 17 | 1856 | True | True |

## Criterio EV

El dataset trata `charger_X_Y.csv` como toma/loadpoint controlable Mode 3. Cada equipo fisico agrupa dos tomas mediante `physical_charger_id` y ambas pueden cargar simultaneamente. Los EV no son fijos 1:1 con tomas: cada toma usa un pool de EVs y cada sesion queda gobernada por `electric_vehicle_estimated_soc_arrival` y `electric_vehicle_required_soc_departure`. Las camionetas institucionales/logisticas son las unicas tomas EV con V2G bidireccional (`max_discharging_power > 0`); moto lineal y mototaxi quedan solo carga.

## Evidencia

- Manifest JSON: `D:\MADRLCitytleranflexresdr\outputs\dataset_audit\iquitos_citylearn_v3_dataset_evaluation.json`
- Compuertas previas: `outputs/dataset_audit/csv_integrity_manifest.json` y `outputs/dataset_audit/training_dataset_ready_manifest.json`.
