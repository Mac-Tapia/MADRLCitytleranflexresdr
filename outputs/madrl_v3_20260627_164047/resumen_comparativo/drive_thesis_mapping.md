# Análisis Colab/Drive — madrl_v3_20260627_164047

## Conclusiones

- La corrida canónica en Drive fue localizada usando el conector de Google Drive en la carpeta compartida del usuario.
- La estructura real en Drive sigue el layout del proyecto: `outputs/madrl_v3_20260627_164047/{HAPPO,MASAC,MATD3,MAAC}/{E1,E2,E3}/`.
- El análisis local correcto se apoya en `outputs/_drive_madrl/kpis/` y `outputs/madrl_v3_20260627_164047/resumen_comparativo/`.
- El mejor MADRL global entre algoritmos con KPIs auditados es **MATD3**.
- `HAPPO` no debe entrar al ranking final todavía: quedó en `completed_with_salvage`, 49/50 episodios y sin KPIs post-evaluación.

## Qué corresponde a cada artefacto

- `best_madrl_report.json`: selección global del mejor MADRL, ranking y KPIs primarios.
  Ubicación: Capítulo 5.3 y Capítulo 6.
- `episode_audit.json`: evidencia de completitud real por `episodes_recorded`.
  Ubicación: Capítulo 5.1.
- `comparison_metrics_colab.csv`: base larga comparativa por algoritmo/escenario.
  Ubicación: tablas auxiliares del Capítulo 5.
- `drive_objective_summary.csv`: resumen sintético por objetivo OE1/OE2/OE3 generado en este análisis.
  Ubicación: Tabla operativa de resultados.
- `drive_ranking_scores.png`: figura de ranking global.
  Ubicación: Figura 5.1.
- `drive_objective_kpis.png`: figura comparativa por objetivo.
  Ubicación: apoyo para Figuras 5.2–5.5.
- `drive_episode_completion.png`: figura de cobertura de episodios.
  Ubicación: Sección 5.1, nota metodológica.

## Estado por algoritmo

- `HAPPO`: E1=49, E2=49, E3=49, `has_kpis=False`, `status=completed_with_salvage`. 49/50 episodios; sin KPIs; pendiente resume celda 2.3 por VecEnvWrapper.
- `MASAC`: E1=50, E2=50, E3=50, `has_kpis=True`, `status=ok`. KPIs auditados desde Drive y reconciliados por output_dir.
- `MATD3`: E1=50, E2=50, E3=50, `has_kpis=True`, `status=ok`. KPIs auditados desde Drive y reconciliados por output_dir.
- `MAAC`: E1=50, E2=50, E3=50, `has_kpis=True`, `status=ok`. KPIs auditados desde Drive y reconciliados por output_dir.

## Interpretación

- `MATD3` gana OE1 flexibilidad y OE2 CO₂ por los criterios usados en el flujo local.
- `MAAC` gana OE3 costo, pero pierde el ranking global.
- `MASAC` queda tercero entre algoritmos con KPIs.
- La narrativa del proyecto debe reportar `episodes_recorded=50` para MATD3/MAAC/MASAC y no el campo `episodes` del último resume.
