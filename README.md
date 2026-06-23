# CityLearn v3 MADRL para comunidades inteligentes

Proyecto: **Multi-agente de aprendizaje por refuerzo profundo para gestion coordinada de flexibilidad energetica, emisiones de carbono y eficiencia economica en comunidades inteligentes**.

Este repositorio integra CityLearn v2 como simulador base y agrega una capa experimental CityLearn v3 para entrenar y evaluar algoritmos MADRL bajo Dec-POMDP, CTDE, tres ejes de investigacion y comparacion contra agentes originales CityLearn v2.

> **"v2" y "v3" no son dos paquetes ni dos instalaciones separadas.** Ambos viven dentro del mismo submodulo `CityLearn/` (fork propio) y se instalan con un solo `-e ./CityLearn` (incluido en `requirements.txt`). "v2" es el simulador base (`CityLearn/citylearn/*.py`: fisica, edificios, DERs, EVs, KPIs) y "v3" es la capa adicional en `CityLearn/citylearn/v3/` (Dec-POMDP, CTDE, recompensa multiobjetivo) que se apoya sobre la v2. No existe un segundo `pip install` para "v3".

## Resumen

El proyecto conserva CityLearn v2 como fuente oficial de datos, fisica, edificios, DERs, EVs y KPIs, y agrega una capa CityLearn v3 para:

- Modelar 17 edificios institucionales/comerciales reales de Iquitos + EV por edificio/tipo/concurrencia como comunidad multiagente.
- Exponer un entorno Dec-POMDP con observaciones locales y estado global para CTDE.
- Conectar cuatro backends MADRL oficiales: HAPPO, MASAC, MATD3 y MAAC.
- Ejecutar tres ejes cientificos: flexibilidad energetica, emisiones de CO2 y costos energeticos.
- Guardar artefactos reproducibles: checkpoints, JSON, CSV, figuras, tablas y trazas.
- Comparar CityLearn v3 MADRL contra agentes originales CityLearn v2.
- Aplicar 4 pruebas estadisticas sobre los resultados de entrenamiento MADRL para demostracion de hipotesis de tesis.

## Estado actual

Actualizado: 2026-06-23.

### Cambios aplicados (2026-06-23) — optimizacion 3 niveles de memoria (GPU + SSD + RAM)

Correccion definitiva de OOM (165 GB RAM → 87 GB RAM). Tres niveles de almacenamiento usados optimamente:

| Recurso | Antes | Ahora | Uso real |
|---|---|---|---|
| **RAM sistema** | 165 GB / 167 GB (99% → OOM SIGKILL) | ~87 GB / 167 GB | **52%** |
| **GPU VRAM** | 33 / 80 GiB (41%) | ~37 / 80 GiB | **46%** |
| **SSD local Colab** | 0 GB | ~7 GB | MATD3 buffer |

**MASAC → GPU VRAM (A100 80 GiB):**
- `GpuBackedNdArray`: buffer QMIX pre-allocado en CUDA float32 en lugar de numpy float64 en RAM. 3 jobs × 6.85 GiB = 20.6 GiB GPU; libera 3 × 13.71 GiB = **41 GiB de RAM**.
- Bug corregido: implementacion anterior usaba `from_numpy()` que dejaba el array float64 vivo (PyTorch retenia referencia interna). Fix: `zeros()` + `data[key]=None` antes de alocar GPU + `gc.collect()` — el refcount baja a 0 y Python libera la RAM inmediatamente.
- `preload_batch_device=cuda`: los batches de entrenamiento van directo a CUDA desde el buffer GPU (zero-copy).
- `cuda_fraction=0.22` (17.6 GiB/job): cubre buffer float32 (6.85) + modelo/overhead (0.9).

**MATD3 → SSD local Colab /content/ (≈ 2 GB/s):**
- `DiskBackedNdArray` (numpy.memmap): las arrays de `MlpPolicyBuffer` (obs, share_obs, next_obs, acts, rewards, dones) se copian al SSD local tras el warmup y se liberan de RAM.
- 3 jobs × 2.4 GiB = **7.2 GiB liberades de RAM**. `__getitem__` devuelve numpy normal — transparente para el codigo externo (sin cambios en MARL off-policy).
- Path automatico: `/content/madrl_buf_tmp/matd3_E{n}_s{seed}/` (auto-detecta Colab).
- OS page-cache mantiene paginas calientes en RAM tras el primer acceso → velocidad similar a DRAM en steady-state.

**TF32 en A100 (ya activo via profile `aws`):**
- `torch.backends.cuda.matmul.allow_tf32 = True` + `set_float32_matmul_precision("high")`: 3× mas rapido en operaciones GEMM de la A100. Activo automaticamente para los 4 algoritmos.

**MAAC / HAPPO sin cambios de buffer:**
- MAAC: buffer 300 MB total, usa `np.roll()` interno que crearia nuevos arrays numpy y desharia la migracion.
- HAPPO: on-policy, buffer de 1 episodio (~26 MB), irrelevante.

### Cambios aplicados (2026-06-22) — optimizaciones A100 + two_phase_concurrent

- ✅ **two_phase_concurrent**: nuevo modo de ejecucion — 12 jobs simultaneos (HAPPO+MATD3+MAAC x3 + MASAC x3 al mismo tiempo). Tiempo total: **~54 h** vs ~67 h secuencial. MASAC usa `cuda_fraction=0.18` (14.4 GiB x3 = 43.2 GiB) + ~14 GiB Phase 1 = ~57/80 GiB GPU (71%).
- ✅ **Auto-stop 11.5 h**: celda 7.2 detiene el launcher graciosamente 30 min antes del limite Colab para garantizar que los checkpoints se guarden antes del timeout de 12 h.
- ✅ **MATD3 replay buffer**: corregido de 6 000 (< 1 episodio) a **200 000 pasos** (~22 episodios de experiencia diversa). Batch aumentado de 512 → **2 048**.
- ✅ **MASAC critic_batch**: aumentado de 64 → **256**; `preload_batch_device=cpu` en modo concurrent para evitar OOM.
- ✅ **MAAC buffer**: aumentado de 100 000 → **200 000** pasos.
- ✅ **Torch threads 1**: en modo concurrent (12 jobs / 12 vCPU) el launcher parchea todos los jobs a `--torch-threads 1` para evitar contienda.
- ✅ **Live progress 300**: reducido de 1 000 → 300 pasos (~150 s a 2 FPS concurrent) para monitor actualizado cada ~2.5 min.
- ✅ **Artifact profile full**: `efficient` → `full`; guarda results.json + timeseries.csv + trace.csv + checkpoints.
- ✅ **HAPPO hidden 512**: confirmado (no se reversa a 384); SubprocVecEnv x4 operativo.
- ✅ **Validador actualizado**: `validate_training_system.py` acepta `two_phase_concurrent` como modo valido.

### Cambios aplicados (2026-06-21) — corrida Colab A100 en curso (paralelo 12 jobs)

