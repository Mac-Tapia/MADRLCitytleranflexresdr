# Hoja de ruta por módulos hasta el entrenamiento

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Revisión:** 2026-11-08 · **Fuente de pendientes:** [STATUS](../../specs/STATUS.md), `git log` y [remediación integrada](remediacion_integrada.md)

## Regla del propietario (2026-11-06)

Los módulos se implementan y cierran uno por uno. **No se entrena hasta que el proyecto esté completo**: todos los specs sin pendientes y la arquitectura terminada. La autorización de `pilot` dada ese día queda aplazada hasta el módulo final; `authorized_stages` sigue vacío.

**Estado al 2026-11-08:** la regla sigue vigente y no se cumple todavía, porque los módulos 3b, 5, 6 y 7 tienen trabajo abierto. Ninguna etapa está autorizada. Los estados de abajo incluyen trabajo escrito sin commit, y se indica cuando es así.

Un módulo se cierra con spec, pruebas en rojo y luego en verde, puerta `-Scope Repository` aprobada sobre su commit, CI en verde, registros actualizados y publicación.

## Módulos

| Módulo | Alcance | Specs y tareas | Estado |
|---|---|---|---|
| 1. Tarifas oficiales | PDF PBA, contraste, factura con cargo por potencia | SPEC-013 | Cerrado |
| 2. Dataset físico y reconexión | `iquitos_v5`, FV/carga, integridad, S9 | SPEC-014 | Cerrado |
| 3. Contrato de algoritmos y recursos ([SPEC-015](../../specs/015-modulo3-algoritmos/spec.md)) | **Hecho:** requisitos derivados del dataset activo y por candidato (FR-015.1 y FR-015.2); MASAC con capacidad nativa, sin reformular su búfer (D-M3-1 sustituye a D05); los 4 MADRL con la capacidad de sus autores, MAAC con su esquema original (D-M3-5, FR-015.3); conformidad de `NativeBackend` y cancelación de hijos (FR-015.4, FR-003.5). `training_state.pt` en los 4 lanzadores (FR-015.5); recompensa por edificio con cuadre por paso (FR-015.6); D03 con máscaras (FR-015.7). Puerta `Repository` sobre `e5ae4d4f`: 1 663 pruebas | SPEC-015, SPEC-002, SPEC-003, SPEC-004, D03 | Cerrado |
| 3b. Dataset `iquitos_v6` adecuado a los 4 MADRL ([SPEC-016](../../specs/016-iquitos-v6/spec.md)), justo después de cerrar el módulo 3 | **Normas peruanas para el aire acondicionado (propietario, 2026-11-06):** las capacidades se toman de normas peruanas y proyectos hospitalarios, no de un valor genérico: RNE EM.050 (climatización) y EM.030 (ventilación) para todos los edificios; para B11 y B12, las NTS del MINSA 110 (segundo nivel) y 119 (tercer nivel), que remiten a ASHRAE 170, y la RM 666-2025/MINSA frente al calor extremo. Las cifras (temperatura de diseño, renovaciones por hora) se toman de los PDF oficiales del MINSA y del Ministerio de Vivienda, citando el artículo; los 18 000 BTU/h por split quedan solo donde ninguna norma dé valor. **BESS (propietario, 2026-11-06), sustituye el recorte del 20 % del pico:** se dimensiona para almacenar el excedente solar del edificio y cargar sus vehículos eléctricos. Energía = excedente FV diario + energía diaria de carga de los vehículos no cubierta directamente por la FV, sobre la ventana útil y la eficiencia de la batería, en el día de mayor excedente del año de diseño (propietario, 2026-11-06), así que la batería guarda todo el excedente de cualquier día; potencia = máximo entre el excedente horario y la potencia de carga de los vehículos. **Aire acondicionado en todos los edificios (propietario, 2026-11-06):** su tamaño depende del tipo de edificio, la afluencia de personas, la potencia por área techada y los pisos y oficinas. En `iquitos_v5` la potencia se autodimensiona desde la demanda modelada y contradice el inventario (B11, hospital con 120 splits: 199 kW, 4,7 W/m²; B14, 22 splits: 9,5 kW, 0,5 W/m²; B04: 175,6 W/m²). En `v6`: potencia = splits del inventario × 18 000 BTU/h (5,3 kW, valor típico declarado como supuesto) + sistemas grandes por densidad del tipo, contrastada con el rango de W/m² de cada tipo; personas = área × densidad de ocupación por defecto de ASHRAE 62.1 (Tabla 6.2.2.1); sin pisos en el inventario, el área techada se toma como área total, declarado. La energía anual del aire acondicionado sale de la parte de la factura que depende de la temperatura. El propietario reemplaza los valores típicos cuando tenga los reales. **Carga base en todos los edificios (propietario, 2026-11-06):** todos tienen iluminación, tomacorrientes y consumo básico, así que la carga base nunca es 0. Su cantidad sale de las facturas reales (parte que no depende de la temperatura); su forma, de horarios de funcionamiento con fuente: los 11 horarios de `configs/dataset/building_types.yaml` son `assumption` y se sustituyen por los de los edificios de referencia del DOE y ASHRAE 90.1 para cada tipo, ajustados a las horas reales de cada edificio. Puerta: carga base mayor que 0 en todas las horas de los 17 edificios. **FV:** los perfiles de pvlib (`ModelChain` SAPM, NASA POWER observado) están en `solar_generation`; producción 2023 de 1 267 a 1 405 kWh/kWp, el 63 % entre 10:00 y 14:00. **Cargadores de vehículos (propietario, 2026-11-06), sustituye el piloto de 2 motos solo en B01:** según el tipo de edificio, el área y las plazas de estacionamiento y los vehículos estacionados, con más cargadores en edificios grandes, comerciales y de oficinas de mucha afluencia. Plazas = `Area_Estacionamiento_m2` ÷ superficie por plaza del tipo de vehículo predominante (cifra a verificar en el Reglamento Nacional de Edificaciones); cargadores = 1 por cada 10 plazas (EPBD 2024, art. 14, edificios no residenciales existentes con más de 20 plazas); vehículos eléctricos = 5 % de los vehículos estacionados (meta MINEM 2030). Perú: el D.S. 036-2023-EM regula la carga privada pero no fija un mínimo por plaza. Es un escenario a 2030 con respaldo oficial, no la situación actual. La afluencia por edificio de `dimension_ev_chargers.py` no tiene fuente y no se usa sin confirmación. **Controlables por edificio (propietario, 2026-11-06):** aire acondicionado, cargadores de vehículos y BESS; la máquina desplazable deja de ser acción y su energía queda en la carga base. **Balance de `iquitos_v5`, sin control, 2023:** refrigeración + carga base + agua caliente + máquina suman la factura en los 17 edificios (1,0000), pero la carga base es 0 en 10 de ellos (B03, B04, B05, B09, B11, B12, B13, B14, B16 y B17), así que el 73 % controlable del distrito está inflado. Los cargadores de B01 quedan fuera de la factura (demanda nueva del piloto) y el BESS no suma, porque desplaza energía. `v6` debe cumplir por edificio: suma igual a la factura, carga base mayor que 0 salvo que las facturas digan lo contrario, y reparto obtenido de los datos reales. **Reparto refrigeración y carga base (D3-006, confirmado el 2026-11-06):** en `iquitos_v5` la carga no desplazable es 0 todo el año en B03, B04, B09, B14 y B17, y casi 0 en B13, porque la destilación prioriza la refrigeración del modelo físico y deja la carga base como residuo de la factura. En `v6` el reparto se estima con las facturas reales: regresión con punto de cambio del consumo mensual frente a la temperatura (ASHRAE Guideline 14, PRISM), que separa la parte que depende del clima de la carga base. **Control de la refrigeración (propietario, 2026-11-06):** cada edificio controla su refrigeración dentro de un límite de confort, con valor tomado de una norma de confort térmico para clima cálido y húmedo, que se propone al propietario; requiere validar la dinámica térmica de cada edificio y va después de corregir el reparto. **D04 (propietario, 2026-11-06), recompensa con la factura:** el costo de cada hora es su energía más el aumento del cargo por potencia cuando supera el pico que el mes llevaba en el bloque de 18:00 a 23:00 (`P·precio + tarifa_potencia × max(0, P − pico_del_mes)`); sumado en el mes da la factura sin cargo fijo. La tarifa de potencia entra al dataset (`iquitos_v6`), porque la recompensa no lee archivos del proyecto. No se reutiliza el costo del dataset anterior: repartía todo lo facturado como precio por kWh (0,38 a 1,07 USD/kWh) y CityLearn le añadía una forma diaria senoidal inventada (`scenario_manager.py:336-340`). **Contraste de picos (D3-008):** comparar, por edificio y mes, el pico de la curva generada con el pico medido que dan el factor de carga de las facturas (`energía / (horas × factor de carga)`) y la máxima demanda de `resultados_preliminares.xlsx`; si la desviación es grande, destilar para reproducir energía y pico medidos a la vez. **Vehículos:** corregir 230 V a 220 V, la tensión nominal de baja tensión en Perú; declarar que su energía se suma a la factura de B01 como demanda nueva del piloto; verificar la energía de las sesiones frente a km/día × kWh/km. **BESS:** puerta de conservación de energía anual (carga × eficiencia − descarga − variación del estado de carga); tomar eficiencia, profundidad de descarga, pérdidas y curvas de un modelo del catálogo de baterías comerciales que trae CityLearn (`Battery.autosize`, `sizing_data`) en lugar de los puntos medios; el 20 % de recorte sigue como regla del propietario y se declara conservador frente a CityLearn, que dimensiona para 1,5 a 3,5 h de demanda. **FV:** citar en SPEC-014 que el límite FV/carga ≤ 1,0 coincide con `PV.autosize` de CityLearn (fracción de energía neta cero entre 0,7 y 1,0). Todo con los datos reales que ya existen; los supuestos que solo puede confirmar el propietario se le piden con recomendación | SPEC-014 (D3-008), `configs/dataset/ev_pilot.yaml`, `configs/dataset/bess_design_rule.yaml` | **Hecho, falta el commit de `iquitos_v6_trial11`.** Dataset activo con 12 de 12 puertas y hash `d4ccd3d3…`; rejilla de D-M3-10 y capacidad térmica de D-V6-56. Siguen abiertos D-V6-20 (facturas) y los datos medidos para validar el 5R1C |
| 4. Estadística y selección | IQM con 3 semillas, `decide_oe_winner` sin Kruskal-Wallis, `select_best_model` sin significancia ni estado de corridas; verdad estadística única | SPEC-005 (defectos), SPEC-009 (documental) | **Cerrado** (`a45c8449`). La ejecución sobre la campaña real sigue en el módulo 8 |
| 5. Flujo y herramientas | Subcomandos por etapa en la CLI; 30 herramientas obsoletas; 16 que requieren decisión del propietario; reportes, tablas y `FigureRenderer` extraídos a `uc3m/application/evaluation/` y `uc3m/adapters/` (FR-003.4), con lo que SPEC-003 queda cerrado; descomposición por paso de la recompensa en el episodio de evaluación congelada (FR-002.5, evaluación) | SPEC-011, SPEC-003 (FR-003.4), SPEC-002 (FR-002.5) | **Parcial.** Herramientas (`data/audits/evaluation_tools_inventory.json`): 11 conservadas por el propietario y 3 obsoletas que siguen en el árbol con sus bloqueos registrados; las demás se retiraron en `6cd518e7` y `72a69690`, y 7 borrados más están preparados sin commit. Escritos, sin commit: FR-002.5 (recompensa por término en la evaluación) y los puertos (`ExperimentTrackerPort`, `uc3m/adapters/matplotlib_figures.py`). STATUS mantiene abiertos los subcomandos por etapa de la CLI |
| 6. Artefactos e higiene | Reglas de `.gitignore` de FR-008.4; ramas `codex/*`/`cursor/*`, duplicados y prueba de higiene integral | SPEC-008, SPEC-012 | **Parcial.** Reglas de ignorado y prueba de higiene en `da1cb226`; no hay ramas `codex/*` ni `cursor/*`. Sigue abierto FR-012.4 (duplicados) |
| 7. Agentes, skills y licencias | Invocación real, eficiencia, migración de 4 skills, hook heredado; pedidos de licencia | SPEC-007, SPEC-001 | **Parcial.** Tarea 7.1: 0 de 4 skills migrados, necesita una decisión del propietario por skill (`tools/skills/registry.yaml`, sin commit); el hook heredado ya salió del árbol (`72a69690`). Tarea 7.2: necesita sesiones medidas; `data/audits/skill_invocation_log.json` no tiene entradas y su puerta sigue abierta. Tarea 7.3: pedidos de licencia publicados el 2026-11-08, respuestas pendientes |
| 8. Entrenamiento y evaluación ([plan](modulo8_campana.md)) | Piloto, HPO, confirmación y sensibilidad en Colab; prueba real de Colab y copia fuera de la máquina; observaciones experimentales del jurado; tesis (SPEC-006) | SPEC-005, SPEC-006, SPEC-008, SPEC-009, SPEC-013, SPEC-014 | **Último, sin empezar.** Plan escrito; nada se ha ejecutado en Colab y ninguna etapa está autorizada |

