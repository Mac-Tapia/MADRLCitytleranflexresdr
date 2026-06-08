# Informe de auditoria EV - Iquitos CityLearn V3

## Resultado ejecutivo

El dataset queda dimensionado con cargadores AC IEC 61851 modo 3. En CityLearn cada `charger_X_Y` representa una toma o loadpoint controlable; el equipo fisico real agrupa dos tomas mediante `physical_charger_id` y `socket_count_per_physical_unit = 2`.

- Tomas controlables CityLearn: 185
- Equipos fisicos modo 3 de dos tomas: 96
- Tomas de reserva por equipos con una toma libre: 7
- Potencia EV nominal total: 749.4 kW
- Edificios recortados por limite de estacionamiento: 0

## Revision de `external/evcc` y carpeta `external`

Se reviso `external/evcc` como referencia tecnica de control de carga, no como motor de dimensionamiento de parqueo. EVCC modela loadpoints AC, corriente minima/maxima, fases, OCPP y plantillas de equipos, pero no calcula el numero de cargadores por edificio. Por eso el dimensionamiento del dataset usa afluencia diaria, tipo de edificio, permanencia, porcentaje que carga, utilizacion objetivo y area de estacionamiento del inventario local.

Tambien se reviso la estructura restante de `external/`: `MicroGrids` y `prosumpy` son referencias de optimizacion/dispatch PV+BESS; `HARL`, `MAAC`, `MARL`, `MARLlib`, `MATD3implementation` y `off-policy` son backends de aprendizaje. Ninguno contiene un modelo local de dimensionamiento de cargadores por motos, mototaxis, camionetas, parqueo y afluencia de Iquitos, por lo que no se usan directamente para calcular las tomas EV.

Parametros adoptados desde la logica de control tipo EVCC/IEC:

- Modo de carga: IEC 61851 modo 3 AC
- Conector/toma: IEC_62196_Type_2_socket
- Tension nominal monofasica: 230 V
- Corriente minima por toma: 6 A
- Potencia minima de control por toma: 1.38 kW
- Balance de fases: asignacion L1/L2/L3 por potencia nominal de cada toma
- V2G: deshabilitado (`max_discharging_power = 0.0`)

## Metodo de dimensionamiento

El numero de tomas por edificio se calcula con Peak Demand Factor y Ley de Little:

`N_tomas = ceil(N_diario * min(permanencia_h, operacion_h) / operacion_h * pct_carga / utilizacion)`

Luego se valida que el area EV-ready no exceda el estacionamiento disponible del edificio. El area por plaza usada es 2.5 m2 para moto lineal, 7.5 m2 para mototaxi y 25.0 m2 para camioneta. Los edificios remotos reciben mayor fraccion EV-ready porque el usuario necesita carga para el retorno.

## Tipos EV usados

| Tipo EV | Potencia toma | Bateria | Uso local |
|---|---:|---:|---|
| Moto lineal electrica | 3.0 kW | 4.0 kWh | Estudiantes, trabajadores, visitantes urbanos |
| Mototaxi electrica | 4.0 kW | 6.0 kWh | Transporte publico ligero dominante en Iquitos |
| Camioneta electrica | 7.4 kW | 47.0 kWh | Operacion institucional, salud, puerto, logistica y servicios |

## Dimensionamiento final por edificio

