# Informe de auditoria de dimensionamiento DER - Iquitos CityLearn

Este informe se genera con `tools/dataset/audit_der_sizing.py` y no modifica el dataset.

## Hallazgos

- PV aplicado al dataset de entrenamiento usa el area de techo suministrada por edificio en `CityLearn/data/buildingcsv/building.csv` (`Area_Techada_m2`) y densidad tecnica `0.24 kWp/m2`; no usa areas inventadas.
- La curva horaria `solar_generation` se calcula con `pvlib` para Iquitos y se normaliza como W/kW; `schema.json` escala esa curva con `pv.nominal_power` de cada edificio.
- Los factores `0.63`, `0.85` y `1.00` se conservan solo como escenarios de sensibilidad/auditoria, no como criterio aplicado al dataset vigente.
- `size_bess_optimal.py` usa balance horario por edificio: carga electrica base, carga EV, PV, PV directo a EV, PV directo al edificio, excedente PV y deficit residual de red publica.
- La red publica no se reemplaza artificialmente: `grid_before_bess = EV_deficit + edificio_deficit` y `grid_after_bess` queda como deficit residual despues de la descarga factible del BESS.
- El excedente solar dimensiona el BESS: se desplaza hasta `70%` de la energia diaria factible PV->deficit, priorizando primero EV en la ventana operativa del edificio y luego carga del edificio.
- El BESS conserva un piso de corte de pico minimo de `10%` sobre la importacion maxima de red en todo el horizonte horario del dataset.
- La ventana operativa por edificio define que energia EV entra como prioridad BESS hasta el cierre; la EV fuera de ventana queda separada en la auditoria.
- La capacidad final es el maximo entre desplazamiento solar diario con prioridad EV y corte de pico; la potencia final es el maximo entre carga FV, descarga a EV/edificio, descarga de pico y recarga valle/nocturna.
- El dimensionador EV v3 aporta `185` tomas controlables en el schema actual; la energia EV se suma solo cuando `electric_vehicle_charger_state == 1` en cada `charger_*.csv`.
- AC se reporta como pico real de `cooling_demand` del CSV en kW termicos, porque `cooling_device` esta en `autosize=True`.

## Parametros PV

- Modulo Sandia: `SunPower_SPR_315E_WHT__2007__E__`
- Potencia modulo: `0.3151` kWp
- Area modulo: `1.6310` m2
- Eficiencia STC: `19.32%`
- Criterio aplicado al dataset: `Area_Techada_m2 * 0.24 kWp/m2`
- Fuente de area: `CityLearn/data/buildingcsv/building.csv`, columna `Area_Techada_m2`
- Escenario conservador de sensibilidad: `0.63 = 70% techo util * 90% packing`
- Escenario agresivo de sensibilidad: `0.85`
- Escenario techo maximo teorico de sensibilidad: `1.00`

## Balance BESS auditado

- `Carga total` = energia electrica real estimada del edificio antes de BESS, incluyendo EV.
- `Carga base medida` = demanda electrica base + climatizacion electrica + ACS electrico.
- `Maquina controlada` = carga flexible por edificio cargada mediante `Washing_Machine_X.csv` y expuesta como accion CityLearn.
- `Carga sin EV` = carga base medida + maquina controlada.
- `EV MWh` = carga horaria de tomas modo 3 cuando el CSV del cargador indica `state=1`.
- `EV ventana` = parte de EV dentro del horario operativo del edificio; esta energia es prioridad de descarga BESS.
- `PV a EV` = solar directo asignado primero a EV antes de cubrir carga del edificio.
- `BESS a EV` = descarga BESS dedicada a EV dentro de la ventana operativa.
- `PV exportada` = excedente solar remanente despues del desplazamiento BESS factible.
- `Red antes` = energia que compraria el edificio a la red despues del autoconsumo PV directo y antes del BESS.
- `Red despues` = energia residual de red despues de descarga BESS y recarga valle desde red.
- `Pico obj.` = 90% del pico global de importacion de red antes del BESS; se mantiene como piso de potencia/capacidad.
- `PV uso` = autoconsumo directo + carga BESS desde PV + exportacion; debe cerrar en 100% salvo redondeo.

## Tabla auditada

