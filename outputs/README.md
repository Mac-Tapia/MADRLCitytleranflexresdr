# outputs/

Arbol plano: solo entrenamiento MADRL + archivo historico.

```
outputs/
  README.md
  latest_colab_output_root.txt
  latest_visible_training_output_root.txt
  <run_timestamp>/              # corrida activa o nueva (madrl_v3_* / citylearn_v3_madrl_full_*)
    happo|E1_seed_0/ ...
    masac/ matd3/ maac/
    official_full_status.json
  _archive/                       # todo lo demas (dry-runs, benchmarks, runs viejos) — sin subcarpetas
```

Auditorias de dataset: `data/dataset_audit/` (no van aqui).
Cache CSV: `data/cache/` (no versionar).

Reorganizar: `powershell -ExecutionPolicy Bypass -File scripts/simplify_outputs.ps1`