## FV, BESS y vehículos frente a CityLearn original (2026-11-06)

Criterios del código de CityLearn (`citylearn/energy_model.py`): `PV.autosize` genera una fracción de energía neta cero entre 0,7 y 1,0 de la demanda anual, limitada por el techo; `Battery.autosize` elige un modelo comercial real del catálogo y lo dimensiona para cubrir la demanda horaria de 1,5 a 3,5 h; los vehículos de sus datasets siguen horarios sintéticos.

| Dataset | FV/carga | BESS kWh / carga diaria | BESS kW / suma de picos | Vehículos |
|---|---|---|---|---|
| CityLearn 2022 | 0,61 | 0,23 | 0,72 | 0 |
| CityLearn 2022 con vehículos | 0,86 | 0,23 | 0,72 | 8 |
| CityLearn 2023 | 0,13 | 0,60 | 0,20 | 0 |
| Iquitos original, anterior a `v1` | 0,80 | 0,16 | 0,42 | 1 850 |
| `iquitos_v5` | 0,21 | 0,04 | 0,09 | 2 |

Base común: carga más demanda térmica del año de diseño, que no es carga eléctrica; sirve para comparar entre datasets, no como valor absoluto (sobre carga eléctrica, `iquitos_v5` tiene FV/carga 0,51 y BESS de 19,1 % de los picos).

