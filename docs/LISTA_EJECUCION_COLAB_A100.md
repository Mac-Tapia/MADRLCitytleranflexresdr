# Lista de ejecucion Colab A100 - madrl_citylearn_v3_tutorial.ipynb

Usar este listado como checklist rapido para ejecutar el notebook:

```text
examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb
```

## 0. Antes de ejecutar

- Abrir el notebook en VS Code.
- Seleccionar kernel `Google Colab`.
- Elegir runtime `A100`.
- Confirmar que se usa la cuenta con Colab Pro/Pro+.

## 1. Verificacion inicial

Ejecutar:

1. `0.verify - Verificar conexion al runtime A100`

Debe mostrar:

```text
GPU: NVIDIA A100
Entorno: Google Colab
CUDA disponible
```

Si no aparece A100, detenerse y cambiar el runtime.

## 2. Celdas opcionales de arquitectura

Estas celdas son solo visuales/documentales. No son obligatorias para entrenar.

```text
0.0 Helper Mermaid
0.1 Diagrama 1
0.2 Diagrama 2
0.3 Diagrama 3
0.4 Diagrama 4
0.5 Diagrama 5
0.6 Diagrama 6
0.7 Diagrama 7
0.8 Diagrama 8
0.9 Diagrama 9
```

Para entrenar rapido, se pueden omitir y pasar a la seccion 1.

## 3. Configuracion obligatoria

Ejecutar en este orden:

```text
1.1  Verificar GPU
1.2  Clonar repositorio con submodulos desde rama validada
1.2b Validar espejo del proyecto Colab antes de entrenar
1.3  Instalar dependencias del proyecto de forma reproducible
1.4  Configurar sys.path, CUDA y smoke imports
1.5  Montar Google Drive para checkpoints y reanudacion
```

Reglas:

- Si `1.1` no detecta A100, detenerse.
- Si `1.2b` falla, no entrenar.
- Si `1.3` pide reiniciar runtime por paquetes binarios cargados, reiniciar y repetir desde `1.1`.
- `1.5` debe montar Drive antes de entrenamiento largo.

## 4. Crear salida de la corrida

Ejecutar:

```text
2.1 Rutas, timestamp y directorio de salida recuperable
```

Copiar y guardar el valor de:

```text
OUTPUT_ROOT
```

Debe tener forma:

```text
/content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/colab_madrl_a100_<timestamp>
```

## 5. Validaciones previas recomendadas

Ejecutar:

```text
3.1 Verificar estructura del dataset
4.1 Crear entorno smoke-test y describir agentes
5.1 Visualizar pesos de recompensa por escenario
```

Debe confirmar:

- 17 agentes/edificios.
- 222 CSV del dataset.
- Escenarios `E1`, `E2`, `E3`.
- Recompensas multiobjetivo correctas.

## 6. Confirmar modo de entrenamiento

Ejecutar:

```text
6.1 Configuracion central de entrenamiento A100
```

Para corrida oficial:

```python
QUICK_TEST = False
EPISODES = 75
EPISODE_STEPS = 8760
```

Para prueba corta:

```python
QUICK_TEST = True
```

## 7. Lanzamiento

Ejecutar:

```text
7.0 Helpers de ejecucion y monitor
7.1 Preflight A100 + dry-run oficial
```

`7.1` debe terminar con:

```text
Dry-run validado: 12 jobs planificados, A100 config lista, outputs aislados en OUTPUT_ROOT.
```

Despues ejecutar:

```text
7.2 Lanzar entrenamiento completo recuperable
```

La celda `7.2` lanza el entrenamiento si:

```python
LAUNCH_FULL_TRAINING = True
```

## 8. Monitoreo

Durante la ejecucion, usar:

```text
7.3 Monitor visible en notebook
7.4 Resumen global de jobs y artefactos
```

Revisar que se creen carpetas:

```text
OUTPUT_ROOT/happo/E1_seed_0/
OUTPUT_ROOT/happo/E2_seed_0/
OUTPUT_ROOT/happo/E3_seed_0/
OUTPUT_ROOT/masac/E1_seed_0/
OUTPUT_ROOT/masac/E2_seed_0/
OUTPUT_ROOT/masac/E3_seed_0/
OUTPUT_ROOT/matd3/E1_seed_0/
OUTPUT_ROOT/matd3/E2_seed_0/
OUTPUT_ROOT/matd3/E3_seed_0/
OUTPUT_ROOT/maac/E1_seed_0/
OUTPUT_ROOT/maac/E2_seed_0/
OUTPUT_ROOT/maac/E3_seed_0/
```

Al final deben existir 12 archivos:

```text
*/data/results.json
```

## 9. Reanudacion si Colab se desconecta

Reconectar a A100 y ejecutar:

```text
0.verify
1.1
1.2
1.2b
1.3
1.4
1.5
```

En `2.1`, colocar el `OUTPUT_ROOT` anterior:

```python
RESUME_OUTPUT_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/colab_madrl_a100_<timestamp>'
```

Luego ejecutar:

```text
2.1
6.1
7.0
7.2
```

El launcher usa `--skip-completed`, asi que no repite jobs completos.

## 10. Analisis final

Cuando terminen las 12 corridas, ejecutar:

```text
8.1 Cargar todos los results.json
8.2 Curvas de convergencia
9.1 Suite de pruebas estadisticas
10  Resumen final de la sesion Colab
```

La corrida queda lista cuando:

- Hay 12 `results.json`.
- Existe `official_full_status.json`.
- Existe `run_context_manifest.json`.
- `8.1`, `8.2`, `9.1` y `10` corren sin errores.
