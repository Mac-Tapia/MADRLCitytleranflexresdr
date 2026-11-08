# Módulo 8: campaña de entrenamiento en Colab

**Para:** el propietario del proyecto, que ejecuta la campaña.
**Fecha:** 2026-11-08. **Revisión leída:** `df4f5ccc`, rama `fix/madrl-traceability-docs`, más el árbol de trabajo con las correcciones de esta tanda, todavía sin commit.
**Origen:** [plan completo, módulo 8](implementacion_completa.md).
**Estado:** plan. Este documento no autoriza ninguna etapa y nada de lo que describe se ha ejecutado en Colab.

Los números de línea corresponden a ese árbol de trabajo y pueden moverse con el commit. Las rutas usan `<alias>`, que es `storage_alias` de `configs/experiments/iquitos.yaml`; el cuaderno lo lee del mismo sitio (celda C3).

**Dataset y acciones de esta campaña.** El dataset definitivo es `iquitos_v6_trial13`, 13/13 puertas (decisión 4, abajo). Al leer, su carpeta no tiene `dataset_acceptance.json` y `iquitos.yaml` todavía nombra el dataset anterior. Los 4 algoritmos actúan sobre la rejilla común de D-M3-10: 5 niveles por equipo, 44 equipos y 220 acciones.

## Decisiones del propietario del 2026-11-08

Están decididas. Ninguna autoriza una etapa.

1. **`confirm` también se evalúa en `validation_2024`:** son 144 evaluaciones más, porque `pipeline select` las necesita. El orden en `confirm` es C9 en `validation_2024`, C10 con análisis y selección sobre esa partición, y después C9 y C10 en `test_2025`.
2. **Un ganador inferencial tiene que ganar en los tres ejes** (`selection_inference` en `uc3m/application/pipeline.py`). Las decisiones por eje quedan en el informe. No tener ganador es un resultado válido.
3. **La energía horaria de ASHRAE G14 es solo informativa,** no una condición para entrenar. CityLearn v2 evalúa su modelo térmico con el RMSE y el MAPE de la temperatura (`CityLearn/citylearn/end_use_load_profiles/neighborhood.py:362-369`). El criterio térmico es el error de temperatura, como en v2.
4. **`iquitos_v6_trial13` se construye una vez,** con D-V6-57 y D-V6-58 ([SPEC-016](../../specs/016-iquitos-v6/spec.md)), y no se reconstruye más 13/13 puertas. D-V6-20 queda cerrada por D-V6-58.

## 1. Lo primero que hay que saber

**Los dos bloqueos de código del piloto están corregidos, pero sin commit, y el piloto no se ha ejecutado.** El tercer problema se redujo y no desaparece: el piloto sigue sin alcanzar el pico de memoria de MASAC. Falta además lo que pide la sección 2, incluida la decisión escrita del propietario.

| Id | Problema | Estado | Qué se eligió | Evidencia |
|---|---|---|---|---|
| B1 | El tratamiento `pilot/masac/e1/seed_901` no llevaba `--rnn-hidden-dim`. La comprobación de recursos lo rechazaba, y por eso MATD3 y MAAC nunca empezaban. | **Resuelto** en el árbol de trabajo | Dar al piloto de MASAC el único ancho que busca, 128 (D-M3-8), con `--rnn-hidden-dim 128`. Los otros tres algoritmos no cambian. | `single_candidate_arguments` en `uc3m/application/training/fresh_campaign.py`. Prueba: `tests/fresh_training/test_pilot_launchable.py`. El DAG en memoria da `--rnn-hidden-dim 128`. |
| B2 | Autorizar una etapa exigía editar `iquitos.yaml`, que forma parte de la identidad de la campaña. Tras preparar la campaña, la CLI respondía `campaign_inputs_changed`. | **Resuelto** en el árbol de trabajo | La opción `--owner-authorized <texto>` de la CLI autoriza un lanzamiento y añade una línea con ese texto a `outputs/campaigns/<alias>/stages/owner_authorizations.jsonl`, fuera de la identidad. `authorized_stages` sigue en `[]` y no se edita. | `uc3m/application/training/cli.py`. Prueba: `tests/fresh_training/test_pilot_launchable.py`, que comprueba además que el YAML no cambia. |
| B3 | El piloto de 3 episodios no alcanza el lote de 32 episodios del crítico de MASAC. | **Reducido, sigue abierto** | C6 guarda el pico de VRAM en `stages/<stage>_gpu_memory.json` y lo imprime. Ya hay una lectura, pero de lotes de hasta 3 episodios, así que la comparación con los 74,5 GiB sigue siendo una extrapolación (sección 6). | `tools/colab/colab_session.py`. Lote del crítico: `external/MARL/src/runner_msac.py:68`. |

B1 y B2 son cambios aplicados por la sesión que integra esta tanda. El propietario los acepta o los rechaza al revisarla: el repositorio no guarda todavía una decisión suya sobre ellos.

**Riesgo conocido.** MASAC alcanza su lote de 32 episodios del crítico por primera vez en `confirm`, en el episodio 32. Por eso ni el piloto ni HPO miden su pico de VRAM (sección 6).

## 2. Requisitos antes del piloto

Cada punto tiene responsable y estado comprobable. Una casilla marcada significa que se comprobó el 2026-11-08 en el árbol de trabajo. Ningún punto autoriza el piloto.

