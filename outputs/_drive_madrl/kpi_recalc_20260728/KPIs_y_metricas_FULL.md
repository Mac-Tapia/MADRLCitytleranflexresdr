# KPIs y metricas recalculados desde Drive (evaluate_v2 completo)

Fuente: [Drive folder](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)
Run: `madrl_v3_20260627_164047`
Generado: 2026-07-28T23:56:58.368286+00:00

- Catalogo `citylearn_v3_report.all_values`: **58** KPIs
- Valores totales (4 algos x 3 escenarios): **680**
- Mejor MADRL (4/4, incluye HAPPO): **MAAC**
- Mejor MADRL (canonico 3/3, sin HAPPO): **MATD3**

## Ranking OE — 4 algoritmos

| Rank | Algoritmo | Score | OE1 | OE2 | OE3 | flex_E1 | CO2d_E2 | Costd_E3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MAAC | 0.9538 | 0.8951 | 0.9662 | 1.0000 | 1.012426 | 70654.19 | 9515.15 |
| 2 | MATD3 | 0.8805 | 1.0000 | 1.0000 | 0.6415 | 1.000923 | 23070.42 | 44399.36 |
| 3 | MASAC | 0.8679 | 0.7479 | 0.9612 | 0.8944 | 1.028553 | 77648.99 | 19792.79 |
| 4 | HAPPO | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.110541 | 1431341.15 | 106827.99 |

## Ranking OE — canonico (MASAC/MATD3/MAAC)

| Rank | Algoritmo | Score | OE1 | OE2 | OE3 | flex_E1 | CO2d_E2 | Costd_E3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MATD3 | 0.6667 | 1.0000 | 1.0000 | 0.0000 | 1.000923 | 23070.42 | 44399.36 |
| 2 | MAAC | 0.5706 | 0.5837 | 0.1282 | 1.0000 | 1.012426 | 70654.19 | 9515.15 |
| 3 | MASAC | 0.2351 | 0.0000 | 0.0000 | 0.7054 | 1.028553 | 77648.99 | 19792.79 |

## KPI-gains por OE (all_values)

| Grupo | Algoritmo | n | Media | Mediana | Mejorados | % |
| --- | --- | --- | --- | --- | --- | --- |
| OE1_E1_flex | HAPPO | 6 | -0.1572 | -0.0972 | 2 | 33.3% |
| OE1_E1_flex | MASAC | 6 | -0.0277 | -0.0253 | 2 | 33.3% |
| OE1_E1_flex | MATD3 | 6 | -0.0055 | -0.0010 | 2 | 33.3% |
| OE1_E1_flex | MAAC | 6 | -0.0127 | -0.0117 | 2 | 33.3% |
| OE2_E2_co2 | HAPPO | 2 | -715670.8531 | -715670.8531 | 0 | 0.0% |
| OE2_E2_co2 | MASAC | 2 | -38824.5197 | -38824.5197 | 0 | 0.0% |
| OE2_E2_co2 | MATD3 | 2 | -11535.2303 | -11535.2303 | 0 | 0.0% |
| OE2_E2_co2 | MAAC | 2 | -35327.1189 | -35327.1189 | 0 | 0.0% |
| OE3_E3_cost | HAPPO | 2 | -53414.0103 | -53414.0103 | 0 | 0.0% |
| OE3_E3_cost | MASAC | 2 | -9896.3991 | -9896.3991 | 0 | 0.0% |
| OE3_E3_cost | MATD3 | 2 | -22199.6866 | -22199.6866 | 0 | 0.0% |
| OE3_E3_cost | MAAC | 2 | -4757.5772 | -4757.5772 | 0 | 0.0% |

## Inferencia episodica (Shapiro + Kruskal)

| OE | Algo | n | mean | median | Shapiro p | KW p |
| --- | --- | --- | --- | --- | --- | --- |
| OE1 | HAPPO | 49 | -0.6302595084115008 | -0.6303079866851847 | 0.00035935695632360876 |  |
| OE1 | MASAC | 50 | -0.6133306039931886 | -0.6198266866174633 | 1.3063412040992262e-07 |  |
| OE1 | MATD3 | 50 | -0.6330435627356475 | -0.6208251460013352 | 4.9697614912247445e-09 |  |
| OE1 | MAAC | 50 | -0.6051573274768176 | -0.6126499299083629 | 8.482652447128203e-08 |  |
| OE1 | ALL_KRUSKAL | 199 | nan | nan | 1.959331223860867e-11 | 1.959331223860867e-11 |
| OE2 | HAPPO | 49 | 883.002641347598 | 804.8168544769287 | 0.008154917508363724 |  |
| OE2 | MASAC | 50 | 1078.3684531803428 | 1132.6354122161863 | 1.4532379566389864e-07 |  |
| OE2 | MATD3 | 50 | 1132.1936166521907 | 1137.4043860435486 | 2.921810016154325e-10 |  |
| OE2 | MAAC | 50 | 1056.3903547742964 | 1132.6330785155296 | 1.0447892329068509e-08 |  |
| OE2 | ALL_KRUSKAL | 199 | nan | nan | 2.7416281510917326e-05 | 2.7416281510917326e-05 |
| OE3 | HAPPO | 49 | 352.5740728388179 | 232.48682975769043 | 2.9542197808041237e-05 |  |
| OE3 | MASAC | 50 | 812.1612727615982 | 689.5406340360641 | 5.34453548084457e-09 |  |
| OE3 | MATD3 | 50 | 759.2885912102461 | 690.9834417104721 | 5.992915248498321e-07 |  |
| OE3 | MAAC | 50 | 795.3938091005385 | 689.5406326055527 | 1.1234708718887987e-09 |  |
| OE3 | ALL_KRUSKAL | 199 | nan | nan | 1.6425113687237728e-10 | 1.6425113687237728e-10 |

## Archivos generados

- `tables/all_evaluate_v2_kpis_long.csv`
- `tables/all_evaluate_v2_kpis_wide.csv`
- `tables/E1_OE1_all_values.csv`
- `tables/E2_OE2_all_values.csv`
- `tables/E3_OE3_all_values.csv`
- `tables/ranking_oe_scores_all_values.csv`
- `tables/kpi_gains_summary_all_values.csv`
- `tables/episode_inferential_by_oe.csv`
- `kpi_metrics_report_full.json`