## Costo y CO2: por qué E2 y E3 no se separan hoy (2026-11-06)

Medido sobre los archivos de cada dataset:

| Señal | `iquitos_v5` | CityLearn 2022 y 2023 |
|---|---|---|
| Precio | Pliego Osinergmin por edificio y mes, plano dentro del mes (34 valores en 3 años) | Tarifa horaria de 2 a 5 niveles |
| Carbono | Constante, 0,667 kg/kWh (IPCC diésel, eficiencia supuesta 0,40) | Serie horaria de la red, unos 8 750 valores |
| Correlación horaria precio-carbono | No aplica (carbono constante) | 0,02 a 0,31 |

En `iquitos_v5`, costo y CO2 horarios tienen correlación 1,000 (línea base de `train_2023`): con el costo de energía en la recompensa, E2 y E3 enseñarían lo mismo. La señal real que los separa es el cargo por potencia del bloque de 18:00 a 23:00. **Recomendación para D04, en el módulo 3:** el eje de costo de la recompensa usa la factura con su cargo por potencia, igual que la evaluación. No se inventa tarifa horaria ni carbono variable. Mejoras que solo proceden con datos reales: carbono de la central de Iquitos desde combustible y generación de Electro Oriente, y revisar si algún pliego de usuario final de los edificios distingue energía en punta.

