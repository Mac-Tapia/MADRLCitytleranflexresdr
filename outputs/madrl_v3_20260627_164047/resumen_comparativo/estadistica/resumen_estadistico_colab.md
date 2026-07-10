# Estadistica Colab/Drive — madrl_v3_20260627_164047

Fuente: episodios reales timeseries.csv + KPI-gains auditados (MATD3, MAAC, MASAC; HAPPO sin KPIs finales).

## Descriptivo — episodios por OE (mean, median, std, min, max)

| OE | Algoritmo | n ep. | Media | Mediana | Desv. | Min | Max |
|----|-----------|-------|-------|---------|-------|-----|-----|
| OE1 | HAPPO | 49 | -0.6303 | -0.6303 | 0.0213 | -0.7062 | -0.5953 |
| OE1 | MAAC | 50 | -0.6052 | -0.6126 | 0.0147 | -0.6215 | -0.5844 |
| OE1 | MASAC | 50 | -0.6133 | -0.6198 | 0.0141 | -0.6278 | -0.5896 |
| OE1 | MATD3 | 50 | -0.6330 | -0.6208 | 0.0470 | -0.7408 | -0.5918 |
| OE2 | HAPPO | 49 | 883.0026 | 804.8169 | 287.0341 | 468.0088 | 1524.4027 |
| OE2 | MAAC | 50 | 1056.3904 | 1132.6331 | 99.3812 | 873.2478 | 1139.5708 |
| OE2 | MASAC | 50 | 1078.3685 | 1132.6354 | 121.1007 | 925.7449 | 1638.7394 |
| OE2 | MATD3 | 50 | 1132.1936 | 1137.4044 | 236.7845 | 925.7449 | 1864.8390 |
| OE3 | HAPPO | 49 | 352.5741 | 232.4868 | 381.7126 | -0.0000 | 1415.9391 |
| OE3 | MAAC | 50 | 795.3938 | 689.5406 | 211.9561 | 643.3720 | 1138.8164 |
| OE3 | MASAC | 50 | 812.1613 | 689.5406 | 206.3762 | 643.3720 | 1192.3210 |
| OE3 | MATD3 | 50 | 759.2886 | 690.9834 | 303.8794 | 13.4390 | 1143.6113 |

## Inferencial — protocolo KPI-gains (Shapiro → KW → MWU → Wilcoxon)

- Kruskal-Wallis ALL: H=3.7230956751395587, p=0.1554 (no significativo α=0.05)
- Kruskal-Wallis OE.1: p=0.2806
- Kruskal-Wallis OE.2: p=0.5457
- Kruskal-Wallis OE.3: p=0.3881
- Shapiro-Wilk: normalidad rechazada en MASAC, MATD3, MAAC → tests no parametricos justificados.
- Wilcoxon significativos (α=0.05): OE1: MASAC vs MATD3 p=0.0410; OE1: MASAC vs MAAC p=0.0013; OE2: MASAC vs MAAC p=0.0077; OE3: MASAC vs MAAC p=0.0333; ALL: MASAC vs MATD3 p=0.0049; ALL: MASAC vs MAAC p=0.0000

## Inferencial — score por escenario (notebook 9.1, 3 algos)

- Kruskal-Wallis: H=4.3556, p=0.1133
- MAAC: media score escenario=0.8066, desv=0.1474
- MASAC: media score escenario=0.1694, desv=0.2028
- MATD3: media score escenario=0.6323, desv=0.3752

## Referencia local v4 (5 ep, 4 algos)

- Kruskal-Wallis ALL p=0.0459 (historico); no sustituye la corrida canonica Colab.

Archivos: analisis_estadistico_madrl.csv, comparaciones_mwu_madrl.csv, comparaciones_wilcoxon_madrl.csv, hipotesis_estadisticas_madrl.csv