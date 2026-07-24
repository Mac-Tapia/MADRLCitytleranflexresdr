# -*- coding: utf-8 -*-
"""Surgical cleanup of madrl_citylearn_v3_tutorial.ipynb.

Preserves: two_phase_happo_masac, N_EPISODES=50, from-scratch flow, scientific intent.
Removes: duplicated guides, stale paths, broken imports, contradictory defaults.
"""
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

NB_PATH = Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb")
BACKUP = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_backup_madrl_citylearn_v3_tutorial.ipynb")
REPORT = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_cleanup_report.txt")


def cell_src(cell) -> str:
    src = cell.get("source", [])
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def set_src(cell, text: str) -> None:
    # Jupyter prefers list-of-lines ending with \n except possibly last
    if not text.endswith("\n") and text:
        text = text + "\n"
    lines = text.splitlines(keepends=True)
    cell["source"] = lines


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 70, f"Expected 70 cells, got {len(cells)}"
    shutil.copy2(NB_PATH, BACKUP)
    changes: list[str] = []

    # ─── Cell 001: Guia rapida — remove Paso 1–7 duplicate (Flujo A/B already covers it) ───
    c001 = cell_src(cells[1])
    marker = "\n---\n\n### Paso 1 — Seleccionar runtime A100 o H100"
    if marker in c001:
        # Keep Flujo A/B + special cases; drop Paso 1-7 + trailing artifact tree duplicate
        head = c001.split(marker)[0].rstrip()
        # Soften Flujo B row about 2.3 being required; keep as optional recovery
        head = head.replace(
            "| 5 | **2.3** *(si HAPPO 49/50 salvage sin KPIs)* | `dry_run` → `execute` | `results.json` con KPIs |\n| 6 | **7.2** sola |",
            "| 5 | **2.3** *(opcional: solo si HAPPO salvage 49/50 sin KPIs)* | `skip` por defecto; `execute` solo si aplica | KPIs HAPPO |\n| 6 | **7.2** sola |",
        )
        head = head.replace(
            "-> 2.1 -> 2.1b -> [2.3 si HAPPO salvage sin KPIs] -> 6.1 -> 7.0 -> 7.1 -> 7.2",
            "-> 2.1 -> 2.1b -> 6.1 -> 7.0 -> 7.1 -> 7.2\n# (opcional) 2.3 solo si HAPPO salvage 49/50 sin KPIs",
        )
        head = head.replace(
            "> **HAPPO salvage 49/50:** la celda **7.2** reanuda el tail KPI en las mismas carpetas Drive (paralelo si VRAM). Celda **2.3** sigue disponible como atajo solo-KPI sin re-entrenar.",
            "> **HAPPO salvage 49/50 (opcional):** en reanudacion, **7.2** cubre tails KPI. Celda **2.3** es atajo solo-KPI (`HAPPO_KPI_MODE='skip'` por defecto; no forma parte del flujo desde cero).",
        )
        # Trim nav map: mark 2.2/2.3 as recovery-only
        head = head.replace(
            "| Rutas | **2.1** [→ **2.1b** verificar] [→ **2.1c** limpieza] [→ **2.2** rescate] [→ **2.3** HAPPO 49→50] | `OUTPUT_ROOT` auto (nuevo o resume) |",
            "| Rutas | **2.1** → **2.1b** [→ **2.1c** limpieza] | `OUTPUT_ROOT` auto (nuevo o resume). **2.2/2.3** solo recuperacion |",
        )
        # Append compact note instead of Paso 1-7
        tail = """

---

### Recordatorio (sin duplicar el flujo)

- Runtime: **H100** (primario) o **A100** · High-RAM.
- Fuente unica de HPs: celda **6.1** (`N_EPISODES=50`, `EXECUTION_MODE=two_phase_happo_masac`).
- Entrenamiento oficial: **7.0 → 7.1 → 7.2**. Analisis: **8.x / 9.x**.
- Artefactos: `{OUTPUT_ROOT}/{HAPPO|MASAC|MATD3|MAAC}/E{1,2,3}/` + `official_full_status.json`.
"""
        set_src(cells[1], head + tail)
        changes.append("001: removed Paso 1-7 duplicate; clarified 2.2/2.3 as recovery-only")
    else:
        changes.append("001: SKIP (Paso 1 marker not found)")

    # ─── Cell 016: missing imports ───
    c016 = cell_src(cells[16])
    if "import sys" not in c016:
        c016 = c016.replace(
            "# ── 1.1  Verificar entorno: IN_COLAB, GPU, CUDA, Python 3.9 ─────────────────\n\n"
            "# ── Deteccion automatica de entorno ──────────────────────────────────────────\n"
            "import importlib.util\n",
            "# ── 1.1  Verificar entorno: IN_COLAB, GPU, CUDA, Python 3.9 ─────────────────\n"
            "import sys\n"
            "import subprocess\n"
            "import importlib.util\n\n"
            "# ── Deteccion automatica de entorno ──────────────────────────────────────────\n",
        )
        set_src(cells[16], c016)
        changes.append("016: added missing import sys/subprocess")
    else:
        changes.append("016: imports already present")

    # ─── Cell 017: missing import os ───
    c017 = cell_src(cells[17])
    if "import os" not in c017.split("PHASE_JOBS")[0]:
        c017 = c017.replace(
            "mientras el entrenamiento avanza sin afectarlo.\n"
            "import subprocess\n"
            "import shutil\n",
            "mientras el entrenamiento avanza sin afectarlo.\n"
            "import os\n"
            "import subprocess\n"
            "import shutil\n",
        )
        set_src(cells[17], c017)
        changes.append("017: added missing import os")
    else:
        changes.append("017: import os already present")

    # ─── Cell 032: 2.3 markdown — optional recovery, not mandatory from-scratch ───
    set_src(
        cells[32],
        """### 2.3 (Opcional) Completar HAPPO salvage (49→50) + KPIs

> **Fuera del flujo desde cero.** Por defecto `HAPPO_KPI_MODE='skip'`.
> Usar solo al **reanudar** un run donde HAPPO tiene checkpoints pero `results.json` salvage sin KPIs.

1. Ejecuta **2.1** (mismo `OUTPUT_ROOT` del run a reparar).
2. `HAPPO_KPI_MODE = 'dry_run'` → preflight checkpoints + comando resume.
3. `HAPPO_KPI_MODE = 'execute'` → 1 episodio restante × escenario + KPIs.
4. Continua con **7.2** (si faltan otros jobs) o **8.x** (si ya estan los 12).

> El entrenamiento oficial desde cero no requiere esta celda: **7.2** + `--skip-completed` cubre tails HAPPO.
""",
    )
    changes.append("032: reframed 2.3 as optional recovery (not mandatory)")

    # ─── Cell 033: default skip for from-scratch ───
    c033 = cell_src(cells[33])
    c033 = c033.replace(
        "# ── 2.3  Completar HAPPO (49→50) + KPIs — obligatorio para 4/4 MADRL ───────────\n",
        "# ── 2.3  (Opcional) Completar HAPPO salvage (49→50) + KPIs ───────────────────\n"
        "# Default skip: el flujo desde cero / two_phase usa 7.2. Activa dry_run/execute solo\n"
        "# si reanudas un run con HAPPO salvage sin KPIs.\n",
    )
    c033 = c033.replace(
        "HAPPO_KPI_MODE = 'dry_run'  # 'skip' | 'dry_run' | 'execute'\n",
        "HAPPO_KPI_MODE = 'skip'  # 'skip' | 'dry_run' | 'execute'  (skip = flujo desde cero)\n",
    )
    set_src(cells[33], c033)
    changes.append("033: HAPPO_KPI_MODE default skip for from-scratch")

    # ─── Cell 030: clarify optional in title already OK; tighten markdown ───
    set_src(
        cells[30],
        """### 2.2 (Opcional) Rescatar HAPPO de un run fallido

> **Fuera del flujo desde cero.** `RESCUE_MODE='skip'` por defecto.

Ejecutar **solo si** un run previo murió (p. ej. MASAC OOM) y quieres conservar checkpoints HAPPO parciales antes de borrarlo o relanzar con un `OUTPUT_ROOT` nuevo.

1. Define `FAILED_OUTPUT_ROOT` (run roto) y opcionalmente `HAPPO_RESCUE_ARCHIVE`.
2. Ejecuta la celda → copia checkpoints + `live_progress.json` a `outputs/rescued_happo_*`.
3. Para **retomar HAPPO** en un run nuevo: ejecuta `2.1` (nuevo timestamp), luego esta celda en modo `inject` antes de `7.2`.

> El rescate no completa el experimento 12/12; solo preserva progreso HAPPO intra-job.
""",
    )
    changes.append("030: clarified 2.2 outside from-scratch path")

    # ─── Cells 040 + 041: unique Section 6 header with two-phase + hyperparams ───
    set_src(
        cells[40],
        """## Sección 6: Hiperparámetros y estrategia two_phase

### Estrategia de entrenamiento en dos fases (Colab A100 / H100)

| Fase | Algoritmos | Jobs paralelos | Notas |
|:---:|:---|:---:|:---|
| **1** | HAPPO + MASAC | 6 (E1/E2/E3) | MASAC buffer en GPU VRAM; arrancan los 6 a la vez |
| **2** | MATD3 + MAAC | 6 (E1/E2/E3) | Backfill dinámico: cada job de Fase 2 (más liviano primero: MAAC, luego MATD3) entra **solo al terminar un job de Fase 1** |

Regla (`run_dynamic_backfill_jobs`): la Fase 2 **nunca** arranca antes de que termine un job de Fase 1. Modo launcher: `--execution-mode two_phase_happo_masac` (backfill dinámico por defecto; `--no-dynamic-backfill` = barrera estricta). Reanudación: `--skip-completed`.
""",
    )
    set_src(
        cells[41],
        """### 6.1 Fuente única de hiperparámetros (A100 estable · 50 episodios/corrida)

Perfil `two_phase_happo_masac`: 6 jobs/fase (sin stagger). La celda **6.1** es la **fuente única de verdad** (`N_EPISODES`, fracciones CUDA, buffers); el launcher aplica overrides de fase. Los hilos de CPU se **auto-ajustan** a las vCPU del runtime.

| Algoritmo | Parametro clave | Valor two_phase (celda 6.1) | OOM retry |
|---|---|---|---|
| **HAPPO** | hidden / n_rollout_threads | 512 / **auto (vCPU)** | hidden 256 |
| **MASAC** | buffer ep / max GiB / critic_batch | **4 / 8.0 / 1** | 2 / 6.0 / 1 (+ CPU replay) |
| **MASAC** | rnn / qmix / hyper hidden | **64 / 32 / 64** | 64 / 32 / 64 |
| **MATD3** | batch / buffer / hidden | **256 / 4096 / 256** | 768 / 1M / 512 |
| **MAAC** | batch / buffer / hidden / num_updates | **768 / 450K / 768 / 12** | 512 / 500K / 512 / 8 |

| Global | Valor |
|---|:---:|
| Episodios × pasos | 50 × 8 760 (por corrida, reanudable con `--skip-completed`) |
| Torch threads | auto por fase (celda 6.1) |
| CUDA fraction HAPPO/MATD3/MAAC | **0.14–0.15** |
| CUDA fraction MASAC | **0.16–0.22** |
| MASAC replay device | **cpu** |
| Reanudacion | `--skip-completed` |
""",
    )
    changes.append("040+041: unique Seccion 6 with two-phase + aligned HP table")

    # ─── Cell 042: SCHEMA reuse, QUICK_TEST comment, HYPERPARAMS sync ───
    c042 = cell_src(cells[42])
    c042 = c042.replace(
        "SCHEMA_PATH = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'\n",
        "SCHEMA_PATH = globals().get(\n"
        "    'SCHEMA_PATH',\n"
        "    f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json',\n"
        ")\n",
    )
    c042 = c042.replace(
        "# ── QUICK_TEST ────────────────────────────────────────────────────────────\n"
        "# False  → usa N_EPISODES con el pipeline oficial two_phase (celda 7.2).\n"
        "# True   → prueba de infraestructura rapida (3 episodios, ~15 min) en la celda 6.2.\n"
        "#\n"
        "# >>> ENTRENAMIENTO OFICIAL: 50 EPISODIOS POR CORRIDA <<<\n"
        "# N_EPISODES = 50 corre las 12 corridas reales (4 algos x 3 escenarios) a\n"
        "# 50 episodios cada una. Si Colab se desconecta, se reanuda con --skip-completed\n"
        "# (reiniciando y reanudando desde los checkpoints existentes) hasta completar los 50.\n"
        "QUICK_TEST      = False\n"
        "N_EPISODES      = 50           # Entrenamiento: 50 episodios por corrida.\n"
        "EPISODES        = 3 if QUICK_TEST else N_EPISODES\n",
        "# ── QUICK_TEST ────────────────────────────────────────────────────────────\n"
        "# False → entrenamiento oficial: N_EPISODES=50 via two_phase (celda 7.2).\n"
        "# True  → (a) celda 6.2: smoke 1 ep/algo; (b) si lanzas 7.2, EPISODES=3 (infra).\n"
        "# No uses QUICK_TEST=True para resultados de tesis.\n"
        "QUICK_TEST      = False\n"
        "N_EPISODES      = 50           # Entrenamiento oficial: 50 episodios por corrida.\n"
        "EPISODES        = 3 if QUICK_TEST else N_EPISODES\n",
    )
    # Align HYPERPARAMS with SIX_JOB_* (source of truth for launcher)
    old_masac = '''    "MASAC": {
        # Off-policy multi-agent SAC + QMIX — acciones discretizadas (axis 89)
        "actor_lr"          : 3e-4,
        "critic_lr"         : 5e-4,
        "alpha_lr"          : 3e-4,
        "gamma"             : 0.9999,
        "tau"               : 0.005,     # fijo en backend QMIX (qmix_msac.soft_update)
        "batch_size"        : 512,
        "replay_buffer_size": 2,
        "max_replay_buffer_gib": 8.0,'''
    new_masac = '''    "MASAC": {
        # Off-policy multi-agent SAC + QMIX — acciones discretizadas (axis 89)
        # Buffers alineados a SIX_JOB_MASAC_* (fuente de verdad del launcher 6-parallel).
        "actor_lr"          : 3e-4,
        "critic_lr"         : 5e-4,
        "alpha_lr"          : 3e-4,
        "gamma"             : 0.9999,
        "tau"               : 0.005,     # fijo en backend QMIX (qmix_msac.soft_update)
        "batch_size"        : 512,
        "replay_buffer_size": SIX_JOB_MASAC_BUF,
        "max_replay_buffer_gib": SIX_JOB_MASAC_GIB,'''
    if old_masac in c042:
        c042 = c042.replace(old_masac, new_masac)
        changes.append("042: MASAC HYPERPARAMS aligned to SIX_JOB_*")
    else:
        changes.append("042: WARN MASAC HYPERPARAMS block not matched")

    old_matd3 = '''    "MATD3": {
        # Off-policy Multi-Agent Twin Delayed DDPG — acciones continuas
        "actor_lr"          : 3e-4,
        "critic_lr"         : 3e-4,
        "gamma"             : 0.9999,
        "tau"               : 0.005,
        "policy_noise"      : 0.2,       # ruido en actualizacion del target
        "noise_clip"        : 0.5,
        "policy_delay"      : 2,         # twin delayed: 1 actor cada 2 critic updates
        "batch_size"        : 1024,
        "replay_buffer_size": 2_000_000,
        "hidden_size"       : 768,       # 6-parallel fase 2: menos VRAM/job que 1024
        "max_grad_norm"     : 1.0,
        "train_interval"    : 50,
        "share_policy"      : False,
    },'''
    new_matd3 = '''    "MATD3": {
        # Off-policy Multi-Agent Twin Delayed DDPG — acciones continuas
        # Alineado a SIX_JOB_MATD3_* (config estable 6-parallel fase 2).
        "actor_lr"          : 3e-4,
        "critic_lr"         : 3e-4,
        "gamma"             : 0.9999,
        "tau"               : 0.005,
        "policy_noise"      : 0.2,       # ruido en actualizacion del target
        "noise_clip"        : 0.5,
        "policy_delay"      : 2,         # twin delayed: 1 actor cada 2 critic updates
        "batch_size"        : SIX_JOB_MATD3_BATCH,
        "replay_buffer_size": SIX_JOB_MATD3_BUF,
        "hidden_size"       : SIX_JOB_MATD3_HIDDEN,
        "max_grad_norm"     : 1.0,
        "train_interval"    : 50,
        "share_policy"      : False,
    },'''
    if old_matd3 in c042:
        c042 = c042.replace(old_matd3, new_matd3)
        changes.append("042: MATD3 HYPERPARAMS aligned to SIX_JOB_*")
    else:
        changes.append("042: WARN MATD3 HYPERPARAMS block not matched")

    old_maac = '''    "MAAC": {
        # Off-policy SAC con critic de atencion multiagente — acciones discretas
        "actor_lr"          : 3e-4,
        "critic_lr"         : 1e-3,
        "gamma"             : 0.9999,
        "tau"               : 5e-3,
        "batch_size"        : 512,
        "attention_heads"   : 4,         # launcher build_jobs usa attend_heads=4 (estable)
        "hidden_dim"        : 768,       # 6-parallel fase 2: menos VRAM/job que 1024
        "replay_buffer_size": 1_000_000,
        "steps_per_update"  : 50,
        "num_updates"       : 12,
        "reward_scale"      : 10.0,
        "action_bins"       : 3,
        "n_discrete_actions": 89,
    },'''
    new_maac = '''    "MAAC": {
        # Off-policy SAC con critic de atencion multiagente — acciones discretas
        # Alineado a SIX_JOB_MAAC_* (6-parallel fase 2).
        "actor_lr"          : 3e-4,
        "critic_lr"         : 1e-3,
        "gamma"             : 0.9999,
        "tau"               : 5e-3,
        "batch_size"        : SIX_JOB_MAAC_BATCH,
        "attention_heads"   : 4,         # launcher build_jobs usa attend_heads=4 (estable)
        "hidden_dim"        : SIX_JOB_MAAC_HIDDEN,
        "replay_buffer_size": SIX_JOB_MAAC_BUF,
        "steps_per_update"  : 50,
        "num_updates"       : SIX_JOB_MAAC_UPDATES,
        "reward_scale"      : 10.0,
        "action_bins"       : 3,
        "n_discrete_actions": 89,
    },'''
    if old_maac in c042:
        c042 = c042.replace(old_maac, new_maac)
        changes.append("042: MAAC HYPERPARAMS aligned to SIX_JOB_*")
    else:
        changes.append("042: WARN MAAC HYPERPARAMS block not matched")

    # HAPPO n_rollout_threads: use auto-allocated value
    c042 = c042.replace(
        '        "n_rollout_threads" : 2,         # SubprocVecEnv: 2 rollouts paralelos/job\n',
        '        "n_rollout_threads" : HAPPO_ROLLOUT_THREADS,  # auto por vCPU (celda 6.1)\n',
    )
    c042 = c042.replace(
        "POST_TRAINING_INCLUDE_SECTION_8 = True   # 8.1, 8.1b, 8.2\n"
        "POST_TRAINING_INCLUDE_SECTION_9 = True   # 9.1, 9.2 (evaluacion estadistica)\n",
        "POST_TRAINING_INCLUDE_SECTION_8 = True   # 8.1 (+export) y 8.2\n"
        "POST_TRAINING_INCLUDE_SECTION_9 = True   # 9.1 (+resumen_comparativo)\n",
    )
    set_src(cells[42], c042)

    # ─── Cell 043: clarify quick test vs official ───
    set_src(
        cells[43],
        """### 6.2 Prueba rápida de validación — 1 episodio por algoritmo

> **SOLO PARA VERIFICAR QUE EL PIPELINE FUNCIONA.** No usar como resultado de entrenamiento.
> El entrenamiento oficial usa **N_EPISODES = 50** por corrida (celda **7.2**), reanudable con `--skip-completed`.

Activa con `QUICK_TEST = True` en la celda **6.1**, luego ejecuta esta celda. Comprueba:
- que el launcher, los scripts y los módulos cargan correctamente;
- que cada algoritmo arranca 1 episodio corto (168 pasos) sin error.

Si `QUICK_TEST = False` (default), la celda solo imprime instrucciones y no entrena.
""",
    )
    changes.append("043: clarified 6.2 vs official training")

    # ─── Cell 049: from-scratch + two-phase clear; salvage as secondary ───
    set_src(
        cells[49],
        """### 7.2 Entrenamiento de 50 episodios por corrida (reanudable con --skip-completed)

Ejecuta **12 corridas desde cero o reanudadas** en **dos fases** (`two_phase_happo_masac`):
- **Fase 1** HAPPO×3 + MASAC×3 (6 paralelos) → **Fase 2** MATD3×3 + MAAC×3 (6 paralelos)

Prior de tiempo: ~12 min/ep por fase → **~20 h** wall con 50 ep (ETA dinámico con FPS en `live_progress.json`).

**Desde cero:** deja `LAUNCH_FULL_TRAINING = True` y ejecuta tras **6.1 → 7.0 → 7.1**. Se crean/usan las 12 carpetas bajo `OUTPUT_ROOT`.

**Reanudación:** si Colab se desconecta, **re-ejecuta solo esta celda 7.2**. El bootstrap integrado hace: git hard sync, montar Drive, detectar el mismo `OUTPUT_ROOT`, dry-run interno y lanzamiento con `--skip-completed` (omite jobs con `results.json` completo; reanuda checkpoints `.pt`).

> **Opcional (salvage HAPPO 49/50):** si el plan es solo tails KPI, **7.2** también los cubre; celda **2.3** es atajo solo-KPI (`skip` por defecto).

Al terminar con exit=0: verifica artefactos (12/12) y, si `AUTO_RUN_POST_TRAINING=True`, ejecuta **7.3→9.x** (`AUTO_DISCONNECT_COLAB=False` por defecto).
""",
    )
    changes.append("049: clarified from-scratch + two-phase; salvage secondary")

    # ─── Insert markdown for 7.4 before cell 053 (if missing) ───
    # Check if cell 052 is already markdown about 7.4
    prev = cell_src(cells[52])
    if "7.4" not in prev and cells[53]["cell_type"] == "code":
        new_md = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 7.4 Auditoría y reorganización de artefactos\n",
                "\n",
                "Tras el entrenamiento (o al reabrir el notebook), la celda **7.4** verifica que cada uno de los 12 jobs tenga `results.json`, `timeseries.csv` y checkpoints. La celda **7.4b** (opcional) exporta al formato canónico de tesis bajo `outputs/{MADRL}/{escenario}/`.\n",
            ],
        }
        cells.insert(53, new_md)
        changes.append("INSERT: markdown 7.4 before audit cells")
    else:
        changes.append("7.4 markdown: skipped (already present or unexpected layout)")

    # Re-resolve indices after possible insert
    # Find section 10 code cell and section 8 markdown by content
    idx_s8 = next(i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and "Sección 8:" in cell_src(c))
    idx_s10_code = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "code" and "RESUMEN FINAL — MADRL CityLearn v3" in cell_src(c)
    )
    idx_informe_md = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "markdown" and "Informe Técnico de Supervisión" in cell_src(c)
    )
    idx_proximos = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "markdown" and "Proximos pasos y referencias" in cell_src(c)
    )

    # Fix section 8 artifact tree
    set_src(
        cells[idx_s8],
        """## Sección 8: Análisis de resultados y KPIs

### Estructura de artefactos (formato canónico `outputs/{MADRL}/{escenario}/`)
```
{OUTPUT_ROOT}/
  HAPPO/
    E1/  data/results.json  data/timeseries.csv  checkpoints/  figures/
    E2/  ...
    E3/  ...
  MASAC/ MATD3/ MAAC/  → misma estructura
  resumen_comparativo/   (generado en 9.x)
    comparison_metrics.csv  best_madrl_selection.csv
    best_madrl_report.json  global_comparison.png
```

> **Nota:** El launcher escribe `{MADRL}/E*/data/`. La celda **7.4b** puede exportar nombres simples de tesis. Las celdas **8.1** y **8.2** leen ambos layouts.
""",
    )
    changes.append(f"{idx_s8:03d}: fixed Seccion 8 artifact paths (E1/E2/E3)")

    # Insert section 10 markdown if missing before resumen code
    before_s10 = cell_src(cells[idx_s10_code - 1]) if idx_s10_code > 0 else ""
    if "Sección 10" not in before_s10 and "Seccion 10" not in before_s10:
        md10 = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Sección 10: Resumen final de la sesión\n",
                "\n",
                "Imprime un resumen ejecutivo del run (`OUTPUT_ROOT`, jobs completos, rutas clave). Ejecutar al cierre de la sesión Colab o tras reanudar.\n",
            ],
        }
        cells.insert(idx_s10_code, md10)
        changes.append("INSERT: markdown Seccion 10 before resumen")
        # indices after this insert shift by 1 for later cells
        idx_informe_md += 1
        idx_proximos += 1

    # Fix proximos pasos paths
    set_src(
        cells[idx_proximos],
        """## Próximos pasos y referencias

### Para el entrenamiento de 50 episodios por corrida (reanudable)
1. Si Colab se desconecta, vuelve a ejecutar la celda **7.2** (bootstrap + `--skip-completed`).
2. Para revisar estado sin entrenar: `CityLearn/scripts/colab_a100_live_monitor.py --output-root <OUTPUT_ROOT> --once`.

### Artefactos generados por corrida (12 jobs principales)
```
{OUTPUT_ROOT}/
  HAPPO/  MASAC/  MATD3/  MAAC/
    E1 / E2 / E3 /
      data/
        results.json           — artefactos + KPIs finales
        timeseries.csv         — metricas por episodio
        training_summary.json  — hiperparametros + resumen
      checkpoints/             — modelos .pt por agente
      figures/                 — graficos de KPIs vs baseline
  official_full_status.json
  live_progress.json
```

### Para validez estadistica fuerte
- Repetir con seeds adicionales (`--seed 1, 2, ...`) cuando haya presupuesto GPU.
- Benchmarks CityLearn v2 (PPO/SAC/A2C): celda **7.6** (no forman parte de los 12 jobs MADRL).

### Repositorio
[Mac-Tapia/CityLearn](https://github.com/Mac-Tapia/CityLearn) · [MADRLCitytleranflexresdr](https://github.com/Mac-Tapia/MADRLCitytleranflexresdr)
Tesis: *Diseño y validación de un sistema eléctrico inteligente con control multiagente MADRL, Iquitos 2026*
Contacto: mac.tapia@unmsm.edu.pe
""",
    )
    changes.append(f"{idx_proximos:03d}: fixed Proximos pasos paths + accents")

    # ─── Cell 000: tiny consistency (keep scientific content) ───
    c000 = cell_src(cells[0])
    if "two_phase_happo_masac (6+6 paralelo)" in c000:
        changes.append("000: left scientific intro intact")

    # ─── Sanity: ensure EXECUTION_MODE / N_EPISODES / two_phase still in 6.1 ───
    # Find 6.1 code cell
    idx_61 = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "code" and "EXECUTION_MODE = 'two_phase_happo_masac'" in cell_src(c)
    )
    src61 = cell_src(cells[idx_61])
    assert "N_EPISODES      = 50" in src61
    assert "EXECUTION_MODE = 'two_phase_happo_masac'" in src61
    assert "LAUNCH_FULL_TRAINING" not in src61  # belongs to 7.2

    idx_72 = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "code" and "LAUNCH_FULL_TRAINING = True" in cell_src(c)
    )
    src72 = cell_src(cells[idx_72])
    assert "('happo', 'masac')" in src72 and "('matd3', 'maac')" in src72

    # Final count
    nb["cells"] = cells
    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Build post-map
    map_lines = [f"Total cells after cleanup: {len(cells)}", ""]
    for i, c in enumerate(cells):
        s = cell_src(c).strip()
        first = s.splitlines()[0][:100] if s else "(empty)"
        map_lines.append(f"{i:03d} [{c['cell_type'][:8]:8}] {first}")

    report = [
        "CLEANUP REPORT",
        "=" * 60,
        f"Backup: {BACKUP}",
        f"Cells before: 70",
        f"Cells after: {len(cells)}",
        "",
        "Changes:",
        *[f"  - {x}" for x in changes],
        "",
        "Sanity:",
        f"  - 6.1 cell idx={idx_61}: N_EPISODES=50 + two_phase OK",
        f"  - 7.2 cell idx={idx_72}: LAUNCH_FULL_TRAINING + phase tuples OK",
        "",
        *map_lines,
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report[:40]))
    print(f"... wrote full report to {REPORT}")


if __name__ == "__main__":
    main()