| ID | Edificio | Area m2 | PV kWp | BESS kWh | BESS kW | Ventana EV/recarga | EV tomas | EV MWh | EV ventana MWh | PV a EV MWh | BESS a EV MWh | Pico global -% |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| B01 | ELECTRO ORIENTE S.A. | 14,000.00 | 3,360.2 | 6,747.0 | 1,609.0 | electro_oriente_lun_vie_07_18 | 4 | 143.2 | 143.2 | 83.5 | 57.5 | 1.3 |
| B02 | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | 8,000.00 | 1,920.0 | 244.0 | 50.0 | municipalidad_lun_vie_08_15 | 6 | 15.1 | 15.1 | 15.0 | 0.1 | 27.7 |
| B03 | AEROPUERTO INTERNACIONAL | 6,000.00 | 1,440.2 | 2,363.0 | 511.0 | aeropuerto_24h | 8 | 182.7 | 182.7 | 67.6 | 114.3 | 2.6 |
| B04 | HIPERMERCADOS TOTTUS ORIENTE SAC | 2,500.00 | 600.2 | 454.0 | 409.0 | tottus_lun_dom_08_22 | 6 | 60.1 | 60.1 | 43.1 | 8.8 | 0.0 |
| B05 | HOTEL PLAZA S.A. | 1,141.89 | 274.1 | 234.0 | 124.0 | hotel_24h | 3 | 55.5 | 55.5 | 12.3 | 20.8 | 0.0 |
| B06 | MALL AVENTURA S.A. | 20,637.00 | 4,952.9 | 2,541.0 | 835.0 | mall_lun_dom_10_22 | 32 | 349.9 | 349.9 | 296.1 | 31.0 | 0.0 |
| B07 | UNAP-FACULTAD DE BIOLOGIA-AULAS | 8,103.45 | 1,944.9 | 984.0 | 240.0 | unap_lun_vie_07_14 | 42 | 615.0 | 615.0 | 290.0 | 321.2 | 7.7 |
| B08 | PNP- ESCUELA TECNICA SUPERIOR-IQUITOS | 21,000.00 | 5,040.2 | 601.0 | 129.0 | pnp_ets_academico_lun_vie_07_18 | 17 | 468.5 | 468.5 | 257.6 | 208.3 | 24.3 |
| B09 | GOBIERNO REGIONAL DE LORETO - COER | 4,479.67 | 1,075.3 | 138.0 | 30.0 | coer_24h | 10 | 69.6 | 69.6 | 46.1 | 23.5 | 57.0 |
| B10 | GOBIERNO REGIONAL DE LORETO | 14,295.73 | 3,431.1 | 2,353.0 | 591.0 | gorel_lun_vie_07_15 | 6 | 200.8 | 200.8 | 105.9 | 94.7 | 12.9 |
| B11 | HOSPITAL REGIONAL DE LORETO | 42,649.33 | 10,236.1 | 1,901.0 | 424.0 | hospital_regional_24h | 3 | 130.7 | 130.7 | 67.5 | 62.7 | 0.0 |
| B12 | SEGURO SOCIAL DE SALUD - ESSALUD | 18,197.48 | 4,367.5 | 4,346.0 | 960.0 | essalud_24h | 3 | 132.0 | 132.0 | 68.7 | 63.3 | 13.7 |
| B13 | UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO | 2,723.00 | 653.8 | 272.0 | 69.0 | unap_lun_vie_07_14 | 11 | 165.2 | 165.2 | 79.0 | 84.9 | 5.0 |
| B14 | AUTORIDAD PORTUARIA NACIONAL | 17,761.00 | 4,262.9 | 229.0 | 48.0 | apn_operativo_24h | 4 | 142.4 | 142.4 | 51.0 | 90.3 | 42.3 |
| B15 | DREL- COLEGIO NACIONAL DE IQUITOS | 9,889.92 | 2,373.8 | 500.0 | 104.0 | cni_lun_vie_07_18 | 8 | 147.1 | 147.1 | 71.5 | 75.2 | 8.9 |
| B16 | SIMA - IQUITOS S.R.LTDA | 10,294.00 | 2,470.8 | 1,622.0 | 357.0 | sima_lun_vie_07_17 | 11 | 195.7 | 195.7 | 95.8 | 98.6 | 35.0 |
| B17 | ASOCIACION CIVIL SELVA AMAZONICA | 1,611.23 | 386.9 | 737.0 | 158.0 | acsa_salud_24h | 11 | 194.2 | 194.2 | 78.5 | 107.3 | 3.5 |

## Balance energetico por edificio

