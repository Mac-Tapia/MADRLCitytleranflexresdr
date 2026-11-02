# Contribuciones locales a CityLearn

## Persistencia, reanudación y catálogo explícito — continuación

Las fachadas write_json/write_csv y append estable delegan en
uc3m.application.training.persistence. JSON/CSV completos se reemplazan
atómicamente; append rechaza columnas inesperadas y encabezados distintos.

Se corrigió un defecto observado por pruebas existentes: preload conservaba
el contador de filas escritas pero vaciaba el búfer, omitiendo nuevos episodios.
Ahora ambos conservan el mismo prefijo. Coste explícito: memoria histórica
proporcional a las filas. No se proclama una optimización de streaming.

ScenarioManager aplica el catálogo solo mediante UC3M_SCENARIO_CATALOG;
los lanzadores históricos no cambian su tarifa por defecto. Los tratamientos
no soportados de recompensa/restricción se rechazan. Se conserva el criterio
de no aceptar corridas sin KPI ni con etiqueta de escenario incompatible.

Pruebas antiguas que exigían omitir corridas sin KPI se actualizaron al criterio
estricto del SPEC aprobado; no se debilitó producción para satisfacerlas.
El fixture canónico HAPPO actual contiene 50 episodios y KPI auditados, por lo
que su expectativa se actualizó. La prueba de etiquetas erróneas ahora crea
su propio archivo determinista, en vez de omitir la prueba cuando no hay errores.

## 2026-10-31 — Extracción modular de rutas de entrenamiento

Autorización: el usuario pidió realizar los pendientes en su proyecto y aclaró
expresamente que incluye los proyectos derivados open source. Esta autorización
levanta la restricción previa de modificación local de CityLearn y external;
no sustituye las licencias de autores de terceros ni autoriza publicación remota.

Cambio: `CityLearn/scripts/citylearn_v3_training_common.py` reexporta las cinco
funciones de layout desde `uc3m/application/training/layout.py`. Se conserva
`HAPPO/E1` para semilla cero y `HAPPO/E1_s7` para semilla siete, las carpetas de
artefactos y las funciones legacy de descubrimiento/reanudación. No se movieron
datasets, checkpoints ni resultados. Se preservaron los demás cambios locales.

Pruebas: `tests/unit/application/training/test_layout.py` pasó de tres fallos
por módulo inexistente a tres aprobadas. La prueba existente
`CityLearn/tests/test_internal_refactor_parity.py` aprobó sus dos casos.

La extracción hace que los scripts CityLearn requieran la carpeta padre UC3M
para estas funciones; el lanzador agrega PROJECT_ROOT antes de importarlas.
El repositorio derivado debe distribuirse junto al superproyecto o con UC3M
instalado; ya no es autónomo para estos lanzadores.

## Sustento científico (APA)

Charbonnier, F. (2023). *Multi-agent reinforcement learning for the coordination
of residential energy flexibility* [Tesis doctoral, University of Oxford].
https://doi.org/10.5287/ora-ovzyxredj

Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy
Optimization: Taxonomy and Experimental Evaluation in CityLearn* [Tesis de
maestría, Politecnico di Torino]. https://webthesis.biblio.polito.it/40396/

Charbonnier, F., Morstyn, T., & McCulloch, M. (2022). Scalable multi-agent
reinforcement learning for distributed control of residential energy flexibility.
*Applied Energy*. Registro institucional y manuscrito:
https://ora.ox.ac.uk/objects/uuid:e5bfd168-d8ca-4462-a0a3-6ccd1f97376c

Estos trabajos sustentan comparación experimental y evaluación de coordinación
energética. La extracción de módulos es una decisión de ingeniería para mantener
esa reproducibilidad; no se atribuye a estas fuentes una arquitectura Python
específica ni validación del código local.

## Hallazgo de procedencia

HARL declara MIT en su `setup.py` local y en
https://github.com/PKU-MARL/HARL/blob/main/setup.py . La auditoría conservadora
anterior solo inspecciona LICENSE/LICENCE/COPYING de raíz. La declaración es
evidencia adicional, no un texto de licencia recuperado ni una resolución de
las otras dependencias. No se ha añadido una licencia ajena por conjetura.

## 2026-11-01 — Deriva SOC de EV no conectados: índice por vehículo

Archivo: `citylearn/internal/runtime.py`, `CityLearnRuntimeService.simulate_unconnected_ev_soc`.
El método recorría, en cada paso, todos los cargadores para cada vehículo (1 850 EV × 185 tomas
en la campaña Iquitos v1). Según un perfil cProfile de un microentrenamiento MATD3, esto consumía
el 91 % del tiempo, unos 18 s por paso, y afectaba por igual a los cuatro backends. Ahora los
cargadores se indexan una vez por paso por el id de vehículo actual o siguiente, en el orden
original de edificio y cargador. Solo esos cargadores pueden actuar sobre un vehículo, así que el
resultado, incluidas las extracciones del generador aleatorio, no cambia.
Verificación: `tests/fresh_training/test_ev_drift_speed.py` compara con una copia literal del
bucle original. SOC de los 1 850 EV, potencia neta por edificio y recompensas son idénticos en
4 pasos, y la versión nueva es más de 5 veces más rápida.
Autorización: el usuario pidió continuar con todo lo necesario para el entrenamiento nuevo; el
fork es propio (preferencia registrada del usuario).

