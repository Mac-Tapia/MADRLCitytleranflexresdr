# Informe de auditoria de parametros de edificios Iquitos
**Dataset auditado:** `CityLearn/data/datasets/citylearn_iquitos_2023_2025`  
**Objetivo:** corregir el cuadro de `AC (kW)`, `PV (kWp)`, `BESS (kWh)` y `EV` para que refleje las fuentes reales del proyecto.
## Fuentes usadas
- `tools/skills/iquitos-citylearn-dataset/references/module-a-building-configs.md`: constantes corregidas de `NON_SHIFTABLE_BASE`, `COOLING_PEAK` y `SHIFTABLE`.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`: `pv.attributes.nominal_power`, `electrical_storage.attributes.capacity`, `electrical_storage.attributes.nominal_power` y cargadores EV.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/solar_fix_log.json`: validacion `pvlib_SAPM` de potencia DC para B02-B17.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/Building_X.csv`: auditoria del maximo de `cooling_demand`; no se usa como potencia instalada AC.
## Cuadro corregido
| ID | Edificio | Tipo | Area (m2) | AC modulo (kW) | PV schema (kWp) | BESS (kWh) | EV |
|----|----------|------|:---------:|---------------:|----------------:|-----------:|---:|
| B01 | Electro Oriente S.A. | industrial | 14,000.00 | 126.86 | 1,703.6 | 4,020.0 | 2 |
| B02 | Municipalidad Distrital San Juan Bautista | administrativo | 8,000.00 | 29.00 | 973.6 | 2,382.0 | 4 |
| B03 | Aeropuerto Internacional de Iquitos | transporte_24h | 6,000.00 | 67.00 | 730.0 | 2,905.6 | 4 |
| B04 | Hipermercados Tottus Oriente | mall | 2,500.00 | 29.50 | 304.0 | 2,495.0 | 3 |
| B05 | Hotel Plaza S.A. | hotelero_24h | 1,141.89 | 150.50 | 138.9 | 1,205.3 | 3 |
| B06 | Mall Aventura Iquitos | mall | 20,637.00 | 850.00 | 2,511.4 | 15,075.3 | 8 |
| B07 | UNAP Facultad de Biologia | universitario | 8,103.45 | 167.00 | 986.2 | 2,550.3 | 3 |
| B08 | PNP Escuela Tecnica Superior Iquitos | educacion | 21,000.00 | 222.00 | 2,555.5 | 6,836.0 | 2 |
| B09 | Gobierno Regional Loreto COER | transporte_24h | 4,479.67 | 19.50 | 545.1 | 851.5 | 2 |
| B10 | Gobierno Regional de Loreto | administrativo | 14,295.73 | 117.50 | 1,739.5 | 3,964.5 | 3 |
| B11 | Hospital Regional de Loreto | salud_24h | 42,649.33 | 366.60 | 5,190.2 | 6,661.9 | 4 |
| B12 | Seguro Social de Salud EsSalud | salud_24h | 18,197.48 | 222.00 | 2,214.6 | 3,158.7 | 3 |
| B13 | UNAP Facultad de Ciencias Economicas | universitario | 2,723.00 | 62.50 | 331.1 | 798.2 | 2 |
| B14 | Autoridad Portuaria Nacional Iquitos | portuario_24h | 17,761.00 | 49.50 | 2,161.4 | 5,767.3 | 2 |
| B15 | DREL Colegio Nacional de Iquitos | educacion | 9,889.92 | 48.00 | 1,203.6 | 3,220.7 | 2 |
| B16 | SIMA Iquitos S.R.Ltda | industrial | 10,294.00 | 100.00 | 1,252.7 | 2,496.7 | 1 |
| B17 | Asociacion Civil Selva Amazonica | salud_24h | 1,611.23 | 93.00 | 196.0 | 1,640.7 | 2 |
## Auditoria por modulo
| ID | AC modulo (kW) | AC CSV max (kW) | PV schema (kWp) | PV log (kWp) | BESS (kWh) | BESS P (kW) | EV | EV P total (kW) | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B01 | 126.86 | 439.05 | 1,703.6 | N/D | 4,020.0 | 1,005.0 | 2 | 14.8 | PV log pendiente B01 |
| B02 | 29.00 | 80.73 | 973.6 | 973.6 | 2,382.0 | 595.5 | 4 | 16.0 | OK |
| B03 | 67.00 | 764.40 | 730.0 | 730.0 | 2,905.6 | 726.4 | 4 | 20.8 | OK |
| B04 | 29.50 | 1,235.26 | 304.0 | 304.0 | 2,495.0 | 623.8 | 3 | 12.0 | OK |
| B05 | 150.50 | 390.64 | 138.9 | 138.9 | 1,205.3 | 301.3 | 3 | 15.4 | OK |
| B06 | 850.00 | 8,408.33 | 2,511.4 | 2,511.4 | 15,075.3 | 3,768.8 | 8 | 42.2 | OK |
| B07 | 167.00 | 160.37 | 986.2 | 986.2 | 2,550.3 | 637.6 | 3 | 13.4 | OK |
| B08 | 222.00 | 129.17 | 2,555.5 | 2,555.5 | 6,836.0 | 1,709.0 | 2 | 14.8 | OK |
| B09 | 19.50 | 32.87 | 545.1 | 545.1 | 851.5 | 212.9 | 2 | 8.0 | OK |
| B10 | 117.50 | 827.98 | 1,739.5 | 1,739.5 | 3,964.5 | 991.1 | 3 | 22.2 | OK |
| B11 | 366.60 | 477.16 | 5,190.2 | 5,190.2 | 6,661.9 | 1,665.5 | 4 | 20.8 | OK |
| B12 | 222.00 | 963.00 | 2,214.6 | 2,214.6 | 3,158.7 | 789.7 | 3 | 17.8 | OK |
| B13 | 62.50 | 70.42 | 331.1 | 331.1 | 798.2 | 199.5 | 2 | 6.0 | OK |
| B14 | 49.50 | 30.05 | 2,161.4 | 2,161.4 | 5,767.3 | 1,441.8 | 2 | 14.8 | OK |
| B15 | 48.00 | 86.82 | 1,203.6 | 1,203.6 | 3,220.7 | 805.2 | 2 | 8.0 | OK |
| B16 | 100.00 | 408.44 | 1,252.7 | 1,252.7 | 2,496.7 | 624.2 | 1 | 3.0 | OK |
| B17 | 93.00 | 185.38 | 196.0 | 196.0 | 1,640.7 | 410.2 | 2 | 6.0 | OK |

## Conclusiones tecnicas
- Los valores antiguos de `Pico AC kW` eran constantes iniciales y no coincidian con las correcciones detalladas del Modulo A. Fueron reemplazados por `COOLING_PEAK_B*_KW` corregidos.
- `PV (kWp)` y `BESS (kWh)` del cuadro anterior si coincidian con `schema.json`; se mantuvieron, pero se agrego trazabilidad explicita.
- `BESS P (kW)` cumple `capacity/4` en los 17 edificios, coherente con 4 horas de autonomia.
- `EV` corresponde al conteo de cargadores por edificio en `schema.json`; la potencia total EV no siempre es `EV * 7.4` porque hay cargadores de 3.0, 4.0, 7.4 y 11.0 kW.
- `AC CSV max (kW)` se reporta solo como auditoria de la senal `cooling_demand`; no debe sustituir `AC modulo (kW)` porque CityLearn tiene `cooling_device.autosize=true` y la serie puede representar demanda termica horaria.
- B01 no aparece en `solar_fix_log.json`; se conserva `PV schema=1,703.6 kWp`, pero se recomienda regenerar el log solar completo si se requiere trazabilidad pvlib para los 17 edificios.