| ID | Base medida MWh | Maquina ctrl MWh | Carga sin EV MWh | EV MWh | EV ventana MWh | PV MWh | PV a EV MWh | PV a edificio MWh | PV a BESS MWh | BESS a EV MWh | BESS a edificio MWh | PV exportada MWh | Red EV despues MWh | Red edificio despues MWh | BESS solar kWh |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B01 | 17,223.3 | 11.6 | 17,234.9 | 143.2 | 143.2 | 10,331.5 | 83.5 | 5,325.5 | 3,356.3 | 57.5 | 2,970.5 | 1,566.2 | 2.2 | 8,938.9 | 6,747.0 |
| B02 | 204.5 | 27.9 | 232.4 | 15.1 | 15.1 | 5,931.4 | 15.0 | 83.5 | 113.7 | 0.1 | 102.5 | 5,719.2 | 0.0 | 46.4 | 244.0 |
| B03 | 2,868.4 | 104.1 | 2,972.5 | 182.7 | 182.7 | 4,409.2 | 67.6 | 952.4 | 1,390.6 | 114.3 | 1,140.5 | 1,998.5 | 0.8 | 879.6 | 2,363.0 |
| B04 | 4,047.5 | 24.3 | 4,071.8 | 60.1 | 60.1 | 1,853.6 | 43.1 | 1,668.5 | 93.3 | 8.8 | 75.4 | 48.8 | 8.2 | 2,327.9 | 454.0 |
| B05 | 2,836.1 | 108.5 | 2,944.6 | 55.5 | 55.5 | 803.7 | 12.3 | 702.4 | 58.0 | 20.8 | 31.6 | 31.0 | 22.4 | 2,210.6 | 234.0 |
| B06 | 34,079.9 | 192.9 | 34,272.8 | 349.9 | 349.9 | 14,754.8 | 296.1 | 13,401.7 | 558.5 | 31.0 | 473.3 | 498.5 | 22.8 | 20,397.8 | 2,541.0 |
| B07 | 668.5 | 30.7 | 699.2 | 615.0 | 615.0 | 5,987.8 | 290.0 | 295.5 | 552.5 | 321.2 | 177.3 | 4,849.9 | 3.8 | 226.4 | 984.0 |
| B08 | 327.4 | 77.8 | 405.1 | 468.5 | 468.5 | 14,965.1 | 257.6 | 145.3 | 359.6 | 208.3 | 116.1 | 14,202.7 | 2.7 | 143.7 | 601.0 |
| B09 | 151.9 | 13.3 | 165.2 | 69.6 | 69.6 | 3,287.9 | 46.1 | 58.3 | 98.8 | 23.5 | 65.7 | 3,084.7 | 0.0 | 41.2 | 138.0 |
| B10 | 3,619.9 | 17.4 | 3,637.3 | 200.8 | 200.8 | 10,546.5 | 105.9 | 1,790.7 | 1,436.4 | 94.7 | 1,201.2 | 7,213.5 | 0.2 | 645.4 | 2,353.0 |
| B11 | 2,808.2 | 80.0 | 2,888.2 | 130.7 | 130.7 | 31,540.0 | 67.5 | 1,019.7 | 1,484.0 | 62.7 | 1,276.4 | 28,968.8 | 0.5 | 592.1 | 1,901.0 |
| B12 | 6,950.8 | 37.8 | 6,988.6 | 132.0 | 132.0 | 13,280.3 | 68.7 | 2,385.4 | 3,476.4 | 63.3 | 3,073.7 | 7,349.8 | 0.0 | 1,529.5 | 4,346.0 |
| B13 | 211.8 | 11.6 | 223.4 | 165.2 | 165.2 | 2,008.8 | 79.0 | 103.4 | 156.2 | 84.9 | 56.0 | 1,670.1 | 1.2 | 64.0 | 272.0 |
| B14 | 134.0 | 51.5 | 185.5 | 142.4 | 142.4 | 12,984.4 | 51.0 | 49.8 | 174.4 | 90.3 | 67.0 | 12,709.3 | 1.1 | 68.7 | 229.0 |
| B15 | 518.3 | 18.3 | 536.6 | 147.1 | 147.1 | 7,317.7 | 71.5 | 212.0 | 306.6 | 75.2 | 201.4 | 6,727.7 | 0.4 | 123.3 | 500.0 |
| B16 | 1,898.8 | 40.1 | 1,938.9 | 195.7 | 195.7 | 7,608.8 | 95.8 | 648.2 | 1,055.0 | 98.6 | 853.5 | 5,809.8 | 1.3 | 437.2 | 1,622.0 |
| B17 | 1,183.4 | 28.8 | 1,212.2 | 194.2 | 194.2 | 1,190.5 | 78.5 | 396.6 | 453.2 | 107.3 | 301.6 | 262.2 | 8.4 | 513.9 | 737.0 |

## Archivos generados

- CSV: `outputs\dataset_audit\der_sizing_audit.csv`
- JSON: `outputs\dataset_audit\der_sizing_audit.json`

## Reproduccion tecnica

Este auditor no sobrescribe `schema.json` ni los CSV, pero documenta el estado aplicado. Para reproducir el dimensionamiento vigente del dataset:

```powershell
# PV aplicado al entrenamiento: Iquitos TMY via PVGIS/pvlib + area techada suministrada * 0.24 kWp/m2
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\fix_solar_pvlib.py --weather-source tmy --capacity-method power-density --power-density-kwp-m2 0.24 --parking-factor 0.0 --dry-run

# Aplicar PV al dataset si se necesita regenerar los CSV solares
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\fix_solar_pvlib.py --weather-source tmy --capacity-method power-density --power-density-kwp-m2 0.24 --parking-factor 0.0

# EV v3 aplica cargadores y escribe schema/charger CSV
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\dimension_ev_chargers.py

# BESS con PV->EV y BESS->EV prioritario por ventana operativa, solo verificar
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\size_bess_optimal.py --dry-run

# Aplicar BESS corregido al schema.json despues de EV
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\size_bess_optimal.py --write
```