## 2026-11-01 — Recompensa v3: auditoría, módulo propio y facturación neta

Autorización del propietario (2026-11-01): modificar la recompensa del fork, trasladarla a
CityLearn v3 («haslo traslada») y no desperdiciar excedente FV («si existe exceso de
generación se debe almacenar en BESS o suministrar a la red pública … nada se debe
desperdiciar», opción «Crédito a precio de compra»; los tres ejes deben reflejarlo).

- Módulo: `CityLearnV3MADRLRewardFunction`, `scenario_catalog_axis_weights` y las tablas v3
  se trasladaron de `citylearn/reward_function.py` a `citylearn/v3/reward.py`. En el módulo
  antiguo queda solo un alias perezoso (PEP 562) al mismo objeto: la ruta
  `citylearn.reward_function.CityLearnV3MADRLRewardFunction` y los checkpoints siguen
  resolviendo, sin segunda implementación. Ruta canónica en `citylearn/v3/config.py`,
  `citylearn/v3/environment.py` y en la etiqueta de los cuatro `train_citylearn_v3_*.py`.
  Las recompensas base (MARL, SolarPenaltyReward, …) no cambian.
- Pesos: la recompensa lee `axis_weights` del catálogo `UC3M_SCENARIO_CATALOG`
  (`configs/objective_policies.yaml` o un catálogo derivado de sensibilidad con hash); la
  tabla embebida queda como respaldo heredado. `scenario_manager.py` dejó de rechazar
  políticas derivadas (validadas por el cargador).
- Perfil `fresh_kpi_aligned_v6_net_billing` (v5 + facturación neta):
  - sin mezcla 0,70/0,30 interna (no tenía efecto bajo `team_mean`); pago común por
    `CityLearnDecPOMDPEnv.reward_aggregation="team_mean"`; `team_reward_ratio` es error;
  - flexibilidad sobre la potencia neta distrital bidireccional: pico cuadrático de |P|
    (un pico de inyección penaliza como uno de importación) y rampa lineal de |ΔP|;
  - costo = consumo neto × precio (exportación acreditada al precio de compra);
    CO2 = consumo neto × intensidad (la inyección desplaza generación térmica);
    términos con signo acotados simétricamente en ±`term_bound`, saturación registrada;
  - EV (déficit de servicio y violación de carga) y ciclado BESS solo como penalizaciones
    fuera del vector ponderado; no se usan los incentivos energéticos EV de la base;
  - desglose por término `raw_*`, `norm_*`, `bounded_*`, `sat_*`, `weighted_*`, `local_reward`.
  Guardar o exportar lo decide el compromiso ponderado E1/E2/E3, sin reglas fijas.
- Evaluación alineada (`uc3m/application/evaluation/kpi_contract.py`,
  `configs/evaluation/kpis.yaml`): costo y CO2 netos; pico diario de |P|, rampa |ΔP| y
  1 − media|P|/max|P|. El factor de carga no tiene término por paso en la recompensa; en
  una traza de almacenamiento que lleva la potencia a cero empeora aunque pico, rampa,
  costo y CO2 mejoren (prueba `test_store_versus_export_moves_the_three_axes_consistently`).
- Núcleo CityLearn sin cambios: `Building.net_electricity_consumption_cost` ya es neto
  (consumo neto × precio, puede ser negativo), mientras que
  `net_electricity_consumption_emission` se recorta en 0 (`max(0, net × intensidad)`,
  `building.py` ~2517-2520). Los KPI nativos `evaluate_v2` de emisiones siguen esa
  convención sin crédito; la evaluación nueva usa la traza física, no esos agregados.

Pruebas: `tests/uc3m/test_reward_net_billing.py`, `tests/uc3m/test_reward_kpi_alignment.py`,
`tests/uc3m/test_reward_term_telemetry.py`, `CityLearn/tests/test_citylearn_v3_reward_hierarchy.py`,
`tests/fresh_training/test_kpi_physical_contract.py`.

## 2026-11-01 — MASAC con capacidad nativa, sin recortes silenciosos

Instrucción del propietario: «los MADRL entrenan a su máxima potencia y su naturaleza sin
restricciones … entrenamiento largo colab pro con los recursos ya definidos en el notebook».

`scripts/train_citylearn_v3_masac.py`:
- se eliminaron los recortes aplicados cuando `episode_limit >= 1000` (`critic_batch_size → 1`,
  `critic_train_steps → 1`, anchos `rnn/qmix/hyper → 64/32/64`) y el bucle que reducía
  `buffer_size` hasta caber bajo `--max-replay-buffer-gib`;
- `resolve_masac_capacity` (función pura): valores del autor (`external/MARL/src/common/arguments.py`:
  lote del crítico 32 episodios, 1 paso de crítico, réplica 5000 episodios) salvo lo que fija la
  campaña; `qmix = rnn/2` y `hyper = rnn` (razón del autor 64/32/64) si no se pasan; la réplica
  nunca guarda más episodios que la corrida (cota sin pérdida, registrada en `capacity_notes`);
