# Informe de auditoria EV - Iquitos CityLearn V3

## Resultado ejecutivo

El dataset queda dimensionado como escenario EV de tesis para Iquitos por edificio, tipo de vehiculo y concurrencia. En CityLearn cada `charger_X_Y` representa una toma o loadpoint controlable Mode 3; el equipo fisico real agrupa dos tomas simultaneas mediante `physical_charger_id` y `socket_count_per_physical_unit = 2`. Los EV no son 1:1 con tomas: cada toma usa un pool de vehiculos para que cada sesion cargue segun `estimated_soc_arrival` y `required_soc_departure`.

- Tomas controlables CityLearn: 185
- Equipos fisicos modo 3 de dos tomas: 96
- Tomas de reserva por equipos con una toma libre: 7
- EVs simulados en pool: 1850
- Potencia EV nominal total: 749.4 kW
- Tomas camioneta con V2G bidireccional: 31
- Edificios recortados por limite de estacionamiento: 0

## Contexto externo usado

La actualizacion no interpreta el marco normativo peruano como evidencia de una flota electrica historica medida en Iquitos. El Decreto Supremo 036-2023-EM se usa como marco habilitante de infraestructura; la estadistica MTC de parque vehicular se usa como fuente oficial de contexto; y el listado publico Electromaps Peru se usa como contraste de infraestructura visible. El dataset modela un escenario EV reproducible para entrenamiento, no un censo de EV actuales.

| Fuente | Uso en el modelo | URL |
|---|---|---|
| MINEM DS 036-2023-EM | Marco regulatorio de infraestructura de carga | https://www.gob.pe/institucion/minem/normas-legales/5325447-036-2023-em |
| MTC parque vehicular | Contexto oficial de movilidad terrestre | https://www.gob.pe/institucion/mtc/informes-publicaciones/344892-estadistica-servicios-de-transporte-terrestre-por-carretera-parque-automotor |
| Electromaps Peru | Contraste publico de puntos de carga visibles | https://www.electromaps.com/es/puntos-carga/peru |
| EAFO Recharging Systems | Diferencia estacion/punto/conector de recarga | https://alternative-fuels-observatory.ec.europa.eu/general-information/recharging-systems |
| EMSD EV charging facilities | Guia publica de modos de carga EV y Mode 3 con EVSE dedicado | https://www.emsd.gov.hk/filemanager/en/content_444/Guidelines_for_EV_charging_facilities.pdf |

## Revision web de cargadores Mode 3

La revision tecnica confirma que Mode 3 corresponde a carga AC por EVSE dedicado con control y protecciones, no a una relacion fija un cargador-un vehiculo durante todo el horizonte. Las referencias publicas de infraestructura separan estacion/equipo fisico, punto de recarga y conector/toma. Por eso el dataset modela `charger_X_Y` como toma/loadpoint controlable; un equipo fisico Mode 3 agrupa dos tomas simultaneas, y cada toma atiende sesiones de EV segun SOC de llegada y SOC requerido.

## Revision de `external/evcc` y carpeta `external`

Se reviso `external/evcc` como referencia tecnica de control de carga, no como motor de dimensionamiento de parqueo. EVCC modela loadpoints AC, corriente minima/maxima, fases, OCPP y plantillas de equipos, pero no calcula el numero de cargadores por edificio. Por eso el dimensionamiento vigente usa una politica local de escenario por tipo de edificio, concurrencia y area disponible, sin asumir demanda EV historica medida.

Tambien se reviso la estructura restante de `external/`: `MicroGrids` y `prosumpy` son referencias de optimizacion/dispatch PV+BESS; `HARL`, `MAAC`, `MARL`, `MARLlib`, `MATD3implementation` y `off-policy` son backends de aprendizaje. Ninguno contiene un modelo local de dimensionamiento de cargadores por motos, mototaxis, camionetas, parqueo y afluencia de Iquitos, por lo que no se usan directamente para calcular las tomas EV.

Parametros adoptados desde la logica de control tipo EVCC/IEC:

- Modo de carga: IEC 61851 modo 3 AC
- Conector/toma: IEC_62196_Type_2_socket
- Tension nominal monofasica: 230 V
- Corriente minima por toma: 6 A
- Potencia minima de control por toma: 1.38 kW
- Balance de fases: asignacion L1/L2/L3 por potencia nominal de cada toma
- V2G: habilitado solo para camionetas institucionales/logisticas (`max_discharging_power = 7.4 kW`, `power_flow_direction = bidirectional_v2g`); motos y mototaxis quedan solo carga.

## Metodo de dimensionamiento

El numero de tomas por edificio se calcula con PE + FC + duracion de carga por SOC + Ley de Little:

- `N_EV_dia = flujo_vehicular_diario * PE`.
- `t_carga_SOC = ((SOC_requerido - SOC_llegada) * bateria_kWh) / (potencia_toma_kW * eficiencia)`.
- `N_concurrente = N_EV_dia * FC * min(t_carga_SOC, horario_operativo) / horario_operativo`.
- `tomas = ceil(N_concurrente / utilizacion_objetivo)` por tipo EV.
- Cada edificio se calcula por moto lineal, mototaxi y camioneta; luego se limita por area EV-ready.

Luego se valida que el area EV-ready no exceda el estacionamiento disponible del edificio. Cada equipo fisico Mode 3 contiene 2 tomas, pero el dimensionamiento CityLearn se mantiene por toma porque ambas pueden cargar simultaneamente.

## Factores PE/FC usados

