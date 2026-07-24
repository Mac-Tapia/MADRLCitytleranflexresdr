## Guia Rapida de Lanzamiento en Colab A100 / H100

> **Tiempo estimado:** entrenamiento de 50 episodios por corrida en **H100 (~26 vCPU, objetivo primario)**; ~2x más lento en A100 (12 vCPU, compatible). Reanudable con `--skip-completed` si Colab se desconecta. two_phase: Fase1 HAPPO+MASAC + Fase2 MATD3+MAAC; 6 jobs/fase; cuello = CPU de CityLearn.
> **Prerequisito:** Runtime A100 o H100 activado antes de ejecutar celda 1.1. La Seccion 6 auto-ajusta los hilos a las vCPU del runtime.

### Mapa de navegacion (orden obligatorio)

| Bloque | Celdas | Funcion |
|--------|--------|---------|
| Setup | **0.verify** → **1.1–1.5** | GPU A100/H100, clone/sync, venv 3.9, Drive |
| Rutas | **2.1** [→ **2.1b** verificar] [→ **2.1c** limpieza] [→ **2.2** rescate] [→ **2.3** HAPPO 49→50] | `OUTPUT_ROOT` auto (nuevo o resume) |
| Validacion | **3.1** → **4.1** → **5.1** | Dataset, env, pesos recompensa |
| Config | **6.1** [→ **6.2** si `QUICK_TEST`] | Fuente unica de HPs + `EXECUTION_MODE=two_phase_happo_masac` |
| Lanzamiento | **7.0** → **7.1** → **7.2** | Helpers, dry-run 12 jobs, entrenamiento |
| Post | **7.3–7.7**, **8.x**, **9.x** | Monitor, auditoria, KPIs, estadistica |

**Sync git (celda 1.2):** padre `codex/fix-madrl-traceability-docs` · CityLearn `codex/iquitos-distillation-madrl-docs` · external/MAAC `codex/integrar-limpieza-diagnosticos` (fix cuda/cpu Adam) · protocolo `two_phase_happo_masac_v3` only. La celda **1.2** verifica los 3 parches (MAAC cuda-sync, validacion de corrida completa, ImportError del launcher) y aborta el setup si falta alguno.

**Flujo unico (desde cero o reanudar):** `1.1–1.5` → `2.1` → `2.1b` → `6.1` → `7.0` → `7.1` → `7.2`. La celda **2.1** decide sola si crea run nuevo o reanuda el ultimo; **2.1b** solo verifica el plan.

**Garantias de persistencia al reanudar (Drive):**
- **No se crea carpeta nueva** al reconectar: `2.1` reutiliza el ultimo `madrl_v3_*`.
- **Jobs completos** (`results.json`) se **omiten** (`--skip-completed`); sus archivos no se tocan.
- **Jobs interrumpidos** reanudan desde checkpoint `.pt` y continuan los episodios restantes.
- **`timeseries.csv` / `trace.csv`**: cada episodio terminado se guarda en Drive al instante; al reanudar se **precargan** y se **continua appendeando** (no se pierden episodios ya entrenados).
- **Al completar los 50 episodios**: `write_training_artifacts` genera el archivo **integra y completo** (`results.json`, CSV finales, figuras) y `artifact_audit.json` valida filas/episodios esperados.
- **Escritura atomica** (tmp+replace): un corte de Colab no deja CSV a medias en Drive.
- **Checkpoints `.pt`**, `live_progress.json` y `results.json` de jobs completos permanecen intactos en Drive.

**Outputs en Drive:** carpeta canónica compartida (`1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX`) y workspace escribible `MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_<timestamp>/` (dentro del run: `{MADRL}/E{1,2,3}/`).

---

## Flujo A — Lanzamiento DESDE CERO (Colab, primera vez)

**Cuando usarlo:** Drive vacio (sin carpetas `madrl_v3_*`) o quieres un run completamente nuevo.

**No toques banderas** — deja los defaults de `2.1` (`AUTO_RESUME_LATEST=True`, `FORCE_NEW_RUN=False`).

