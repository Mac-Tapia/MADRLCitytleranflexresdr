# Informe de validacion integral del dataset CityLearn Iquitos

Fecha de validacion: 2026-06-12

Dataset activo:

`CityLearn/data/datasets/citylearn_iquitos_2023_2025`

## Estado final

El dataset quedo sincronizado, limpio y cargable por CityLearn v3 antes de normalizacion MADRL.

| Control | Resultado |
|---|---:|
| Orquestacion integral | ready |
| Compuerta de entrenamiento | ready |
| Dataset crudo cargado antes de normalizar | true |
| Normalizacion permitida para entrenamiento | true |
| Archivos CSV activos auditados | 222 |
| Celdas NaN/vacias | 0 |
| Celdas infinitas | 0 |
| Archivos huerfanos activos del schema | 0 |
| Schemas antiguos archivados en limpieza final | 0 |
| Edificios CityLearn | 17 |
| Tomas EV controlables | 185 |
| Equipos fisicos modo 3 doble toma | 96 |
| EV en pool de simulacion | 1,850 |
| Maquinas controladas | 17 |
| Referencias weather/pricing/carbon en schema | 17/17/17 |

## Orden de ejecucion validado

La construccion queda centralizada en:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\orchestrate_citylearn_dataset.py --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025
```

Para reconstruir sobre el dataset base existente:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\orchestrate_citylearn_dataset.py --skip-base-generation --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025
```

Etapas ejecutadas y validadas:

1. Destilar cargas reales y costos horarios desde `CityLearn/data/buildingcsv`.
2. Aplicar PV con `pvlib`/TMY por edificio.
3. Dimensionar EV por edificio y cargar `charger_*.csv` en `schema.json`.
4. Cargar una maquina controlada por edificio en `Washing_Machine_X.csv`.
5. Aplicar margen numerico de cooling autosize en `schema.json`.
6. Dimensionar BESS con PV, EV, red publica, carga no controlada y cargas controladas.
7. Auditar DER: PV, EV, BESS, red, cargas y picos.
8. Auditar procedencia de entrenamiento: datos reales, simulados, costos y emisiones.
9. Eliminar archivos generados no referenciados por `schema.json`.
10. Auditar integridad CSV: filas, columnas, NaN, infinitos y referencias.
11. Ejecutar evaluacion exhaustiva del dataset calibrado.
12. Ejecutar analisis profundo de carga CityLearn v3.
13. Ejecutar compuerta final antes de normalizacion MADRL.

## Datos reales y capas sincronizadas

| Capa | Estado |
|---|---|
| `building.csv` | Cargado como inventario de 17 edificios |
| `B_02.csv`..`B_17.csv` | Cargados como mediciones mensuales requeridas |
| `B_01.csv` | No existe; B01 queda como perfil de inventario documentado |
| `Building_1.csv`..`Building_17.csv` | 26,304 filas, 12 columnas, sin NaN |
| `weather.csv` | 26,304 filas, 16 columnas, sin NaN |
| `pricing.csv` | 26,304 filas, 4 columnas, sin NaN |
| `carbon_intensity.csv` | 26,304 filas, 1 columna, sin NaN |
| `charger_*.csv` | 185 archivos/tomas referenciados, sin NaN |
| `Washing_Machine_*.csv` | 17 archivos referenciados, sin NaN |

Los centinelas negativos que permanecen son semantica oficial de CityLearn, no datos faltantes: `-1` para tiempo ausente y `-0.1` para SOC ausente en EV, y `-1` para ventana inactiva de maquina controlada.

## Resultados energeticos agregados

| Metrica | Valor |
|---|---:|
| Carga EV controlada total | 3,267.587 MWh |
| Carga EV fuera de ventana operativa | 0.000000 MWh |
| Maquinas controladas total | 876.592 MWh |
| PV total | 148,802.232 MWh |
| PV directo a EV | 1,729.262 MWh |
| PV a BESS | 15,123.505 MWh |
| BESS a EV | 1,462.346 MWh |
| BESS total | 26,266 kWh |
| Potencia BESS total | 6,648 kW |
| Red publica reduccion global | 25.791 % |

## Validaciones clave

| Auditoria | Resultado |
|---|---:|
| `training_dataset_validation.json` | all_valid = true |
| Max delta base B02-B17 | 0.000000145 % |
| Meses pronosticados declarados | 8 |
| Cierre maximo PV | 0.001000 MWh |
| `csv_integrity_manifest.json` | status = ok |
| NaN en CSV activos | 0 |
| Infinitos en CSV activos | 0 |
| `orphaned_dataset_files_manifest.json` | 0 huerfanos activos |
| `check_training_dataset_ready.py` | status = ready |

## Carga CityLearn v3

La compuerta final cargo el dataset crudo en CityLearn v3 antes de normalizacion:

| Escenario | Estado | Agentes | Observaciones min/max |
|---|---:|---:|---:|
| E1 | ok | 17 | 54 / 327 raw; state_dim 1856 |
| E2 | ok | 17 | 54 / 327 raw; state_dim 1856 |
| E3 | ok | 17 | 54 / 327 raw; state_dim 1856 |

## Archivos de evidencia

- `outputs/dataset_audit/dataset_orchestration_manifest.json`
- `outputs/dataset_audit/training_dataset_ready_manifest.json`
- `outputs/dataset_audit/csv_integrity_manifest.json`
- `outputs/dataset_audit/orphaned_dataset_files_manifest.json`
- `outputs/dataset_audit/training_dataset_validation.csv`
- `outputs/dataset_audit/training_dataset_validation.json`
- `outputs/dataset_audit/der_sizing_audit.csv`
- `outputs/dataset_audit/der_sizing_audit.json`
- `docs/INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md`
- `docs/INFORME_AUDITORIA_DIMENSIONAMIENTO_DER_IQUITOS.md`
- `docs/INFORME_EVALUACION_FINAL_DATASET_IQUITOS_CITYLEARN_V3.md`

## Limitaciones declaradas

- B01 no tiene archivo mensual directo `B_01.csv`; su perfil base se mantiene como perfil de inventario documentado.
- B06 tiene 8 meses pronosticados por solapamiento de calendario desde meses medidos; quedan marcados como pronosticados.
- EV, maquinas controladas y PV son capas reproducibles de simulacion para entrenamiento, no submediciones historicas independientes.

## Conclusion

El dataset activo queda limpio, sin NaN, sin infinitos, sin archivos antiguos conectados al schema, con costos, emisiones, clima, cargas controladas, EV, PV y BESS cargados para CityLearn v3. La normalizacion MADRL queda permitida solo despues de esta compuerta.
