# Dataset Iquitos 2023-2025: destilacion para CityLearn v3

Este documento registra el flujo validado para convertir los insumos reales de
`CityLearn/data/buildingcsv/` al dataset horario
`CityLearn/data/datasets/citylearn_iquitos_2023_2025/`.

## Alcance

- `buildingcsv` es insumo de destilacion, no un dataset CityLearn cargable
  directamente.
- Los archivos `B_02.csv` a `B_17.csv` contienen mediciones mensuales por
  edificio, medidor y componente.
- `building.csv` contiene nombres, areas techadas, oficinas y equipos
  controlados por edificio.
- `Building_1.csv` se conserva porque no existe archivo B_01 equivalente en
  `buildingcsv`.

## Transformacion de datos

La destilacion convierte valores mensuales medidos a valores horarios mediante
calculos deterministas:

- expansion por calendario real de 2023, 2024 y 2025;
- asignacion horaria por componente electrico y tipo de medidor;
- separacion de cargas no controladas y controladas;
- balance mensual por edificio y componente;
- registro de meses pronosticados cuando faltan mediciones.

No se debe usar generacion sintetica arbitraria para rellenar cargas. Los
faltantes se pronostican con una regla matematica documentada y quedan en el
reporte de destilacion.

## Archivos principales

| Archivo | Funcion |
|---|---|
| `tools/dataset/buildingcsv_inputs.py` | Parser comun de `buildingcsv`, normalizacion de nombres, areas y columnas reales. |
| `tools/dataset/distill_building_loads.py` | Destila mediciones mensuales a cargas horarias CityLearn. |
| `tools/dataset/dataset_docs/distillation_report.csv` | Reporte de balance y meses pronosticados. |
| `tools/dataset/generate_iquitos_dataset.py` | Sincroniza schema, metadata, nombres, oficinas, equipos y areas. |
| `tools/dataset/fix_solar_pvlib.py` | Recalcula/sincroniza generacion solar de B_02 a B_17. |
| `tools/dataset/verify_solar.py` | Verifica areas techadas, PV nominal y consistencia solar. |
| `CityLearn/data/datasets/citylearn_iquitos_2023_2025/building_metadata.json` | Metadata consolidada por edificio. |

## Comandos de regeneracion

Ejecutar desde la raiz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\distill_building_loads.py
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\generate_iquitos_dataset.py
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\fix_solar_pvlib.py
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\verify_solar.py
```

## Validacion sin entrenamiento

Estas pruebas no lanzan entrenamiento completo:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py `
  --strict `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\run_citylearn_v3_env_smoke.py `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1 `
  --episode-time-steps 4 `
  --steps 3
```

Estado validado:

- 17 agentes activos.
- EV actions/observations habilitados.
- `state_dim=879`.
- `CityLearnV3MADRLRewardFunction` con agregacion `team_mean`.
- KPIs CityLearn v2 disponibles desde la capa v3.
- Los 4 entrypoints MADRL importan en Python 3.9.
- La cadena smoke `E1 x HAPPO, MASAC, MATD3, MAAC` termina con exit code 0.

## Entrenamiento

La cadena completa de entrenamiento GPU debe lanzarse solo con confirmacion
explicita. El launcher oficial usa `SchemaPath` para evitar cargar datasets
anteriores por accidente:

```powershell
.\CityLearn\scripts\launch_citylearn_v3_official_training.ps1 `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 5 `
  -SchemaPath CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  -OutputRoot <OutputRoot> `
  -TorchThreads 8 `
  -GpuProfile local4060_fast `
  -LiveProgressInterval 250 `
  -Cuda
```