- ✅ **HAPPO SubprocVecEnv x4**: `ShareDummyVecEnv` (secuencial, ~4 FPS) reemplazado por `ShareSubprocVecEnv` con `--happo-n-rollout-threads 4` — cada escenario corre 4 subprocesos paralelos de CityLearn, bypasando el GIL. FPS efectivo: ~11 × 4 = **~44 FPS** → HAPPO pasa de ~30 h a **~2.8 h**.
- ✅ **HAPPO hidden-size 512**: revertido de 1024 (era 4× mas lento) a 512 — objetivo ~11 FPS base por hilo.
- ✅ **Bug argparse eliminado**: `--happo-n-rollout-threads` tenia definicion duplicada (default=1 + default=4) en el launcher; ahora queda solo `default=4`.
- ✅ **MASAC/MATD3/MAAC sin cambios (correcto)**: algoritmos off-policy son GPU-bound; `num_envs=1` y `n_rollout_threads=1` son correctos. No requieren SubprocVecEnv.
- ✅ **Drive path aplanado**: eliminados 2 niveles extra (`MADRL_CityLearn_v3/MADRLCitytleranflexresdr/`). Nuevo path: `MyDrive/MADRLCitytleranflexresdr/outputs/` — espejo exacto de la estructura local.
- ✅ **Auditoria completa del notebook**: verificados todos los valores criticos (N_EPISODES=50, QUICK_TEST=False, parallel-scenarios=3, hidden-sizes, buffers, steps-per-update) contra valores prohibidos; cero residuos antiguos.
- ✅ **platformdirs re-añadido a BASE_DEPS** (celda 1.3): `platformdirs>=3.0` habia sido eliminado accidentalmente por el autosave de Colab en commits intermedios; restaurado en BASE_DEPS y añadido como instalacion explicita post-lote para garantizar que `pip 21.3.1` no lo omita silenciosamente.
- ✅ **Stdout garantizado celda 7.2**: `subprocess.Popen(stdout=None)` reemplazado por `PIPE + dos reader threads` (`_pipe_to_cell`) que hacen `sys.stdout.write(line)` explicito — garantiza que los prints del launcher (START/DONE/monitor) lleguen a la celda Colab independientemente del routing de fd1 en la sesion.
- ✅ **Monitor celda 7.2 capture_output**: llamada externa al monitor cada 60 s ahora usa `capture_output=True` + `sys.stdout.write(_mr.stdout)` explicito.
- ✅ **Monitor todos los jobs en paralelo** (`colab_a100_live_monitor.py`): `print_progress` ahora itera sobre **todos** los jobs activos simultaneamente (HAPPO/E1, E2, E3 en paralelo) en vez de solo el primero — cada bloque muestra episodio, paso_ep, paso_global, pesos OE1/OE2/OE3, rewards y heartbeat. `print_logs` muestra los logs de todos los jobs en ejecucion simultanea (con lineas reducidas por job para evitar exceso de output).
- ✅ **Paralelismo real 12 jobs simultáneos** (`colab_a100_official_launcher.py`): `--max-parallel 12` (default) lanza los 12 jobs (HAPPO, MASAC, MATD3, MAAC) x (E1, E2, E3) con `ThreadPoolExecutor(max_workers=12)`. Monitor espera ver: `E1: happo:running | masac:running | matd3:running | maac:running` para los 3 escenarios. OOM retry, skip-completed y lock de escritura en `official_full_status.json` preservados. `--max-parallel 1` restaura modo secuencial.
- ✅ **Validacion de sintaxis + badge Colab** (`scripts/validate_notebook_syntax.py`): valida newlines literales, `ast.parse()` por celda y URL del badge Open-in-Colab apuntando a `citylearn-v3-madrl`.
- ✅ **Push integrado** (`scripts/push.py`): un solo comando valida + push CityLearn a `mac-tapia/citylearn-v3-madrl` + bump padre + push padre — el badge siempre refleja el ultimo commit.

### Cambios actualizados (2026-06-20)

- ✅ Corrida v4 completada 12/12 — HAPPO/MASAC/MATD3/MAAC × E1/E2/E3
- ✅ Artefactos canonicos en `outputs/{ALGO}/{escenario}/` (CSV, JSON, PNG)
- ✅ Informe tecnico de supervision: **APROBADO** — Mejor MADRL: **MATD3** (KW p=0.0459)
- ✅ Tutorial notebook actualizado a **NVIDIA A100-SXM4-80GB + 167 GiB RAM** (eliminadas todas las referencias RTX 4060 como entorno objetivo)
- ✅ Launcher `colab_a100_official_launcher.py`: `--parallel-scenarios 3`, hyperparams A100-80GB, MASAC buffer CPU (3x40 GiB = 120 GiB RAM)
- ✅ 9 submodulos registrados e inicializados en `.gitmodules`
- ✅ Git LFS configurado para checkpoints `.pt` — resultados versionados en GitHub

### Corrida oficial activa — Google Colab A100-SXM4-80GB

| Campo | Valor |
| ----- | ----- |
| Hardware | NVIDIA A100-SXM4-80GB · 80 GiB VRAM · 167 GiB RAM · SSD 235 GB · CUDA 12.6 · PyTorch 2.8.0+cu126 |
| Episodios | 50 x 8760 pasos = 438 000 pasos/corrida |
| Modo ejecucion | `two_phase_concurrent` — 12 jobs en paralelo (HAPPO+MATD3+MAAC x3 + MASAC x3 simultaneos) |
| Paralelismo | **12 jobs simultáneos** · RAM: ~87/167 GiB (52%) · GPU: ~37/80 GiB (46%) · SSD: ~7 GB |
| HAPPO hidden | [512, 512] · `--happo-n-rollout-threads 4` (SubprocVecEnv) |
| HAPPO rollout | `ShareSubprocVecEnv` — 4 procesos paralelos por escenario, ~44 FPS efectivo |
| MASAC | off-policy GPU-bound · critic_batch 256 · **buffer GPU VRAM** (`GpuBackedNdArray` float32, 6.85 GiB/job) · `preload=cuda` · cuda_frac 0.22 |
| MATD3 | off-policy GPU-bound · hidden 1024 · buffer **200 000** steps · batch **2 048** · **buffer SSD** (`DiskBackedNdArray` memmap, 2.4 GiB/job) |
| MAAC | off-policy GPU-bound · hidden 1024 · buffer **50 000** · steps-per-update 1 |
| GPU profile | `aws` (TF32 habilitado: `allow_tf32=True`, `matmul_precision=high`) |
| Tiempo estimado | **~54 h** (two_phase_concurrent) vs ~67 h two_phase secuencial |
| Drive outputs | `MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_TIMESTAMP/` |
| Notebook Colab | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (celda 42 = resume) |
| Reiniciar entrenamiento | Ejecutar celda 42 del notebook — actualiza git, valida, relanza con `--skip-completed` |

### Corridas de referencia y definitiva

| Corrida | Sesion | Estado | Descripcion |
| ------- | ------ | ------ | ----------- |
| **v3 referencia** | `citylearn_v3_madrl_full_20260613_010234` | COMPLETADA 12/12 | Perfiles `*_unified_comparable_v3`, todas las 12 corridas con artefactos validos |
| **v4 definitivo** | `citylearn_v3_madrl_full_20260615_074011_v4` | COMPLETADA 12/12 | Penalidad BESS degradacion (LiFePO4 C-rate/Arrhenius) + urgencia EV (SOC); artefactos canónicos reparados y sin duplicados raíz |

### Estado v4 definitivo (corrida activa)

| Algoritmo | E1 | E2 | E3 |
| --------- | -- | -- | -- |
| **HAPPO** | Completado | Completado | Completado |
| **MASAC** | Completado | Completado | Completado |
| **MATD3** | Completado | Completado | Completado |
| **MAAC** | Completado | Completado | Completado |

La corrida v4 finalizó el 2026-06-16 22:44:19 con `official_full_status.json: completed` y 12 jobs con `exit_code=0`. El monitor fue corregido para cerrar automáticamente al detectar `completed` salvo uso explícito de `-KeepOpenOnComplete`.

### Resultados v4 regenerados y comparados

Artefactos actualizados desde los checkpoints de `outputs/citylearn_v3_madrl_full_20260615_074011_v4`:

- Evidencia estadistica: `outputs/thesis_objective_evidence/madrl_checkpoint_stats_v4`.
- Figuras canonicas de entrenamiento regeneradas: 156 PNG bajo `*/figures/` (12 corridas x 13 figuras).
- Tablas canonicas regeneradas: 144 CSV bajo `*/figures/tables/` (12 corridas x 12 CSV; cada carpeta conserva tambien sus pares Markdown).
- Figuras comparativas regeneradas: 12 PNG bajo `outputs/comparison_citylearn_v2_vs_v3_madrl/E1..E3`.
- PNG internos antiguos de MASAC bajo `data/backend_results/` eliminados; quedan 0 PNG fuera de `figures/`.

Resumen descriptivo e inferencial:

| Alcance | Mejor por mediana de gain relativo | Kruskal-Wallis p | Significativo 0.05 | Nota |
| ------- | ---------------------------------- | ---------------: | ------------------ | ---- |
| OE1 flexibilidad | MATD3 | 0.4450 | No | Sin diferencia global significativa por eje |
| OE2 CO2 | MASAC | 0.1655 | No | Sin diferencia global significativa por eje |
| OE3 costos | MAAC | 0.0774 | No | Tendencia, pero no significativa a 0.05 |
| ALL global | MATD3 | 0.0459 | Si | Diferencia global significativa entre agentes |