| Paso | Celda | Que hace | Que debes ver |
|------|-------|----------|---------------|
| 1 | **Runtime Colab** | Entorno > A100 o H100 | GPU detectada |
| 2 | **0.verify** | Verifica conexion al runtime | OK |
| 3 | **1.1** | GPU, CUDA, Python | `NVIDIA A100` o `H100` |
| 4 | **1.2** | Clone repo + submodulos | codigo en `/content/MADRLCitytleranflexresdr` |
| 5 | **1.2b** | Valida ramas git | OK |
| 6 | **1.3** | Instala deps en `.venv39-citylearn-v3` | pip OK |
| 7 | **1.4** | sys.path + smoke imports | imports OK |
| 8 | **1.5** | Monta Google Drive | Drive montado |
| 9 | **2.1** | Crea `OUTPUT_ROOT` nuevo | `MODO RUN : NUEVO run (no habia runs previos)` |
| 10 | **2.1b** | Verifica plan 12 jobs | 12 x `PENDIENTE (fresh)` |
| 11 | **3.1** → **4.1** → **5.1** | Dataset, env, pesos (recomendado 1ra vez) | OK |
| 12 | **6.1** | Hiperparametros (`N_EPISODES=50`) | config impresa |
| 13 | **7.0** | Helpers launcher/monitor | OK |
| 14 | **7.1** | Preflight + dry-run 12 jobs | `dry-run OK` / `PASSED` |
| 15 | **7.2** | Entrenamiento oficial (two_phase) | monitor por MADRL activo |
| 16 | **7.3** (auto si `AUTO_RUN_POST_TRAINING`) | Monitor + auditoria post-train | progreso individual |
| 17 | **8.x / 9.x** | Analisis KPIs (al terminar jobs) | `results.json` x 12 |

**Secuencia minima (copiar/pegar orden):**
```
0.verify -> 1.1 -> 1.2 -> 1.2b -> 1.3 -> 1.4 -> 1.5
-> 2.1 -> 2.1b -> 6.1 -> 7.0 -> 7.1 -> 7.2
```

**Que se crea en Drive:**
```
outputs/madrl_v3_<timestamp>/
  HAPPO/E1/data/timeseries.csv   (crece episodio a episodio)
  HAPPO/E1/checkpoints/*.pt
  MASAC/E1/ ... MATD3/ ... MAAC/ ...
  official_full_status.json
```

---

## Flujo B — REINICIO y REANUDACION (Colab se desconecto)

**Cuando usarlo:** Colab cerro sesion, perdiste runtime, o quieres continuar un entrenamiento ya iniciado.

**No toques banderas** — `2.1` hace AUTO-RESUME del ultimo `madrl_v3_*` en Drive.

| Paso | Celda | Que hace | Que debes ver |
|------|-------|----------|---------------|
| 1 | **Runtime Colab** | Nuevo runtime A100/H100 | GPU detectada |
| 2 | **1.1 → 1.5** | Re-sync codigo + remontar Drive | mismo setup que Flujo A |
| 3 | **2.1** | Reutiliza ultimo run | `MODO RUN : AUTO-RESUME por checkpoints en Drive` |
| 4 | **2.1b** | Reporte por job (12 corridas) | ver tabla abajo |
| 5 | **2.3** *(si HAPPO 49/50 salvage sin KPIs)* | `dry_run` → `execute` | `results.json` con KPIs |
| 6 | **7.2** sola | Bootstrap integral + entrenamiento | mismo `OUTPUT_ROOT` Drive |
| 7 | **8.x** *(tras 2.3 execute)* | Agregador KPIs / ranking | HAPPO incluido en 4/4 MADRL |

**Secuencia minima (copiar/pegar orden):**
```
1.1 -> 1.2 -> 1.2b -> 1.3 -> 1.4 -> 1.5
-> 2.1 -> 2.1b -> [2.3 si HAPPO salvage sin KPIs] -> 6.1 -> 7.0 -> 7.1 -> 7.2

**Reconexion / resume:** solo **7.2** (incluye git sync + Drive + mismo OUTPUT_ROOT).
-> 8.x (o aggregate_colab_drive_kpis.py tras 2.3)
```

