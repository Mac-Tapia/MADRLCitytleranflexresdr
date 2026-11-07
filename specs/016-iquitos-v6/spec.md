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

## Requisitos funcionales

- **FR-016.1** — Reparto refrigeración y carga base según D-V6-14, por edificio: refrigeración del modelo físico de FR-016.3 calibrado con las facturas (criterios de ASHRAE Guideline 14 para simulación calibrada) y carga base como resto. La suma de componentes reproduce cada factura mensual (punta + fuera de punta, D-V6-15). Un edificio cuyo modelo calibrado no cumple los criterios queda marcado y bloquea la puerta.
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