- [ ] **Regla del propietario.** Responsable: propietario. No se entrena hasta cerrar los módulos 3 a 7 (D-V6-11, en `configs/experiments/iquitos.yaml:2`). Hoy no están todos cerrados: los módulos 3b, 5, 6 y 7 tienen trabajo abierto ([hoja de ruta](hoja_ruta_modulos.md)). Para lanzar antes, el propietario tendría que cambiar esta regla por escrito.
- [ ] **B1 y B2 en un commit.** Responsable: integrador. Código y pruebas están en el árbol de trabajo. Faltan el commit y la puerta `-Scope Repository`.
- [ ] **Dataset definitivo en un commit.** Responsable: integrador. Si `iquitos_v6_trial13` pasa sus puertas, hay que apuntar a él `storage_alias`, `campaign_id` y `dataset_root`, y hacer commit de su carpeta. Si no las pasa, decide el propietario.
- [x] **Facturas (D-V6-20).** Cerrada por D-V6-58: el propietario decidió no esperar confirmaciones externas. Lo que queda declarado está en la sección 8.
- [ ] **Publicación.** Responsable: integrador, con permiso del propietario para publicar. La celda C1 clona GitHub y hace `git checkout` del commit del paquete, así que ese commit y los de los submódulos deben estar publicados. Publicar `CityLearn` antes que el repositorio principal. Al leer, el principal iba 12 commits por delante de `origin` y `CityLearn` 4.
- [ ] **Paquete regenerado (D3).** Responsable: integrador. Se genera al final, después del último commit, porque el ZIP guarda el commit y el hash de cada archivo. El ZIP que hay en disco es de otra campaña y C3 lo rechazaría.
- [x] **Requisitos de memoria para `<alias>`.** `configs/algorithms/native.yaml` mantiene 50 GiB de RAM y 74 GiB de VRAM para MASAC. Lo comprueba `tests/fresh_training/test_runtime_requirements.py` con el alias que hoy nombra `iquitos.yaml`, y hay que repetirlo al cambiarlo. Son estimaciones, no mediciones.
- [ ] **Espacio en Google Drive** y una cuenta de Colab con acceso a la GPU elegida. Responsable: propietario.
- [ ] **Decisión escrita sobre `pilot`.** Responsable: propietario. Ver la sección 4.

## 3. Etapas y presupuesto

Las cifras se obtuvieron ejecutando en memoria `load_campaign_config` y `build_dag`, sin escribir nada, sobre `configs/experiments/iquitos.yaml` y `configs/algorithms/native.yaml`. Se repitió el 2026-11-08 con el alias que hoy nombra ese archivo. No se ejecutó `--stage prepare`. Coinciden con las reglas de esos dos archivos, y `--stage prepare` las imprime en el campo `budget`.

### Etapas que entrenan

| Etapa | Composición | Tratamientos | Episodios por tratamiento | Pasos por tratamiento | Episodios en total | Pasos de entorno en total |
|---|---|---:|---:|---:|---:|---:|
| `pilot` | 4 algoritmos × E1 × semilla 901 | 4 | 3 | 26 280 | 12 | 105 120 |
| `hpo` | (8 + 8 + 8 + 4 candidatos) × 3 escenarios × 3 semillas (901, 902, 903) | 252 | 10 | 87 600 | 2 520 | 22 075 200 |
| `confirm` | 4 × 3 escenarios × 12 semillas (1001 a 1012) | 144 | 50 | 438 000 | 7 200 | 63 072 000 |
| `sensitivity` | 4 × 3 escenarios × 2 dominancias (0,55 y 0,65) × 3 semillas (1001 a 1003) | 72 | 50 | 438 000 | 3 600 | 31 536 000 |
| **Total** | | **472** | | | **13 332** | **116 788 320** |

- Un episodio dura 8 760 pasos (`configs/experiments/iquitos.yaml:27-41`).
- En HPO, MASAC tiene 4 candidatos porque solo busca `rnn_hidden_dim` 128 (D-M3-8, `configs/algorithms/native.yaml:67`). Los otros tres tienen 8.
- Un paso de entorno es una hora del distrito completo de 17 edificios.

### Reparto por fases

Una etapa corre por fases. La fase 2 empieza solo si todos los tratamientos de la fase 1 terminan bien (`configs/experiments/iquitos.yaml:13-17`, `uc3m/application/training/phases.py:179`).

| Etapa | Fase 1: HAPPO y MASAC | Fase 2: MATD3 y MAAC |
|---|---:|---:|
| `pilot` | 2 | 2 |
| `hpo` | 108 | 144 |
| `confirm` | 72 | 72 |
| `sensitivity` | 36 | 36 |

Requisitos por trabajador (`configs/algorithms/native.yaml`):

| Algoritmo | RAM (GiB) | VRAM (GiB) |
|---|---:|---:|
| HAPPO | 8 | 4 |
| MASAC | 50 | 74 |
| MATD3 | 40 | 4 |
| MAAC | 8 | 4 |

Cada trabajador reserva el mayor requisito de su fase (`uc3m/application/training/phases.py:43-71`). Con los valores de ejemplo que usa `tests/fresh_training/test_stage_phases.py:130` (83 GiB de RAM, 74,5 GiB de VRAM, 12 CPU), la fase 1 tendría 1 trabajador y la fase 2 tendría 2. Eso es aritmética sobre valores de prueba, no una medición de Colab: el dato real es `phase_plan` en la salida de C5.

### Etapas que no entrenan

El orden es: `hpo` en C6, C9 con `EVAL_STAGE='hpo'` y C8. Después, `confirm` en C6, C9 en `validation_2024`, C10 con análisis y selección, y `sensitivity` en C6, C9 y C10 sobre `validation_2024`. Al final, C9 y C10 de `confirm` en `test_2025`. En el cuaderno, C9 va antes que C8, su valor por defecto es `hpo`, y C10 usa la etapa y la partición fijadas en C9.

