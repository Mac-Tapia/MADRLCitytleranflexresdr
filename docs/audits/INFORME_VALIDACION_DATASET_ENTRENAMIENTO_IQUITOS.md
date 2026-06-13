# Informe de validacion del dataset de entrenamiento - Iquitos

Este informe valida trazabilidad y cierre energetico del dataset `citylearn_iquitos_2023_2025` usado para entrenamiento MADRL.

## Resultado ejecutivo

- Estado global: `OK`.
- Maximo delta base B02-B17 contra fuente mensual: `0.000000145%`.
- Meses pronosticados marcados: `8`.
- Cierre PV maximo: `0.001000` MWh.
- B01 no tiene factura mensual `B_01.csv`; se marca como perfil simulado desde inventario suministrado.
- EV es carga controlada de escenario, no carga historica medida; se integra desde `charger_*.csv` cuando `state=1`.

## Reglas verificadas

- Inventario: `CityLearn/data/buildingcsv/building.csv`.
- Facturas mensuales: `CityLearn/data/buildingcsv/B_02.csv..B_17.csv`.
- Solar: `PVGIS TMY Iquitos via pvlib, repetido 2023-2025` con `pvlib_ModelChain_SAPM`.
- PV instalada: `Area_Techada_m2 * 0.24 kWp/m2, parking_factor=0.0`.
- BESS: `PV directo se asigna primero a EV; el BESS desplaza excedente PV primero a deficit EV dentro de la ventana operativa de cada edificio y luego a deficit del edificio, con piso global de peak-shaving.`.
- Carga base: `B02-B17 base load is validated as non_shiftable_load + cooling_demand/COP + dhw_demand/COP against monthly active-energy inputs.`.
- Maquina controlada: `Each building loads one Washing_Machine_X.csv as a controlled shiftable-load dataset parameterized by building type and supplied shiftable energy.`.
- Costos: `pricing.csv is referenced by every building and is generated from monthly billing inputs during load distillation.`.
- Emisiones: `carbon_intensity.csv is referenced by every building and represents the Iquitos isolated diesel/solar Scope 2 hourly factor.`.
- Separacion control/no control: `Uncontrolled building load remains non_shiftable_load. Controlled building loads are cooling, DHW, EV and one shiftable machine dataset per building; EV and machine loads are scenario loads, not subtracted from measured historical meter energy.`.

## Tabla por edificio

