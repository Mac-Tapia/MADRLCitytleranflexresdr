## Sección 8: Análisis de resultados y KPIs

### Estructura de artefactos (formato canónico `outputs/{MADRL}/{escenario}/`)
```
{OUTPUT_ROOT}/
  HAPPO/
    E1/  metrics.csv  rewards.csv  training_monitor.csv
                  resource_usage.csv  config.json  checkpoint.pt  figures/
    escenario_2/  ...
    escenario_3/  ...
  MASAC/ MATD3/ MAAC/  → misma estructura
  resumen_comparativo/
    comparison_metrics.csv  best_madrl_selection.csv
    best_madrl_report.json  global_comparison.png
```

> **Nota:** La celda 7.4b reorganiza los artefactos del launcher
> (`HAPPO/E1/data/`) con nombres simples. Las celdas 8.1 y 8.2 leen
> ambos formatos para garantizar compatibilidad.
