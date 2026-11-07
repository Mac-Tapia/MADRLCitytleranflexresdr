# SPEC-016 — Dataset `iquitos_v6`: realista, por edificio y con datos reales

**Estado:** `draft`, todas las decisiones del propietario cerradas
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Estado conciliado:** [STATUS](../STATUS.md) · **Hoja de ruta:** [hoja_ruta_modulos.md](../../docs/plans/hoja_ruta_modulos.md) (módulo 3b)
**Revisión:** 2026-11-07 (D-V6-14 y D-V6-15)

## Propósito

Construir el dataset con el que se entrenará, de modo que cada uno de los 17 edificios tenga sus propios datos, sus propios equipos y su propia factura, todo anclado a datos reales o a normas citadas, y que los agentes MADRL aprendan a controlar los recursos controlables de cada edificio. No entrena: el entrenamiento es el módulo 8.

Cada valor del dataset lleva su origen: `measured` (facturas, inventario), `cited` (norma o fuente publicada, con artículo), `design_rule` (decisión del propietario) o `assumption` (sin fuente, declarado, reemplazable por el propietario). Ninguna cifra se inventa.

## Datos reales disponibles

| Fuente | Contenido | Granularidad |
|---|---|---|
| Facturas `B_02.csv` a `B_17.csv` | Energía en punta y fuera de punta, reactiva, factor de carga, total facturado, tarifa | Mensual, 2023-2025 |
| `resultados_preliminares.xlsx` | Energía activa y máxima demanda (kW) | Mensual, desde 2020 en algunos edificios |
| Inventario `building.csv` | Área techada, tipo de uso, oficinas y locales, equipos split, sistemas grandes, área de estacionamiento, vehículo predominante | Por edificio |
| Pliegos y PDF de Osinergmin | Tarifas de energía y de potencia | Por vigencia |
| NASA POWER | Clima observado 2023-2025 | Horaria |

No existe ningún perfil horario medido. B01 no tiene factura medida: `B_01.csv` es generado por el proyecto.

## Decisiones del propietario (2026-11-06)

