# Manual de ejecucion desde cero - MADRL CityLearn v3 en Colab A100

**Proyecto:** `MADRLCitytleranflexresdr`  
**Notebook:** `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`  
**Modo objetivo:** Google Colab A100, 75 episodios, 12 corridas  
**Ultima verificacion local:** 2026-06-19 con `.venv39-citylearn-v3` / Python 3.9.25

Este manual explica como lanzar el entrenamiento oficial desde cero usando el
notebook `madrl_citylearn_v3_tutorial.ipynb`.

## 1. Reglas importantes

- Usar solo este proyecto: `D:\MADRLCitytleranflexresdr`.
- No usar `D:\madrl_lima` para este flujo.
- El entrenamiento real se ejecuta en Colab A100, no en la maquina local.
- El notebook esta preparado para 4 algoritmos x 3 escenarios:
  `happo`, `masac`, `matd3`, `maac` x `E1`, `E2`, `E3`.
- La corrida completa usa 75 episodios por job:
  `75 x 8760 = 657000` pasos por corrida.
- Tiempo estimado: alrededor de 30 horas para las 12 corridas, segun carga de
  Colab y estabilidad del runtime.

## 2. Requisitos previos

En la maquina local:

- Git instalado.
- VS Code instalado.
- Extension de VS Code `google.colab` instalada.
- Repositorio local en `D:\MADRLCitytleranflexresdr`.
- Rama actual sincronizada con GitHub.

En Google:

- Cuenta con acceso a Colab Pro/Pro+.
- Runtime A100 disponible.
- Google Drive disponible para guardar checkpoints y resultados.

## 3. Preparar el repo local

Desde PowerShell:

```powershell
cd D:\MADRLCitytleranflexresdr
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
git status -sb
```

Debe mostrar un contexto valido para `D:/MADRLCitytleranflexresdr`.

Si se parte de cero en una maquina nueva:

```powershell
cd D:\
git clone --recurse-submodules --branch codex/fix-madrl-traceability-docs https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd D:\MADRLCitytleranflexresdr
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
```

## 4. Abrir el notebook

Abrir en VS Code:

```text
CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb
```

No ejecutar el notebook con un kernel local para el entrenamiento completo. El
kernel debe ser Google Colab A100.

## 5. Conectar VS Code a Colab A100

En el notebook:

1. Clic en `Select Kernel`.
2. Elegir `Google Colab`.
3. Iniciar sesion con la cuenta que tiene Colab Pro/Pro+.
4. Elegir `New runtime (A100)`.
5. Confirmar que el runtime tiene GPU A100.

Si no aparece Google Colab:

```text
Ctrl+Shift+P -> Colab: Sign In
```

Despues repetir la seleccion de kernel.

## 6. Orden de ejecucion desde cero

Ejecutar las celdas en este orden.

### Paso 0 - Verificar conexion

Ejecutar:

- `0.verify Verificar conexion al runtime A100`

Resultado esperado:

```text
GPU: A100
RAM: aprox. 83 GB
Entorno: Google Colab
```

Si no aparece A100, cambiar el runtime antes de continuar.

### Seccion 0 - Diagramas

Las celdas de diagramas `0.0` a `0.9` son documentales. No son necesarias para
entrenar. Se pueden ejecutar si se quiere visualizar la arquitectura, pero para
lanzar el entrenamiento se puede pasar directo a la seccion 1.

### Seccion 1 - Configuracion inicial

Ejecutar en orden:

1. `1.1 Verificar GPU`
2. `1.2 Clonar repositorio con submodulos desde rama validada`
3. `1.2b Validar espejo del proyecto Colab antes de entrenar`
4. `1.3 Instalar dependencias del proyecto de forma reproducible`
5. `1.4 Configurar sys.path, CUDA y smoke imports`
6. `1.5 Montar Google Drive para checkpoints y reanudacion`

Puntos criticos:

- `1.1` debe detectar A100.
- `1.2` clona la rama `codex/fix-madrl-traceability-docs` en
  `/content/MADRLCitytleranflexresdr`.
- `1.2b` valida submodulos, dataset y que `CityLearn` coincida con el commit
  fijado por el repo padre.
- `1.3` instala dependencias compatibles para Colab.
- Si `1.3` indica que ya habia modulos binarios cargados, reiniciar runtime y
  repetir desde `1.1`.
- `1.5` es obligatorio para una corrida larga, porque guarda checkpoints en
  Drive.

### Seccion 2 - Crear OUTPUT_ROOT

Ejecutar:

- `2.1 Rutas, timestamp y directorio de salida recuperable`

Resultado esperado:

```text
OUTPUT_ROOT : /content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/colab_madrl_a100_<timestamp>
SCHEMA_PATH : /content/MADRLCitytleranflexresdr/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json OK
```

Guardar el valor exacto de `OUTPUT_ROOT`. Es necesario para reanudar si Colab se
desconecta.

### Secciones 3, 4 y 5 - Validaciones recomendadas

Ejecutar:

1. `3.1 Verificar estructura del dataset`
2. `4.1 Crear entorno smoke-test (4 pasos) y describir agentes`
3. `5.1 Visualizar pesos de recompensa por escenario`

Estas celdas no entrenan, pero validan que el dataset, el entorno Dec-POMDP y
las recompensas esten correctos.

Resultados esperados:

- 17 edificios/agentes.
- Dataset con 222 CSV.
- Escenarios `E1`, `E2`, `E3` disponibles.
- Recompensas multiobjetivo cargadas por escenario.

### Seccion 6 - Confirmar hiperparametros

Ejecutar:

- `6.1 Configuracion central de entrenamiento A100`

Valores actuales del notebook:

```python
QUICK_TEST = False
EPISODES = 75
EPISODE_STEPS = 8760
SEED = 0
SCENARIOS = ['E1', 'E2', 'E3']
ALGORITHMS = ['happo', 'masac', 'matd3', 'maac']
GPU_PROFILE = 'aws'
CUDA_MEMORY_FRACTION = 0.92
```

Para una prueba corta de infraestructura, cambiar temporalmente:

```python
QUICK_TEST = True
```

Para la corrida oficial, dejar:

```python
QUICK_TEST = False
```

### Seccion 7 - Lanzamiento oficial

Ejecutar:

1. `7.0 Helpers de ejecucion y monitor`
2. `7.1 Preflight A100 + dry-run oficial`
3. `7.2 Lanzar entrenamiento completo recuperable`

La celda `7.1` es obligatoria antes de entrenar. Debe confirmar:

```text
Dry-run validado: 12 jobs planificados, A100 config lista, outputs aislados en OUTPUT_ROOT.
```

La celda `7.2` inicia el entrenamiento real. Actualmente esta asi:

```python
LAUNCH_FULL_TRAINING = True
```

Eso significa que al ejecutar `7.2` se lanza la corrida completa de 75 episodios.

Si solo se quiere revisar comandos sin entrenar, cambiar temporalmente:

```python
LAUNCH_FULL_TRAINING = False
```

## 7. Monitoreo durante entrenamiento

Mientras entrena:

- Usar la celda `7.3 Monitor visible en notebook`.
- Usar la celda `7.4 Resumen global de jobs y artefactos`.
- Revisar archivos dentro de `OUTPUT_ROOT`.

Estructura esperada:

```text
OUTPUT_ROOT/
  happo/E1_seed_0/data/results.json
  happo/E2_seed_0/data/results.json
  happo/E3_seed_0/data/results.json
  masac/E1_seed_0/data/results.json
  masac/E2_seed_0/data/results.json
  masac/E3_seed_0/data/results.json
  matd3/E1_seed_0/data/results.json
  matd3/E2_seed_0/data/results.json
  matd3/E3_seed_0/data/results.json
  maac/E1_seed_0/data/results.json
  maac/E2_seed_0/data/results.json
  maac/E3_seed_0/data/results.json
  official_full_status.json
  live_progress.json
  run_context_manifest.json
```

El launcher usa `--skip-completed`, por lo que no repite jobs que ya terminaron
correctamente.

## 8. Reanudar si Colab se desconecta

1. Reconectar VS Code a un runtime Colab A100.
2. Ejecutar:
   - `0.verify`
   - `1.1`
   - `1.2`
   - `1.2b`
   - `1.3`
   - `1.4`
   - `1.5`
3. En `2.1`, poner el `OUTPUT_ROOT` anterior:

```python
RESUME_OUTPUT_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/colab_madrl_a100_<timestamp>'
```

4. Ejecutar:
   - `2.1`
   - `6.1`
   - `7.0`
   - `7.2`

No es obligatorio repetir `7.1` al reanudar una corrida ya iniciada, siempre que
no se hayan cambiado parametros. `7.2` usara `--skip-completed` y continuara con
los jobs faltantes.

## 9. Analisis despues del entrenamiento

Cuando las 12 corridas terminen, ejecutar:

1. `8.1 Cargar todos los results.json`
2. `8.2 Curvas de convergencia`
3. `9.1 Suite de pruebas estadisticas`
4. `10 Resumen final de la sesion Colab`

Resultado esperado:

- DataFrame con los KPIs de los 12 jobs.
- Curvas de convergencia por algoritmo y escenario.
- Ranking estadistico final.
- Archivo `colab_session_summary.json` dentro de `OUTPUT_ROOT`.

## 10. Verificacion local antes de usar Colab

Desde PowerShell local:

```powershell
cd D:\MADRLCitytleranflexresdr
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe tools\test_notebook_cells.py
```

Para validar readiness por escenario:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E2
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E3
```

Dry-run local sin A100, solo para revisar planificacion:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\colab_a100_official_launcher.py --dry-run --scenario ALL --seed 0 --episode-time-steps 8760 --episodes 75 --output-root outputs\notebook_verify_dryrun --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --skip-gpu-preflight --no-require-a100 --no-smoke-imports --skip-completed
```

## 11. Errores comunes

### No aparece A100

Cambiar el runtime:

```text
Runtime -> Change runtime type -> A100 GPU
```

Despues repetir `0.verify` y `1.1`.

### Google Drive no monta

Revisar cuenta de Google y ejecutar de nuevo `1.5`. Para corrida larga, Drive es
obligatorio.

### Error ABI numpy/pandas/scipy/sklearn

Reiniciar runtime de Colab y repetir:

```text
1.1 -> 1.2 -> 1.2b -> 1.3 -> 1.4
```

No importar `numpy`, `pandas`, `scipy` o `sklearn` antes de ejecutar `1.3`.

### Se desconecta Colab

No borrar `OUTPUT_ROOT`. Repetir el flujo de reanudacion de la seccion 8.

### Un job falla por OOM

El launcher tiene `--oom-retry`. Revisar `official_full_status.json` y logs en
`OUTPUT_ROOT`. Si el runtime sigue disponible, reejecutar `7.2`.

## 12. Criterio de listo

Antes de considerar la corrida valida:

- `7.1` debe planificar 12 jobs.
- Las salidas deben quedar bajo un unico `OUTPUT_ROOT`.
- Debe existir `run_context_manifest.json`.
- Al final deben existir 12 `results.json`.
- `8.1`, `8.2`, `9.1` y `10` deben ejecutarse sin errores.

Si esos puntos se cumplen, la ejecucion queda lista para analisis y reporte.