## Decisiones del propietario que siguen abiertas

| Decisión | Módulo | Recomendación |
|---|---|---|
| Supuestos económicos sin fuente (CAPEX FV, tasa de descuento) | 8 | Verificar con IRENA y la tasa social del MEF antes de la tesis final |
| Retirar `iquitos_v1` (D01) | 8 | Conservarlo hasta tener el piloto |
| 4 skills antiguos: retirarlos o migrarlos, uno por uno (tarea 7.1) | 7 | Ver `legacy_skills_review` en `tools/skills/registry.yaml` |
| Revisar si las facturas cubren todos los suministros (D-V6-20) | 3b, 8 | Decidir antes de pagar el entrenamiento: si un recibo es parcial, el dataset cambia |
| Decisión escrita para cada etapa | 8 | Ver la sección 4 de [modulo8_campana.md](modulo8_campana.md) |

Ya resueltas: D04, con el eje de costo y el cargo por potencia en la recompensa (D-V6-50); las 16 herramientas (`72a69690`); y la publicación de los pedidos de licencia (2026-11-08).

## Datos reales disponibles por edificio (revisión del 2026-11-06)

No existe ningún perfil horario medido: ni medidor horario, ni telemetría, ni SCADA. La destilación (`tools/dataset/distill_building_loads.py`) existe por eso: transforma entradas medidas **mensuales** en los archivos horarios de CityLearn.