| ID | Decisión |
|---|---|
| D-V6-1 | **Controlables por edificio:** aire acondicionado, cargadores de vehículos y BESS. La máquina desplazable deja de ser acción y su energía queda en la carga base |
| D-V6-2 | **Aire acondicionado en los 17 edificios**, controlable dentro de un límite de confort tomado de una norma de confort para clima cálido y húmedo |
| D-V6-3 | **Capacidad del aire acondicionado** según tipo de edificio, personas, potencia por área techada, pisos y oficinas: RNE EM.050 y EM.030 para todos; NTS 110 y 119 del MINSA (ASHRAE 170) y RM 666-2025/MINSA para B11 y B12, con valores de los PDF oficiales; 18 000 BTU/h por split solo donde ninguna norma dé cifra |
| D-V6-4 | **Personas** = área × densidad por defecto de ASHRAE 62.1 (Tabla 6.2.2.1); sin pisos en el inventario, el área techada es el área total, declarado |
| D-V6-5 | **Carga base en todos los edificios**, nunca 0: cantidad = factura real − refrigeración calibrada (D-V6-14), forma desde horarios de funcionamiento de los edificios de referencia del DOE y ASHRAE 90.1 por tipo, ajustados a las horas de cada edificio |
| D-V6-6 | **Cargadores** por tipo de edificio, área y plazas de estacionamiento y vehículos estacionados: 1 punto por cada 10 plazas (EPBD 2024, art. 14, existentes) y 5 % de los vehículos estacionados eléctricos (meta MINEM 2030). Escenario a 2030; sustituye el piloto de 2 motos en B01 |
| D-V6-7 | **BESS** para almacenar el excedente solar y cargar los vehículos, dimensionado en el **día de mayor excedente** del año de diseño; parámetros de un modelo del catálogo comercial de CityLearn |
| D-V6-8 | **Recompensa con la factura (D04):** costo horario = energía + aumento del cargo por potencia cuando supera el pico del mes en el bloque de 18:00 a 23:00 |
| D-V6-9 | **FV** con pvlib (SAPM, NASA POWER observado), limitada por el área techada × 0,63 y por FV/carga ≤ 1,0, que coincide con `PV.autosize` de CityLearn (0,7 a 1,0) |
| D-V6-10 | **Tensión de carga** de 220 V, la nominal de baja tensión en Perú |
| D-V6-11 | **Sin entrenar** hasta cerrar todos los módulos |
| D-V6-12 | **Un agente por edificio:** cada agente controla todo el aire acondicionado, los cargadores y el BESS de su edificio; no se divide por pisos |
| D-V6-13 | **Acciones según la operación de cada equipo** (propietario, 2026-11-06): cada equipo controlable es una acción propia con su sentido físico: el BESS carga o descarga, cada cargador fija la potencia hacia su vehículo y el aire acondicionado enfría dentro del límite de confort. Los cargadores no se agrupan. Los 4 MADRL conservan su interfaz nativa con máscaras (SPEC-015 D-M3-6) |
| D-V6-14 | **Refrigeración por modelo físico calibrado** (propietario, 2026-11-07), sustituye la regresión con punto de cambio. En Iquitos la temperatura media mensual solo varía 1,94 °C y la regresión atribuye entre −17 % y +9 % a la refrigeración ([auditoría](../../docs/audits/cambio_punto_iquitos_20261107/README.md)). La refrigeración horaria sale del inventario y las normas de D-V6-3 (capacidad instalada × curva de carga parcial con la temperatura horaria y el horario de uso) y se calibra contra las 36 facturas con los criterios de simulación calibrada de ASHRAE Guideline 14 (CV(RMSE) y NMBE mensuales, cifras a confirmar en el texto de la guía). La factura fija el total; carga base = factura − refrigeración, mayor que 0. |
| D-V6-15 | **Energía medida = punta + fuera de punta** (propietario, 2026-11-07). `totalEnergiaActiva` no coincide en B02, B09, B11, B16 y B17; queda como campo de auditoría y cada discrepancia se registra en `quality_flags`. |
| D-V6-16 | **Capacidad del aire acondicionado = inventario + ventilación** (propietario, 2026-11-07), corrige D-V6-3. Las normas peruanas no dan capacidad: EM.050 no tiene cifras y RM 666-2025-MINSA no trata del calor extremo ([auditoría](../../docs/audits/normas_climatizacion_20261107/README.md)). La capacidad es: splits × 18 000 BTU/h (5,275 kW térmicos, `assumption`) más, si el edificio tiene un sistema grande, la carga del aire exterior de EM.030 art. 6 (`Vbz = Rp·Pz + Ra·Az`, Tabla N° 01, `cited`) y la ganancia de los ocupantes. Las condiciones exteriores son el 1 % de NASA POWER 2023 (`measured`) y las interiores las de D-V6-17. La potencia eléctrica es la térmica ÷ COP. La calibración de D-V6-14 contrasta la capacidad: un edificio que no ajusta queda marcado. No se usan cifras de W/m² sin fuente primaria. |
| D-V6-17 | **Límite de confort = 24 °C** (propietario, 2026-11-07): NTS 110 y 119 del MINSA, áreas generales, 24 °C y 45-60 % de HR (`cited`). Se aplica a los 17 edificios como `design_rule` hasta que el propietario aporte ASHRAE 55; las salas de operaciones y la UCI de B11 y B12 conservan sus propias filas de la Tabla 6. |
| D-V6-18 | **Refrigeración física con tope en la factura** (propietario, 2026-11-07), concreta D-V6-14: las facturas mensuales no pueden calibrar la fracción de refrigeración con 2 °C de rango térmico; solo la acotan. Refrigeración horaria = capacidad (D-V6-16) × carga parcial ÷ COP; la carga parcial es la diferencia de entalpía exterior-interior respecto a la de diseño por el horario de uso (`assumption`: carga dominada por el aire exterior). Si un mes supera la factura menos un piso de carga base, se recorta a ese tope y el edificio queda marcado. El piso es el 30 % de la factura (`design_rule`), coherente con RM 666-2025-MINSA, que sitúa la climatización en el 60-70 % del consumo de un establecimiento de salud, el tipo más intensivo. Carga base = factura − refrigeración, repartida con su forma horaria. Control medible: la carga base diaria implícita es estable entre meses (CV ≤ 15 %, criterio mensual de ASHRAE G14 vía FEMP 4.0); si no, el edificio queda marcado. Un edificio marcado bloquea la puerta. |
| D-V6-19 | **Ajuste de D-V6-18 con los datos reales de 2023** (propietario, 2026-11-07). (1) Se retira el control de estabilidad de la carga base: su CV reproduce el de la propia factura (B02 de 45 a 233 kWh/día, B06 ×4), porque en Iquitos la variación no climática pertenece a la carga base; el CV solo se informa. (2) El recorte no bloquea: en B11 (211 %), B09 (149 %), B03, B02 y B14 la refrigeración física supera la factura, se recorta al 70 % y se declara «capacidad sobreestimada por el inventario»; el propietario revisa B11 y B09 cuando tenga datos reales. |
| D-V6-20 | **Facturas posiblemente parciales** (propietario, 2026-11-07). Con el COP de CityLearn, la refrigeración física del inventario supera la factura todo el año en 11 de 16 edificios (B11 1 195 %: unos 100 kW de media en 42 649 m², 2,3 W/m²; B09 806 %; [auditoría](../../docs/audits/calibracion_refrigeracion_20261107/README.md)). Se mantiene el tope declarado de D-V6-19 y el propietario verifica si `B_xx.csv` cubre todos los suministros de: B11, B09, B03, B14, B02, B12, B16, B17, B08 y B13. Si una factura resulta parcial, se completa con los suministros que falten; si es completa, se revisa el inventario de ese edificio. |
| D-V6-21 | **Cargadores y vehículos con fuentes verificadas** (propietario, 2026-11-07), concreta D-V6-6 ([auditoría](../../docs/audits/cargadores_vehiculos_20261107/README.md)). Plazas = área de estacionamiento ÷ área por plaza derivada de RNE A.010 (arts. 54 y 57), incluido medio pasillo: auto 20,6 m² de uso público y 19,2 m² de uso privado (oficinas y hoteles); moto 8,6 m² y 8,25 m². Puntos de carga = 1 por cada 10 plazas cuando hay más de 20 (EPBD 2024, art. 14(2)). Vehículos eléctricos = 5 % de las plazas (`assumption_pending_user_verification`: la cifra del MINEM solo consta en prensa; la NDC, MINAM 2023, da 171 359 vehículos ligeros y excluye motos). Potencia: motos y mototaxis en modo 2 a 220 V y 16 A (3,5 kW); autos en modo 3 a 220 V y 32 A (7,0 kW), según D.S. 036-2023-EM. Los edificios con vehículos pesados (B08, B09, B14 y B16) cuentan su estacionamiento como plazas de auto para el personal y las visitas; sus vehículos pesados quedan fuera de la electrificación, declarado. |
| D-V6-22 | **Acción solo para los cargadores con vehículo** (propietario, 2026-11-07), concreta D-V6-13. De los 398 puntos de carga, solo los 202 con un vehículo eléctrico asignado son acciones (B06: 52); los demás se informan como infraestructura instalada según la EPBD y no se simulan, porque sin vehículo la acción no tiene sentido. Cada cargador simulado sigue siendo una acción propia, sin agrupar. |
| D-V6-23 | **Tres clases de vehículo eléctrico** (propietario, 2026-11-07), corrige el reparto moto/auto de D-V6-21: motos eléctricas, mototaxis eléctricos y camionetas eléctricas. Solo las camionetas son bidireccionales (V2G): su cargador descarga hacia el edificio (`max_discharging_power` > 0 en CityLearn); motos y mototaxis solo cargan. Batería, potencia de carga y descarga y energía diaria de cada clase, con fuente citada. |
| D-V6-24 | **Reparto de la flota por el tipo predominante** (propietario, 2026-11-07, `design_rule`). Cada palabra del tipo del inventario fija una clase: `Motos` y `Bicycles_Motos` dan motos; `Motokars` y `Taxis`, mototaxis; `Pickups`, `Cars`, `Ambulances`, `Staff`, `Trucks`, `Military`, `Emergency` y `Cranes`, camionetas en plazas livianas. `Students` no añade clase y los buses quedan fuera, como vehículos pesados. Cuando el tipo nombra varias clases, los vehículos eléctricos se reparten por igual entre ellas; el área por plaza es la de la primera clase. El propietario puede ajustar el reparto por edificio. |
| D-V6-25 | **Todo se construye en la capa CityLearn v3 para MADRL** (propietario, 2026-11-07): `CityLearn/citylearn/dec_pomdp.py` (Dec-POMDP), `CityLearn/citylearn/v3/` (entorno, `marllib_env.py`, recompensa y objetivos) y el adaptador de los backends `CityLearn/scripts/citylearn_v3_training_common.py`, nunca las clases de la v2 original. La recompensa con la factura, las observaciones del pico del mes, del bloque y de la tarifa, el V2G de las camionetas y una acción por cargador se implementan y prueban a través del entorno v3. Los módulos de `uc3m/application/dataset/` solo generan el esquema y los CSV que v3 consume, y sus funciones (por ejemplo `incremental_bill_cost`) sirven de oráculo en las pruebas. |
| D-V6-26 | **Flota bien distribuida por edificio, 80/20** (propietario, 2026-11-07), sustituye el reparto de D-V6-24: las clases que nombra el tipo predominante se reparten el 80 % de los vehículos eléctricos del edificio y las otras el 20 %, con redondeo por mayor resto (`design_rule`, editable por edificio en `configs/dataset/ev_v6.yaml`). Todo edificio con 4 o más vehículos tiene motos, mototaxis y camionetas. Distrito: 72 motos, 52 mototaxis y 78 camionetas V2G. Ejemplos: B06 21/21/10, B03 13/13/6, B11 1/1/9, B07 5/1/1 y B16 1/1/10. Las plazas se miden con la primera clase nombrada (moto o auto). |
| D-V6-27 | **Carga por cola con modo, tiempo y factores** (propietario, 2026-11-07), sustituye D-V6-22. (1) **Cola real:** los vehículos de cada clase llegan según su horario y esperan en una cola FIFO los cargadores de su clase; puede haber más vehículos que cargadores. Las acciones son los cargadores y el vehículo conectado a cada uno cambia a lo largo del día. (2) **Modo y tiempo de carga:** cada clase carga en su modo del D.S. 036-2023-EM; tiempo = energía requerida ÷ potencia del modo. Las ventanas de conexión se precalculan a potencia nominal, declarado; el agente decide la potencia dentro de cada ventana. (3) **Factor de penetración (PE):** fracción eléctrica de los vehículos por clase, que sustituye el 5 % único de D-V6-21. (4) **Factor de coincidencia o demanda (FC):** limita la potencia conjunta de carga del edificio según la tabla de factor de demanda del D.S. 036-2023-EM, art. 13.3.1. (5) **Factor de carga del cargador:** energía entregada ÷ (potencia × 24 h), informado y contrastado por clase. Cada valor con fuente citada o declarado como supuesto. |
| D-V6-28 | **La descarga de las camionetas es V2B detrás del medidor** (propietario, 2026-11-07), concreta D-V6-23. Ninguna camioneta vendida en Latinoamérica documenta V2G real (Maxus eTerron 9 y Riddara RD6: V2L; Ford F-150 Lightning: V2H) y el D.S. 036-2023-EM no contempla la inyección desde vehículos ([fuentes](../../docs/audits/cargadores_vehiculos_20261107/clases_vehiculo.md)). La camioneta descarga solo hacia el consumo de su edificio, con la descarga de cada hora limitada a la demanda del edificio y sin exportación a la red. Escenario 2030 fuera de la regulación vigente, declarado. |
| D-V6-29 | **Llegadas por horario del edificio y clase** (propietario, 2026-11-07, `assumption`): motos y camionetas del personal llegan en las 2 primeras horas tras la apertura del edificio (`configs/dataset/building_types.yaml`) y salen al cierre; los mototaxis hacen 2 paradas cortas al día, de 12 a 14 h y de 18 a 20 h. Horas sorteadas con semilla fija; el SOC requerido a la salida cubre el siguiente recorrido. La cola FIFO por clase genera el CSV horario de cada cargador en el formato de CityLearn (`ChargerSimulation`). |
| D-V6-30 | **El BESS también recorta picos y traslada de punta a valle** (propietario, 2026-11-07), amplía D-V6-7. Recorte = 20 % del mayor bloque horario de importación de 18:00 a 23:00 del año (`assumption_pending_user_verification`, la fracción de la regla v4); energía trasladada = recorte × horas del bloque. Energía = máx(excedente + vehículos; energía trasladada) y potencia = máx(excedente, vehículos, recorte): una sola batería cumple ambas funciones y los MADRL aprenden su control según los tres ejes (flexibilidad, CO₂ y costo con factura). |

