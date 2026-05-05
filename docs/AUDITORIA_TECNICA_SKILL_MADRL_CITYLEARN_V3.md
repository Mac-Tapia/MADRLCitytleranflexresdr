# Auditoria tecnica con skill MADRL CityLearn

Fecha: 2026-05-05

## Objetivo

Ejecutar el skill `madrl-citylearn-literature-review` como guia de auditoria tecnica interna para identificar archivos que pueden mejorar, modernizar y sostener cientificamente el proyecto CityLearn v3 propuesto, sin detener el entrenamiento activo.

La auditoria mantiene las reglas terminologicas del proyecto:

- CityLearn v2 es el entorno base existente.
- CityLearn v3 propuesto es la extension experimental de tesis.
- El enfoque de algoritmos es MADRL.
- MARLlib se conserva solo como nombre propio de framework de referencia.

## Resultado principal

El cuello de botella dominante no esta en la capacidad CUDA sino en la ejecucion secuencial del entorno CityLearn v2 desde Python, el registro de trazas por edificio y la serializacion de progreso/artefactos. La GPU se usa en fases de actualizacion de redes, pero la simulacion del entorno, el armado de observaciones y el registro de metricas siguen siendo CPU-bound.

## Mejora aplicada

Archivo modificado:

- `CityLearn/scripts/citylearn_v3_training_common.py`

Cambio:

- Se agregaron acumuladores incrementales para `episode_return_cumulative`, `episode_reward_mean_cumulative`, `total_return_cumulative` y `total_reward_mean_cumulative`.
- Antes, cada escritura de `live_progress.json` recorria `timeseries_records` acumulado para recalcular retornos.
- Ahora, el progreso vivo usa acumuladores actualizados en cada paso.

Alcance:

- No cambia funcion reward.
- No cambia pesos por eje.
- No cambia acciones.
- No cambia KPIs.
- No cambia Dec-POMDP ni CTDE.
- Afecta solo los jobs que carguen el codigo despues del cambio.

## Archivos prioritarios para mejorar

| Prioridad | Archivo | Hallazgo | Mejora recomendada |
|---|---|---|---|
| Alta | `CityLearn/scripts/citylearn_v3_training_common.py` | Adaptador comun concentra entorno, trazas, progreso vivo, artefactos y wrappers. Es el punto de mayor impacto. | Seguir separando registro de entrenamiento, exportacion de artefactos y wrappers MADRL en modulos mas pequenos. |
| Alta | `CityLearn/scripts/train_citylearn_v3_maac.py` | Convierte observaciones NumPy a tensores en cada paso y mueve listas a GPU paso a paso. | Preasignar buffers/tensores cuando sea posible y reducir conversiones CPU-GPU dentro del loop. |
| Alta | `CityLearn/scripts/train_citylearn_v3_masac.py` | Backend MASAC es sensible a memoria GPU y genera alto costo con `qmix_msac.py`. | Mantener perfil estable 8 GB; documentar alternativa CPU o modo CUDA reducido; evaluar parche externo solo en rama controlada. |
| Alta | `external/MARL/src/ac_discrete/qmix_msac.py` | El error OOM ocurrio en `inputs.cuda()` al construir batches. Es backend externo. | No modificar directamente en master sin rama; proponer patch aislado con `to(device, non_blocking=True)` y limpieza de tensores. |
| Media | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` | Ejecucion secuencial preserva reproducibilidad, pero no expone modo resume ni selector desde job especifico. | Agregar parametros `-StartAtJob`, `-OnlyAlgorithm`, `-OnlyScenario` y `-SkipCompleted` para relanzar sin limpiar todo. |
| Media | `CityLearn/scripts/monitor_citylearn_v3_official_training.ps1` | Monitor lee archivos completos `trace.csv`/`timeseries.csv` cuando existen. | Para corridas largas, leer solo tail textual o ultimas lineas CSV sin `Import-Csv` completo. |
| Media | `CityLearn/configs/citylearn_v3_madrl_training.yaml` | Config canonica ya refleja perfiles, pero el launcher aun tiene parametros duplicados. | Hacer que el launcher lea JSON/YAML para evitar divergencia entre documento y ejecucion. |
| Media | `CityLearn/configs/citylearn_v3_madrl_training.json` | Duplica YAML. | Generar JSON desde YAML o validar igualdad automaticamente antes de entrenar. |
| Media | `CityLearn/citylearn/v3/marllib_env.py` | MARLlib existe como adaptador de referencia, no como ruta oficial del launcher. | Crear smoke test documentado que verifique registro, espacios y policy mapping sin entrenar. |
| Media | `CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py` | Comparador depende de artefactos completos. | Agregar modo incremental que detecte corridas terminadas y cree ranking parcial por eje. |
| Media | `CityLearn/scripts/benchmark_citylearn_v2_agents.py` | Necesario para demostrar mejora contra v2. | Alinear salida con el mismo esquema de `objective_kpis.csv` y `axis_baseline_comparison.csv`. |
| Media | `tools/skills/madrl-citylearn-literature-review/` | Skill integrado como sustento cientifico. | Ejecutar busqueda bibliografica real y llenar Excel con DOI/PDF/dataset/GitHub verificados. |
| Baja | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` | Tutorial esta actualizado, pero puede quedar grande para VS Code. | Mantener version generadora `.py` como fuente canonica y limpiar salidas pesadas del notebook. |
| Baja | `docs/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` | Arquitectura documentada. | Agregar seccion de cuello de botella CPU-bound y perfil MASAC estable. |

## Modernizacion recomendada

1. Crear configuracion unica de entrenamiento:
   - Fuente canonica: `citylearn_v3_madrl_training.yaml`.
   - JSON generado automaticamente.
   - Launcher PowerShell leyendo la config para no duplicar hiperparametros.

2. Crear modo de relanzamiento selectivo:
   - `-OnlyScenario E2`
   - `-OnlyAlgorithm MASAC`
   - `-StartAtJob masac:E1`
   - `-SkipCompleted`

3. Reducir I/O del monitor:
   - Evitar `Import-Csv` sobre archivos grandes.
   - Leer ultimas lineas con `Get-Content -Tail`.
   - Mostrar `live_progress.json` como fuente principal durante entrenamiento.

4. Separar responsabilidades del adaptador comun:
   - `training_common_artifacts.py`
   - `training_common_wrappers.py`
   - `training_common_progress.py`
   - `training_common_plots.py`

5. Agregar perfil de diagnostico de rendimiento:
   - pasos por segundo por job;
   - tiempo medio de `env.step`;
   - tiempo medio de update PyTorch;
   - memoria GPU antes/despues de update;
   - filas de trace y timeseries generadas.

## Acciones no recomendadas durante entrenamiento activo

- No modificar pesos reward de E1/E2/E3.
- No cambiar los KPIs ya validados.
- No limpiar `outputs/citylearn_v3_madrl_official_full_cuda_v2`.
- No matar procesos Python del entrenamiento.
- No editar backends externos directamente sin rama de prueba.

## Estado del entrenamiento durante la auditoria

El entrenamiento oficial siguio activo. La auditoria no detuvo launcher, monitor ni procesos Python de CityLearn v3.

