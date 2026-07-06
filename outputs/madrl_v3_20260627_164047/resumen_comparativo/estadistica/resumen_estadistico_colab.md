# Estadistica Colab/Drive — madrl_v3_20260627_164047

Fuente: KPIs auditados (MATD3, MAAC, MASAC; HAPPO sin KPIs finales).

## Descriptivo — distrito (9 tratamientos con KPI)

| Algoritmo | Esc. | Flex | Delta CO2 (kg) | Delta costo (EUR) | EV exito |
|-----------|------|------|----------------|-------------------|----------|
| MASAC | E1 | 1.0286 | 81,227 | 14,672 | 3.9% |
| MASAC | E2 | 1.0318 | 77,649 | 15,020 | 4.1% |
| MASAC | E3 | 1.0297 | 90,900 | 19,793 | 4.1% |
| MATD3 | E1 | 1.0009 | 36,723 | 33,075 | 43.9% |
| MATD3 | E2 | 1.0007 | 23,070 | 13,935 | 36.4% |
| MATD3 | E3 | 1.0006 | 41,293 | 44,399 | 48.2% |
| MAAC | E1 | 1.0124 | 38,566 | 3,628 | 4.2% |
| MAAC | E2 | 1.0172 | 70,654 | 13,275 | 4.1% |
| MAAC | E3 | 1.0138 | 73,411 | 9,515 | 4.1% |

## Inferencial — KPI-level (231 scores, signed_relative_gain)

- Kruskal-Wallis ALL: H=3.7230956751395587, p=0.1554 (no significativo α=0.05)
- Shapiro-Wilk: normalidad rechazada en MASAC, MATD3, MAAC → tests no parametricos justificados.
- Wilcoxon ALL: MASAC vs MATD3 p=0.0049 (significativo); demas pares no significativos en MWU.

## Inferencial — score por escenario (notebook 9.1, 3 algos)

- Kruskal-Wallis: H=4.3556, p=0.1133
- MAAC: media score escenario=0.8066, desv=0.1474
- MASAC: media score escenario=0.1694, desv=0.2028
- MATD3: media score escenario=0.6323, desv=0.3752

## Referencia local v4 (5 ep, 4 algos)

- Kruskal-Wallis ALL p=0.0459 (historico); no sustituye la corrida canonica Colab.

Archivos: analisis_estadistico_madrl.csv, comparaciones_mwu_madrl.csv, comparaciones_wilcoxon_madrl.csv, hipotesis_estadisticas_madrl.csv