## Reglas propuestas por la implementación, pendientes de confirmar (2026-11-07)

Estas reglas las fijó la implementación, no el propietario. Están en el código y en la configuración citados, declaradas, y no cuentan como decisión hasta que el propietario las confirme o las cambie.

| ID | Regla | Dónde está | Origen |
|---|---|---|---|
| P-V6-1 | El agua caliente (DHW) queda dentro de la carga base y nunca supera el 50 % de ella en cada hora | `tools/dataset/distill_building_loads.py`, `calibrate_building_physical` | implementación |
| P-V6-2 | La forma horaria de la carga base es el horario de `building_types.yaml` con un mínimo de 0,05 (consumo nocturno) | mismo archivo | implementación |
| P-V6-3 | El COP usa el objetivo de refrigerante del esquema (8,5 °C por defecto), no el setpoint de la sala | `physical_cop_params` | implementación, por la fórmula de CityLearn |
| P-V6-4 | La batería es el primer modelo del catálogo de CityLearn que declara eficiencia, profundidad de descarga y pérdidas (PowerPlus LiFe2433P), con unidades en paralelo | `uc3m/application/dataset/bess_sizing.py` | implementación |
| P-V6-5 | Sin punto de carga no hay vehículo eléctrico en el edificio | `uc3m/application/dataset/ev_sizing.py` | implementación; revisar con la cola de D-V6-27 |
| P-V6-6 | La descarga V2B de la camioneta es de 7,04 kW, el mismo límite de la conexión monofásica de 32 A | `configs/dataset/ev_v6.yaml` | implementación |
| P-V6-7 | Asignación de filas de EM.030: la escuela militar como aulas; los edificios de salud con `rd` de oficina y 3 de las 2-3 renovaciones por hora de la NTS 110 | `configs/dataset/hvac_norms.yaml` | implementación |
| P-V6-8 | Asignación de filas del factor de demanda: el aeropuerto como parqueo público; el laboratorio como parqueo privado; la escuela militar como educación | `configs/dataset/ev_v6.yaml` | implementación |
| P-V6-9 | Factor de demanda en el extremo inferior de cada rango (0,6 y 0,5) | `configs/dataset/ev_v6.yaml` | implementación, por el «como mínimo» del decreto |
| P-V6-10 | Valores de cálculo: densidad del aire 1,2 kg/m³; altura de techo 3 m; ganancia por ocupante 130 W; fracción ocupada 1,0; HR interior 50 % (punto medio de 45-60 %); diseño exterior en el percentil 99 | `configs/dataset/hvac_norms.yaml` | implementación (`assumption`) |
| P-V6-11 | Recorrido diario de 40 km para motos y camionetas; 38,25 km para mototaxis, deducido de 4,78 kWh/día ÷ 0,125 kWh/km | `configs/dataset/ev_v6.yaml` | implementación |
| P-V6-12 | Potencia de carga de la moto de 0,6 kW, la del cargador a bordo del Super Soco CPx | `configs/dataset/ev_v6.yaml` | implementación |
| P-V6-13 | Tolerancia de cierre de 1e-3 kWh por bloque, por la escritura del CSV con 6 decimales | `tests/fresh_training/test_distill_physical.py` | implementación |
| P-V6-14 | Los cargadores de un edificio se reparten entre las clases en proporción a sus vehículos (mayor resto), con uno por clase con vehículos primero si alcanzan; una clase sin vehículos no recibe cargadores | `uc3m/application/dataset/ev_sizing.py` (`charger_split`) | implementación |
| P-V6-15 | Un día es de apertura si su factor de día es al menos 0,5 (oficina: lunes a viernes; 24 h: todos los días). El vehículo llega habiendo gastado la energía de una sesión (moto 1,56 kWh; mototaxi 2,39 kWh por parada; camioneta 10,68 kWh) y pide batería llena; si la conexión se corta por la salida, pide solo lo que alcanza a potencia nominal. Semilla 0 | `configs/dataset/ev_v6.yaml` (`queue_rules`), `uc3m/application/dataset/ev_queue.py` | implementación |
| P-V6-16 | El cargador se libera al terminar el tiempo de carga a potencia nominal (D-V6-27 (2)): la camioneta queda conectada unas 2 h al día, lo que limita su descarga V2B a esas horas | `uc3m/application/dataset/ev_queue.py` | implementación; **a revisar**: si la camioneta debe quedar conectada hasta su salida cuando nadie espera, para ampliar el V2B |