> **HAPPO salvage 49/50:** la celda **7.2** reanuda el tail KPI en las mismas carpetas Drive (paralelo si VRAM). Celda **2.3** sigue disponible como atajo solo-KPI sin re-entrenar.

**Que significa el reporte de 2.1b (por cada MADRL/E1..E3):**

| Estado en 2.1b | Que hace 7.2 | Archivos en Drive |
|----------------|--------------|-------------------|
| `OK COMPLETO 50/50 ep` | **OMITE** (`--skip-completed`) | Intactos (`results.json`, CSV, figuras) |
| `REANUDA ep X/50` | Carga `.pt`, continua ep X+1..50 | CSV se **continua appendeando** |
| `REANUDA 49/50` HAPPO salvage sin KPIs | **EJECUTA vía 2.3** (no 7.2 solo) | Checkpoints intactos; falta KPI en `results.json` |
| `PENDIENTE (fresh)` | Arranca de cero ese job | Crea archivos nuevos en su carpeta |

**Garantias al reanudar:**
- **No se crea carpeta nueva** (`madrl_v3_*` duplicada) — mismo `OUTPUT_ROOT`.
- **No se pierden episodios ya entrenados** — CSV incremental + preload.
- **Jobs completos no se repiten** — `--skip-completed`.
- **Al llegar a 50 ep** — `results.json` + `artifact_audit.json` (`status: ok`) listos para analisis OE1/OE2/OE3.

**Opcional tras reconectar:** **2.1c** reporta runs duplicados en Drive (borrar con `DELETE_DUPLICATE_RUNS=True`).

**Casos especiales (solo si los necesitas):**

Reanudar un run **concreto** (no el ultimo) — antes de **2.1**:
```python
RESUME_OUTPUT_ROOT = '/content/drive/MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_20260626_004846'
```

Empezar de cero **ignorando** runs viejos en Drive — antes de **2.1**:
```python
FORCE_NEW_RUN = True
```

---

### Paso 1 — Seleccionar runtime A100 o H100

En Colab: **Entorno de ejecucion > Cambiar tipo de entorno de ejecucion**
Acelerador de hardware: **H100 GPU** (recomendado, objetivo primario) o **A100 GPU** (compatible) (requiere Colab Pro+). H100 da ~26 vCPU (~2x) para la simulacion CityLearn ligada a CPU.

> Si Colab entrega kernel Python 3.11, no se usa para el stack MADRL: la celda **1.3** crea/usa `.venv39-citylearn-v3` con Python 3.9 y las celdas de entrenamiento llaman a ese interprete.

---

### Paso 2 — Ejecutar la configuracion inicial (Seccion 1)

| Celda | Accion |
|-------|--------|
| **1.1** | Verificar GPU — debe mostrar `NVIDIA A100-SXM4-80GB` o `NVIDIA H100` |
| **1.2** | Clonar repo + submodulos (`--recurse-submodules --depth 1`) |
| **1.3** | Instalar dependencias (`pip install -e CityLearn/ external/HARL/ ...`) |
| **1.4** | Configurar `sys.path`, CUDA env y smoke imports |
| **1.5** | Montar Google Drive (workspace canonico; carpeta compartida `1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX`) |
| **2.1** | Auditar `outputs/` en Drive (MyDrive + carpeta compartida) y elegir `OUTPUT_ROOT` sin mirror |

---

### Paso 3 — Configurar rutas de salida (Seccion 2)

Ejecutar **celda 2.1** sola. **No hace falta** crear banderas manuales en la mayoria de casos.

La celda **2.1** decide automaticamente (defaults: `AUTO_RESUME_LATEST=True`, `FORCE_NEW_RUN=False`):