El mejor agente global de la corrida v4 es **MATD3**. Tambien gana el ranking ponderado global en las tres comparativas por escenario: E1 score 0.7486, E2 score 0.7515 y E3 score 0.7333. La comparacion inferencial global detecta diferencia significativa (`Kruskal-Wallis p=0.0459`) y las comparaciones contra HAPPO favorecen a MATD3 (`MWU p=0.0182`, `Wilcoxon p=2.62e-06`). Los warnings esperados de Wilcoxon por muestras pequeñas/ceros quedan suprimidos y documentados en `wilcoxon_status`.

### Tiempos reales corrida v3 (referencia historica — RTX 4060 Laptop 5 ep piloto)

| Algoritmo | E1 (flex) | E2 (CO2) | E3 (costo) | Total |
| --------- | --------: | -------: | ---------: | ----: |
| HAPPO | 66.50 min | 66.15 min | 57.75 min | 190.4 min |
| MASAC | 125.88 min | 148.33 min | 135.72 min | 409.9 min |
| MATD3 | 95.13 min | 95.30 min | 80.70 min | 271.1 min |
| MAAC | 52.33 min | 51.74 min | 54.16 min | 158.2 min |

Hardware (referencia v4 piloto): RTX 4060 Laptop 8 GiB VRAM, CUDA 12.6. Corrida oficial: NVIDIA A100-SXM4-80GB 80 GiB VRAM, 167 GiB RAM, CUDA 12.4 (Colab).

### Tiempos estimados corrida oficial A100-SXM4-80GB (50 ep, --parallel-scenarios 3)

| Algoritmo | Tipo | FPS base | x rollout | FPS efectivo | Tiempo 3 esc. | Nota |
| --------- | ---- | -------: | --------: | -----------: | ------------: | ---- |
| HAPPO | on-policy | ~11 FPS | x4 SubprocVecEnv | **~44 FPS** | **~2.8 h** | CPU-bound resuelto; hidden 512 |
| MASAC | off-policy | ~15-30 FPS | x1 (GPU-bound) | ~15-30 FPS | ~8-16 h | Buffer 40 ep CPU; GPU critico |
| MATD3 | off-policy | ~20-50 FPS | x1 (GPU-bound) | ~20-50 FPS | ~5-12 h | GPU-intensivo; A100 >> RTX 4060 |
| MAAC | off-policy | ~20-40 FPS | x1 (GPU-bound) | ~20-40 FPS | ~6-12 h | Attention SAC; GPU-bound |
| **Total** | | | | | **~54 h** (concurrent) | two_phase_concurrent — todos simultáneos |

HAPPO era el cuello de botella (~30 h con DummyVecEnv secuencial). Con `ShareSubprocVecEnv` x4 el tiempo HAPPO se reduce a ~2.8 h. Los algoritmos off-policy (MASAC/MATD3/MAAC) son GPU-bound y no requieren cambios de VecEnv.

FPS limitado principalmente por simulacion Python de 17 edificios. A100 acelera GPU training (MATD3 2 FPS -> 8 FPS) pero el simulador CityLearn es el cuello de botella dominante en HAPPO.

### Cambios aplicados en v3 y v4

**v3 (corrida de referencia) — desde 2026-06-14:**

- **Bug SOC corregido**: penalidad de salida EV tenia signo invertido en v2 (`+25` en lugar de `-25`); en v3 es `-abs(25)*mult` (agente ya no aprende a NO cargar EVs).
- **ev_weight**: 0.12 → **0.25** (mayor peso al cumplimiento EV).
- **`_ev_service_constraint_term()`**: nueva restriccion de urgencia por salida — penaliza en proporcion al deficit de SOC y horas restantes.
- **V2G habilitado**: 31 tomas de camioneta con `bidirectional_v2g`, `max_discharging_power=7.4 kW`.
- Submodulo CityLearn commits: `afb68187` (reward fix) + `acc0ada6` (V2G schema).

**v4 (corrida definitiva) — desde 2026-06-15:**

- **Penalidad degradacion BESS**: modelo LiFePO4 con ciclo Arrhenius. Penaliza C-rate alto durante carga/descarga de la bateria; incentiva ciclos suaves para prolongar vida util.
- **Urgencia EV por SOC**: penalizacion proporcional al deficit de carga cuando el EV esta proximo a la hora de salida. Fuerza priorizacion de carga en ventana horaria restante.
- Perfil activo: `*_unified_comparable_v4` con los mismos pesos de escenario que v3.

### Configuracion fija

- Dataset activo: `citylearn_iquitos_2023_2025` (17 edificios reales de Iquitos, 2023-2025, 222 CSV activos auditados, 185 tomas EV Mode 3, 96 equipos fisicos doble toma, 1,850 EV en pool y 17 maquinas controladas).
- EV/V2G validado: las 31 tomas de camioneta institucional/logistica son bidireccionales (`max_discharging_power=7.4 kW`, `power_flow_direction=bidirectional_v2g`); moto lineal y mototaxi quedan solo carga.
- Entorno unico: `.venv39-citylearn-v3` (Python 3.9.25, CityLearn editable, torch 2.8.0+cu126, ray 1.8.0, gymnasium 0.28.1).
- Recompensa activa: `CityLearnV3MADRLRewardFunction`, perfiles **`*_unified_comparable_v3`**: team_ratio=0.70, peak_weight=0.45, ramp_weight=0.35, ev_weight=0.25, reward_scale=1.00. Pesos por escenario: E1=[0.70,0.15,0.15], E2=[0.15,0.70,0.15], E3=[0.25,0.15,0.60].
- Horizonte oficial ajustado para nuevas ejecuciones A100: 50 episodios x 8760 pasos = 438 000 pasos/corrida. 12 corridas totales (4 algoritmos x 3 escenarios).
- Resultados finales aceptados: solo cuando existan `data/results.json`, `data/timeseries.csv`, `data/trace.csv`, `data/training_summary.json`, `data/checkpoint_manifest.json`, `data/artifact_audit.json` y `figures/figures_manifest.json` por algoritmo/escenario.
- Contrato de trazabilidad: `data/` es la fuente canónica por corrida; no se escriben espejos raíz ni `statistical_comparison/` salvo flags heredados explícitos. `live_progress.json` es transitorio y se elimina al finalizar correctamente.
- Cooperacion CTDE: critico centralizado ve estado global s=[o1,...,o17] durante entrenamiento; ejecucion descentralizada. team_reward=mean(rewards_i); mixed_reward_i=0.30*reward_i+0.70*team_reward.
- Perfil GPU Colab (oficial): `aws` — A100-SXM4-80GB 80 GiB VRAM, 3 escenarios concurrentes por algoritmo (`--parallel-scenarios 3`). Perfil local de referencia: `local4060_fast` (RTX 4060 8 GiB, 1-2 escenarios).
- Validacion cooperativa CTDE: `passed` para 4 MADRL x 3 ejes; `python39_core_ready=true`.
- Suite de pruebas estadisticas: Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U y Wilcoxon signed-rank.

## Ejes del proyecto

| Eje | Escenario | Objetivo | KPIs principales |
| --- | --------- | -------- | ---------------- |
| OE1 | E1 | Flexibilidad energetica: desplazar cargas y aprovechar almacenamiento, EVs y autoconsumo. | `peak_average`, `ramping_average`, `one_minus_load_factor_average`, KPIs PV/bateria/EV. |
| OE2 | E2 | Emisiones de CO2: reducir huella ambiental y evitar importacion en horas de alta intensidad de carbono. | `carbon_emissions`, `carbon_emissions_control`, `carbon_emissions_baseline`, `carbon_emissions_delta`. |
| OE3 | E3 | Costos energeticos: optimizar gasto, reducir picos y aprovechar tarifas dinamicas. | `electricity_cost`, `electricity_cost_delta`, `price_signal_deviation`, KPIs de costo pico/rampa. |

## Arquitectura real implementada

Flujo principal:

```text
Dataset citylearn_iquitos_2023_2025 (17 edificios Iquitos, 2023-2025)
  -> CityLearn v2 base (simulador)
  -> Capa CityLearn v3 (Dec-POMDP, CTDE, recompensa multiobjetivo)
  -> UC3MEnv wrapper (BACTTensor 29D, RewardAxes 7D, HPHI)
  -> 4 MADRL: HAPPO, MASAC, MATD3, MAAC
  -> Launcher oficial -Scenario ALL
  -> Artefactos por algoritmo/eje/seed
  -> generate_thesis_objective_evidence.py
  -> 4 pruebas estadisticas (SW, KW, MWU, Wilcoxon SR)
  -> Benchmark CityLearn v2
  -> Comparador CityLearn v2 vs CityLearn v3
  -> Resultados para tesis
```

