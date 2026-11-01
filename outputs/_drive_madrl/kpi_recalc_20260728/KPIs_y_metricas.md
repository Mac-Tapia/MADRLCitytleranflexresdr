# KPIs y metricas recalculados desde Drive

Fuente: [Drive folder](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)
Run: `madrl_v3_20260627_164047`
Generado: 2026-07-28T23:53:23.959930+00:00

- Tratamientos: **12**/12
- Catalogo core KPI: **14** nombres
- Valores core: **176**
- Filas building KPI: **15300**
- Mejor MADRL (score global normalizado): **MAAC**

## Ranking OE

| Rank | Algoritmo | Score global | OE1 flex | OE2 CO2 | OE3 costo | flex_composite E1 | CO2 delta E2 | Cost delta E3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MAAC | 0.9538 | 0.8951 | 0.9662 | 1.0000 | 1.012426 | 70654.1907 | 9515.1518 |
| 2 | MATD3 | 0.8805 | 1.0000 | 1.0000 | 0.6415 | 1.000923 | 23070.4185 | 44399.3641 |
| 3 | MASAC | 0.8679 | 0.7479 | 0.9612 | 0.8944 | 1.028553 | 77648.9878 | 19792.7926 |
| 4 | HAPPO | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.110541 | 1431341.1469 | 106827.9908 |

## Resumen KPI-gains (hipotesis)

| Grupo | Algoritmo | n | Media gain | Mediana | Mejorados | No mejorados | % mejorados |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OE1_E1_flex | HAPPO | 4 | -0.1105 | -0.0972 | 1 | 3 | 25.0% |
| OE1_E1_flex | MASAC | 4 | -0.0286 | -0.0253 | 1 | 3 | 25.0% |
| OE1_E1_flex | MATD3 | 4 | -0.0009 | -0.0010 | 1 | 3 | 25.0% |
| OE1_E1_flex | MAAC | 4 | -0.0124 | -0.0117 | 1 | 3 | 25.0% |
| OE2_E2_co2 | HAPPO | 2 | -715670.8531 | -715670.8531 | 0 | 2 | 0.0% |
| OE2_E2_co2 | MASAC | 2 | -38824.5197 | -38824.5197 | 0 | 2 | 0.0% |
| OE2_E2_co2 | MATD3 | 2 | -11535.2303 | -11535.2303 | 0 | 2 | 0.0% |
| OE2_E2_co2 | MAAC | 2 | -35327.1189 | -35327.1189 | 0 | 2 | 0.0% |
| OE3_E3_cost | HAPPO | 2 | -53414.0103 | -53414.0103 | 0 | 2 | 0.0% |
| OE3_E3_cost | MASAC | 2 | -9896.3991 | -9896.3991 | 0 | 2 | 0.0% |
| OE3_E3_cost | MATD3 | 2 | -22199.6866 | -22199.6866 | 0 | 2 | 0.0% |
| OE3_E3_cost | MAAC | 2 | -4757.5772 | -4757.5772 | 0 | 2 | 0.0% |
| ALL_hypothesis_kpis | HAPPO | 24 | -146338.7469 | -0.1680 | 5 | 19 | 20.8% |
| ALL_hypothesis_kpis | MASAC | 24 | -12469.2281 | -0.0417 | 3 | 21 | 12.5% |
| ALL_hypothesis_kpis | MATD3 | 24 | -8020.6633 | -0.0076 | 3 | 21 | 12.5% |
| ALL_hypothesis_kpis | MAAC | 24 | -8710.4211 | -0.0235 | 3 | 21 | 12.5% |

## Metricas episodicas (district_episode_kpis)

| Algo | Esc | n | reward mean | emission mean | cost mean |
| --- | --- | --- | --- | --- | --- |
| HAPPO | E1 | 49 | -0.6303 | 1046.35 | 463.72 |
| HAPPO | E2 | 49 | -0.4842 | 883.00 | 195.45 |
| HAPPO | E3 | 49 | -0.5208 | 839.72 | 352.57 |
| MAAC | E1 | 50 | -0.6052 | 1054.33 | 642.61 |
| MAAC | E2 | 50 | -0.5237 | 1056.39 | 707.47 |
| MAAC | E3 | 50 | -0.5387 | 1053.55 | 795.39 |
| MASAC | E1 | 50 | -0.6133 | 1076.48 | 664.74 |
| MASAC | E2 | 50 | -0.5255 | 1078.37 | 701.76 |
| MASAC | E3 | 50 | -0.5409 | 1082.90 | 812.16 |
| MATD3 | E1 | 50 | -0.6330 | 1129.24 | 631.51 |
| MATD3 | E2 | 50 | -0.5336 | 1132.19 | 669.46 |
| MATD3 | E3 | 50 | -0.5504 | 1131.14 | 759.29 |
