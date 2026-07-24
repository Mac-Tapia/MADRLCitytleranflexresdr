### 2.3 Completar HAPPO (49→50 ep) — **no excluido** del estudio MADRL

HAPPO E1/E2/E3 tiene checkpoints en Drive pero `results.json` salvage sin KPIs (`VecEnvWrapper`). **Debe** reanudarse aquí; no se elimina del análisis de 4 algoritmos.

Corrida canónica: `madrl_v3_20260627_164047` · `OUTPUT_ROOT` = carpeta del run en Drive.

1. **1.2 → 1.2b → 1.3** — git sync, verificar parches (`colab_verify_critical_patches.py`) e instalar HARL.
2. `HAPPO_KPI_MODE = 'dry_run'` → preflight checkpoints + comando resume.
3. `HAPPO_KPI_MODE = 'execute'` → 1 episodio restante × escenario + KPIs + `checkpoint_count` en `results.json`.
4. Tras completar: continúa con **Sección 8.x** (agregador KPIs) o ejecuta `python tools/aggregate_colab_drive_kpis.py` para incluir HAPPO en el ranking 4/4 MADRL.

> Checkpoints HAPPO viven en `{OUTPUT_ROOT}/HAPPO/E*/checkpoints/` en Drive — no borrar.