Contrato operativo actualizado: `docs/architecture/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md` y `docs/workflow_manifest.json`.

Componentes principales:

| Componente | Ruta |
| ---------- | ---- |
| Simulador base | `CityLearn/` |
| Capa CityLearn v3 | `CityLearn/citylearn/v3/` |
| Framework UC3M | `uc3m/` |
| Adaptador comun MADRL | `CityLearn/scripts/citylearn_v3_training_common.py` |
| Entrenadores MADRL | `CityLearn/scripts/train_citylearn_v3_*.py` |
| Launcher oficial (Iquitos) | `CityLearn/scripts/launch_citylearn_v3_iquitos_training.ps1` |
| Monitor vivo (Iquitos) | `CityLearn/scripts/monitor_citylearn_v3_iquitos_training.ps1` |
| Launcher oficial (general) | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` |
| Evidencia estadistica tesis | `CityLearn/scripts/generate_thesis_objective_evidence.py` |
| Benchmark v2 | `CityLearn/scripts/benchmark_citylearn_v2_agents.py` |
| Comparador v2 vs v3 | `CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py` |
| Dataset Iquitos | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` |
| Herramientas de dataset | `tools/` |
| Suite de tests | `tests/uc3m/` |

## Framework UC3M (Universal CityLearn v3 Modified)

El paquete `uc3m/` es un framework universal reutilizable sobre CityLearn v2 que implementa el Meta-Dec-POMDP para N edificios arbitrarios.

| Modulo | Ruta | Descripcion |
| ------ | ---- | ----------- |
| `UC3MEnv` | `uc3m/env/uc3m_env.py` | Wrapper universal Dec-POMDP 11-aria; compatible con HARL, MARLlib y RLlib |
| `BACTTensor` | `uc3m/env/bact.py` | Contexto fijo por edificio: 29D = clima (7) + geografico (8) + fisico (14) |
| `RewardAxes` | `uc3m/reward/axes.py` | 7 ejes de recompensa con pesos lambda: CO2, costo, flexibilidad, confort, degradacion BESS, resiliencia, ACS |
| `HPHI` | `uc3m/reward/hphi.py` | Holistic Pareto Hypervolume Index 7D para comparacion integrada de algoritmos |
| `KPIEvaluator` | `uc3m/kpis/evaluator.py` | Calculo holistico de KPIs normalizados contra baseline RBC |
| `AlgorithmFactory` | `uc3m/algorithms/factory.py` | Mapeo centralizado de 4 MADRL a sus backends externos |

Instalar todas las dependencias del proyecto (un solo comando, ver `docs/MANUAL_INSTALACION_DEPENDENCIAS.md`):

```bash
pip install -r requirements.txt
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Ejecutar tests:

```bash
pytest tests/ -q --tb=short
```

## Dataset Iquitos 2023-2025

| Caracteristica | Detalle |
| -------------- | ------- |
| Edificios | 17 institucionales/comerciales reales de Iquitos, Peru |
| Nombres reales | Municipalidad San Juan Bautista, Aeropuerto, Tottus, Hotel Plaza, Mall Aventura, UNAP, PNP, COER, GRL, Hospital Regional, EsSalud, UNAP Economia, Autoridad Portuaria, DREL Colegio, SIMA Iquitos, Selva Amazonica Lab |
| Rango temporal | 2023-2025 (26,304 pasos horarios) |
| Cargadores EV | 185 archivos `charger_X_Y.csv`, 96 equipos fisicos modo 3 doble toma, 1,850 EV en pool, 749.4 kW instalados |
| V2G EV | 31 tomas de camioneta con control bidireccional; 0 tomas no-camioneta con descarga |
| BESS | 138-6,747 kWh por edificio; total 26,266 kWh / 6,648 kW |
| Generacion solar PV | 274.1-10,236.1 kWp DC por edificio; total 48,790.9 kWp |
| Sistema de AC | Por tipo: Chiller agua (B03/B11), Multi-Chiller (B06), Precision AC (B01/B09), Ultra-Freezers -80C (B17) |
| Factor CO2 | 0.671-0.790 kgCO2/kWh (MINAM RAGEI 2019, diesel ELECTRO ORIENTE) |
| Tarifas | Punta 18-22h: $0.38/kWh; Fuera punta: $0.26/kWh (Electro Oriente 2024) |
| Grilla | Sistema aislado diesel ELECTRO ORIENTE + penetracion solar 15% |
| Archivo central | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` |

### Edificios del dataset

| ID | Nombre real | Tipo auditado | Area m2 | kWp PV | BESS kWh | BESS kW | EV tomas | EV kW |
| -- | ----------- | ------------- | ------: | -----: | -------: | ------: | -------: | ----: |
| B01 | ELECTRO ORIENTE S.A. | Office | 14,000 | 3,360.2 | 6,747 | 1,609 | 4 | 21.8 |
| B02 | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | Office | 8,000 | 1,920.0 | 244 | 50 | 6 | 24.4 |
| B03 | AEROPUERTO INTERNACIONAL | Assembly | 6,000 | 1,440.2 | 2,363 | 511 | 8 | 37.8 |
| B04 | HIPERMERCADOS TOTTUS ORIENTE SAC | Retail | 2,500 | 600.2 | 454 | 409 | 6 | 24.4 |
| B05 | HOTEL PLAZA S.A. | MultiFamily_Hotel | 1,142 | 274.1 | 234 | 124 | 3 | 14.4 |
| B06 | MALL AVENTURA S.A. | Commercial_Mall | 20,637 | 4,952.9 | 2,541 | 835 | 32 | 119.6 |
| B07 | UNAP-FACULTAD DE BIOLOGIA-AULAS | Education | 8,103 | 1,944.9 | 984 | 240 | 42 | 153.2 |
| B08 | PNP- ESCUELA TECNICA SUPERIOR-IQUITOS | Assembly_Military | 21,000 | 5,040.2 | 601 | 129 | 17 | 73.6 |
| B09 | GOBIERNO REGIONAL DE LORETO - COER | Office_Critical | 4,480 | 1,075.3 | 138 | 30 | 10 | 37.4 |
| B10 | GOBIERNO REGIONAL DE LORETO | Office | 14,296 | 3,431.1 | 2,353 | 591 | 6 | 36.6 |
| B11 | HOSPITAL REGIONAL DE LORETO | Healthcare_Hospital | 42,649 | 10,236.1 | 1,901 | 424 | 3 | 14.4 |
| B12 | SEGURO SOCIAL DE SALUD - ESSALUD | Healthcare | 18,197 | 4,367.5 | 4,346 | 960 | 3 | 14.4 |
| B13 | UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO | Education | 2,723 | 653.8 | 272 | 69 | 11 | 41.4 |
| B14 | AUTORIDAD PORTUARIA NACIONAL | Industrial_Port | 17,761 | 4,262.9 | 229 | 48 | 4 | 21.8 |
| B15 | DREL- COLEGIO NACIONAL DE IQUITOS | Education | 9,890 | 2,373.8 | 500 | 104 | 8 | 31.4 |
| B16 | SIMA - IQUITOS S.R.LTDA | Industrial | 10,294 | 2,470.8 | 1,622 | 357 | 11 | 41.4 |
| B17 | ASOCIACION CIVIL SELVA AMAZONICA | Laboratory | 1,611 | 386.9 | 737 | 158 | 11 | 41.4 |

### Destilacion desde `buildingcsv`

Los insumos reales estan en `CityLearn/data/buildingcsv/`:

- `building.csv`: nombres oficiales, areas techadas exactas, tipos de uso CityLearn, sistemas de refrigeracion, unidades split estimadas y vehiculos predominantes por edificio.
- `B_02.csv` a `B_17.csv`: mediciones mensuales reales de facturas electricas (kWh punta/fuera punta, total facturado, tarifa).
- `Building_1.csv` sintetico porque no existe `B_01.csv` en buildingcsv.

La destilacion aplica: `NSL_residual = E_medido_mes - cooling_demand/COP - dhw_demand/COP`. Balance mensual garantizado con delta < 0.1%. Meses faltantes pronosticados con `calendar_month_mean_overlap_scaled`.

Documentacion completa del pipeline: `docs/architecture/dataset_construction_pipeline.md`.

Regenerar el dataset desde los insumos:

```powershell
# 1. Generar CSV (usa cache meteorologico, no re-descarga)
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/generate_iquitos_dataset.py --verbose

# 2. Destilar cargas reales B02-B17
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/distill_building_loads.py `
    --buildingcsv-dir CityLearn/data/buildingcsv `
    --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025

# 3. Fix safety factor cooling autosize
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/fix_schema_cooling.py

# 4. Diagnostico de integridad
.\.venv39-citylearn-v3\Scripts\python.exe -B diagnostico_dataset.py
```

## MADRL integrados

| MADRL | Script activo | Wrapper CityLearn v3 | Backend (submodulo) |
| ----- | ------------- | -------------------- | ------------------- |
| HAPPO | `train_citylearn_v3_happo.py` | `CityLearnHARLEnv` | `external/HARL` |
| MASAC | `train_citylearn_v3_masac.py` | `CityLearnSMACDiscreteEnv` | `external/MARL` + `external/MARLlib` |
| MATD3 | `train_citylearn_v3_matd3.py` | `CityLearnOffPolicyVecEnv` | `external/MATD3implementation` |
| MAAC | `train_citylearn_v3_maac.py` | `CityLearnMAACVecEnv` | `external/MAAC` |

Submodulos de referencia adicionales:

| Submodulo | Ruta | Proposito |
| --------- | ---- | --------- |
| MicroGrids | `external/MicroGrids` | Modelos de microgrillas (referencia) |
| evcc | `external/evcc` | Gestor de carga EV open-source (referencia) |
| prosumpy | `external/prosumpy` | Gestion de prosumidores energia (referencia) |

## Recompensa

Los cuatro MADRL usan `CityLearnV3MADRLRewardFunction`. La recompensa combina pesos por eje y perfil por algoritmo.

**Perfiles v3 (corrida referencia):**

- Perfiles: `happo_unified_comparable_v3`, `masac_unified_comparable_v3`, `matd3_unified_comparable_v3`, `maac_unified_comparable_v3`.
- Parametros comunes: `team_ratio=0.70`, `peak_weight=0.45`, `ramp_weight=0.35`, `ev_weight=0.25`, `reward_scale=1.00`.
- EV/SOC: penalizacion de deficit de SOC a la salida + restriccion de servicio EV.

**Perfiles v4 (corrida definitiva) — extensiones sobre v3:**

- **Penalidad BESS**: modelo Arrhenius LiFePO4. Penaliza C-rate alto (carga/descarga intensa) para reducir degradacion ciclica de la bateria.
- **Urgencia EV**: penalizacion proporcional al deficit `(SOC_obj - SOC_actual)` ponderada por `1/horas_restantes`. Fuerza carga prioritaria cuando el EV sale en las proximas horas.
- Perfiles: `happo_unified_comparable_v4`, `masac_unified_comparable_v4`, `matd3_unified_comparable_v4`, `maac_unified_comparable_v4`.

| Escenario | flex | carbon | cost |
| --------- | ---: | -----: | ---: |
| E1 | 0.70 | 0.15 | 0.15 |
| E2 | 0.15 | 0.70 | 0.15 |
| E3 | 0.25 | 0.15 | 0.60 |

## Contrato cooperativo Dec-POMDP/CTDE

- **Cada edificio es un agente** con su propia politica πᵢ(aᵢ|oᵢ) — red neuronal que mapea observacion local a accion local (BESS, EV, lavadora).
- **MADRL** es el framework que entrena las 17 politicas simultáneamente con mecanismos de coordinacion (critico centralizado, team_reward, QMIX/atencion, actualizacion secuencial HAPPO).
- El estado global CTDE `s=[o₁,...,o₁₇]` (17 observaciones concatenadas) es accesible solo por el critico durante entrenamiento — nunca en ejecucion.
- `team_reward = mean(reward_i)` — señal colectiva distrital; `mixed_reward_i = 0.30*reward_i + 0.70*team_reward`.
- Control distrital es **emergente**: no hay agente distrital, el comportamiento coordinado surge de las 17 politicas aprendidas actuando en el mismo entorno fisico.
- La ejecucion permanece completamente descentralizada: cada politica actua solo con oᵢ local, sin comunicacion entre edificios.
- Documentacion completa: `docs/architecture/COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.md`.

Validar el contrato:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\validate_citylearn_v3_cooperative_ctde.py `
  --output outputs\validation\cooperative_ctde_validation.json
```

## Pruebas estadisticas de demostracion de hipotesis

Los 4 tests se aplican sobre los **KPI-gains de entrenamiento de los 4 MADRL** (HAPPO, MASAC, MATD3, MAAC) por cada eje OE1/OE2/OE3. Cada test tiene su propia funcion, CSV de salida y seccion de p-valor en `hipotesis_estadisticas_madrl.csv`.

| Test | Funcion | CSV de salida | Tipo de muestra | Hipotesis H0 |
| ---- | ------- | ------------- | --------------- | ------------ |
| **Shapiro-Wilk** | `statistical_omnibus_rows()` | `analisis_estadistico_madrl.csv` | Por grupo (1 algoritmo) | Los KPI-gains de ALGO siguen distribucion normal |
| **Kruskal-Wallis** | `statistical_omnibus_rows()` | `analisis_estadistico_madrl.csv` | 4 grupos simultaneos | Las distribuciones de HAPPO, MASAC, MATD3 y MAAC son identicas |
| **Mann-Whitney U** | `mann_whitney_pairwise_rows()` | `comparaciones_mwu_madrl.csv` | Muestras **independientes** | La distribucion de KPI-gains de A es igual a la de B |
| **Wilcoxon SR** | `wilcoxon_pairwise_rows()` | `comparaciones_wilcoxon_madrl.csv` | Muestras **pareadas** (mismo KPI/edificio) | La mediana de diferencias d_i = A_i - B_i es cero |

**Flujo de demostracion:**

1. Shapiro-Wilk verifica si los datos son normales por grupo; si alguno rechaza normalidad, justifica los tests no parametricos.
2. Kruskal-Wallis detecta si hay diferencias globales entre los 4 MADRL en el eje.
3. Mann-Whitney U identifica que par especifico difiere (muestras independientes).
4. Wilcoxon signed-rank confirma diferencias sistematicas pareadas (mismo KPI, dos algoritmos).

Todos los resultados se consolidan en `hipotesis_estadisticas_madrl.csv` con columnas `SW_*`, `KW_*`, `MWU_*` y `WC_*` por eje y por algoritmo.

## Evidencia para plan e informe de tesis

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\generate_thesis_objective_evidence.py
```

Salida principal en `outputs/thesis_objective_evidence/`:

```text
Resumen_ejecutivo.csv
objetivos_especificos_cumplimiento.csv
Matriz_KPIs.csv / KPIs_y_metricas.csv
matriz_resultados_madrl.csv
matriz_baseline_por_eje.csv
scores_kpi_algoritmo_madrl.csv
analisis_estadistico_madrl.csv          <- Shapiro-Wilk + Kruskal-Wallis
comparaciones_mwu_madrl.csv             <- Mann-Whitney U (independiente) + tamanos de efecto
comparaciones_wilcoxon_madrl.csv        <- Wilcoxon signed-rank (pareado)
hipotesis_estadisticas_madrl.csv        <- 4 tests unificados por eje
matriz_operacionalizacion_variables.csv
Marco_metodologico_MADRL.csv
matriz_consistencia_objetivos.csv
Backends_MADRL.csv / MARLlib_Integracion.csv
CityLearn_v3_Propuesto.csv
Arquitectura_Propuesta.csv
Aplicabilidad_SEAI_Iquitos.csv
CityLearn_CO2_Costos.csv
Datasets_y_codigo.csv
thesis_skill_feed.json
resumen_evidencia_tesis.md
```

Ademas de los 4 tests no parametricos, `comparaciones_mwu_madrl.csv` incluye tamanos de efecto para cada par MADRL: Cliff's delta, Vargha-Delaney A12, Cohen d, Hedges g y bootstrap CI 95%.

## Validacion previa al entrenamiento

Antes de lanzar una corrida larga, ejecutar solo verificaciones:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py `
  --strict `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\run_citylearn_v3_env_smoke.py `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1 `
  --episode-time-steps 4 `
  --steps 3

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\verify_workflow_integrity.py `
  --manifest-out outputs\dataset_audit\workflow_integrity_manifest.json
```

Validacion actual:

- `python39_core_ready=true` con schema Iquitos.
- `pytest tests/uc3m -q -ra`: OK, con 3 skips existentes.
- `git diff --check`: OK.
- No hay procesos de entrenamiento ni manifiestos `status: running` despues de la limpieza.

## Entrenamiento oficial local

Opcion rapida — doble clic o desde PowerShell:

```powershell
# Genera timestamp automatico, registra outputs\latest_visible_training_output_root.txt
# y lanza cadena completa
.\relanzar_entrenamiento_madrl.bat
```

Comando completo manual (requiere PowerShell 7 — `pwsh.exe`):

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\run_citylearn_v3_full_training_visible.ps1 `
  -OutputRoot $root `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 50 `
  -TorchThreads 8 `
  -LiveProgressInterval 1000 `
  -ArtifactProfile efficient `
  -TraceRecordInterval 10 `
  -TraceDetail compact `
  -GpuProfile local4060_fast `
  -Cuda
```

Para continuar una corrida interrumpida sin reejecutar lo ya completado:

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\run_citylearn_v3_full_training_visible.ps1 `
  -OutputRoot $root -Scenario ALL -Seed 0 `
  -EpisodeTimeSteps 8760 -Episodes 50 -TorchThreads 8 `
  -LiveProgressInterval 1000 -ArtifactProfile efficient `
  -TraceRecordInterval 10 -TraceDetail compact `
  -GpuProfile local4060_fast -Cuda -SkipCompleted
```

Antes del comando manual:

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8
```

Esto genera 12 corridas (4 algoritmos x 3 ejes) con etapas por algoritmo. En 8 GB, HAPPO y MATD3 pueden ejecutar hasta 2 escenarios en paralelo; MASAC y MAAC conservan concurrencia 1 por memoria de replay/critic.

```text
HAPPO x E1/E2/E3 -> MASAC x E1/E2/E3 -> MATD3 x E1/E2/E3 -> MAAC x E1/E2/E3
```

Fixes aplicados al launcher:
- `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1`: previene `forrtl: error (200)` al cerrar ventana.
- `PYTHONUNBUFFERED=1`: flush inmediato de stdout a logs.
- Monitor en tiempo real: episodio, paso, retorno, pesos OE1/OE2/OE3, CO2, precio, historial por episodio, GPU y logs. Para display rico dentro de cada job usar `-LiveOutput $true`, sabiendo que desactiva el paralelismo de escenarios.

### Entrenamiento en paralelo (3 MADRL simultaneos, AWS)

`launch_citylearn_v3_official_training.ps1` corre los 4 algoritmos en serie (HAPPO -> MASAC -> MATD3 -> MAAC), paralelizando solo los escenarios (E1/E2/E3) dentro de cada uno. Para correr varios algoritmos en paralelo (uno por proceso, cada uno con sus propios escenarios en paralelo) usar `scripts\run_3madrl_parallel.ps1`:

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\run_3madrl_parallel.ps1 `
  -Algorithms happo,matd3,maac `
  -Episodes 50 `
  -GpuProfile aws
```

Requiere una GPU con VRAM suficiente para varios algoritmos+escenarios a la vez (no viable en RTX 4060 8 GB); el script bloquea la ejecucion si detecta <=8.5 GiB de VRAM dedicada salvo que se pase `-AllowGpuOversubscription`. Instancia AWS recomendada: `g5.2xlarge` (A10G, 24 GB VRAM). MASAC queda fuera de la lista por defecto por su mayor consumo de memoria de replay; se puede agregar explicitamente con `-Algorithms happo,masac,matd3,maac` si la VRAM lo permite.

### Perfil GPU-tuned local (referencia historica — RTX 4060 Laptop 8 GB)

| MADRL | Backend | Ajustes activos |
| ----- | ------- | --------------- |
| HAPPO | HARL (on-policy) | `hidden_size=256`, `torch_threads=12`, `team_ratio=0.70` (unified_comparable_v3) |
| MASAC | MARLlib (off-policy, RNN+QMIX) | `rnn_hidden_dim=64`, `qmix_hidden_dim=32`, `buffer_size=2` |
| MATD3 | off-policy PyTorch | `batch_size=256`, `buffer_size=4096`, `hidden_size=256` |
| MAAC | Attention SAC | `batch_size=64`, `buffer_length=256`, `hidden_size=128`, `attend_heads=4` |

### Herramientas de diagnostico y monitoreo

```powershell
# Verificar integridad del dataset (17 edificios, filas, columnas, chargers)
.\.venv39-citylearn-v3\Scripts\python.exe -B diagnostico_dataset.py

# Ver metricas del ultimo entrenamiento completado
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py

# Ver todos los runs disponibles
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py --todos

# Ver run especifico
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py --run <nombre_run>
```

## Monitor de entrenamiento

```powershell
# Monitor en tiempo real (refresca cada 5 segundos)
$root = Get-Content outputs\latest_visible_training_output_root.txt
powershell -NoProfile -ExecutionPolicy Bypass `
  -File CityLearn\scripts\monitor_citylearn_v3_official_training.ps1 `
  -OutputRoot $root `
  -IntervalSeconds 5 `
  -LogTail 12
```

El monitor muestra: estado global, jobs completados/en cola, pesos OE1/OE2/OE3,
paso/episodio actual, retorno acumulado, CO2, precio electricidad, GPU y logs
filtrados (sin ruido de arrays Box de inicializacion).

## Requisitos

- Windows PowerShell para el launcher local.
- Python 3.9.
- PyTorch CUDA para entrenamiento GPU.
- GPU NVIDIA recomendada.
- Submodulos Git inicializados.

```text
.venv39-citylearn-v3
torch 2.8.0+cu126
CUDA 12.6
```

Instalar todas las dependencias (CityLearn + UC3M + stack RL) con un solo comando desde la raiz:

```bash
pip install -r requirements.txt
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Manual completo paso a paso (Windows y AWS): `docs/MANUAL_INSTALACION_DEPENDENCIAS.md`.

## Entrenamiento en Google Colab A100

Abre el tutorial oficial y ejecuta celda a celda — clona, instala y entrena los 4 MADRL directamente en la GPU A100 de Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/citylearn-v3-madrl/examples/madrl_citylearn_v3_tutorial.ipynb)

El notebook ejecuta las 12 corridas (4 algoritmos × 3 escenarios) con `N_EPISODES=50` y genera los artefactos canonicos en `outputs/{ALGO}/{escenario}/`.

**Hardware requerido: NVIDIA A100-SXM4-80GB + 167 GiB RAM** (Colab Pro+ > runtime A100 High-RAM).

Verificacion de hardware en celda 1.2 del notebook (salida esperada):

```text
[OK] GPU: NVIDIA A100-SXM4-80GB (80.0 GiB VRAM)
[OK] RAM: ~167 GiB
[OK] Python: 3.11.13 (Linux x86_64)
[OK] CUDA: 12.4
```

Lanzar entrenamiento (celda 7.2 del notebook — ya configurada):

```bash
python -B CityLearn/scripts/colab_a100_official_launcher.py \
  --execution-mode two_phase_concurrent \
  --two-phase-masac-cuda-fraction 0.18 \
  --scenario ALL --seed 0 --episodes 50 --episode-time-steps 8760 \
  --torch-threads 1 --live-progress-interval 300 --live-heartbeat-seconds 30 \
  --artifact-profile full --trace-record-interval 24 --trace-detail compact \
  --gpu-profile aws --cuda-memory-fraction 0.92 \
  --matd3-buffer-size 200000 --matd3-batch-size 2048 \
  --masac-critic-batch-size 256 \
  --maac-buffer-length 200000 \
  --require-a100 --smoke-imports --oom-retry \
  --live-monitor --monitor-interval 30 --skip-completed
```

El launcher corre E1/E2/E3 en paralelo por grupo de algoritmo (`_run_group`). El progreso de cada escenario aparece en la celda cada 60 s via monitor con `capture_output` explicito.

## Clonar el repositorio

El repositorio tiene **9 submodulos** que deben inicializarse correctamente.

### Clon completo (recomendado)

```bash
git clone \
  --branch master \
  --depth 1 \
  --recurse-submodules \
  --shallow-submodules \
  https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr
```

Esto descarga el repo padre y los 9 submodulos en un solo comando:

| Submodulo | Repositorio |
| --------- | ----------- |
| `CityLearn/` | `Mac-Tapia/CityLearn` (rama `citylearn-v3-madrl`) |
| `external/HARL` | `Mac-Tapia/HARL` |
| `external/MAAC` | `Mac-Tapia/MAAC` |
| `external/MARL` | `Mac-Tapia/MARL` |
| `external/MARLlib` | `Mac-Tapia/MARLlib` |
| `external/MATD3implementation` | `Mac-Tapia/MATD3implementation` |
| `external/MicroGrids` | `Mac-Tapia/MicroGrids` |
| `external/evcc` | `evcc-io/evcc` |
| `external/prosumpy` | `Mac-Tapia/prosumpy` |

### Activar CityLearn en su rama viva

Despues del clon, `CityLearn/` queda en detached HEAD apuntando al commit fijado por el padre. Para llevarlo a la rama viva `citylearn-v3-madrl`:

```bash
git -C CityLearn remote add mac-tapia https://github.com/Mac-Tapia/CityLearn.git
git -C CityLearn fetch --depth 1 mac-tapia citylearn-v3-madrl
git -C CityLearn checkout -B citylearn-v3-madrl mac-tapia/citylearn-v3-madrl
```

El notebook (celda 1.2) hace esto automaticamente en Colab.

### Si ya se clono sin submodulos

```bash
git submodule init
git submodule update --init --recursive --depth 1
```

### Verificar submodulos

```bash
git submodule status
# Todos deben mostrar un commit sin prefijo '-' (no inicializado) ni 'U' (conflicto).
# El prefijo '+' en CityLearn es esperado: esta en rama viva (adelante del commit fijado).
```

## Inicio rapido AWS EC2 Ubuntu + Docker

Flujo recomendado para una instancia Ubuntu con driver NVIDIA/CUDA y Docker:

```bash
cd ~
git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr
git submodule update --init --recursive

docker --version
docker compose version
nvidia-smi
docker run --rm --gpus all ubuntu:22.04 nvidia-smi   # verificar GPU en Docker

mkdir -p outputs
docker compose -f deploy/aws/training/docker-compose.yml up -d --build
docker compose -f deploy/aws/training/docker-compose.yml logs -f
```

El Compose ejecuta `happo,masac,matd3,maac` en `E1,E2,E3` con `--episodes 50`,
`--episode-time-steps 8760`, `--cuda`, `--max-parallel-jobs 1` y
`--log-chunk-size 10M --log-max-files 100`. Los logs se ven en
`docker compose logs -f` y quedan como texto plano rotado por escenario y
algoritmo: `outputs/aws_citylearn_v3_madrl_*/logs/E1_happo-00001.log`,
`E1_happo-00002.log`, etc. Los artefactos quedan con la misma organizacion
que el flujo local: `outputs/aws_citylearn_v3_madrl_*/happo/E1_seed_0/`,
`masac/E2_seed_0/`, etc. El launcher crea desde el inicio las carpetas
`E1_seed_0`, `E2_seed_0` y `E3_seed_0` de cada algoritmo; al principio pueden
estar vacias si `--max-parallel-jobs 1` aun esta ejecutando el job anterior.
El contenedor usa `restart: unless-stopped`: sobrevive
cierres de SSH/VS Code y reinicios de EC2 sin necesidad de tmux. Al completar
el entrenamiento se crea `outputs/.training_completed`; si falla, se crea
`outputs/.training_failed` para evitar bucles de reinicio.

Monitoreo y validacion rapida:

```bash
# Monitor interactivo (refresca cada 10 s)
bash deploy/aws/training/tail_aws_training.sh

# Estado general del entrenamiento
cat "$(cat outputs/latest_visible_training_output_root.txt)/official_full_status.json"

# Jobs planificados/activos por algoritmo y escenario
cat "$(cat outputs/latest_visible_training_output_root.txt)/official_full_status.json" | \
  jq '.jobs[] | {algorithm, scenario, status, output_dir}'

# Estado y acceso directo al contenedor
docker ps --filter name=madrl-training
docker exec -it madrl-training nvidia-smi
docker exec -it madrl-training ps aux | grep python

# Verificar rotacion de logs (no debe haber archivos >10 MB)
find "$(cat outputs/latest_visible_training_output_root.txt)" -path "*/logs/*.log" -size +10M -print

# Detener cuando termine (o para relanzar)
docker compose -f deploy/aws/training/docker-compose.yml stop
rm outputs/.training_completed   # solo si se quiere un nuevo entrenamiento
```

Manual completo con instalacion del NVIDIA Container Toolkit:
`deploy/aws/README_TRAINING_AWS.md`.

## Resumen operativo de entrenamiento

| Paso | Windows local | Ubuntu/AWS | Comentario |
| ---- | ------------- | ---------- | ---------- |
| Entrar al proyecto | `cd D:\MADRLCitytleranflexresdr` | `cd ~/MADRLCitytleranflexresdr` | Ejecutar siempre desde la raiz del repositorio correcto. |
| Verificar contexto | `powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1` | `pwd && git remote -v` | En Windows este proyecto exige el verificador antes de editar o usar git. |
| Verificar GPU | `nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader` | `nvidia-smi` | Confirma que la GPU NVIDIA esta visible antes de entrenar. |
| Lanzar local visible | `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\run_citylearn_v3_full_training_visible.ps1 -OutputRoot $root -Scenario ALL -Seed 0 -EpisodeTimeSteps 8760 -Episodes 5 -GpuProfile local4060_fast -Cuda -SelfLaunched` | No aplica | Perfil local RTX 4060; util para pruebas visibles o corridas locales cortas. |
| Lanzar AWS bare-metal | No aplica | `bash deploy/aws/training/run_aws_training.sh --scenario ALL --algorithms happo,masac,matd3,maac --episodes 50 --episode-time-steps 8760 --max-parallel-jobs 1 --log-chunk-size 10M --log-max-files 100 --cuda` | Configuracion canonica AWS sin cambiar hiperparametros. |
| Lanzar AWS Docker | No aplica | `docker compose -f deploy/aws/training/docker-compose.yml up -d --build` | Usa la misma configuracion AWS y monta `outputs/` en el host. |
| Monitorear | `powershell -File CityLearn\scripts\monitor_citylearn_v3_official_training.ps1 -OutputRoot $root` | `bash deploy/aws/training/tail_aws_training.sh` | El monitor AWS lee status, live progress y logs rotados. |
| Revisar resultados | `Get-ChildItem $root -Recurse -Filter results.json` | `find "$OUTPUT_ROOT" -name results.json -type f | sort` | Los `results.json` aparecen cuando cada job termina. |

## Salidas esperadas por corrida

```text
outputs/<run_activo>/
  official_full_status.json
  official_full_manifest.json
  logs/
    E1_happo-00001.log
    E1_masac-00001.log
    ...
  happo/
    E1_seed_0/
    E2_seed_0/
    E3_seed_0/
  masac/
    E1_seed_0/
    E2_seed_0/
    E3_seed_0/
  matd3/
    E1_seed_0/
    E2_seed_0/
    E3_seed_0/
  maac/
    E1_seed_0/
    E2_seed_0/
    E3_seed_0/
```

Cada corrida contiene:

- `data/results.json`, `data/training_summary.json`, `data/artifact_audit.json`
- `data/timeseries.csv`, `data/trace.csv`, `data/checkpoint_manifest.json`
- `data/building_behavior_summary.csv`, `data/building_kpis.csv`
- `data/building_observation_action_schema.csv`, `data/building_trace_sample.csv`
- `live_progress.json` solo durante entrenamiento activo; al completar se elimina como estado transitorio
- `figures/` con retornos, convergencia y comparacion KPI
- `figures/tables/` con tablas Markdown por edificio

## Benchmark y comparacion

Ejecutar agentes originales CityLearn v2 para linea base (el script apunta por defecto al dataset Iquitos `citylearn_iquitos_2023_2025/schema.json`):

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\benchmark_citylearn_v2_agents.py `
  --scenario ALL `
  --episode-time-steps 8760 `
  --agents baseline hour_rbc `
  --output-dir outputs\citylearn_v2_original_benchmark
```

Comparar CityLearn v2 contra CityLearn v3 MADRL. Si faltan artefactos v2, el comparador los genera con los agentes originales indicados:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\compare_citylearn_v2_vs_v3_madrl.py `
  --v2-root outputs\citylearn_v2_original_benchmark `
  --v3-root $root `
  --output-dir outputs\comparison_citylearn_v2_vs_v3_madrl `
  --scenario ALL `
  --auto-benchmark-v2 `
  --v2-agents baseline hour_rbc
```