| Situacion | Que hace 2.1 | Necesitas tocar algo? |
|-----------|--------------|----------------------|
| **Primera vez** (Drive sin `madrl_v3_*`) | Crea run nuevo `madrl_v3_<timestamp>` | **No** |
| **Reiniciar / reanudar** (ya hay runs en Drive) | **Audita todos los runs** y elige el mas completo por artefactos MADRL (no el timestamp mas reciente) | **No** |
| **Reanudar un run concreto** (no el mejor) | Usa `RESUME_OUTPUT_ROOT` con la ruta exacta | Solo si quieres otro run |
| **Empezar de cero ignorando runs viejos** | `FORCE_NEW_RUN=True` | Solo caso especial |

Luego **2.1b** (verificacion): reporta por cada uno de los 12 jobs si esta COMPLETO, REANUDABLE o PENDIENTE. **No lanza entrenamiento** — solo confirma el plan antes de **7.2**.

Opcional: **2.1c** limpia runs `madrl_v3_*` duplicados en Drive (reporta por defecto; borra con `DELETE_DUPLICATE_RUNS=True`).

Si un run previo fallo (MASAC OOM, etc.) y quieres conservar HAPPO parcial: **celda 2.2** (`rescue` → `2.1` → opcional `inject` → `6.1` → `7.2`).

---

### Paso 4 — Verificar dataset y entorno (Secciones 3-5)

Opcional pero recomendado en la primera corrida:

- **3.1** Verificar 222 CSV, 17 edificios, 26 304 pasos.
- **4.1** Smoke-test del entorno Dec-POMDP (4 pasos, 17 agentes).
- **5.1** Ver pesos de recompensa por escenario E1/E2/E3.

---

### Paso 5 — Configurar hiperparametros (Seccion 6)

Ejecutar **celda 6.1**. Variables clave:

```python
QUICK_TEST = False   # True = 3 ep (prueba infra), False = N_EPISODES (real)
N_EPISODES = 50      # episodios por corrida (reanudable con --skip-completed)
GPU_PROFILE = 'aws'  # perfil memoria CUDA para A100
```

---

### Paso 6 — Lanzar entrenamiento (Seccion 7)

| Celda | Accion | Duracion aprox. |
|-------|--------|-----------------|
| **7.0** | Cargar helpers de ejecucion | < 1 s |
| **7.1** | **Dry-run / Preflight** — valida A100/H100 + 12 jobs | ~ 20 s |
| **7.2** | **Lanzar entrenamiento completo** (50 ep x 12 corridas, two_phase_happo_masac) | ~ 20 h |
| **7.3** | Monitor manual (puede ejecutarse mientras corre) | en cualquier momento |

> Si Colab se desconecta (limite ~12 h): **solo celda 7.2** (bootstrap integral: git + Drive + mismo OUTPUT_ROOT + entrenamiento). Primera vez desde cero: `1.1–1.5` → `2.1` → `2.1b` → `6.1` → `7.0` → `7.1` → `7.2`.
> `--skip-completed` omite jobs ya terminados (`results.json`). **Resume intra-job** continua el job interrumpido desde el ultimo checkpoint (`.pt` + `live_progress.json`).

---

### Paso 7 — Analisis de resultados (Secciones 8-9)

| Celda | Accion |
|-------|--------|
| **8.1** | Cargar `results.json` de 12 corridas → DataFrame de KPIs |
| **8.2** | Curvas de convergencia por algoritmo y escenario |
| **9.1** | Suite estadistica: Kruskal-Wallis, Mann-Whitney U, ranking global |
| **10** | Resumen final de la sesion |

---

### Estructura de artefactos generados

```
OUTPUT_ROOT/
  HAPPO/E1/data/results.json        # KPIs finales
  HAPPO/E1/data/timeseries.csv      # reward por paso
  HAPPO/E1/checkpoints/models/*.pt      # modelos guardados
  HAPPO/E1/figures/*.png            # 13 graficas
  MASAC/E1/...
  MATD3/E1/...   <- ganador corrida v4
  MAAC/E1/...
  official_full_status.json                # estado global 12 jobs
  live_progress.json                       # ultimo snapshot en tiempo real
```
