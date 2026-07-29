# KPIs distrito y edificio — Drive 50 episodios (4 MADRL)

Corrida canónica: `madrl_v3_20260627_164047`.
Fuente: `kpi_recalc_20260728` + `building_behavior_summary.csv` (no caja negra).

## 1. Distrito — ranking por escenario

### E1 (OE.1)

| Rank | Algoritmo | KPI primario | Valor |
|------|-----------|--------------|-------|
| 1 | MATD3 | flex_composite | 1.0009 |
| 2 | MAAC | flex_composite | 1.0124 |
| 3 | MASAC | flex_composite | 1.0286 |
| 4 | HAPPO | flex_composite | 1.1105 |

### E2 (OE.2)

| Rank | Algoritmo | KPI primario | Valor |
|------|-----------|--------------|-------|
| 1 | MATD3 | carbon_emissions_delta | 23,070 |
| 2 | MAAC | carbon_emissions_delta | 70,654 |
| 3 | MASAC | carbon_emissions_delta | 77,649 |
| 4 | HAPPO | carbon_emissions_delta | 1,431,341 |

### E3 (OE.3)

| Rank | Algoritmo | KPI primario | Valor |
|------|-----------|--------------|-------|
| 1 | MAAC | electricity_cost_delta | 9,515 |
| 2 | MASAC | electricity_cost_delta | 19,793 |
| 3 | MATD3 | electricity_cost_delta | 44,399 |
| 4 | HAPPO | electricity_cost_delta | 106,828 |

## 2. Mejor edificio por algoritmo × escenario

| Algo | Esc. | OE | Mejor edificio | Nombre | Valor KPI | BESS thr. | EV charge | EV éxito |
|------|------|----|----------------|--------|-----------|-----------|-----------|----------|
| HAPPO | E1 | OE.1 | B11 | HOSPITAL REGIONAL DE LORETO | 0.0022 | 438,445 | 1,980 | 0.415 |
| HAPPO | E2 | OE.2 | B09 | GOBIERNO REGIONAL DE LORETO - CO | -6,060 | 99,087 | 5,926 | 0.573 |
| HAPPO | E3 | OE.3 | B11 | HOSPITAL REGIONAL DE LORETO | 193,218 | 1,267,328 | 1,741 | 0.454 |
| MASAC | E1 | OE.1 | B05 | HOTEL PLAZA S.A. | -0.0052 | 7,074 | 255 | 0.044 |
| MASAC | E2 | OE.2 | B09 | GOBIERNO REGIONAL DE LORETO - CO | -847 | 3,618 | 244 | 0.022 |
| MASAC | E3 | OE.3 | B11 | HOSPITAL REGIONAL DE LORETO | 2,304 | 28,456 | 494 | 0.065 |
| MATD3 | E1 | OE.1 | B14 | AUTORIDAD PORTUARIA NACIONAL | 0.1267 | 64 | 0 | 0.000 |
| MATD3 | E2 | OE.2 | B12 | SEGURO SOCIAL DE SALUD - ESSALUD | 2,163 | 1,223 | 0 | 0.000 |
| MATD3 | E3 | OE.3 | B12 | SEGURO SOCIAL DE SALUD - ESSALUD | 2,672 | 1,223 | 0 | 0.000 |
| MAAC | E1 | OE.1 | B05 | HOTEL PLAZA S.A. | -0.0023 | 4,820 | 203 | 0.050 |
| MAAC | E2 | OE.2 | B02 | MUNICIPALIDAD DISTRITAL DE SAN J | -715 | 3,220 | 60 | 0.017 |
| MAAC | E3 | OE.3 | B14 | AUTORIDAD PORTUARIA NACIONAL | 684 | 6,435 | 451 | 0.010 |

## 3. Criterio de ranking edificio

- **OE.1 / E1 flexibilidad:** `flex_gain_vs_baseline = 1 − import_ratio` (mayor = mejor).
- **OE.2 / E2 CO₂:** `co2_reduction_kgco2 = −emissions_delta` (mayor = más reducción).
- **OE.3 / E3 costo:** `cost_reduction_eur = −cost_delta` (mayor = más reducción).
- Control de recursos reportado: throughput BESS, carga EV, éxito salida EV, rol de red.