## Sustento cientifico y skills

| Recurso | Ruta | Proposito |
| ------- | ---- | --------- |
| Skill dataset Iquitos | `tools/skills/iquitos-citylearn-dataset/` | Generacion, actualizacion y validacion del dataset de Iquitos para entrenamiento MADRL |
| Skill de tesis integrado | `tools/skills/madrl-citylearn-thesis-integrated/` | Informe de tesis profesionalizante con estructura Guia N. 02, APA, matrices de consistencia |
| Skill de plan de tesis | `tools/skills/madrl-citylearn-thesis-plan/` | Plan de Tesis bajo Guia N. 01, estructura 5.1, cronograma, presupuesto, metodologia |
| Sustento capa v3 | `tools/skills/madrl-sustento-doc-capa v3/` | Modelado matematico Dec-POMDP, CTDE y fundamentos de la capa v3 |

## Documentacion generada

| Documento | Ruta |
| --------- | ---- |
| **Historia de creacion del proyecto** | `docs/HISTORIA_CREACION_PROYECTO_MADRL_CITYLEARN.md` |
| **Pipeline dataset** | `docs/architecture/dataset_construction_pipeline.md` |
| **Flujo operativo vigente** | `docs/architecture/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md` |
| **Manifest machine-readable del flujo** | `docs/workflow_manifest.json` |
| **Justificacion recompensas multiobjetivo** | `docs/decisions/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md` |
| **Justificacion diseno experimental** | `docs/decisions/JUSTIFICACION_DISENO_EXPERIMENTAL_ESCENARIOS_PARALELO.md` |
| **Cooperacion, coordinacion y control distrital** | `docs/architecture/COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.md` |
| **Informe optimizacion VRAM** | `docs/audits/INFORME_OPTIMIZACION_CITYLEARN_MADRL_VRAM.md` |
| **Registro reorganizacion + politica paralelismo** | `docs/decisions/REGISTRO_CAMBIOS_REORGANIZACION_Y_POLITICA_PARALELISMO_2026-06-13.md` |
| Arquitectura y flujo (MD) | `docs/architecture/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` |
| Arquitectura y flujo (PDF) | `docs/architecture/ARQUITECTURA_FLUJO_CITYLEARN_V3_MADRL.pdf` |
| Flujo operativo (PDF) | `docs/architecture/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.pdf` |
| Arquitectura operativa entrenamiento (PDF) | `docs/architecture/ARQUITECTURA_OPERATIVA_ENTRENAMIENTO_VISIBLE_CITYLEARN_V3_MADRL.pdf` |
| Cooperacion/coordinacion/control (PDF) | `docs/architecture/COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.pdf` |
| Pipeline dataset (PDF) | `docs/architecture/DATASET_CONSTRUCTION_PIPELINE.pdf` |
| Infografias PNG (arquitectura + flujo) | `docs/architecture/ARQUITECTURA_CITYLEARN_V3_MADRL.png`, `FLUJO_TRABAJO_CITYLEARN_V3_MADRL.png` |
| Destilacion dataset Iquitos | `docs/audits/DATASET_IQUITOS_DESTILACION_CITYLEARN_V3.md` |
| Auditoria tecnica skill MADRL | `docs/audits/AUDITORIA_TECNICA_SKILL_MADRL_CITYLEARN_V3.md` |
| Tutorial notebook | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` |
| Quickstart notebook | `CityLearn/examples/madrl_citylearn_v3_quickstart.ipynb` |
| Informe de tesis | `docs/thesis/INFORME_TESIS_MADRL_V1_COMPLETO.docx` |
| Plan de tesis | `docs/thesis/PLAN_TESIS_MADRL_CITYLEARN_V3.docx` |

## Reproducibilidad

Cada resultado debe poder rastrearse a:

```text
dataset -> escenario -> algoritmo -> seed -> hiperparametros
  -> checkpoint -> timeseries/trace -> KPIs -> comparacion v2 vs v3
  -> 4 tests estadisticos sobre KPI-gains -> hipotesis_estadisticas_madrl.csv
```

Los backends externos estan fijados en:

```text
external/backends.lock.json
```

## Estado de investigacion

Este repositorio esta orientado a investigacion de tesis. La arquitectura y los artefactos estan preparados para demostrar, con resultados cuantitativos y pruebas estadisticas, si CityLearn v3 MADRL mejora o caracteriza mejor que CityLearn v2 original los tres ejes:

- **OE1** Flexibilidad energetica.
- **OE2** Emisiones de CO2.
- **OE3** Costos energeticos.

La demostracion de hipotesis sigue el flujo: Shapiro-Wilk (normalidad) → Kruskal-Wallis (diferencias globales entre 4 MADRL) → Mann-Whitney U (diferencias por par, independiente) → Wilcoxon signed-rank (diferencias por par, pareado), aplicados sobre KPI-gains de entrenamiento de HAPPO, MASAC, MATD3 y MAAC.

## Cambios Recientes
- **2026-06-22 20:31**: 1.2, 1.2b, 1.3, 1.4 (+5 mas)
- **2026-06-22 (actual)**: `two_phase_concurrent` — 12 jobs simultaneos; MATD3 buffer 200k/batch 2048; MASAC critic_batch 256 + preload_cpu; MAAC buffer 200k; torch_threads 1; live_progress 300; artifact_profile full; auto-stop 11.5h celda 7.2; README + notebook actualizados
- **2026-06-21 21:58**: outputs/dataset_cache/citylearn_csv_4fef05da2f6c8f5ade87.meta.json
- **2026-06-21 11:53**: _cell_src.py
- **2026-06-21 (actual)**: `colab_a100_live_monitor.py` — `print_progress` muestra todos los jobs paralelos (E1/E2/E3 simultaneos); celda 7.2 stdout garantizado via PIPE+threads+capture_output; `platformdirs` re-añadido a BASE_DEPS
- **2026-06-21 07:50**: tools/_fix_notebook_newlines.py
- **2026-06-21 07:11**: README.md, nb_keycells.txt
- **2026-06-21 07:08**: nb_keycells.txt
- **2026-06-21 05:52**: tools/generate_colab_notebook.py, tools/test_notebook_cells.py
- **2026-06-20 22:40**: tools/_find_cell.py
- **2026-06-20 22:24**: tools/_find_cell.py, tools/_patch_cell72.py
- **2026-06-20 (actual)**: `madrl_citylearn_v3_tutorial.ipynb` — actualizado a A100-SXM4-80GB (80 GiB VRAM, 167 GiB RAM, CUDA 12.4); eliminadas todas las referencias RTX 4060 como entorno objetivo; MIN_VRAM 39→78 GiB, MIN_RAM 60→120 GiB, --gpu-profile local→aws
- **2026-06-20 (actual)**: `colab_a100_official_launcher.py` — `--parallel-scenarios 3` (ThreadPoolExecutor), hyperparams A100-80GB (HAPPO hidden 512, MATD3 buffer 1M batch 1024, MASAC buffer 40 GiB CPU), manifest thread-safe con threading.Lock
- **2026-06-20 17:42**: outputs/citylearn_v3_madrl_full_20260615_074011_v4 — masac checkpoints E1/E2/E3, resumen_comparativo/global_comparison.png (+7 mas)
- **2026-06-20 17:28**: tools/generate_informe_final.py, tools/test_notebook_cells.py, tools/verify_notebook.py, tools/verify_workflow_integrity.py
- **2026-06-20 15:50**: README.md, tools/fix_colab_cell2.py, tools/generate_informe_final.py, tools/patch_notebook_final.py
- **2026-06-20 11:47**: docs/workflow_manifest.json, scripts/restart_happo_masac_v3.ps1, scripts/restart_masac_matd3_maac.ps1, scripts/run_3madrl_parallel.ps1 (+3 mas)

<!-- auto_save.sh inserta entradas nuevas justo debajo de este encabezado -->

## Licencias y citacion

Este proyecto integra software externo mediante submodulos. Revise las licencias de CityLearn y de los backends en `external/` antes de redistribuir o publicar derivados.

Referencias base:

- CityLearn v2: Nweye et al. (2025), *Journal of Building Performance Simulation*.
- CityLearn original: Vazquez-Canteli et al. (2020), arXiv.
- HAPPO/HARL, MASAC, MATD3 y MAAC segun los repositorios externos fijados en `external/backends.lock.json`.