| Paso | Qué hace | Comando o celda | Requisito |
|---|---|---|---|
| Evaluación de HPO | Evalúa los 252 intentos en `validation_2024`. El congelado la exige. | C9 con `EVAL_STAGE='hpo'`, `EVAL_SPLIT='validation_2024'` | HPO completo |
| Congelado | Elige una configuración por algoritmo y escribe `configuration_freezes.json` y `test_unlock.json`. Si un algoritmo queda bloqueado, no se congela ninguno. | C8 (`pipeline freeze`) | Evaluación de HPO (`freeze_hpo` en `uc3m/application/pipeline.py`) |
| Evaluación de `confirm` en validación | Evalúa los 144 intentos de `confirm` en `validation_2024`. `pipeline select` la necesita. C9 copia a Drive mientras corre. | C9 con `EVAL_STAGE='confirm'`, `EVAL_SPLIT='validation_2024'` | `confirm` completo |
| Análisis en validación | `pipeline analyze` calcula la tabla por semilla y las pruebas. Un análisis incompleto se rechaza sin publicarse: C10 no usa `--publish-incomplete`, y un análisis publicado no se reemplaza. | C10 con `RUN_ANALYSIS = True` | Evaluación completa |
| Selección | Candidato descriptivo por hipervolumen, escrito una vez en `model_selection.json`. Solo acepta `validation_2024`. El ganador inferencial exige ganar en los tres ejes, y el estudio puede terminar sin ganador. | C10 con `RUN_SELECTION = True` (`pipeline select`) | Análisis completo en validación (`select_model` en `uc3m/application/pipeline.py`) |
| Sensibilidad | Evalúa los 72 intentos en `validation_2024` y analiza cada variante por separado. No alimenta la selección. | C9 con `EVAL_STAGE='sensitivity'`, `EVAL_SPLIT='validation_2024'`; C10 con `ANALYSIS_CANDIDATE` en `p055` y luego en `p065` | `sensitivity` completa. `pipeline analyze` la rechaza sin `--candidate`. |
| Evaluación congelada en test | Evalúa los 144 intentos de `confirm` en `test_2025`. | C9 con `EVAL_STAGE='confirm'`, `EVAL_SPLIT='test_2025'` | `test_unlock.json` válido (`uc3m/application/evaluation/test_access.py`) |
| Informe estadístico en test | `pipeline analyze` calcula. `tools/eval/build_campaign_statistical_report.py` no calcula nada: solo lee ese análisis tras reverificarlo. Solo `confirm` en `test_2025` puede quedar como `scientifically_complete`. | C10 con `RUN_ANALYSIS = True` | Evaluación completa (`_analyze_stage` en `uc3m/application/pipeline.py`). `pipeline select` rechaza esta partición: dejar `RUN_SELECTION = False`. |

La sección 4 de `docs/architecture/runbook.md` fija el mismo orden. El código no impide abrir `test_2025` antes de seleccionar, porque `test_unlock.json` se escribe al congelar: este orden depende de quien ejecuta las celdas. El código tampoco fija cuándo va la sensibilidad, que aquí conserva su lugar anterior, antes de test.

«Entrenar sin B01» (tarea 8.3, D7) queda cerrado: el propietario decidió el 2026-11-08 que los 17 edificios, incluido B01, entrenan en todas las etapas; no hay campaña sin B01 y la sensibilidad sin B01 queda solo en la evaluación (D-M2-4).

## 4. Autorizar una etapa

Cada etapa necesita una decisión explícita del propietario. Ni este plan, ni un agente, ni una sesión anterior pueden darla. **Hoy ninguna etapa está autorizada.**

1. **El propietario decide y lo deja escrito,** con fecha y etapa. El lugar propuesto es `docs/plans/traspaso_sesiones.md`.
2. En Colab, deja `STAGE` en esa etapa en C5 y revisa el plan que imprime C5.
3. En C6 pone `EXECUTE_STAGE = True`, escribe en `OWNER_DECISION` dónde y cuándo quedó esa decisión, y ejecuta la celda. C6 lanza la CLI con `--owner-authorized <texto>`, y la CLI añade a `stages/owner_authorizations.jsonl` la etapa, la fecha UTC, el texto y la vía.
4. Al terminar, vuelve a dejar `EXECUTE_STAGE = False`. Si queda en `True` y se cambia `STAGE`, C6 lanza la etapa nueva.

**No se edita `configs/experiments/iquitos.yaml` y no hace falta ningún commit para autorizar.** Ese archivo entra en la identidad de la campaña: editarlo después de preparar la campaña la invalida. `authorized_stages` sigue en `[]`.

Cada lanzamiento añade una línea al registro. Relanzar la misma etapa tras una desconexión no es una etapa nueva: se repite la misma referencia en `OWNER_DECISION`, y queda registrado igual.

**Lo que este mecanismo no hace.** La CLI no comprueba que exista la decisión escrita ni que el texto sea cierto: `--owner-authorized` es una declaración de quien ejecuta la celda. El archivo prueba que hubo un lanzamiento, no que el propietario lo aprobara. Por eso la decisión escrita es el control real.

Hay tres seguros más: `EXECUTE_STAGE` es `False` por defecto, C6 se detiene si `OWNER_DECISION` está vacío, y sin la opción o con el texto vacío la CLI responde `not_authorized` con código 2.

### Generar el paquete

Se hace una vez por campaña, después del último commit, y no es parte de la autorización:

1. `powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1`
2. `.\.venv39-citylearn-v3\Scripts\python.exe -B tools/colab/build_modular_colab_notebook.py`

Esto reescribe el cuaderno y `outputs/colab_delivery/colab_modular_overlay.zip`.

**Conservar el ZIP mientras dure la campaña.** Otro ZIP con otras fuentes hace que la campaña restaurada de Drive se rechace por entradas cambiadas. Tras una desconexión hay que subir el mismo archivo.

## 5. El piloto en Colab, paso a paso

### 5.1 Antes de lanzar

1. Abrir Colab en el navegador, **Archivo → Subir notebook**, y elegir `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb` recién generado (`docs/architecture/colab.md`).
2. **Entorno de ejecución → Cambiar tipo:** GPU A100, con RAM alta. El plan del módulo 8 asume una A100 de 80 GB. Que Colab ofrezca ese modelo a esta cuenta está **sin verificar**, y Colab no garantiza GPU ni duración de sesión.
3. Usar un solo entorno de ejecución por campaña. El bloqueo protege la copia a Drive, pero no impide que dos sesiones entrenen lo mismo.

### 5.2 Orden de las celdas