| Fuente | Contenido | Granularidad |
|---|---|---|
| Facturas `B_02.csv` a `B_17.csv` | Energía en punta y fuera de punta, reactiva, factor de carga, total facturado, tarifa | Mensual, 2023-2025 |
| `resultados_preliminares.xlsx` | Energía activa y máxima demanda (kW) | Mensual, desde 2020 en algunos edificios |
| `B_01.csv` | Generado por el proyecto, no medido | — |

El factor de carga y la máxima demanda no se usan hoy para validar las curvas, salvo en `generate_b01_billing.py`.

## Diseño de vehículos y BESS en cada versión

| Versión | Vehículos (cargadores) | BESS | Criterio |
|---|---|---|---|
| `v1` | 1 850 (185) | 11 429 kWh / 2 709 kW | Escenario de adopción masiva (`build_legacy_scenario_charger_config`), marcado en el código como no realista; aceptado sin puertas |
| `v2` | 2 (2) | 0 | Piloto de 2 motos (propietario, 2026-11-01); BESS del modelo de optimización |
| `v3` | 2 (2) | 44 kWh | Igual; el modelo casi no instala baterías con exportación acreditada 1:1 |
| `v4`, `v5` | 2 (2) | 6 796 kWh / 1 359 kW | Regla del propietario (2026-11-02): recortar el 20 % del pico de 18:00 a 23:00 |

El balance con las facturas (`citylearn_balance`) excluye FV, BESS y vehículos. El BESS solo se verifica en recorte de picos, no en conservación de energía.

## Decisiones tomadas el 2026-11-06

- El piloto se ejecutará en Colab A100 cuando llegue el módulo 8.
- MASAC se reformula antes de entrenar (D05). **Sustituida por D-M3-1:** MASAC conserva su capacidad nativa, sin reformular el búfer. Reducir solo el búfer no basta: el búfer muestrea con reemplazo (`external/MARL/src/common/replay_buffer.py:58`), así que el crítico se actualiza sobre 32 episodios aunque el búfer guarde menos, y eso fija la VRAM.
