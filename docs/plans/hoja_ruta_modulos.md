# Hoja de ruta por módulos hasta el entrenamiento

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Revisión:** 2026-11-06 · **Fuente de pendientes:** [STATUS](../../specs/STATUS.md) y [remediación integrada](remediacion_integrada.md)

## Regla del propietario (2026-11-06)

Los módulos se implementan y cierran uno por uno. **No se entrena hasta que el proyecto esté completo**: todos los specs sin pendientes y la arquitectura terminada. La autorización de `pilot` dada ese día queda aplazada hasta el módulo final; `authorized_stages` sigue vacío.

Un módulo se cierra con spec, pruebas en rojo y luego en verde, puerta `-Scope Repository` aprobada sobre su commit, CI en verde, registros actualizados y publicación.

## Módulos

| Módulo | Alcance | Specs y tareas | Estado |
|---|---|---|---|
| 1. Tarifas oficiales | PDF PBA, contraste, factura con cargo por potencia | SPEC-013 | Cerrado |
| 2. Dataset físico y reconexión | `iquitos_v5`, FV/carga, integridad, S9 | SPEC-014 | Cerrado |
| 3. Contrato de algoritmos y recursos | Capacidad de MASAC con las dimensiones de `iquitos_v5` y reformulación de su búfer (D05); requisitos derivados del contrato y no fijos; conformidad de `NativeBackend` y cancelación de hijos; `save_training_state` en los 4 lanzadores; descomposición de la recompensa en los registros | SPEC-002, SPEC-003, SPEC-004, D03, D05 | En curso |
| 3b. Realismo del dataset con datos reales | **Carga base en todos los edificios (propietario, 2026-11-06):** todos tienen iluminación, tomacorrientes y consumo básico, así que la carga base nunca es 0. Su cantidad sale de las facturas reales (parte que no depende de la temperatura); su forma, de horarios de funcionamiento con fuente: los 11 horarios de `configs/dataset/building_types.yaml` son `assumption` y se sustituyen por los de los edificios de referencia del DOE y ASHRAE 90.1 para cada tipo, ajustados a las horas reales de cada edificio. Puerta: carga base mayor que 0 en todas las horas de los 17 edificios. **FV:** los perfiles de pvlib (`ModelChain` SAPM, NASA POWER observado) están en `solar_generation`; producción 2023 de 1 267 a 1 405 kWh/kWp, el 63 % entre 10:00 y 14:00. **Cargadores de vehículos (propietario, 2026-11-06), sustituye el piloto de 2 motos solo en B01:** según el tipo de edificio, el área y las plazas de estacionamiento y los vehículos estacionados, con más cargadores en edificios grandes, comerciales y de oficinas de mucha afluencia. Plazas = `Area_Estacionamiento_m2` ÷ superficie por plaza del tipo de vehículo predominante (cifra a verificar en el Reglamento Nacional de Edificaciones); cargadores = 1 por cada 10 plazas (EPBD 2024, art. 14, edificios no residenciales existentes con más de 20 plazas); vehículos eléctricos = 5 % de los vehículos estacionados (meta MINEM 2030). Perú: el D.S. 036-2023-EM regula la carga privada pero no fija un mínimo por plaza. Es un escenario a 2030 con respaldo oficial, no la situación actual. La afluencia por edificio de `dimension_ev_chargers.py` no tiene fuente y no se usa sin confirmación. **Controlables por edificio (propietario, 2026-11-06):** aire acondicionado, cargadores de vehículos y BESS; la máquina desplazable deja de ser acción y su energía queda en la carga base. **Balance de `iquitos_v5`, sin control, 2023:** refrigeración + carga base + agua caliente + máquina suman la factura en los 17 edificios (1,0000), pero la carga base es 0 en 10 de ellos (B03, B04, B05, B09, B11, B12, B13, B14, B16 y B17), así que el 73 % controlable del distrito está inflado. Los cargadores de B01 quedan fuera de la factura (demanda nueva del piloto) y el BESS no suma, porque desplaza energía. `v6` debe cumplir por edificio: suma igual a la factura, carga base mayor que 0 salvo que las facturas digan lo contrario, y reparto obtenido de los datos reales. **Reparto refrigeración y carga base (D3-006, confirmado el 2026-11-06):** en `iquitos_v5` la carga no desplazable es 0 todo el año en B03, B04, B09, B14 y B17, y casi 0 en B13, porque la destilación prioriza la refrigeración del modelo físico y deja la carga base como residuo de la factura. En `v6` el reparto se estima con las facturas reales: regresión con punto de cambio del consumo mensual frente a la temperatura (ASHRAE Guideline 14, PRISM), que separa la parte que depende del clima de la carga base. **Control de la refrigeración (propietario, 2026-11-06):** cada edificio controla su refrigeración dentro de un límite de confort, con valor tomado de una norma de confort térmico para clima cálido y húmedo, que se propone al propietario; requiere validar la dinámica térmica de cada edificio y va después de corregir el reparto. **D04 (propietario, 2026-11-06), recompensa con la factura:** el costo de cada hora es su energía más el aumento del cargo por potencia cuando supera el pico que el mes llevaba en el bloque de 18:00 a 23:00 (`P·precio + tarifa_potencia × max(0, P − pico_del_mes)`); sumado en el mes da la factura sin cargo fijo. La tarifa de potencia entra al dataset (`iquitos_v6`), porque la recompensa no lee archivos del proyecto. No se reutiliza el costo del dataset anterior: repartía todo lo facturado como precio por kWh (0,38 a 1,07 USD/kWh) y CityLearn le añadía una forma diaria senoidal inventada (`scenario_manager.py:336-340`). **Contraste de picos (D3-008):** comparar, por edificio y mes, el pico de la curva generada con el pico medido que dan el factor de carga de las facturas (`energía / (horas × factor de carga)`) y la máxima demanda de `resultados_preliminares.xlsx`; si la desviación es grande, destilar para reproducir energía y pico medidos a la vez. **Vehículos:** corregir 230 V a 220 V, la tensión nominal de baja tensión en Perú; declarar que su energía se suma a la factura de B01 como demanda nueva del piloto; verificar la energía de las sesiones frente a km/día × kWh/km. **BESS:** puerta de conservación de energía anual (carga × eficiencia − descarga − variación del estado de carga); tomar eficiencia, profundidad de descarga, pérdidas y curvas de un modelo del catálogo de baterías comerciales que trae CityLearn (`Battery.autosize`, `sizing_data`) en lugar de los puntos medios; el 20 % de recorte sigue como regla del propietario y se declara conservador frente a CityLearn, que dimensiona para 1,5 a 3,5 h de demanda. **FV:** citar en SPEC-014 que el límite FV/carga ≤ 1,0 coincide con `PV.autosize` de CityLearn (fracción de energía neta cero entre 0,7 y 1,0). Todo con los datos reales que ya existen; los supuestos que solo puede confirmar el propietario se le piden con recomendación | SPEC-014 (D3-008), `configs/dataset/ev_pilot.yaml`, `configs/dataset/bess_design_rule.yaml` | Pendiente, tras el módulo 3 |
| 4. Estadística y selección | IQM con 3 semillas, `decide_oe_winner` sin Kruskal-Wallis, `select_best_model` sin significancia ni estado de corridas; verdad estadística única | SPEC-005 (defectos), SPEC-009 (documental) | Pendiente |
| 5. Flujo y herramientas | Subcomandos por etapa en la CLI; 30 herramientas obsoletas; 16 que requieren decisión del propietario | SPEC-011 | Pendiente |
| 6. Artefactos e higiene | Reglas de `.gitignore` de FR-008.4; ramas `codex/*`/`cursor/*`, duplicados y prueba de higiene integral | SPEC-008, SPEC-012 | Pendiente |
| 7. Agentes, skills y licencias | Invocación real, eficiencia, migración de 4 skills, hook heredado; pedidos de licencia | SPEC-007, SPEC-001 | Pendiente |
| 8. Entrenamiento y evaluación | Piloto, HPO, confirmación y sensibilidad en Colab; entrenar sin B01; D04; prueba real de Colab y copia fuera de la máquina; observaciones experimentales del jurado; tesis (SPEC-006) | SPEC-005, SPEC-006, SPEC-008, SPEC-009, SPEC-013, SPEC-014 | Último |

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
| D04, recompensar la factura | 3 | **Cambiada el 2026-11-06:** el eje de costo de la recompensa usa la factura con cargo por potencia, porque sin él costo y CO2 horarios tienen correlación 1,000 y E2 y E3 no se separan |
| Supuestos económicos sin fuente (CAPEX FV, tasa de descuento) | 8 | Verificar con IRENA y la tasa social del MEF antes de la tesis final |
| Retirar `iquitos_v1` (D01) | 8 | Conservarlo hasta tener el piloto |
| 16 herramientas que requieren decisión | 5 | Se proponen una por una en el módulo 5 |
| Publicar los pedidos de licencia | 7 | Publicarlos; no inventar licencias |

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
- MASAC se reformula antes de entrenar (D05). Reducir solo el búfer no basta: el búfer muestrea con reemplazo (`external/MARL/src/common/replay_buffer.py:58`), así que el crítico se actualiza sobre 32 episodios aunque el búfer guarde menos, y eso fija la VRAM.
