### Estrategia de entrenamiento en dos fases (Colab A100)

| Fase | Algoritmos | Jobs paralelos | Notas |
|:---:|:---|:---:|:---|
| **1** | HAPPO + MASAC | 6 (E1/E2/E3) | MASAC buffer en GPU VRAM; arrancan los 6 a la vez |
| **2** | MATD3 + MAAC | 6 (E1/E2/E3) | Backfill dinámico: cada job de Fase 2 (más liviano primero: MAAC, luego MATD3) entra **solo al terminar un job de Fase 1** (uno-a-uno), respetando el cap de 6 |

Regla del lanzamiento (robusta, `run_dynamic_backfill_jobs`): la Fase 2 **nunca** arranca antes de que termine un job de Fase 1; cada finalización de Fase 1 habilita exactamente un ingreso de Fase 2 (lightest-first), dentro del cap por VRAM. Modo launcher: `--execution-mode two_phase_happo_masac` (backfill dinámico por defecto; `--no-dynamic-backfill` usa barrera estricta). Reanudacion: `--skip-completed`.
