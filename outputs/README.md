# outputs/

Solo artefactos del pipeline MADRL CityLearn v3. Estructura vigente:

```
outputs/
  README.md
  latest_colab_output_root.txt          # puntero al OUTPUT_ROOT activo (Colab)
  latest_visible_training_output_root.txt
  dataset_audit/                        # compuertas de dataset (no es un run de entrenamiento)
  runs/                                 # corridas oficiales y Colab (12 jobs MADRL)
    citylearn_v3_madrl_full_<timestamp>/
    madrl_v3_<timestamp>/
    rescued_happo_<timestamp>/          # rescates parciales HAPPO (opcional)
  _archive/
    dryruns/                            # validate_*, codex_*, notebook_verify_*, etc.
    benchmarks/                         # v2 baseline, SB3 smoke, comparaciones
    reports/                            # PDF/plan tesis, evidencia objetiva, informes
    <runs obsoletos o fallidos>
```

## Layout de cada run (`runs/<nombre>/`)

```
<happo|masac|matd3|maac>/E{1,2,3}_seed_0/
  data/results.json
  data/timeseries.csv
  checkpoints/
  figures/
  live_progress.json
official_full_status.json
official_full_manifest.json
run_context_manifest.json
```

## Reglas

- Nuevos entrenamientos → `outputs/runs/` (nunca en la raíz de `outputs/`).
- Dry-runs y pruebas → `outputs/_archive/dryruns/`.
- No mezclar benchmarks ni documentos de tesis en `runs/`.
- Reorganizar con: `powershell -ExecutionPolicy Bypass -File scripts/reorganize_outputs.ps1`