| Celda | Acción | Comprobar | Si falla |
|---|---|---|---|
| C1 | Subir `colab_modular_overlay.zip`. Clona, hace checkout y aplica el paquete. | Imprime «Checkout verificado». | Detenerse: el paquete no coincide. |
| C2 | Instala Python 3.9 y dependencias fijadas. | Imprime la GPU detectada y «C2 OK». | Si pide reiniciar, repetir desde C1. |
| C3 | Monta Drive y comprueba campaña, dataset y fuentes. Anotar la ruta `DRIVE_ROOT`. | Imprime campaña, hash y Drive. | Si las fuentes difieren, detenerse. |
| C4 | Restaura de Drive los intentos verificados. | En la primera sesión, 0 restaurados. | Conflictos o rechazos detienen la celda: no borrar nada, revisar. |
| C5 | Prepara la campaña, sin entrenar. Dejar `STAGE = 'pilot'`. | Ver abajo. | Código 2 muestra el motivo. |
| M1 | Celda temporal de monitor (5.3). | Crece `gpu.csv` en Drive. | Sin monitor no hay curva de VRAM para G9: no lanzar. |
| P1 | Celda temporal de prueba del bloqueo (5.4). | Resultado esperado. | Anotar; es una puerta del piloto. |
| C6 | Con la decisión escrita de la sección 4, poner `EXECUTE_STAGE = True`, escribir la referencia en `OWNER_DECISION` y ejecutar. | Código 0 y `training_complete`. Imprime el pico de VRAM y avisa si falló alguna copia a Drive. | Código 1, 2 o `insufficient_resources` lanzan error. |
| Después | C7 (estado) y C9 con `RUN_EVALUATION = True`, `EVAL_STAGE, EVAL_SPLIT = 'pilot', 'validation_2024'`. | Cada intento aceptado y evaluado. | Es la primera evaluación real en Colab. |

El cuaderno trae las celdas finales en este orden: C7, C9, C8, C10 y C11. En el piloto hay que cambiar `EVAL_STAGE` de C9, cuyo valor por defecto es `hpo`, y no ejecutar C8, C10 ni C11. Las celdas temporales y los valores editados no cambian la identidad, porque `examples_madrl_v3/` queda fuera de las fuentes vigiladas.

**Qué leer en C5 antes de lanzar:**

- `Presupuesto`: debe coincidir con la sección 3.
- `Recursos medidos`: anotar `ram_gib`, `vram_gib` y `cpu_count`. Es la primera medición real.
- `Plan de la etapa pilot`: cada fase con `workers` de 1 o más.
- Si `vram_gib` es menor que 74 o `ram_gib` menor que 50, MASAC se rechazará aunque el piloto consuma mucho menos: la comprobación aplica desde 1 000 pasos por episodio.
- Los 74,5 GiB de una GPU de 80 GB son una conversión usada en las pruebas y en `native.yaml`, no una medición de Colab.

### 5.3 Monitorizar

C6 ocupa el cuaderno y la CLI solo imprime su JSON final, porque la salida de cada intento va a `child.log`. Una celda en silencio no significa un fallo. C6 guarda solo el pico de la etapa; la curva que pide la sección 6 sale de esta celda temporal, que no se guarda en el repositorio y hay que lanzar antes de C6:

```python
# [M1] Monitor temporal del piloto
import subprocess
MONITOR = DRIVE_ROOT.parent/'monitor_piloto'
MONITOR.mkdir(exist_ok=True)
subprocess.Popen(f"nvidia-smi --query-gpu=timestamp,name,memory.total,memory.used,utilization.gpu "
                 f"--format=csv -l 5 >> '{MONITOR}/gpu.csv'", shell=True)
subprocess.Popen(f"while true; do date -u +%FT%TZ; free -g | sed -n 2p; sleep 30; done >> '{MONITOR}/ram.txt'",
                 shell=True, executable='/bin/bash')
```

- Mientras corre, revisar en Drive `gpu.csv`, `ram.txt` y la aparición de `completion.json` dentro de `DRIVE_ROOT`.
- Si la cuenta tiene terminal de Colab (**sin verificar**), se puede ver el avance con `tail -f` sobre el `child.log` más reciente de `outputs/campaigns/<alias>/`.
- `memory.used` muestra lo que PyTorch tiene reservado, no lo que usa en cada instante. Es una cota, no el dato exacto.
- Cada intento guarda `runtime_resources.json`, con la memoria libre **antes** de empezar.
- C6 guarda el pico en `stages/pilot_gpu_memory.json`, que la sincronización copia a Drive. Es la memoria más alta de `nvidia-smi` en toda la etapa, leída cada 30 s, y no separa algoritmos. Una subida más corta que ese intervalo puede no verse.
- Si el entorno muere, las últimas líneas de los registros en Drive pueden perderse: **sin verificar**.

### 5.4 Probar el bloqueo de Drive

El bloqueo es `.sync.lock` en `DRIVE_ROOT` (`uc3m/application/training/drive_sync.py:143` y `:272`). Solo está probado en disco local (`docs/architecture/colab.md`, sección «Fronteras y estado real»). Ejecutar después de C5:

```python
# [P1] Con el bloqueo tomado, una copia debe rechazarse
import subprocess, time
RETENER = ("import sys, time; from pathlib import Path; from uc3m.application.training.lock import run_lock\n"
           "with run_lock(Path(sys.argv[1])): time.sleep(45)")
retenedor = subprocess.Popen([str(PYTHON), '-c', RETENER, str(DRIVE_ROOT/'.sync.lock')], cwd=PROJECT_ROOT)
time.sleep(10)
ocupado = subprocess.run(SYNC + ['--sync'], cwd=PROJECT_ROOT, capture_output=True, text=True)
print('Con bloqueo:', ocupado.returncode, ocupado.stdout[-300:])   # esperado: 2 y refused
retenedor.wait()
libre = subprocess.run(SYNC + ['--sync'], cwd=PROJECT_ROOT, capture_output=True, text=True)
print('Sin bloqueo:', libre.returncode, libre.stdout[-300:])        # esperado: 0
```

Esto prueba dos procesos en un mismo entorno. Si el bloqueo funciona entre dos entornos distintos sobre Drive está **sin verificar**, y por eso se usa un solo entorno.

### 5.5 Probar la desconexión y la reanudación

En este proyecto, «reanudar» significa repetir desde cero lo interrumpido y reutilizar lo verificado. **Ningún intento continúa desde un checkpoint** (`docs/architecture/runbook.md`, «Reglas que no cambian»).

1. Esperar a que aparezca en Drive el `completion.json` del primer tratamiento. Con 1 trabajador en la fase 1 es HAPPO.
2. Con el segundo tratamiento ya en marcha, **Entorno de ejecución → Desconectar y eliminar**. Hacerlo pronto reduce el trabajo que se repite.
3. Abrir un entorno nuevo y ejecutar C1 con el **mismo ZIP**, luego C2, C3 y C4. C4 debe mostrar 1 o más restaurados completos.
4. **Anotar `stages/pilot_gpu_memory.json` antes de relanzar.** C6 empieza de nuevo la lectura en cada lanzamiento y sobrescribe el pico de la sesión anterior.
5. Ejecutar C5, M1 y C6.
6. Comprobar en `outputs/campaigns/<alias>/stages/pilot_result.json`:
   - el primer tratamiento tiene `reused_verified_attempt: true`;
   - el interrumpido tiene un intento nuevo desde el episodio 0;
   - `launch_history` registra el lanzamiento.