| Tipo EV | PE base | FC base | PE remoto | FC remoto | t_carga_SOC |
|---|---:|---:|---:|---:|---:|
| Moto lineal electrica | 0.500 | 0.466 | 0.500 | 0.932 | 0.77 h |
| Mototaxi electrica | 0.700 | 0.577 | 0.700 | 0.963 | 0.74 h |
| Camioneta electrica | 0.650 | 0.822 | 0.650 | 0.822 | 2.84 h |

## Tipos EV usados

| Tipo EV | Potencia toma | Potencia descarga V2G | Bateria | Uso local |
|---|---:|---:|---:|---|
| Moto lineal electrica | 3.0 kW | 0.0 kW | 4.0 kWh | Escenario EV por flujo de motos del edificio |
| Mototaxi electrica | 4.0 kW | 0.0 kW | 6.0 kWh | Escenario EV por flujo de mototaxis/motokars |
| Camioneta electrica V2G | 7.4 kW | 7.4 kW | 40.0 kWh | Escenario EV institucional/logistico con control bidireccional |

## Dimensionamiento final por edificio

| ID | Edificio | Tipo | Estac. m2 | Politica | ML | MT | CV | Tomas | Equipos modo 3 | Reserva | kW | Uso EV-ready | Recorte |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B01 | Electro Oriente S.A. | institucional | 1350 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 2 | 4 | 2 | 0 | 21.8 | 24.7% | no |
| B02 | Municipalidad Distrital San Juan Bautista | deportivo | 900 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 3 | 2 | 1 | 6 | 3 | 0 | 24.4 | 29.3% | no |
| B03 | Aeropuerto Internacional de Iquitos | transporte_24h | 5500 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 5 | 2 | 8 | 4 | 0 | 37.8 | 7.4% | no |
| B04 | Hipermercados Tottus Oriente | retail | 2500 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 3 | 2 | 1 | 6 | 3 | 0 | 24.4 | 9.5% | no |
| B05 | Hotel Plaza S.A. | hotelero | 200 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 97.2% | no |
| B06 | Mall Aventura Iquitos | mall | 9000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 22 | 6 | 4 | 32 | 16 | 0 | 119.6 | 10.1% | no |
| B07 | UNAP Facultad de Biologia | universitario | 1250 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 25 | 14 | 3 | 42 | 21 | 0 | 153.2 | 57.1% | no |
| B08 | PNP Escuela Tecnica Superior Iquitos | militar | 3000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 8 | 5 | 4 | 17 | 9 | 1 | 73.6 | 16.4% | no |
| B09 | Gobierno Regional Loreto COER | deportivo | 1500 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 6 | 3 | 1 | 10 | 5 | 0 | 37.4 | 23.1% | no |
| B10 | Gobierno Regional de Loreto | administrativo | 2500 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 4 | 6 | 3 | 0 | 36.6 | 24.4% | no |
| B11 | Hospital Regional de Loreto | salud | 4500 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 3.2% | no |
| B12 | Seguro Social de Salud EsSalud | salud | 2000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 1 | 3 | 2 | 1 | 14.4 | 7.3% | no |
| B13 | UNAP Facultad de Ciencias Economicas | universitario | 750 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 35.9% | no |
| B14 | Autoridad Portuaria Nacional Iquitos | portuario | 3750 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 1 | 1 | 2 | 4 | 2 | 0 | 21.8 | 8.9% | no |
| B15 | DREL Colegio Nacional de Iquitos | educacion | 1000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 4 | 3 | 1 | 8 | 4 | 0 | 31.4 | 26.1% | no |
| B16 | SIMA Iquitos S.R.Ltda | educacion | 5000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 6.4% | no |
| B17 | Asociacion Civil Selva Amazonica | educacion | 4000 | dimensionado por tipo de edificio, flujo EV de escenario, concurrencia y area EV-ready | 6 | 4 | 1 | 11 | 6 | 1 | 41.4 | 8.0% | no |

## Archivos modificados para entrenamiento

- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`: cargadores modo 3, dos tomas por equipo fisico, balance de fases y metadatos de hardware.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/charger_*.csv`: perfiles horarios de conexion, salida, SOC requerido y llegada estimada.
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/ev_charger_sizing_log.json`: log reproducible dentro del dataset.
- `outputs/dataset_audit/ev_charger_sizing_audit.csv`: tabla auditable del calculo.
- `outputs/dataset_audit/ev_charger_sizing_audit.json`: parametros y resultados completos del modelo.

## Criterio de control MADRL

Cada edificio conserva sus tomas como recursos controlables dentro del entorno CityLearn. A nivel global, el algoritmo MADRL aprende politicas coordinadas para reducir costo, picos, emisiones y uso ineficiente de energia. A nivel de edificio, el agente decide acciones sobre bateria, carga flexible y cargadores EV observando demanda, PV, estado de carga, precio, emisiones y disponibilidad local. Las tomas EV no se dimensionan como cargas fijas: quedan expuestas como loadpoints controlables para que el entrenamiento pueda desplazar carga dentro de las restricciones de llegada, salida y SOC requerido.

## Validacion esperada

Antes de entrenar debe verificarse que el schema cargue con `CityLearnEnv`, que existan todos los CSV de cargadores, que cada CSV tenga 26 304 filas, que cada cargador tenga `charger_type = 3`, fase L1/L2/L3 y metadatos modo 3, y que las 31 tomas de camioneta sean V2G con `max_discharging_power = 7.4`.