- `estimate_masac_critic_gpu_gib` (estimación conservadora float32 de una actualización QMIX sobre
  B×T) y `check_masac_capacity`: si la RAM disponible medida (psutil) o la VRAM libre
  (`torch.cuda.mem_get_info`) no alcanzan, `MemoryError insufficient_resources:MASAC:<ram|vram>`
  con los números; nada se encoge. Defaults del CLI: `--buffer-size 5000`, `--critic-batch-size 32`,
  `--qmix/--hyper-hidden-dim` derivados, `--max-replay-buffer-gib` = RAM medida.
- Nota: con `two_hyper_layers=False` (autor) `hyper_hidden_dim` no interviene en `QMixNet`.

Pruebas: `tests/fresh_training/test_native_capacity.py`.

## 2026-11-01 — Emisiones netas, recompensa v7 por indicadores de la tesis

- `citylearn/building.py`: `net_electricity_consumption_emission` deja de recortarse en cero
  (`max(0, net × intensidad)` → `net × intensidad`), igual en las variantes `_without_storage` y
  `_without_storage_and_pv` de `Building` (decisión del propietario: la inyección FV desplaza
  generación térmica, ξ^disp = ξ). Prueba: `tests/fresh_training/test_citylearn_net_emissions.py`
  (simulador real; FV ×50; las horas exportadoras dan emisiones negativas).
  No cambiado y pendiente del propietario: `CostFunction.carbon_emissions` y `CostFunction.cost`
  siguen recortando cada paso en cero dentro de las razones `evaluate_v2`
  (`carbon_emissions_total`, `cost_total`), los `DynamicsBuilding` `_partial_load` conservan su
  `.clip(min=0)`, y el schema `iquitos_v1` liquida el costo por el mercado comunitario
  (`community_market.enabled = true`, comercio local a 0,8 × precio, `grid_export_price = 0.0`),
  así que el costo de CityLearn no es facturación neta aunque el término de recompensa sí lo sea.
- `citylearn/v3/reward.py`, perfil `thesis_indicators_v7`: un término denso por indicador de la
  tesis (Tabla 2.1; cap2 §2.2.8), `CITYLEARN_V3_REWARD_TERMS` con eje, indicador, fuente y estado:
  flex = incremento diario exacto de max|P| (peak_average), rampa cuadrática (β1·ΔP²,
  ramping_average), incremento diario exacto de 1 − media|P|/max|P|
  (one_minus_load_factor_average), exceso sobre P_lim_DSO (pendiente, peso 0); CO2 = neto,
  delta frente a la línea base por paso (net − consumo de almacenamiento y cargadores EV, la
  condición WITHOUT_STORAGE_BUT_WITH_PV de evaluate_v2; verificado igual a
  `net_electricity_consumption_without_storage`) y consumo ponderado por CI (solo importación);
  costo = neto y delta; pico facturable y price_signal_deviation pendientes (peso 0). Subpesos
  internos declarados en el perfil, suman 1 por eje, iguales para los 4 MADRL y E1/E2/E3.

Pruebas: `tests/fresh_training/test_kpi_catalog_complete.py`, `tests/uc3m/test_reward_*`.

## 2026-11-01 — CostFunction sin recorte en pasos exportadores («Sí, quitarlo»)

- `citylearn/cost_function.py`: `CostFunction.carbon_emissions` y `CostFunction.cost` ya no
  aplican `.clip(min=0)` por paso; un paso exportador acredita −export × precio y
  −export × intensidad, de modo que las razones de `evaluate_v2` (`carbon_emissions_total`,
  `cost_total`) y los 26 KPI comparables de CityLearn v3 siguen la facturación neta.
- `citylearn/building.py` (`DynamicsBuilding`): las emisiones de línea base
  `_without_storage_and_partial_load[_and_pv]` también dejan de recortarse. Motivo: son la línea
  base de `evaluate_v2` para edificios dinámicos (`WITHOUT_STORAGE_AND_PARTIAL_LOAD_BUT_WITH_PV`);
  si el control acredita la exportación y la línea base no, el delta y la razón quedan sesgados.
  En iquitos_v1 los edificios son `Building`, por lo que no cambia sus valores, solo la coherencia.
- `tests/test_kpi_v2.py`: la expectativa heredada `cost_total = 0.5` («clipped CostFunction.cost
  semantics») pasa a `−0.5` = (−2 + 1)/(1 + 1): es la consecuencia directa y buscada del cambio.
- Pruebas: `tests/fresh_training/test_citylearn_net_cost_function.py` (RED observado: 2 fallos),
  `CityLearn/tests/test_kpi_v2.py`, `test_building_objective_kpis.py`, `test_kpis.py` en verde.
- Advertencia: con facturación neta el baseline de costo o CO2 puede ser ≤ 0 en distritos
  exportadores; las razones `control/baseline` cambian de signo o quedan indefinidas y la
  ganancia orientada usa |baseline| (`objective_kpi_rows`).