| ID | Edificio | Tipo | Estac. m2 | Vehiculo dominante | ML | MT | CV | Tomas | Equipos modo 3 | Reserva | kW | Uso EV-ready | Recorte |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B01 | Electro Oriente S.A. | institucional | 1350 | Mixed_Motos_Trucks | 1 | 1 | 2 | 4 | 2 | 0 | 21.8 | 24.7% | no |
| B02 | Municipalidad Distrital San Juan Bautista | deportivo | 900 | Motos_Motokars | 3 | 2 | 1 | 6 | 3 | 0 | 24.4 | 29.3% | no |
| B03 | Aeropuerto Internacional de Iquitos | transporte_24h | 5500 | Motos_Taxis_Buses | 1 | 5 | 2 | 8 | 4 | 0 | 37.8 | 7.4% | no |
| B04 | Hipermercados Tottus Oriente | retail | 2500 | Motos_Cars | 3 | 2 | 1 | 6 | 3 | 0 | 24.4 | 9.5% | no |
| B05 | Hotel Plaza S.A. | hotelero | 200 | Motos_Cars | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 97.2% | no |
| B06 | Mall Aventura Iquitos | mall | 9000 | Motos_Motokars_Massive | 22 | 6 | 4 | 32 | 16 | 0 | 119.6 | 10.1% | no |
| B07 | UNAP Facultad de Biologia | universitario | 1250 | Motos_Students | 25 | 14 | 3 | 42 | 21 | 0 | 153.2 | 57.1% | no |
| B08 | PNP Escuela Tecnica Superior Iquitos | militar | 3000 | Military_Vehicles | 8 | 5 | 4 | 17 | 9 | 1 | 73.6 | 16.4% | no |
| B09 | Gobierno Regional Loreto COER | deportivo | 1500 | Emergency_Trucks | 6 | 3 | 1 | 10 | 5 | 0 | 37.4 | 23.1% | no |
| B10 | Gobierno Regional de Loreto | administrativo | 2500 | Motos_Staff | 1 | 1 | 4 | 6 | 3 | 0 | 36.6 | 24.4% | no |
| B11 | Hospital Regional de Loreto | salud | 4500 | Emergency_Ambulances | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 3.2% | no |
| B12 | Seguro Social de Salud EsSalud | salud | 2000 | Ambulances_Staff | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 7.3% | no |
| B13 | UNAP Facultad de Ciencias Economicas | universitario | 750 | Motos_Students | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 35.9% | no |
| B14 | Autoridad Portuaria Nacional Iquitos | portuario | 3750 | Heavy_Cargo_Trucks | 1 | 1 | 2 | 4 | 2 | 0 | 21.8 | 8.9% | no |
| B15 | DREL Colegio Nacional de Iquitos | educacion | 1000 | Bicycles_Motos | 4 | 3 | 1 | 8 | 4 | 0 | 31.4 | 26.1% | no |
| B16 | SIMA Iquitos S.R.Ltda | educacion | 5000 | Heavy_Industrial_Cranes | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 6.4% | no |
| B17 | Asociacion Civil Selva Amazonica | educacion | 4000 | Medical_Pickups | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 8.0% | no |

## Archivos modificados para entrenamiento

- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`: cargadores modo 3, dos tomas por equipo fisico, balance de fases y metadatos de hardware.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/charger_*.csv`: perfiles horarios de conexion, salida, SOC requerido y llegada estimada.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/ev_charger_sizing_log.json`: log reproducible dentro del dataset.
- `outputs/dataset_audit/ev_charger_sizing_audit.csv`: tabla auditable del calculo.
- `outputs/dataset_audit/ev_charger_sizing_audit.json`: parametros y resultados completos del modelo.

## Criterio de control MADRL

Cada edificio conserva sus tomas como recursos controlables dentro del entorno CityLearn. A nivel global, el algoritmo MADRL aprende politicas coordinadas para reducir costo, picos, emisiones y uso ineficiente de energia. A nivel de edificio, el agente decide acciones sobre bateria, carga flexible y cargadores EV observando demanda, PV, estado de carga, precio, emisiones y disponibilidad local. Las tomas EV no se dimensionan como cargas fijas: quedan expuestas como loadpoints controlables para que el entrenamiento pueda desplazar carga dentro de las restricciones de llegada, salida y SOC requerido.

## Validacion esperada

Antes de entrenar debe verificarse que el schema cargue con `CityLearnEnv`, que existan todos los CSV de cargadores, que cada CSV tenga 26 304 filas y que cada cargador tenga `charger_type = 3`, fase L1/L2/L3 y metadatos modo 3.