## Estado de cada decisión en el código (2026-11-07)

| Decisión | En el código | Pendiente |
|---|---|---|
| D-V6-14 a D-V6-19 (refrigeración física con tope en la factura) | `hvac_capacity.py`, `cooling_calibration.py`, `calibrate_building_physical` | Conectarlo al constructor del dataset |
| D-V6-15 (punta + fuera de punta) | Destilación de v6 | — |
| D-V6-17 (24 °C) | `hvac_norms.yaml` | Control con confort en v3 (FR-016.4) |
| D-V6-8 (recompensa con factura) | Oráculo `bill_tariff.incremental_bill_cost` y archivos horarios de tarifa | Recompensa en `citylearn/v3/reward.py` |
| D-V6-21, D-V6-23, D-V6-24 y D-V6-26 (cargadores y 3 clases, 80/20) | `ev_sizing.py`, `ev_v6.yaml` | — |
| D-V6-27 (cola, modo, tiempo, PE, FC y factor de carga) | Cola FIFO por clase (`ev_queue.fifo_queue`), tiempo de carga a potencia nominal, PE por clase en el conteo (`ev_sizing.penetrated_fleet`; el 5 % único se retiró de `ev_v6.yaml`), FC (`coincidence_cap_kw`) y factor de carga informado (`ev_queue.load_factor`). Resultado del distrito en 2023: 398 cargadores, 202 vehículos, ninguna sesión sin atender y factor de carga de 1 % a 5 %; con PE = 5 % nunca se forma cola (hay unos 2 cargadores por vehículo) | Conectar al constructor `iquitos_v6` (3b.4) |
| D-V6-28 (V2B detrás del medidor) | Parámetros de la camioneta | Límite de la descarga a la demanda del edificio en v3 |
| D-V6-29 (llegadas) | Reglas en `ev_v6.yaml` (`arrivals`); sesiones (`ev_queue.class_sessions`) y tablas en el formato `ChargerSimulation` de CityLearn (`ev_queue.charger_tables`, SOC en %) | Escribir los CSV en el constructor (3b.4) |
| D-V6-30 (BESS con doble función) | `bess_sizing.py` | Conectarlo al constructor |
| D-V6-20 (facturas posiblemente parciales) | Recorte declarado | Verificación del propietario |
| D-V6-25 (capa v3) | Regla registrada | Toda la integración de 3b.4 y 3b.5 |

