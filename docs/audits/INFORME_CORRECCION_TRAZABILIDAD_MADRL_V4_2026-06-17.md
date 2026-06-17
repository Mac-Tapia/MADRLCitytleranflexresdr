# Informe de correccion de trazabilidad MADRL v4

Fecha: 2026-06-17  
Corrida auditada: `outputs/citylearn_v3_madrl_full_20260615_074011_v4`

## Resultado

La corrida v4 quedo completa y limpia:

- `official_full_status.json`: `completed`
- Jobs completados: 12/12 (`4 MADRL x 3 escenarios`)
- Escenarios: E1 flexibilidad, E2 CO2, E3 costos
- Episodios por job: 5
- Artefactos requeridos faltantes: 0
- Duplicados raiz pendientes: 0
- Candidatos de poda pendientes: 0

## Causa tecnica

El generador de artefactos escribia simultaneamente archivos canonicos en
`data/` y copias espejo en la raiz de cada corrida. Ademas, exportaba copias
derivadas en `statistical_comparison/` y conservaba `live_progress.json`
despues de finalizar. Esto permitia que monitores o validadores leyeran estado
obsoleto aunque la corrida oficial ya estuviera completada.

## Correccion de codigo

Se corrigio `CityLearn/scripts/citylearn_v3_training_common.py` para que:

- `data/` sea la unica fuente canonica por defecto.
- Los espejos raiz solo se generen con `--legacy-root-artifacts`.
- `statistical_comparison/` solo se genere con
  `--statistical-comparison-artifacts`.
- `live_progress.json` se elimine al completar la escritura de artefactos.
- `results.json` y `training_summary.json` declaren explicitamente la politica
  de escritura.

Se corrigio el monitor oficial para:

- Preferir `data/results.json` y demas rutas canonicas.
- Ignorar progreso vivo cuando `official_full_status.json` ya esta en
  `completed`.
- Salir automaticamente al completar, salvo `-KeepOpenOnComplete`.

## Correccion de salida existente

Se conservaron todos los resultados finales, figuras, tablas y checkpoints. Se
eliminaron solo artefactos duplicados o transitorios:

- Copias espejo raiz (`results.json`, `timeseries.csv`, etc.) cuando existia el
  equivalente canonico en `data/`.
- `live_progress.json` de runs completados.
- `statistical_comparison/`, porque contenia copias derivadas de resultados y
  series temporales.
- Logs de TensorBoard dentro de checkpoints que no eran estado de modelo.

La limpieza libero 246.413 MB y no removio ningun checkpoint necesario.

## Validacion

Comandos ejecutados:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -m pytest CityLearn\tests\test_citylearn_v3_training_artifacts.py -q
.\.venv39-citylearn-v3\Scripts\python.exe tools\verify_training_optimization.py
.\.venv39-citylearn-v3\Scripts\python.exe -m py_compile CityLearn\scripts\citylearn_v3_training_common.py CityLearn\tests\test_citylearn_v3_training_artifacts.py tools\repair_citylearn_v3_traceability.py tools\verify_artifact_layout.py tools\verify_training_optimization.py
powershell -ExecutionPolicy Bypass -File tools\prune_citylearn_v3_training_artifacts.ps1 -OutputRoot outputs\citylearn_v3_madrl_full_20260615_074011_v4
```

Resultado:

- Tests de artefactos: `6 passed`
- Verificador de optimizacion: `OK`
- Compilacion Python: `OK`
- Parseo PowerShell: `OK`
- Dry-run de poda final: `No prune candidates found`

## Contrato vigente

Para una corrida completada, cada job debe conservar:

```text
data/results.json
data/training_summary.json
data/artifact_audit.json
data/checkpoint_manifest.json
data/timeseries.csv
data/trace.csv
checkpoints/
figures/figures_manifest.json
figures/tables/
```

No se deben usar copias raiz como fuente de resultados finales. `live_progress.json`
solo representa estado en vivo durante entrenamiento activo.