| ID | Edificio | Fuente base | Med/Pron | Base dataset MWh | Maq ctrl MWh | EV MWh | EV ventana MWh | PV kWp | PV a EV MWh | PV a BESS MWh | BESS a EV MWh | BESS kWh | BESS kW | OK | Limitacion |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| B01 | ELECTRO ORIENTE S.A. | inventario_suministrado_sin_factura_mensual | 0/0 | 17,223.3 | 11.6 | 143.2 | 143.2 | 3,360.2 | 83.5 | 3,356.3 | 57.5 | 6,747.0 | 1,609.0 | OK | No existe B_01.csv; carga horaria base procede del modelo fisico calibrado por inventario, no de factura mensual. |
| B02 | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | factura_mensual_medida | 36/0 | 204.5 | 27.9 | 15.1 | 15.1 | 1,920.0 | 15.0 | 113.7 | 0.1 | 244.0 | 50.0 | OK |  |
| B03 | AEROPUERTO INTERNACIONAL | factura_mensual_medida | 36/0 | 2,868.4 | 104.1 | 182.7 | 182.7 | 1,440.2 | 67.6 | 1,390.6 | 114.3 | 2,363.0 | 511.0 | OK |  |
| B04 | HIPERMERCADOS TOTTUS ORIENTE SAC | factura_mensual_medida | 36/0 | 4,047.5 | 24.3 | 60.1 | 60.1 | 600.2 | 43.1 | 93.3 | 8.8 | 454.0 | 409.0 | OK |  |
| B05 | HOTEL PLAZA S.A. | factura_mensual_medida | 36/0 | 2,836.1 | 108.5 | 55.5 | 55.5 | 274.1 | 12.3 | 58.0 | 20.8 | 234.0 | 124.0 | OK |  |
| B06 | MALL AVENTURA S.A. | factura_mensual_con_meses_pronosticados | 28/8 | 34,079.9 | 192.9 | 349.9 | 349.9 | 4,952.9 | 296.1 | 558.5 | 31.0 | 2,541.0 | 835.0 | OK | 8 meses pronosticados por calendario desde meses medidos. |
| B07 | UNAP-FACULTAD DE BIOLOGIA-AULAS | factura_mensual_medida | 36/0 | 668.5 | 30.7 | 615.0 | 615.0 | 1,944.9 | 290.0 | 552.5 | 321.2 | 984.0 | 240.0 | OK |  |
| B08 | PNP- ESCUELA TECNICA SUPERIOR-IQUITOS | factura_mensual_medida | 36/0 | 327.4 | 77.8 | 468.5 | 468.5 | 5,040.2 | 257.6 | 359.6 | 208.3 | 601.0 | 129.0 | OK |  |
| B09 | GOBIERNO REGIONAL DE LORETO - COER | factura_mensual_medida | 36/0 | 151.9 | 13.3 | 69.6 | 69.6 | 1,075.3 | 46.1 | 98.8 | 23.5 | 138.0 | 30.0 | OK |  |
| B10 | GOBIERNO REGIONAL DE LORETO | factura_mensual_medida | 36/0 | 3,619.9 | 17.4 | 200.8 | 200.8 | 3,431.1 | 105.9 | 1,436.4 | 94.7 | 2,353.0 | 591.0 | OK |  |
| B11 | HOSPITAL REGIONAL DE LORETO | factura_mensual_medida | 36/0 | 2,808.2 | 80.0 | 130.7 | 130.7 | 10,236.1 | 67.5 | 1,484.0 | 62.7 | 1,901.0 | 424.0 | OK |  |
| B12 | SEGURO SOCIAL DE SALUD - ESSALUD | factura_mensual_medida | 36/0 | 6,950.8 | 37.8 | 132.0 | 132.0 | 4,367.5 | 68.7 | 3,476.4 | 63.3 | 4,346.0 | 960.0 | OK |  |
| B13 | UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO | factura_mensual_medida | 36/0 | 211.8 | 11.6 | 165.2 | 165.2 | 653.8 | 79.0 | 156.2 | 84.9 | 272.0 | 69.0 | OK |  |
| B14 | AUTORIDAD PORTUARIA NACIONAL | factura_mensual_medida | 36/0 | 134.0 | 51.5 | 142.4 | 142.4 | 4,262.9 | 51.0 | 174.4 | 90.3 | 229.0 | 48.0 | OK |  |
| B15 | DREL- COLEGIO NACIONAL DE IQUITOS | factura_mensual_medida | 36/0 | 518.3 | 18.3 | 147.1 | 147.1 | 2,373.8 | 71.5 | 306.6 | 75.2 | 500.0 | 104.0 | OK |  |
| B16 | SIMA - IQUITOS S.R.LTDA | factura_mensual_medida | 36/0 | 1,898.8 | 40.1 | 195.7 | 195.7 | 2,470.8 | 95.8 | 1,055.0 | 98.6 | 1,622.0 | 357.0 | OK |  |
| B17 | ASOCIACION CIVIL SELVA AMAZONICA | factura_mensual_medida | 36/0 | 1,183.4 | 28.8 | 194.2 | 194.2 | 386.9 | 78.5 | 453.2 | 107.3 | 737.0 | 158.0 | OK |  |

## Limitaciones declaradas

- B01 has no monthly meter file B_01.csv, so its base load is a simulated profile from supplied inventory.
- B06 has forecast months completed from measured calendar-month overlap; they are flagged, not treated as direct meter readings.
- EV arrival sessions are simulated from the EV sizing model and supplied parking/traffic assumptions; they are controlled scenario loads, not measured historical building energy.
- Controlled machine loads are shiftable scenario loads derived from supplied building type and shiftable-capacity fields, not separate measured submeter files.
- Solar uses PVGIS TMY through pvlib for Iquitos, not on-site measured irradiance.

## Archivos generados

- CSV: `outputs\dataset_audit\training_dataset_validation.csv`
- JSON: `outputs\dataset_audit\training_dataset_validation.json`

## Reproduccion

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe tools\audit_training_dataset_provenance.py
```