## Requisitos funcionales

- **FR-016.1** — Reparto refrigeración y carga base según D-V6-14, por edificio: refrigeración del modelo físico de FR-016.3 calibrado con las facturas (criterios de ASHRAE Guideline 14 para simulación calibrada) y carga base como resto. La suma de componentes reproduce cada factura mensual (punta + fuera de punta, D-V6-15). Los meses recortados se declaran sin bloquear (D-V6-19).
- **FR-016.2** — Carga base mayor que 0 en todas las horas de los 17 edificios, con la forma horaria de D-V6-5.
- **FR-016.3** — Potencia del aire acondicionado desde el inventario y las normas de D-V6-3, contrastada con el rango de W/m² del tipo; deja de autodimensionarse desde la demanda modelada.
- **FR-016.4** — Aire acondicionado controlable con límite de confort, con la dinámica térmica de cada edificio validada.
- **FR-016.5** — Cargadores y vehículos según D-V6-6, con la potencia de carga por tipo de vehículo de una fuente citada y 220 V. La energía de los vehículos se declara como demanda nueva sumada a la factura.
- **FR-016.6** — BESS según D-V6-7, con puerta de conservación de energía anual (carga × eficiencia − descarga − variación del estado de carga).
- **FR-016.7** — Tarifa de potencia por edificio y mes dentro del dataset, para que la recompensa de D-V6-8 no lea archivos del proyecto.
- **FR-016.8** — Contraste de picos: por edificio y mes, el pico generado frente al pico medido por factor de carga y máxima demanda.
- **FR-016.9** — Todas las puertas de `iquitos_v5` siguen vigentes, más las nuevas de FR-016.1 a FR-016.8.
- **FR-016.10** — Adecuación a los 4 MADRL (HAPPO, MASAC, MATD3 y MAAC), decidida por el propietario el 2026-11-06 para cerrar este spec completo antes de entrenar:
  - **Acciones:** cada agente controla su aire acondicionado, sus cargadores y su BESS. Los espacios de acción continuos (HAPPO, MATD3, MAAC) y discretos (MASAC por ejes) representan los mismos equipos, con la equivalencia declarada (D03).
  - **Observaciones:** incluyen lo que la recompensa necesita para ser markoviana con la factura: el pico del mes en el bloque de 18:00 a 23:00 hasta la hora actual, si la hora está en ese bloque y la tarifa de potencia del edificio, además de temperatura interior y confort para el aire acondicionado.
  - **Recompensa:** la misma para los 4 algoritmos y los 3 escenarios, con el costo de la factura (D-V6-8) y el CO2, de modo que E2 y E3 queden separados.
  - **Capacidad nativa:** los 4 conservan la capacidad de sus autores (SPEC-015 D-M3-5, `tests/fresh_training/test_author_capacity.py`). Las dimensiones nuevas nunca encogen un búfer, un lote ni una red: si no caben, el guardián rechaza la fase con las cifras.
  - **Recursos:** las dimensiones nuevas recalculan los requisitos de memoria por la regla de SPEC-015, verificada por `tests/fresh_training/test_runtime_requirements.py`; las reservas ajustadas de Colab no cambian salvo que dejen de cubrir la estimación.
  - **Prueba de humo:** los 4 algoritmos completan un episodio corto real sobre `iquitos_v6` y guardan su estado de entrenamiento, sin entrenar la campaña.
