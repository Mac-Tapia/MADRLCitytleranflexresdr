# Análisis multiobjetivo Colab/Drive — madrl_v3_20260627_164047

## Alcance

- **Distrito:** KPIs agregados desde `citylearn_v3_report.all_values` en `outputs/_drive_madrl/kpis/*_results.json`.
- **Edificio:** KPIs desde `building_behavior_summary.csv` (17 filas por job) y `building_kpis.csv` (1275 filas).
- **Inventario:** 17 edificios Iquitos con nombre, tipo de uso, elementos controlados/no controlados y **185 cargadores EV** dimensionados.

## Objetivos multiobjetivo

| Escenario | Objetivo | KPI distrito principal | KPI edificio principal |
|-----------|----------|------------------------|-------------------------|
| E1 | OE1 Flexibilidad | flex_composite (peak+ramping+load_factor)/3 | flex_composite_proxy |
| E2 | OE2 CO₂ | carbon_emissions_delta_kg | carbon_emissions_delta_kgco2 |
| E3 | OE3 Costo | electricity_cost_delta_eur | electricity_cost_delta_eur |

## Elementos por edificio

- **Controlados (acciones MADRL):** BESS (`electrical_storage`), cargadores EV (`electric_vehicle_storage_*`), carga desplazable (`washing_machine_*`).
- **No controlados:** `non_shiftable_load`, refrigeración/ACS modeladas, generación FV fija.

## Artefactos generados

- `17`: building_cards_count
- `por_edificio`: building_cards_dir
- `building_detail_maac_by_scenario.md`: building_detail_maac_md
- `building_detail_masac_by_scenario.md`: building_detail_masac_md
- `building_detail_matd3_by_scenario.md`: building_detail_matd3_md
- `drive_building_E1_flex_composite_proxy.png`: building_e1_flex_png
- `drive_building_E2_carbon_emissions_delta_kgco2.png`: building_e2_co2_png
- `drive_building_E3_electricity_cost_delta_eur.png`: building_e3_cost_png
- `drive_building_ev_inventory.png`: building_ev_inventory_png
- `drive_building_ev_success_matd3_e2.png`: building_ev_success_png
- `building_inventory_multiobjective.csv`: building_inventory_csv
- `building_objectives_by_algorithm.csv`: building_objectives_csv
- `district_objectives_by_algorithm.csv`: district_objectives_csv
- `drive_district_objectives.png`: district_objectives_png


## Cobertura por algoritmo

Detalle por edificio disponible para **MASAC**, **MATD3** y **MAAC** (17 edificios × 3 escenarios).

## Edificios incluidos

- **B01 ELECTRO ORIENTE S.A.** (Office): EV=4 (ML=1, MT=1, CV=2); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x4
- **B02 MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA** (Office): EV=6 (ML=3, MT=2, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x6
- **B03 AEROPUERTO INTERNACIONAL** (Assembly): EV=8 (ML=1, MT=5, CV=2); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x8
- **B04 HIPERMERCADOS TOTTUS ORIENTE SAC** (Retail): EV=6 (ML=3, MT=2, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x6
- **B05 HOTEL PLAZA S.A.** (MultiFamily_Hotel): EV=3 (ML=1, MT=1, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x3
- **B06 MALL AVENTURA S.A.** (Commercial_Mall): EV=32 (ML=22, MT=6, CV=4); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x32
- **B07 UNAP-FACULTAD DE BIOLOGIA-AULAS** (Education): EV=42 (ML=25, MT=14, CV=3); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x42
- **B08 PNP- ESCUELA TECNICA SUPERIOR-IQUITOS** (Assembly_Military): EV=17 (ML=8, MT=5, CV=4); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x17
- **B09 GOBIERNO REGIONAL DE LORETO - COER** (Office_Critical): EV=10 (ML=6, MT=3, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x10
- **B10 GOBIERNO REGIONAL DE LORETO** (Office): EV=6 (ML=1, MT=1, CV=4); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x6
- **B11 HOSPITAL REGIONAL DE LORETO** (Healthcare_Hospital): EV=3 (ML=1, MT=1, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x3
- **B12 SEGURO SOCIAL DE SALUD - ESSALUD** (Healthcare): EV=3 (ML=1, MT=1, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x3
- **B13 UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO** (Education): EV=11 (ML=6, MT=4, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x11
- **B14 AUTORIDAD PORTUARIA NACIONAL** (Industrial_Port): EV=4 (ML=1, MT=1, CV=2); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x4
- **B15 DREL- COLEGIO NACIONAL DE IQUITOS** (Education): EV=8 (ML=4, MT=3, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x8
- **B16 SIMA - IQUITOS S.R.LTDA** (Industrial): EV=11 (ML=6, MT=4, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x11
- **B17 ASOCIACION CIVIL SELVA AMAZONICA** (Laboratory): EV=11 (ML=6, MT=4, CV=1); controlados: BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, EV charger x11