Anotar cuánto tarda rehacer C1 a C5: entra en el cálculo de horas.

### 5.6 Copia y restauración con SHA-256

La copia se hace sola durante C6. Si una copia falla, el entrenamiento sigue, y C6 imprime el fallo y lo cuenta en `sync_problems` (D9). Ese aviso no sustituye a estas pruebas: son la evidencia de G7.

**Cerrar la copia y revisarla** (`conflicts` debe quedar vacío):

```python
# [P2] Copia final con informe
print(cs.run_cli(SYNC + ['--sync'], cwd=PROJECT_ROOT, on_line=lambda line: None).report)
```

**Restaurar en un entorno limpio:** C1 a C4 deben terminar sin conflictos ni rechazos. Después se recalcula cada SHA-256 y se compara con el manifiesto de Drive:

```python
# [P3] Cada intento restaurado contra drive_sync_manifest.json
import subprocess
VERIFICAR = """
import json, sys
from pathlib import Path
from uc3m.application.training.drive_sync import directory_digest
artifacts, drive = Path(sys.argv[1]), Path(sys.argv[2])
registro = json.loads((drive/'drive_sync_manifest.json').read_text())
fallos = [r for r, h in registro['attempts'].items()
          if directory_digest(artifacts/r, training_only=True) != h or directory_digest(drive/r, training_only=True) != h]
print('intentos', len(registro['attempts']), 'fallos', fallos)
"""
subprocess.run([str(PYTHON), '-c', VERIFICAR, str(ARTIFACTS), str(DRIVE_ROOT)], cwd=PROJECT_ROOT)
```

**Probar una alteración sobre una copia,** sin tocar la original:

```python
# [P4] Una copia alterada debe rechazarse
import json, shutil, subprocess
CAJA = DRIVE_ROOT.parent/'prueba_alteracion'
shutil.copytree(DRIVE_ROOT, CAJA)
registro = json.loads((CAJA/'drive_sync_manifest.json').read_text())
alterado = sorted(registro['attempts'])[0]
with (CAJA/alterado/'attempt.json').open('ab') as archivo:
    archivo.write(b' ')
r = subprocess.run([str(PYTHON), '-m', 'uc3m.application.training.drive_sync', '--artifacts', '/content/restaurado_alterado',
                    '--drive', str(CAJA), '--restore', '--campaign-id', CAMPAIGN_ID],
                   cwd=PROJECT_ROOT, capture_output=True, text=True)
print(r.returncode, r.stdout[-600:])   # esperado: 2 y drive_copy_digest_mismatch en ese intento
```

**Copia fuera de Drive:** descargar la carpeta `DRIVE_ROOT` a un disco, fuera del repositorio, y conservarla con el registro de cada comprobación.

La tarea 8.1 compara cada SHA-256 con `drive_sync_manifest.json`. Los intentos de esta campaña no generan `evidence.json`, y `backup_run` los rechaza y remite a `drive_sync` (D5). El manifiesto guarda un SHA-256 por archivo de campaña, evaluación y análisis, y uno por instantánea de intento, no uno por cada archivo del intento.

## 6. Criterios para seguir o detenerse

El piloto no es un resultado de tesis. Sus cifras son de infraestructura y `scientific_acceptance` sigue en `false`. **Se sigue solo si se cumple todo.** Lo decide el propietario con la evidencia delante.

| # | Puerta | Se cumple cuando | Evidencia |
|---|---|---|---|
| G1 | Instalación | C1 a C3 sin errores | Salida del cuaderno |
| G2 | Plan | `budget` igual a la sección 3 y todas las fases con trabajadores | Salida de C5 |
| G3 | Aprendizaje | 4 de 4 tratamientos `training_complete`, con `failed_attempts` en 0, salvo el interrumpido a propósito | `pilot_result.json` y C7 |
| G4 | Supervisión | Ningún intento rechazado por `constraint_terms_dominate_weighted_axes` (límite 1,0, solo en E1) | `completion.json` |
| G5 | Bloqueo | P1 da 2 y luego 0 | Salida de P1 |
| G6 | Desconexión | Se cumple la sección 5.5 | `pilot_result.json` |
| G7 | Restauración | P2 sin conflictos, P3 sin fallos, P4 rechaza | Salidas de P2, P3 y P4 |
| G8 | Evaluación | C9 evalúa los 4 intentos sin fallos, y anotar el tiempo | Salida de C9 |
| G9 | VRAM de MASAC | Ver abajo | `gpu.csv`, `stages/pilot_gpu_memory.json` y `runtime_resources.json` |
| G10 | RAM | Ver abajo | `ram.txt` y `runtime_resources.json` |
| G11 | Sesión | El tratamiento más largo cabe en una sesión (sección 7) | Tiempos medidos |
| G12 | Drive | Espacio de los 472 tratamientos disponible (sección 7) | Tamaño de los intentos |
| G13 | Coste | El propietario acepta las horas y el coste estimados | Sección 7 |

### La VRAM de MASAC (G9)

**Requisito:** 74 GiB, que salen de un estimado de 66,47 GiB más el 10 % (`configs/algorithms/native.yaml:60` y `:68`, `native_entrypoint.py:226-229`). **Límite supuesto:** 74,5 GiB. Quedan 0,5 GiB de margen, y sobre un estimado, no sobre una medición.

**Lo que el piloto puede y no puede medir.** El crítico toma `min(episodios guardados, 32)` episodios en cada actualización (`external/MARL/src/runner_msac.py:68`). El búfer guarda como mucho los episodios de la corrida. Este es el estimado del propio código, con 17 agentes, 39 observaciones, estado 633 y las 220 acciones de D-M3-10 (5 niveles por equipo) del alias activo:

| Situación | Episodios del lote | Crítico, `rnn` 128 (GiB) | Búfer en RAM (GiB) |
|---|---:|---:|---:|
| Piloto, episodios 1, 2 y 3 | 1, 2 y 3 | 2,08; 4,15; 6,23 | 2,71 con 3 episodios |
| HPO, último episodio | 10 | 20,77 | 9,03 |
| `confirm` y `sensitivity`, desde el episodio 32 | 32 | **66,47** | 45,14 al llegar al episodio 50 |

- El pico real aparece por primera vez en el episodio 32 de un tratamiento de MASAC en `confirm`, después de pagar HPO. Ni el piloto ni HPO lo alcanzan.
- La frase «to measure real RAM/VRAM» de `configs/experiments/iquitos.yaml:24-25` es cierta solo para lotes de hasta 3 episodios. El pico de `stages/pilot_gpu_memory.json` tiene ese mismo límite.
- El piloto de MASAC corre con `rnn` 128, el mismo ancho de HPO y `confirm` (B1).

**Cómo estimar con el piloto.** En `gpu.csv`, tomar `memory.used` antes de la primera actualización y tras las de 1, 2 y 3 episodios. Con esos puntos se ajusta una recta y se proyecta a 32 episodios:

`VRAM_32 = base + pendiente × 32`

Con `memory.used` puede fallar esa lectura, porque PyTorch no siempre reserva por pasos. Si no se distinguen los 3 puntos, el resultado es **no concluyente**.

**Lectura:**

- `VRAM_32` mayor que la VRAM libre medida en C5: **detenerse**.
- `VRAM_32` menor, pero por menos de lo que varía entre lecturas: **no concluyente**. Es una extrapolación de 3 a 32 episodios; la fragmentación no se ve con lotes pequeños.
- Claramente menor: la puerta se cumple **como estimación**. Queda el riesgo de fallo en el episodio 32 o más. Un fallo así deja el tratamiento incompleto y la fase 2 no empieza.

**Si no cabe o no se puede confirmar.** Estas son las opciones que existen; el propietario decide, y este plan no recomienda ninguna:

| Opción | Choca con |
|---|---|
| GPU con más memoria. El cuaderno prevé una RTX PRO 6000 (celda C2); su disponibilidad y capacidad en Colab están **sin verificar**. | D-M3-4 si cambia el plan de Colab; coste |
| Prueba específica de MASAC con 32 o más episodios antes de HPO (280 320 pasos o más) | No hay etapa para ello: exige cambio de configuración y de código |
| Lanzar primero un tratamiento MASAC de `confirm` para medir | El orden de etapas: necesita el congelado, que necesita HPO |
| Reducir el lote del crítico, 32 episodios, de MASAC | D-M3-1 y D-M3-5, capacidad nativa; hay que declarar la limitación |
| Reducir `rnn_hidden_dim` por debajo de 128 | La rejilla y su prueba; hay que declarar la limitación |
| Reducir el tamaño de observación, estado o acciones, como hicieron D-V6-49 y D-M3-10 | Dataset o rejilla nuevos, y campaña nueva |
| Cambiar la implementación del crítico, por ejemplo en tramos o con otra precisión numérica | Se aparta del autor; necesita spec y pruebas |
| Quitar MASAC del estudio o limitar su campaña | Objetivo de 4 algoritmos; el congelado exige una configuración por algoritmo |
| Usar otro proveedor de cómputo | `configs/experiments/iquitos.yaml:55`, solo Colab |

### La RAM (G10)

- El piloto de MASAC guarda 3 de 50 episodios, así que no mide su RAM final. Estimado a 50 episodios: 45,14 GiB; requisito: 50 GiB.
- MATD3 y MAAC también crecen con la corrida. Sus reservas son 40 y 8 GiB, y las cubre un estimado, no una medición.
- La puerta se cumple si `ram_gib` en C5 supera 50 GiB y `ram.txt` no muestra presión durante el piloto. El búfer de MASAC solo se llena en el episodio 50 de `confirm`, así que su RAM real no se conocerá antes.

## 7. Horas y coste

**Hoy no existe ninguna cifra de horas ni de coste de esta campaña.** Las tiene que medir el piloto. Las «10-12 horas» del antiguo manual de Colab pertenecían a un flujo retirado de 12 corridas y no sirven.

Tampoco vale como estimación de Colab el único tiempo que hay en el repositorio: 2 744 s para 8 783 pasos de evaluación (celda C9), medido en Windows, en CPU y con una política de reglas.

### Qué medir en cada intento

| Medida | Cómo |
|---|---|
| Inicio | `created_at` en `attempt.json` |
| Fin | Fecha de modificación de `completion.json`. El código no guarda un tiempo por intento. |
| Segundos por paso, `s_a` | (fin − inicio) / 26 280, por algoritmo |
| Tamaño | Tamaño del intento en Drive |
| Evaluación, `e` | Segundos de C9 por intento, y `workers` usados |
| Rearranque, `r` | Tiempo de C1 a C5 en un entorno nuevo |
| Unidades de Colab por hora, `u` | Panel de recursos de Colab durante la sesión |

### Cómo calcular

Para cada etapa y cada fase, donde `w` es `workers` de `phase_plan`:

`Horas de fase = suma por algoritmo de (tratamientos_a × pasos por tratamiento × s_a) / w / 3 600`

- `Horas de etapa` = fases + `(evaluaciones × e) / workers de C9 / 3 600` + `r × sesiones necesarias`.
- `Unidades` = horas × `u`.
- `Coste` = unidades × precio que muestre la cuenta de Colab. El repositorio no contiene ese precio.

| Etapa | Tratamientos en fases 1 y 2 | Pasos por tratamiento | Evaluaciones | Horas | Coste |
|---|---|---:|---:|---|---|
| `hpo` | 108 y 144 | 87 600 | 252 en validación | sin medir | sin medir |
| `confirm` | 72 y 72 | 438 000 | 144 en validación y 144 en test | sin medir | sin medir |
| `sensitivity` | 36 y 36 | 438 000 | 72 en `validation_2024` | sin medir | sin medir |

### Por qué el resultado será una cota inferior

