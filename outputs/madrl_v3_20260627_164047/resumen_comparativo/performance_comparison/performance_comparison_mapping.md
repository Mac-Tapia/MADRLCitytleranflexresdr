# Performance comparison — madrl_v3_20260627_164047

## Qué es esta figura

Cada `performance_comparison.png` resume el **desempeño descriptivo** de un MADRL
sobre la corrida canónica de **50 episodios**, en dos escalas:

1. **Distrito:** efecto primario vs baseline CityLearn (`favorable_effect_percent`)
   en E1 (flexibilidad), E2 (CO₂) y E3 (costo), comparado con los otros tres MADRL.
2. **Edificio:** heterogeneidad de los **17 edificios** Iquitos en el KPI del escenario
   (proxy de flexibilidad / ΔCO₂ / Δcosto).

Estas figuras son **descriptivas**. No sustituyen Shapiro → Kruskal/Friedman/Wilcoxon
ni las decisiones HE10–HE31 / H0G–H1G del Cap. 5.

## Archivos por algoritmo (resumen E1–E3)

### MATD3
- Archivo: `outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MATD3_performance_comparison.png`
- Lectura: E1: efecto distrito -0.092% sobre Efecto flex_composite vs baseline (%); 17 edificios en el panel inferior. E2: efecto distrito -0.419% sobre Efecto CO₂ total vs baseline (%); 17 edificios en el panel inferior. E3: efecto distrito -0.918% sobre Efecto costo eléctrico vs baseline (%); 17 edificios en el panel inferior.

### MAAC
- Archivo: `outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MAAC_performance_comparison.png`
- Lectura: E1: efecto distrito -1.243% sobre Efecto flex_composite vs baseline (%); 17 edificios en el panel inferior. E2: efecto distrito -1.353% sobre Efecto CO₂ total vs baseline (%); 17 edificios en el panel inferior. E3: efecto distrito -0.268% sobre Efecto costo eléctrico vs baseline (%); 17 edificios en el panel inferior.

### MASAC
- Archivo: `outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MASAC_performance_comparison.png`
- Lectura: E1: efecto distrito -2.855% sobre Efecto flex_composite vs baseline (%); 17 edificios en el panel inferior. E2: efecto distrito -1.704% sobre Efecto CO₂ total vs baseline (%); 17 edificios en el panel inferior. E3: efecto distrito -0.556% sobre Efecto costo eléctrico vs baseline (%); 17 edificios en el panel inferior.

### HAPPO
- Archivo: `outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/HAPPO_performance_comparison.png`
- Lectura: E1: efecto distrito -11.054% sobre Efecto flex_composite vs baseline (%); 17 edificios en el panel inferior. E2: efecto distrito -31.218% sobre Efecto CO₂ total vs baseline (%); 17 edificios en el panel inferior. E3: efecto distrito -2.978% sobre Efecto costo eléctrico vs baseline (%); 17 edificios en el panel inferior.

## Archivos por job (algoritmo × escenario)

| Algoritmo | Escenario | Archivo | Efecto distrito (%) | Líder escenario | Edificios |
|---|---|---|---:|---|---:|
| MATD3 | E1 | `outputs/madrl_v3_20260627_164047/MATD3/E1/figures/performance_comparison.png` | -0.092 | MATD3 | 17 |
| | | *En distrito (E1), MATD3 obtiene efecto primario -0.092% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.092%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MATD3 | E2 | `outputs/madrl_v3_20260627_164047/MATD3/E2/figures/performance_comparison.png` | -0.419 | MATD3 | 17 |
| | | *En distrito (E2), MATD3 obtiene efecto primario -0.419% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.419%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MATD3 | E3 | `outputs/madrl_v3_20260627_164047/MATD3/E3/figures/performance_comparison.png` | -0.918 | MAAC | 17 |
| | | *En distrito (E3), MATD3 obtiene efecto primario -0.918% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MAAC (-0.268%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MAAC | E1 | `outputs/madrl_v3_20260627_164047/MAAC/E1/figures/performance_comparison.png` | -1.243 | MATD3 | 17 |
| | | *En distrito (E1), MAAC obtiene efecto primario -1.243% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.092%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MAAC | E2 | `outputs/madrl_v3_20260627_164047/MAAC/E2/figures/performance_comparison.png` | -1.353 | MATD3 | 17 |
| | | *En distrito (E2), MAAC obtiene efecto primario -1.353% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.419%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MAAC | E3 | `outputs/madrl_v3_20260627_164047/MAAC/E3/figures/performance_comparison.png` | -0.268 | MAAC | 17 |
| | | *En distrito (E3), MAAC obtiene efecto primario -0.268% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MAAC (-0.268%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MASAC | E1 | `outputs/madrl_v3_20260627_164047/MASAC/E1/figures/performance_comparison.png` | -2.855 | MATD3 | 17 |
| | | *En distrito (E1), MASAC obtiene efecto primario -2.855% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.092%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MASAC | E2 | `outputs/madrl_v3_20260627_164047/MASAC/E2/figures/performance_comparison.png` | -1.704 | MATD3 | 17 |
| | | *En distrito (E2), MASAC obtiene efecto primario -1.704% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.419%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| MASAC | E3 | `outputs/madrl_v3_20260627_164047/MASAC/E3/figures/performance_comparison.png` | -0.556 | MAAC | 17 |
| | | *En distrito (E3), MASAC obtiene efecto primario -0.556% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MAAC (-0.268%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| HAPPO | E1 | `outputs/madrl_v3_20260627_164047/HAPPO/E1/figures/performance_comparison.png` | -11.054 | MATD3 | 17 |
| | | *En distrito (E1), HAPPO obtiene efecto primario -11.054% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.092%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| HAPPO | E2 | `outputs/madrl_v3_20260627_164047/HAPPO/E2/figures/performance_comparison.png` | -31.218 | MATD3 | 17 |
| | | *En distrito (E2), HAPPO obtiene efecto primario -31.218% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MATD3 (-0.419%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |
| HAPPO | E3 | `outputs/madrl_v3_20260627_164047/HAPPO/E3/figures/performance_comparison.png` | -2.978 | MAAC | 17 |
| | | *En distrito (E3), HAPPO obtiene efecto primario -2.978% (valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). Mejor descriptivo del escenario: MAAC (-0.268%). El panel derecho muestra la dispersión entre los 17 edificios: en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio.* | | | |

## Cómo leer los signos

- En distrito, el `%` es el efecto favorable reportado en `primary_objective_values.csv`.
  Valores **negativos** indican empeoramiento respecto al baseline (=1 o totales baseline).
- En edificio, ΔCO₂/Δcosto **negativo** = reducción local (mejora); **positivo** = aumento.
- HAPPO usa fallback de `building_kpis_raw.csv` cuando no hay fila en multiobjetivo.