- **FR-016.11** — Conformidad con la tupla de CityLearn v3 (propietario, 2026-11-06), `M_e = <N, S, {A_i}, P, r_e, {O_i}, Z, rho_0, gamma, H>` por escenario, definida en `docs/audits/architecture_thesis_20261101/informe.md` §5, con los ejes y KPI de `CityLearn/citylearn/v3/objectives.py` y `configs/evaluation/kpis.yaml`:

  | Elemento | En `iquitos_v6` |
  |---|---|
  | `N` | 17 agentes, uno por edificio; los cargadores pertenecen al edificio, no son agentes |
  | `S` | Estado del simulador, incluido el pico del mes en el bloque de 18:00 a 23:00, que la recompensa con factura necesita |
  | `A_i` | Aire acondicionado, cargadores y BESS del edificio i, con el mapa de decodificación `D_i^(b)` de cada backend declarado |
  | `O_i`, `Z` | Observación local: incluye el pico del mes, la pertenencia al bloque, la tarifa de potencia, la temperatura interior y el confort; normalización declarada |
  | `r_e` | `(1/N) Σ_i scale·[w_flex·F_i + w_co2·C_i + w_cost·K_i + p_EV,i + p_BESS,i]`, con `K_i` = factura del edificio (D-V6-8) |
  | Ejes y pesos | OE1 flexibilidad (E1), OE2 CO2 (E2), OE3 costo (E3), con los pesos de `configs/objective_policies.yaml` |
  | `rho_0` | Estado inicial declarado: estado de carga del BESS y de los vehículos, inicio del split y semilla |
  | `gamma`, `H` | Del tratamiento congelado; `H` cubre días completos para los KPI diarios |

  **Correspondencia obligatoria**, verificada por una prueba de contrato: cada término de recompensa pertenece a un eje y a un KPI del catálogo; cada eje tiene al menos un KPI primario que la evaluación mide; cada acción corresponde a un equipo del edificio y cada observación que la recompensa usa está en `O_i`. Un término sin KPI, un KPI sin eje o una observación faltante hacen fallar la prueba.

## Criterios de aceptación

1. `dataset_verified=true` con todas las puertas, en los 17 edificios.
2. Ningún edificio con carga base 0 en ninguna hora.
3. Para cada edificio, la suma de componentes reproduce cada factura mensual.
4. Cada valor lleva origen `measured`, `cited`, `design_rule` o `assumption`, y cada `cited` nombra la norma y el artículo.
5. Los 4 MADRL completan la prueba de humo de FR-016.10 sobre `iquitos_v6`.
6. La prueba de contrato de FR-016.11 pasa: recompensa, ejes, KPI, acciones y observaciones corresponden a la tupla de v3.
7. Puerta `-Scope Repository` aprobada, CI en verde.

## D-V6-12: por qué no se controla por piso

CityLearn modela cada edificio como una sola zona térmica con un agente, y las facturas y el inventario son por edificio. Controlar por piso exigiría datos por piso (área, equipos, ocupación) que no existen, y repartir una factura entre pisos sería una división inventada. El propietario eligió un agente por edificio el 2026-11-06; si consigue datos por piso, se puede revisar.