- **MASAC:** cada actualización crece con el lote, de 3 episodios en el piloto a 32 después. Multiplicar `s_a` por los pasos subestima su tiempo. Es necesario recalcularlo con el primer dato real de HPO.
- **Hiperparámetros:** el piloto no usa candidatos de la rejilla, sino los valores por defecto del lanzador; la excepción es el ancho 128 de MASAC (B1). Un `hidden_dimension` distinto en HPO cambia el tiempo de los otros tres. Ver `resolved_backend_config.json` de cada intento.
- **Paralelismo:** `s_a` de la fase 2 se mide con los trabajadores de esa sesión. Con otro reparto cambia.
- **Repeticiones:** cada corte o rechazo repite el tratamiento desde cero.
- **GPU:** Colab puede dar otro equipo en otra sesión.

### Dos límites que no son horas

- **Sesión (G11).** Ningún intento continúa tras un corte, así que un tratamiento que dure más que la sesión no terminará nunca. Calcular `438 000 × s_a` para cada algoritmo con la corrección de MASAC. El resultado debe ser menor que la duración real de sesión observada, que el repositorio no documenta. Sin esto, `confirm` no puede completarse.
- **Drive (G12).** Sumar `tratamientos × tamaño por episodio × episodios` por algoritmo, más las evaluaciones. Comparar con el espacio libre. MASAC y los lotes guardados pueden no crecer de forma lineal: **sin verificar**.

## 8. Limitaciones al leer los resultados

- **Aire acondicionado 5R1C.** Está calibrado a facturas y **sus parámetros de Iquitos no están validados con medición propia**. La validación es del método, en un edificio análogo de Bangkok con CU-BEMS ([informe](../audits/validacion_5r1c_cubems_20261108/README.md)):
  - La temperatura a 24 h supera la referencia en 20 de 20 zonas.
  - En simulación libre de 6 meses, el RMSE mediano es 1,68 °C.
  - La energía mensual cumple ASHRAE G14 en 6 de 20 zonas y la horaria en 0 de 20. Por decisión del propietario, G14 es solo informativo y no condiciona el entrenamiento; el criterio térmico es el error de temperatura, como en CityLearn v2.
  - 16 de 20 zonas tienen parámetros en el límite.
  - La capacidad térmica de Iquitos adopta la mediana de ese edificio (2,27 veces la clase media, D-V6-56).
  - Por eso conviene leer los ahorros por hora de refrigeración con cautela, como resultado del modelo y no como medición de Iquitos.
- **Facturas (D-V6-20, cerrada por D-V6-58, [SPEC-016](../../specs/016-iquitos-v6/spec.md)).** La factura de B11 era parcial y se completa con su segundo suministro, `0104007T`. Sus meses sin medir quedan como `modeled`, con el supuesto declarado de que ese suministro existía en 2023 y 2024. Los otros 9 edificios (B09, B03, B14, B02, B12, B16, B17, B08 y B13) no tienen otro identificador en el repositorio: se tratan como completos y su brecha sigue bajo el tope de D-V6-19.
- **El espacio de búsqueda de MASAC es más estrecho:** 4 configuraciones frente a 8 (D-M3-8).
- **Actualizaciones no comparables:** MASAC y MAAC difieren de los demás en actualizaciones por paso de entorno; es una limitación declarada (`configs/algorithms/native.yaml:72` y `:112`).
- **Un solo entorno paralelo** en HAPPO y MAAC, frente a 20 y 12 de los autores (`native.yaml:40` y `:111`).
- **Cabeza de acción cambiada:** MASAC y MAAC usan una rejilla común con varias salidas discretas, y HAPPO y MATD3 redondean su salida continua.
- **Poca potencia estadística:** 12 semillas por celda. No detectar diferencias no prueba que sean iguales, y un solo distrito no da validez geográfica externa (`uc3m/application/evaluation/fresh_analysis.py`).
- **Puede no haber ganador:** el ganador inferencial tiene que ganar en los tres ejes (`selection_inference`), y que no lo haya es un resultado válido. `select_best_model` da un candidato descriptivo, y el informe registra `winner_forced` en `false`.
- **Pendientes del módulo 8 que afectan a la lectura:** los supuestos económicos sin fuente (tarea 8.5) y el peso de B01 (D-M2-4, y D7 en la sección 9).

## 9. Diferencias encontradas entre documentos, cuaderno y código

Estado al 2026-11-08. «Corregido» significa corregido en el árbol de trabajo, sin commit todavía. Las correcciones del cuaderno están en `tools/colab/build_modular_colab_notebook.py`, la única fuente del `.ipynb`, y llegan a Colab solo con el cuaderno y el ZIP regenerados (D3).

### Resueltas o resueltas en esta tanda

