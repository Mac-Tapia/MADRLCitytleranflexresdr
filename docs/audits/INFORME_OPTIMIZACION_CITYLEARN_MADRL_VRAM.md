# Informe de optimizacion CityLearn MADRL y seguridad VRAM

**Fecha:** 2026-06-12  
**Proyecto:** `MADRLCitytleranflexresdr`  
**Alcance:** CityLearn clonado, 12 entrenamientos MADRL, monitor visible, CUDA/VRAM local RTX 4060 Laptop 8 GB.

## Fuentes revisadas

- CityLearn documentation: https://www.citylearn.net/
- CityLearn GitHub: https://github.com/intelligent-environments-lab/CityLearn
- PyTorch CUDA semantics and memory management: https://docs.pytorch.org/docs/stable/notes/cuda.html
- PyTorch multiprocessing best practices: https://docs.pytorch.org/docs/stable/notes/multiprocessing.html
- Ray RLlib environments and vectorization: https://docs.ray.io/en/latest/rllib/rllib-env.html
- MARLlib paper: https://arxiv.org/abs/2210.13708
- HAPPO/HATRPO paper: https://arxiv.org/abs/2109.11251
- MAAC paper: https://arxiv.org/abs/1810.02912

## Criterio tecnico aplicado

CityLearn no se trata como una dependencia intocable en este proyecto: existe un clon dentro de `CityLearn/` y el usuario autorizo modificarlo. La restriccion importante no es "no tocar CityLearn", sino mantener trazabilidad, reproducibilidad y compatibilidad con el flujo de dataset, entrenamiento, comparacion y resultados.

La campana oficial tiene 12 jobs: 4 algoritmos MADRL por 3 escenarios. No debe confundirse el avance temporal ordenado de un entorno CityLearn con una cola global secuencial. Cada job conserva su episodio, semilla, salida y artefactos; la campana completa puede paralelizar escenarios dentro de la misma etapa de algoritmo.

## Decision implementada

- La ruta operativa normal usa monitor visible con `LiveOutput=false`.
- `LiveOutput=true` queda como modo de depuracion visual rica y secuencial.
- En RTX 4060 Laptop 8 GB, el launcher permite hasta 2 escenarios concurrentes.
- MASAC y MAAC se mantienen en 1 por mayor uso de memoria de replay, critic y atencion.
- Cada proceso Python sigue teniendo su propio entorno CityLearn, modelo, tensores CUDA y artefactos; por eso la seguridad de VRAM se controla con:
  - `cuda_memory_fraction` por proceso;
  - `PYTORCH_CUDA_ALLOC_CONF`;
  - perfiles `local4060_fast` y `local4060`;
  - limite diferenciado para algoritmos pesados;
  - `nvidia-smi` con memoria dedicada, no memoria compartida de Windows.

## Archivos sincronizados

- `CityLearn/scripts/launch_citylearn_v3_official_training.ps1`
- `CityLearn/scripts/launch_citylearn_v3_iquitos_training.ps1`
- `scripts/run_citylearn_v3_full_training_visible.ps1`
- `scripts/training_launcher_window.ps1`
- `scripts/training_resume_window.ps1`
- `CityLearn/configs/citylearn_v3_madrl_training.yaml`
- `CityLearn/configs/citylearn_v3_madrl_training.json`
- `README.md`
- `docs/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md`
- `docs/ARQUITECTURA_OPERATIVA_ENTRENAMIENTO_VISIBLE_CITYLEARN_V3_MADRL.md`
- `docs/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md`
- `docs/workflow_manifest.json`
- `tools/ops/verify_workflow_integrity.py`
- `tools/training/verify_training_optimization.py`

## Politica vigente

```text
Default visible run:
  LiveOutput=false
  ParallelScenarios=true
  MaxConcurrentScenarioJobs=2
  MaxConcurrentHeavyJobs=1

Debug visual run:
  LiveOutput=true
  EffectiveParallelScenarios=false
```

## Riesgo residual

El entrenamiento puede seguir siendo largo porque cada job ejecuta 5 episodios de 8,760 pasos y CityLearn conserva simulacion temporal ordenada. La mejora aplicada elimina el cuello artificial de salida visible que reducia la campana a una sola ejecucion activa, pero no convierte CityLearn en un entorno vectorizado compartido entre escenarios. Esa segunda mejora requeriria una refactorizacion mayor del entorno y de los backends para compartir procesos/modelos y no solo lanzar jobs concurrentes.