| Id | Qué pasaba | Estado |
|---|---|---|
| D1 | La celda 0 decía que MASAC pedía 72 GiB de RAM y 82 de VRAM, y que su rechazo en una A100 era lo esperado. `native.yaml` pide 50 y 74 GiB. | Corregido: la celda toma las cifras de `native.yaml`. |
| D2 | C6 decía que MASAC era «el rechazo esperado» en una GPU de 80 GB. | Corregido: un rechazo por recursos se presenta como etapa incompleta que hay que revisar. |
| D3 | El ZIP en disco tiene alias `iquitos_v6`, campaña `fresh_iquitos_20261107_v6` y commit `93591dbe`. C3 lo rechazaría. | **Se resuelve al final de la tanda:** hay que regenerarlo después del último commit (sección 4). Sigue pendiente; el integrador es el responsable. |
| D4 | El texto de C5 decía que `prepare` no consulta la GPU, pero la CLI mide RAM y VRAM también al preparar. | Corregido en el texto de C5. La frase de `fresh_campaign.py` describe `prepare_campaign`, que no mide nada; la medición la hace la CLI. |
| D8 | C8 (congelar) iba antes que C9 (evaluar), con `confirm` por defecto. El congelado exige HPO evaluado en validación. | Corregido: C9 va antes que C8 y su valor por defecto es `hpo`. |
| D9 | El hilo de copia a Drive ignoraba el código de salida, así que un conflicto no se veía. | Corregido: cada copia fallida se muestra y queda en `sync_problems`, y C6 avisa. |
| D10 | C8 no sincronizaba con Drive, y un corte podía perder el congelado local. | Corregido: C8 sincroniza después de congelar. |
| D11 | `docs/architecture/runbook.md` traía alias y campaña de `iquitos_v5`, HPO con 288 tratamientos y `RUN_STAGE`. | Corregido en esta tanda: alias y campaña activos, HPO con 252 tratamientos y 22 075 200 pasos, `STAGE` en C5 y `EXECUTE_STAGE` en C6. |
| D12 | El manual y la lista de Colab antiguos describían una vía retirada. | Retirados del árbol el 2026-11-08 por decisión del propietario (FR-012.4); commit de recuperación en `data/audits/repository_hygiene_manifest.json`. Este plan es la guía vigente. |
| D13 | `docs/architecture/colab.md` hablaba de `RUN_TRAINING=True`, 12 tratamientos, tope de 85 % de VRAM, buffers reducidos y una celda de preflight que comprobaba el bloqueo. | Corregido en esta tanda. Las frases de «no ejecutado en Colab» se conservan porque siguen siendo ciertas. |
| D14 | `configs/algorithms/native.yaml:73` atribuía el tamaño de MASAC a 87 acciones por eje. | Corregido: ahora nombra las 220 acciones de D-M3-10 y da 105 GiB para el candidato 256, que coincide con 95,07 GiB más el 10 % (`native.yaml:60` y `native_entrypoint.py:226-229`). |
| D17 | `docs/plans/hoja_ruta_modulos.md` mostraba los módulos 3b a 7 como «Pendiente». | Corregido en esta tanda: estados actualizados, sin dar por cerrado lo que sigue abierto. |
| D5 | La tarea 8.1 y `backup_run` exigían `evidence.json` y `experiment.json`, que los intentos de esta campaña no generan. | Resuelta. `backup_run` rechaza un intento fresco y remite a `drive_sync`. FR-008.3 se cumple con `drive_sync_manifest.json`: SHA-256 por archivo de campaña, evaluación y análisis, uno por instantánea de intento, verificados al copiar y restaurar, más la regla de confianza. Probado solo en carpetas locales. |
| D6 | `tools/eval/build_campaign_statistical_report.py` no encontraba estos intentos, y `select_best_model` no tenía comando. | Resuelta. `pipeline analyze` calcula, `build_campaign_statistical_report.py` solo lee ese análisis tras reverificarlo, y `pipeline select` da el candidato descriptivo por hipervolumen solo en `validation_2024`. Probado con KPI sintéticos, sin campaña real. |

Los comentarios que nombraban `iquitos_v6_trial10` en `native.yaml` e `iquitos.yaml` también se actualizaron al alias que esos archivos nombran hoy. Además, en el árbol de trabajo, los límites de ejecución ya llegan al entrenador (`_execution_env` en `uc3m/application/training/cli.py`), y la medición de recursos corre en un proceso hijo que termina, para no retener VRAM.

### Abiertas, sin bloquear el piloto

| Id | Diferencia | Responsable | Siguiente acción | Por qué no bloquea el piloto |
|---|---|---|---|---|
| D7 | «Entrenar sin B01» (tarea 8.3). | Cerrada: el propietario decidió el 2026-11-08 que los 17 edificios, incluido B01, entrenan en todas las etapas; no hay campaña sin B01 y la sensibilidad sin B01 queda solo en la evaluación (D-M2-4). | Definir tratamientos, presupuesto y dataset antes de la tarea 8.3. | El piloto no incluye ese escenario. Si se añade, cambia la campaña, y hay que decidirlo antes de preparar la definitiva. |
| D15 | El foco 5 del plan del módulo 8 pide fallar «con la ruta del archivo», y `drive_sync` informa la ruta del intento. | Propietario | Con la salida de P4 delante, decidir si basta la ruta del intento o si hay que cambiarla. | La copia alterada se rechaza igual; solo cambia el detalle del mensaje. |
| D16 | `docs/architecture/runbook.md` dice 8 784 pasos de validación, y C9 trae 8 783 medidos. Puede ser pasos frente a transiciones: **sin verificar**. | Quien ejecute el piloto | Leer el número en la primera evaluación en Colab (G8). | Es una diferencia de texto o de conteo que el propio piloto permite aclarar. |

## 10. Sin verificar

- Todo lo que depende de Colab: instalación, GPU, CUDA, montaje de Drive y duración de sesión. `docs/architecture/colab.md` y el punto 4 de la conciliación de `specs/STATUS.md` lo mantienen pendiente.
- Que Colab ofrezca una A100 de 80 GB a esta cuenta, y su VRAM libre real. Los 74,5 GiB no son una medición.
- Que `source_snapshot` calculado en Windows coincida con el de Linux. C3 lo comprueba y se detiene si no.
- Bloqueo de Drive entre dos entornos.
- Evaluación congelada de los 4 algoritmos en Colab.
- Si `child.log` trae marcas de tiempo por episodio.
- Si las fechas de archivo se conservan en Drive. `shutil.copytree` las copia, pero no se ha probado sobre Drive. Si no se conservan, usar las de la copia local antes de desconectar.
- Que los commits de los submódulos estén disponibles en la URL de `.gitmodules`.
- `drive_sync_manifest.json` sobre Drive real, con evaluaciones y análisis: solo se ha probado en carpetas locales (D5).
- `pipeline analyze`, `build_campaign_statistical_report.py` y `pipeline select` sobre una campaña real: solo se han probado con KPI sintéticos (D6).
- `--owner-authorized`, `sync_problems`, el pico de VRAM, la copia de C9, los límites de ejecución y la medición en un proceso hijo solo tienen pruebas locales. Ninguno ha corrido en Colab.

## 11. Después del piloto

Con las puertas cumplidas y las horas calculadas, el propietario decide si autoriza `hpo`. Las secciones 3 y 7 traen sus cifras. Cada etapa siguiente sigue la sección 4 y repite C1 a C6 cambiando `STAGE`. Las tareas 8.2 a 8.6 de [implementacion_completa.md](implementacion_completa.md) siguen vigentes, y necesitan su propio detalle cuando el piloto dé datos.

Cada sesión de trabajo deja registrados en [traspaso_sesiones.md](traspaso_sesiones.md): etapa, revisión, nombre y SHA-256 del ZIP, GPU, recursos medidos, tiempos, puertas cumplidas y fallos.
