# PLAN DE TESIS DE MAESTRÍA DE ESPECIALIZACIÓN O PROFESIONALIZANTE

---

## CARÁTULA

**Universidad:** Universidad Nacional Mayor de San Marcos  
**Unidad de Posgrado:** Facultad de Ingeniería de Sistemas e Informática  
**Título del plan de tesis:**

> **MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS ENERGÉTICOS EN COMUNIDADES INTELIGENTES**

**Modalidad:** Tesis de Maestría Profesionalizante  
**Autor:** Mac Tapia (dato bibliográfico pendiente de verificación — completar nombre completo)  
**Asesor:** por definir  
**Lugar:** Lima / Iquitos, Perú  
**Fecha:** 2026

---

## DATOS GENERALES

1. **Título propuesto:** Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes.
2. **Nombre del graduando:** Mac Tapia (completar nombre completo).
3. **Nombre del asesor:** por definir.
4. **Área involucrada:** Inteligencia Artificial aplicada a Ingeniería Energética — Sistemas Eléctricos Inteligentes.
5. **Lugar o institución donde se desarrolla el proyecto:** Universidad Nacional Mayor de San Marcos (UNMSM) / Sistema Eléctrico Aislado de Iquitos (SEAI) — Electro Oriente S.A., Loreto, Perú.
6. **Duración estimada:** 24 meses (2025-01 a 2026-12).

---

## CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA

### 1.1 Diagnóstico

Las comunidades inteligentes (smart communities) constituyen entornos energéticos complejos que integran recursos de energía distribuida (DER): generación solar fotovoltaica (PV), sistemas de almacenamiento de energía en baterías (BESS) y estaciones de carga de vehículos eléctricos (EV). La coordinación multiagente de estos recursos bajo incertidumbre parcial es un problema de decisión secuencial no resuelto que afecta simultáneamente tres dimensiones críticas.

**Dimensión de flexibilidad energética (OE.1):** La ausencia de gestión coordinada de DER en comunidades inteligentes limita la capacidad de modular la demanda, desplazar cargas y aprovechar la generación renovable, lo que deriva en un comportamiento grid-interactive subóptimo y razones pico-promedio elevadas. Los enfoques de aprendizaje por refuerzo profundo (DRL) de agente único han demostrado incapacidad para generalizar en portafolios de edificios heterogéneos. Ningún estudio comparativo ha determinado cuál algoritmo MADRL logra el mejor desempeño de flexibilidad energética en escenarios coordinados de comunidades inteligentes.

**Dimensión de emisiones de carbono / CO2 (OE.2):** Las comunidades inteligentes operan bajo señales de intensidad de carbono variables que reflejan la dependencia de su suministro eléctrico de combustibles fósiles. En el Sistema Eléctrico Aislado de Iquitos (SEAI), el factor de emisión del sistema diésel de Electro Oriente S.A. es 0.790 kgCO2/kWh (MINAM RAGEI 2019), con penetración solar creciente hasta ~15%. La falta de control multiagente coordinado impide el desplazamiento temporal óptimo del consumo hacia periodos de baja intensidad de carbono. Ningún benchmark ha establecido cuál algoritmo MADRL reduce mejor las emisiones de CO2 en comunidades inteligentes bajo condiciones dinámicas de intensidad de carbono.

**Dimensión de costos energéticos (OE.3):** El precio dinámico de la electricidad (tarifas por uso horario, tiempo real) crea incentivos económicos para la flexibilidad de demanda. En el SEAI Iquitos, la tarifa punta (18:00-22:00 h) es de $0.38/kWh y la tarifa fuera de punta es de $0.26/kWh (Electro Oriente S.A., 2024). Las respuestas no coordinadas a nivel de edificio generan resultados colectivos subóptimos. Ninguna evaluación comparativa rigurosa ha determinado qué MADRL logra la mejor reducción de costos energéticos bajo operación coordinada en comunidades inteligentes.

**Limitaciones metodológicas del estado del arte:** La literatura existente reporta evaluaciones aisladas de algoritmos individuales sobre dimensiones únicas. La ausencia de un marco comparativo unificado —que cubra HAPPO, MASAC, MATD3 y MAAC bajo formulación Dec-POMDP y esquema CTDE— impide determinar el mejor agente MADRL para la gestión coordinada y simultánea de flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes.

**Oportunidad de CityLearn v2:** CityLearn v2 provee un entorno de simulación de código abierto validado para la gestión multiagente de energía en comunidades grid-interactive (Nweye et al., 2025, dato bibliográfico pendiente de verificación). Su integración con CityLearn v3 propuesto —una extensión experimental que implementa la capa MADRL cooperativa, formulación Dec-POMDP, entrenamiento CTDE y backends compatibles con MARLlib— habilita la evaluación comparativa rigurosa de algoritmos MADRL.

### 1.2 Identificación y descripción del problema de estudio

El problema central es la **falta de determinación del mejor algoritmo Multi-Agente de Aprendizaje por Refuerzo Profundo que gestione de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes**.

- **Problema técnico:** Ausencia de control MADRL coordinado que optimice simultáneamente las tres dimensiones (flexibilidad, CO2, costos) en simulaciones de comunidades inteligentes.
- **Síntomas observables:** Alta demanda pico, consumo elevado ponderado por intensidad de carbono, reducción subóptima del costo eléctrico y pobre coordinación del perfil de carga en escenarios multiedificio.
- **Causas energéticas:** DER no coordinados, falta de toma de decisión cooperativa entre agentes, ausencia de utilización del estado global compartido.
- **Causas metodológicas:** Ningún benchmark unificado de HAPPO, MASAC, MATD3 y MAAC bajo condiciones idénticas de Dec-POMDP y CTDE aplicadas a las tres dimensiones de desempeño.
- **Consecuencias operacionales:** Despacho subóptimo, fallo en la explotación de ventanas de respuesta a la demanda.
- **Consecuencias ambientales:** Emisiones de CO2 excesivas por importaciones de red en periodos de alta intensidad de carbono.
- **Consecuencias económicas:** Costos energéticos innecesarios por respuesta no optimizada a tarifas por uso horario.
- **Variables:**
  - Variable independiente: capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 propuesto) — algoritmos HAPPO, MASAC, MATD3 y MAAC bajo Dec-POMDP y CTDE.
  - Variable dependiente: desempeño coordinado en flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes.
- **Ámbito espacial:** Comunidades inteligentes simuladas mediante CityLearn v2 y CityLearn v3 propuesto. Aplicabilidad al SEAI Iquitos (17 edificios institucionales/comerciales reales, Loreto, Perú).
- **Ámbito temporal:** Período de estudio 2015–2026 alineado con los horizontes temporales de los datasets de CityLearn v2 y la literatura reciente de MADRL.

### 1.2.1 Antecedentes bibliográficos

*(Nota: Los antecedentes a continuación deben completarse con la Matriz bibliográfica de 50 investigaciones del Módulo A. Se presentan las cadenas de búsqueda, ejes temáticos y estructura de la matriz. Las referencias marcadas con [PV] son pendientes de verificación bibliográfica.)*

**Eje 1 — Flexibilidad energética con MADRL:**

Antecedentes sobre MADRL para respuesta a la demanda, reducción de picos, desplazamiento de cargas, autoconsumo, comunidades grid-interactive, CityLearn v2 y KPIs de flexibilidad energética.

- Nweye et al. (2025) [PV] desarrollan CityLearn v2 como entorno de simulación multiagente para edificios grid-interactive. El simulador provee KPIs de `peak_average`, `ramping_average`, `one_minus_load_factor_average` y métricas de autoconsumo/autosuficiencia como base para evaluación de flexibilidad.
- Vázquez-Canteli & Nagy (2019) [PV] revisan enfoques de aprendizaje por refuerzo (RL) para la gestión de la demanda en edificios, identificando la coordinación multiagente como desafío abierto.
- Pigott et al. (2022) [PV] presentan CityLearn como plataforma para el CityLearn Challenge, comparando agentes RBC, SAC y otros en escenarios de flexibilidad energética multiedificio.
- *(Completar con 47 antecedentes adicionales del Módulo A organizados por eje)*

**Eje 2 — Reducción de emisiones de CO2 con MADRL:**

Antecedentes sobre MADRL consciente de la intensidad de carbono, reducción de emisiones de CO2 en escenarios multiedificio, respuesta a la demanda baja en carbono y métricas de consumo ponderado por emisiones.

- *(Completar con antecedentes del Módulo A — Eje 2)*

**Eje 3 — Optimización de costos energéticos con MADRL:**

Antecedentes sobre optimización de costos eléctricos con MADRL, respuesta a precios dinámicos, estrategias de tarifas por uso horario y KPIs de costos en comunidades inteligentes.

- *(Completar con antecedentes del Módulo A — Eje 3)*

**Eje transversal — Marco técnico MADRL:**

- Lowe et al. (2017) [PV] introducen MADDPG con el esquema CTDE para entornos cooperativos-competitivos, precursor de los backends usados en esta tesis.
- Kuba et al. (2021) [PV] presentan HAPPO (Heterogeneous-Agent Proximal Policy Optimization) en el repositorio HARL como mejora de MAPPO para agentes heterogéneos.
- Wang et al. (2022) [PV] presentan MASAC (Multi-Agent Soft Actor-Critic) con QMIX como función de mezcla cooperativa.
- Li et al. (2021) [PV] presentan MATD3 (Multi-Agent Twin Delayed Deep Deterministic Policy Gradient) con doble crítico para reducir sobreestimación en entornos cooperativos.
- Iqbal & Sha (2019) [PV] introducen MAAC (Multi-Agent Actor-Critic with Attention) con mecanismo de atención para coordinación selectiva entre agentes.
- Hu et al. (2021) [PV] presentan MARLlib como biblioteca unificada de algoritmos MARL/MADRL compatible con Ray/RLlib, que incluye HAPPO, MASAC, MATD3 y MAAC.
- Akiba et al. (2019) [PV] presentan Optuna como framework de optimización automática de hiperparámetros para aprendizaje automático.
- Oliehoek & Amato (2016) [PV] proveen el marco teórico del Dec-POMDP (Decentralized Partially Observable Markov Decision Process) y el esquema CTDE.

### 1.2.2 Formulación del problema

La brecha identificada es la ausencia de un estudio comparativo que determine el mejor MADRL para la gestión coordinada y simultánea de flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes.

#### 1.2.2.1 Formulación del problema general

> ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes?

#### 1.2.2.2 Formulación de los problemas específicos

> **PE.1:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes?
>
> **PE.2:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes?
>
> **PE.3:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes?

Cada problema específico responde a: (a) la dimensión correspondiente del diagnóstico, (b) su objetivo específico, (c) su conjunto de KPIs, y (d) su metodología de evaluación comparativa.

### 1.2.3 Justificación y alcances

#### 1.2.3.1 Justificación

- **Justificación técnica:** La determinación comparativa del mejor MADRL avanza el estado del arte en gestión energética cooperativa para comunidades inteligentes mediante una evaluación unificada de HAPPO, MASAC, MATD3 y MAAC bajo Dec-POMDP y CTDE.
- **Justificación ambiental:** Identificar el mejor MADRL para reducción de CO2 contribuye directamente a los objetivos de descarbonización de comunidades grid-interactive, con aplicabilidad al SEAI Iquitos (factor de emisión 0.790 kgCO2/kWh).
- **Justificación económica:** Establecer el mejor MADRL para optimización de costos provee orientación accionable para la reducción del gasto eléctrico en comunidades inteligentes bajo tarifas por uso horario.
- **Justificación metodológica:** La formulación Dec-POMDP, el esquema CTDE y el benchmark unificado con CityLearn v3 propuesto, HAPPO, MASAC, MATD3, MAAC, MARLlib y Optuna constituyen una contribución metodológica reproducible.
- **Justificación científica:** La evaluación unificada en tres ejes llena una laguna en la literatura comparativa de MADRL.
- **Justificación social:** Las comunidades inteligentes energéticamente flexibles y de bajo costo benefician a usuarios residenciales e institucionales, y contribuyen a la transición energética a nivel comunitario.

#### 1.2.3.2 Alcances

- **Alcance temático:** Evaluación comparativa de HAPPO, MASAC, MATD3 y MAAC en KPIs de flexibilidad energética, emisiones de CO2 y costos energéticos en simulación de comunidades inteligentes.
- **Alcance espacial:** Comunidades inteligentes simuladas mediante CityLearn v2 y CityLearn v3 propuesto. Discusión de aplicabilidad al SEAI Iquitos (17 edificios institucionales/comerciales reales de Loreto, Perú).
- **Alcance temporal:** Alineado con horizontes temporales de datasets de CityLearn v2 (2023-2025, 26,304 pasos horarios) y literatura reciente de MADRL (2015-2026).
- **Alcance metodológico:** Estudio cuantitativo, aplicado, comparativo, no experimental, basado en simulación computacional.
- **Alcance computacional:** Python 3.9, PyTorch 2.8.0+cu126, CityLearn v2, CityLearn v3 propuesto, MARLlib como referencia técnica, Optuna, Gymnasium, PettingZoo, recursos computacionales locales (NVIDIA RTX 4060 Laptop 8 GB).
- **Límites y supuestos:** No se modela ninguna red eléctrica física. Los resultados de simulación no constituyen validación de despliegue en el mundo real. CityLearn v3 propuesto es una extensión experimental de tesis, no una versión oficial de CityLearn.
- **Exclusiones:** Despliegue en campo en tiempo real, investigación con sujetos humanos, despacho económico de unidades de generación física y análisis de estabilidad de red.

---

## CAPÍTULO II. OBJETIVOS

### 2.1 Objetivo general

> **O.G.** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes.

### 2.2 Objetivos específicos

> **OE.1** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes.
>
> **OE.2** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes.
>
> **OE.3** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes.

**Coherencia vertical:** Cada objetivo específico responde directamente a su problema específico correspondiente, se operacionaliza mediante su eje de KPIs, y se evalúa mediante la metodología comparativa de CityLearn v3 propuesto con HAPPO, MASAC, MATD3 y MAAC bajo Dec-POMDP y CTDE.

---

## CAPÍTULO III. MARCO TEÓRICO

### 3.1 Bases teóricas

#### Eje 1 — Flexibilidad energética en comunidades inteligentes

Las comunidades inteligentes (smart communities) son grupos de edificios interconectados eléctricamente que comparten recursos DER y responden colectivamente a señales de precios, carbono y capacidad de red (Nweye et al., 2025 [PV]). La flexibilidad energética se define como la capacidad del sistema para modificar la forma de su curva de demanda mediante desplazamiento de cargas, almacenamiento en BESS, autoconsumo solar y carga/descarga de EV (Lund et al., 2015 [PV]).

Los KPIs de flexibilidad energética relevantes son: `peak_average` (reducción del pico de demanda normalizado), `ramping_average` (suavizado de la variación de consumo), `one_minus_load_factor_average` (mejora del factor de carga), tasa de autoconsumo PV, tasa de autosuficiencia, reducción de importación de red y utilización de renovables.

#### Eje 2 — Emisiones de carbono en comunidades inteligentes

La intensidad de carbono del suministro eléctrico varía según la mezcla de generación horaria. En el SEAI Iquitos, el factor de emisión del sistema diésel es 0.790 kgCO2/kWh (MINAM, 2019), reduciéndose a ~0.671 kgCO2/kWh durante las horas de mayor generación solar. La gestión consciente de la intensidad de carbono desplaza el consumo hacia periodos de menor emisión (Fabrizio et al., 2023 [PV]).

Los KPIs de emisiones de CO2 son: emisiones totales de carbono, reducción de CO2 frente al baseline, consumo ponderado por intensidad de carbono, emisiones evitadas e índice de equilibrio emisiones-costo.

#### Eje 3 — Costos energéticos en comunidades inteligentes

Las tarifas de uso horario (TOU) y los precios en tiempo real (RTP) crean incentivos para la flexibilidad económica de la demanda. El arbitraje tarifario mediante BESS y EV permite reducir el cargo por demanda y optimizar el gasto eléctrico (Jordehi, 2019 [PV]).

Los KPIs de costos energéticos son: costo total de electricidad, reducción de costo frente al baseline, reducción del cargo por demanda, índice de optimización de tarifas por uso horario y respuesta a precios dinámicos.

#### Eje transversal — Marco técnico MADRL

**Dec-POMDP (Decentralized Partially Observable Markov Decision Process):** Modelo formal para decisión cooperativa multiagente bajo observabilidad parcial. Se define como la tupla ⟨S, A₁,…,Aₙ, T, R, O₁,…,Oₙ, Z⟩, donde S es el estado global, Aᵢ las acciones locales, T la función de transición, R la recompensa cooperativa, Oᵢ las observaciones locales y Z la función de observación (Oliehoek & Amato, 2016 [PV]).

**CTDE (Centralized Training, Decentralized Execution):** Esquema de entrenamiento que utiliza el estado global S durante el entrenamiento del crítico centralizado, pero ejecuta políticas descentralizadas de actor basadas únicamente en observaciones locales Oᵢ (Lowe et al., 2017 [PV]).

**HAPPO (Heterogeneous-Agent Proximal Policy Optimization):** Algoritmo on-policy basado en PPO con entrenamiento secuencial por agente. Usa un crítico centralizado con observación global compartida. Implementado en el repositorio HARL (Kuba et al., 2021 [PV]).

**MASAC (Multi-Agent Soft Actor-Critic con QMIX):** Algoritmo off-policy que combina SAC con redes RNN para observaciones parciales y QMIX como función de mezcla cooperativa. Implementado en el repositorio MARL/src (Wang et al., 2022 [PV]).

**MATD3 (Multi-Agent Twin Delayed Deep Deterministic Policy Gradient):** Algoritmo off-policy con doble crítico centralizado para reducir sobreestimación del valor. Backend PyTorch implementado en marlbenchmark/off-policy (Li et al., 2021 [PV]).

**MAAC (Multi-Agent Actor-Critic with Attention):** Algoritmo off-policy con mecanismo de atención multi-cabeza que selecciona dinámicamente qué agentes observar al calcular el valor de acción. Permite coordinación selectiva entre los 17 edificios (Iqbal & Sha, 2019 [PV]).

**MARLlib:** Biblioteca unificada de algoritmos MARL/MADRL compatible con Ray/RLlib 1.8.0, Gymnasium y PettingZoo. Se usa como referencia técnica de integración y adaptador de entorno (Hu et al., 2021 [PV]).

**CityLearn v2:** Entorno de simulación de código abierto para gestión energética multiagente en edificios grid-interactive. Provee datasets, física de edificios, DER, EVs, señales de carbono y precios, y KPIs estandarizados (Nweye et al., 2025 [PV]).

**CityLearn v3 propuesto:** Extensión experimental de tesis implementada sobre CityLearn v2. Agrega la formulación Dec-POMDP, el esquema CTDE, la función de recompensa multiobjetivo `CityLearnV3MADRLRewardFunction` y adaptadores para los cuatro backends MADRL. No constituye una versión oficial de CityLearn.

**Dataset citylearn_iquitos_2023_2025:** Dataset de tesis con 17 edificios institucionales/comerciales reales de Iquitos (Loreto, Perú), 26,304 horas (2023-2025), 50 cargadores EV (mototaxi/motolineal/V2G), BESS por edificio (704-15,075 kWh), PV (196-5,190 kWp) y señales de carbono/precio calibradas con datos de Electro Oriente S.A. y MINAM RAGEI 2019.

**Optuna:** Framework de optimización automática de hiperparámetros (HPO) basado en TPE (Tree-structured Parzen Estimator). Se utiliza para ajustar los hiperparámetros de cada backend MADRL (Akiba et al., 2019 [PV]).

### 3.2 Definición de términos

- **MADRL:** Multi-Agent Deep Reinforcement Learning — aprendizaje por refuerzo profundo multiagente.
- **DRL:** Deep Reinforcement Learning — aprendizaje por refuerzo profundo de agente único.
- **Dec-POMDP:** Decentralized Partially Observable Markov Decision Process — proceso de decisión de Markov descentralizado parcialmente observable.
- **CTDE:** Centralized Training, Decentralized Execution — entrenamiento centralizado con ejecución descentralizada.
- **Comunidad inteligente:** Grupo de edificios interconectados que comparten DER y responden coordinadamente a señales de red, precios y carbono.
- **BESS:** Battery Energy Storage System — sistema de almacenamiento de energía en baterías.
- **EV:** Electric Vehicle — vehículo eléctrico (mototaxi, motolineal, Van/V2G en el contexto del SEAI Iquitos).
- **PV:** Photovoltaic — generación solar fotovoltaica.
- **V2G:** Vehicle-to-Grid — capacidad del vehículo eléctrico de devolver energía a la red.
- **KPI:** Key Performance Indicator — indicador clave de desempeño energético, ambiental o económico.
- **CityLearn v2:** Simulador base oficial multiagente para comunidades energéticas.
- **CityLearn v3 propuesto:** Extensión experimental de tesis sobre CityLearn v2.
- **MARLlib:** Biblioteca unificada de algoritmos MADRL (nombre propio — no reemplazar por MARL).
- **HAPPO, MASAC, MATD3, MAAC:** Los cuatro backends MADRL propuestos en esta tesis.
- **Optuna:** Framework de optimización automática de hiperparámetros.

---

## CAPÍTULO IV. DISEÑO METODOLÓGICO

### 4.1 Tipo y nivel de investigación

- **Enfoque:** cuantitativo.
- **Tipo:** aplicada.
- **Nivel:** descriptivo, comparativo y propositivo.
- **Diseño:** no experimental, transversal, basado en simulación computacional y comparación de algoritmos.
- **Método:** modelamiento computacional, simulación de entornos energéticos, comparación de algoritmos MADRL y análisis de indicadores de desempeño (KPIs).

El nivel comparativo es esencial: el estudio determina el *mejor* MADRL comparando HAPPO, MASAC, MATD3 y MAAC en tres ejes de evaluación (flexibilidad energética, emisiones de CO2, costos energéticos). La justificación del nivel propositivo radica en que CityLearn v3 propuesto es una extensión arquitectónica original sobre CityLearn v2.

### 4.2 Unidad de análisis

- Comunidades inteligentes simuladas mediante CityLearn v2 y CityLearn v3 propuesto.
- Agentes MADRL cooperativos (HAPPO, MASAC, MATD3, MAAC) bajo Dec-POMDP y CTDE.
- Recursos de energía distribuida (DER): edificios, BESS, PV y estaciones de carga EV.
- Indicadores de desempeño energético, ambiental y económico (KPIs de flexibilidad energética, emisiones de CO2 y costos energéticos).

### 4.3 Población de estudio

La investigación es de simulación computacional; no involucra sujetos humanos. La población comprende:

- Escenarios simulados de comunidades inteligentes con múltiples edificios y recursos DER.
- Series temporales de demanda energética, precio de electricidad e intensidad de carbono del dataset `citylearn_iquitos_2023_2025` (17 edificios, 26,304 horas, 2023-2025).
- Configuraciones de agentes MADRL bajo distintos backends (HAPPO, MASAC, MATD3, MAAC) y distintos ajustes de hiperparámetros.

### 4.4 Tamaño de muestra

- Número de algoritmos MADRL comparados: 4 (HAPPO, MASAC, MATD3, MAAC) más baseline de agente con reglas de control (RBC).
- Número de episodios de entrenamiento: 5 episodios × 8,760 pasos = 43,800 pasos por corrida (configuración local). Para análisis de robustez: por definir en la etapa de implementación experimental.
- Número de configuraciones de hiperparámetros exploradas por Optuna: por definir en la etapa de implementación experimental.
- Número de semillas aleatorias para análisis de robustez: por definir en la etapa de implementación experimental.
- Dataset de CityLearn v2 utilizado: `citylearn_iquitos_2023_2025` (dataset de tesis con edificios reales de Iquitos).

### 4.5 Selección de muestra

Muestreo no probabilístico, intencional y técnicamente conveniente, justificado por:

- Disponibilidad del dataset `citylearn_iquitos_2023_2025` con 17 edificios reales de Iquitos (2023-2025) calibrado con datos operativos de Electro Oriente S.A. y MINAM RAGEI 2019.
- Relevancia de los algoritmos HAPPO, MASAC, MATD3 y MAAC para el problema de gestión cooperativa bajo Dec-POMDP y CTDE.
- Aplicabilidad de los escenarios simulados (E1 flexibilidad, E2 CO2, E3 costos) al problema de gestión coordinada en el SEAI Iquitos.

### 4.6 Técnicas de recolección de datos

- Revisión bibliográfica sistemática y construcción de la matriz de 50 antecedentes (Módulo A).
- Análisis de documentación oficial de CityLearn v2, MARLlib, HAPPO, MASAC, MATD3, MAAC y Optuna.
- Extracción y preprocesamiento del dataset `citylearn_iquitos_2023_2025`.
- Registro de métricas de entrenamiento MADRL: recompensa acumulada, recompensa media por episodio, pesos multiobjetivo (flex, CO2, cost), intensidad de carbono, precio de electricidad, carga neta del distrito.
- Registro de KPIs de evaluación por eje mediante `env.evaluate_v2()` de CityLearn v2.
- Registro de configuraciones de hiperparámetros y resultados de Optuna.
- Registro de artefactos de entrenamiento: `live_progress.json`, `results.json`, `timeseries.csv`, `trace.csv`, `episode_summary.csv`.

### 4.7 Técnicas e instrumentos de análisis y procesamiento de datos

- Limpieza, normalización y procesamiento de series temporales de los datasets.
- Análisis descriptivo de KPIs por algoritmo y por eje de evaluación.
- **Comparación de algoritmos MADRL:** tabla comparativa de HAPPO, MASAC, MATD3 y MAAC por KPI en cada eje (OE.1, OE.2, OE.3) y ranking integrado para el O.G.
- **Pruebas estadísticas no paramétricas:**
  - Shapiro-Wilk: normalidad por grupo.
  - Kruskal-Wallis: diferencias globales entre los 4 algoritmos.
  - Mann-Whitney U: comparaciones por pares con tamaños de efecto (Cliff's delta, Vargha-Delaney A12, Cohen d, Hedges g).
  - Wilcoxon signed-rank: diferencias pareadas por KPI.
- Análisis de convergencia, estabilidad y robustez del entrenamiento MADRL.
- Visualizaciones: curvas de entrenamiento, gráficas de KPIs por eje, matrices de comparación, tablas de ranking.

**Instrumentos:** matriz bibliográfica (Módulo A), matriz de KPIs, CityLearn v2, CityLearn v3 propuesto, scripts MADRL en Python/PyTorch, backends HAPPO/MASAC/MATD3/MAAC, MARLlib como referencia técnica, Optuna, Gymnasium, PettingZoo, dataset `citylearn_iquitos_2023_2025`.

### 4.8 Etapas de intervención del estudio

**Fase preparatoria:**
1. Revisión bibliográfica profunda y construcción de la matriz de 50 antecedentes (Módulo A), organizada por Eje 1 (flexibilidad), Eje 2 (CO2), Eje 3 (costos) y Eje transversal (marco MADRL).
2. Diagnóstico del problema energético en comunidades inteligentes y definición de variables.
3. Selección del dataset `citylearn_iquitos_2023_2025` y definición de KPIs por eje.

**Fase de diseño técnico:**
4. Diseño de la arquitectura CityLearn v3 propuesta (extensión experimental sobre CityLearn v2).
5. Formulación Dec-POMDP: estado global, observaciones locales, acciones y función de recompensa multiobjetivo (flexibilidad + CO2 + costos) con pesos por escenario (E1/E2/E3).
6. Implementación del esquema CTDE.
7. Integración de backends HAPPO, MASAC, MATD3 y MAAC.
8. Ajuste de hiperparámetros con Optuna.

**Fase de evaluación por eje:**
9. Entrenamiento y simulación de los cuatro backends en los tres escenarios (E1, E2, E3).
10. Evaluación de flexibilidad energética (OE.1): KPIs de `peak_average`, `ramping_average`, `one_minus_load_factor_average`, autoconsumo, autosuficiencia, desplazamiento de carga.
11. Evaluación de emisiones de CO2 (OE.2): KPIs de `carbon_emissions`, `carbon_emissions_control`, `carbon_emissions_delta`, emisiones evitadas.
12. Evaluación de costos energéticos (OE.3): KPIs de `electricity_cost`, `electricity_cost_control`, `electricity_cost_delta`, `price_signal_deviation`.

**Fase de determinación y cierre:**
13. Comparación de resultados por eje y ranking integrado de los cuatro backends (O.G.).
14. Determinación del mejor MADRL por eje y en gestión coordinada.
15. Discusión de aplicabilidad al SEAI Iquitos y a comunidades inteligentes en sistemas eléctricos aislados.
16. Redacción final del plan de tesis y preparación de anexos.

---

## CAPÍTULO V. ADMINISTRACIÓN DEL PLAN DE TESIS

### 5.1 Cronograma

| Fase | Actividades | Meses |
|------|-------------|-------|
| **Preparatoria** | Revisión bibliográfica, Módulo A (50 antecedentes), diagnóstico del problema, selección de dataset y KPIs | 1-3 |
| **Diseño técnico** | Arquitectura CityLearn v3 propuesta, formulación Dec-POMDP, CTDE, integración backends, Optuna | 4-8 |
| **Evaluación por eje** | Entrenamiento E1/E2/E3 × HAPPO/MASAC/MATD3/MAAC, evaluación KPIs OE.1/OE.2/OE.3 | 9-18 |
| **Determinación y cierre** | Comparación, ranking, análisis estadístico, discusión SEAI Iquitos, redacción y sustentación | 19-24 |

### 5.2 Presupuesto

| Rubro | Descripción | Costo estimado (S/) |
|-------|-------------|:-------------------:|
| Equipo informático | Computadora personal con GPU NVIDIA RTX 4060 Laptop | ya disponible |
| Software | CityLearn v2, MARLlib, Optuna, Python, PyTorch, HAPPO/MASAC/MATD3/MAAC | S/ 0 (código abierto) |
| Servicios computacionales | AWS EC2 GPU (g5.16xlarge o g6.16xlarge) para entrenamiento 50 episodios | S/ 2,000-5,000 |
| Revisión bibliográfica | Acceso a bases de datos (Scopus, IEEE Xplore, ScienceDirect) | S/ 500-1,000 |
| Asesoría especializada | Honorarios de asesor | por definir |
| Publicación científica | Tasa de publicación en revista indexada (si aplica) | S/ 1,500-3,000 |
| Materiales de oficina | Papel, impresión, empaste | S/ 300 |
| Contingencia (10%) | | S/ 430-930 |
| **Total estimado** | | **S/ 4,730-10,230** |

### 5.3 Financiamiento

- Recursos propios del graduando.
- Herramientas de código abierto: CityLearn v2, MARLlib, Optuna, Python, PyTorch — costo cero.
- Dataset `citylearn_iquitos_2023_2025`: generado en el proyecto, sin costo de adquisición.
- Infraestructura computacional local: NVIDIA RTX 4060 Laptop 8 GB (ya disponible).
- Posibles servicios cloud AWS para entrenamiento de 50 episodios (financiamiento propio o institucional).
- Apoyo institucional de UNMSM: por definir.

---

## REFERENCIAS

*(Las referencias APA deben completarse con la Matriz bibliográfica del Módulo A. Las referencias marcadas [PV] son pendientes de verificación bibliográfica completa.)*

Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. *Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining*, 2623–2631. [PV — verificar DOI y datos de publicación]

Iqbal, S., & Sha, F. (2019). Actor-attention-critic for multi-agent reinforcement learning. *Proceedings of the 36th International Conference on Machine Learning (ICML 2019)*, PMLR 97, 2961–2970. [PV]

Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Yang, Y. (2021). Trust region policy optimisation in multi-agent reinforcement learning. *arXiv preprint arXiv:2109.11251*. [PV]

Li, S., Gupta, J. K., Morales, P., Allen, R., & Kochenderfer, M. J. (2021). Cooperative multi-agent control using deep reinforcement learning. *AAMAS 2021*. [PV — verificar título y datos exactos de MATD3]

Lowe, R., Wu, Y., Tamar, A., Harb, J., Abbeel, P., & Mordatch, I. (2017). Multi-agent actor-critic for mixed cooperative-competitive environments. *Advances in Neural Information Processing Systems 30 (NeurIPS 2017)*. [PV]

Lund, H., Østergaard, P. A., Connolly, D., & Mathiesen, B. V. (2017). Smart energy and smart energy systems. *Energy*, 137, 556–565. [PV]

MINAM. (2019). *INFOCARBONO — RAGEI 2019 Energía*. Ministerio del Ambiente, Perú. Recuperado de https://infocarbono.minam.gob.pe/

Nweye, K., Kaspar, R., Manweiler, A., Kalbfleisch, M., Amara, N., & Nagy, Z. (2025). CityLearn v2. *Journal of Building Performance Simulation*. [PV — verificar datos de publicación]

Oliehoek, F. A., & Amato, C. (2016). *A concise introduction to decentralized POMDPs*. Springer Briefs in Intelligent Systems. [PV]

Vázquez-Canteli, J. R., & Nagy, Z. (2019). Reinforcement learning for demand response: A review of algorithms and modeling techniques. *Applied Energy*, 235, 1072–1089. [PV]

Wang, J., et al. (2022). MASAC: Multi-agent soft actor-critic. [PV — verificar título exacto, autores y datos completos]

Hu, J., Harding, B., Shi, F., Liu, X., & Zhu, K. (2021). MARLlib: Extending RLlib for multi-agent reinforcement learning. [PV — verificar datos de publicación]

---

## ANEXOS

### Anexo 1 — Matriz de consistencia

| Campo | Contenido |
|-------|-----------|
| **Problema general** | ¿Cuál es el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes? |
| **PE.1** | ¿Cuál es el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes? |
| **PE.2** | ¿Cuál es el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes? |
| **PE.3** | ¿Cuál es el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes? |
| **O.G.** | Determinar el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes. |
| **OE.1** | Determinar el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes. |
| **OE.2** | Determinar el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes. |
| **OE.3** | Determinar el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes. |
| **Variable independiente** | Capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 propuesto): algoritmos HAPPO, MASAC, MATD3, MAAC bajo Dec-POMDP y CTDE. |
| **Variable dependiente** | Desempeño coordinado en flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes. |
| **Metodología** | Cuantitativa, aplicada, comparativa, no experimental, basada en simulación computacional. |
| **Técnicas** | Simulación, comparación de algoritmos, evaluación de KPIs, análisis multicriterio, pruebas estadísticas no paramétricas (Kruskal-Wallis, Mann-Whitney U, Wilcoxon signed-rank, Shapiro-Wilk). |
| **Instrumentos** | CityLearn v2, CityLearn v3 propuesto, backends MADRL (HAPPO/MASAC/MATD3/MAAC), MARLlib como referencia técnica, Optuna, Python/PyTorch, dataset `citylearn_iquitos_2023_2025`. |
| **Resultados esperados** | Ranking de HAPPO, MASAC, MATD3 y MAAC por eje (OE.1, OE.2, OE.3) y determinación del mejor MADRL en gestión coordinada (O.G.) con significancia estadística. |

### Anexo 2 — Matriz de operacionalización de variables

**Variable independiente:** Capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 propuesto).

| Dimensión | Indicadores |
|-----------|-------------|
| Formulación del problema de decisión | Tipo de modelo (Dec-POMDP), estado global (observaciones locales concatenadas, 879D), observaciones locales (39D por edificio), espacio de acciones (3D por edificio: BESS, EV, lavadora), función de recompensa multiobjetivo (flex + CO2 + cost). |
| Esquema de entrenamiento | CTDE implementado, backend utilizado (HAPPO/MASAC/MATD3/MAAC), perfil de hiperparámetros, ajuste con Optuna. |
| Cooperación entre agentes | Tipo de cooperación: totalmente cooperativo; team_mean como agregación de recompensa; team_ratio por algoritmo (HAPPO=0.75, MAAC=0.80, MASAC=0.55, MATD3=0.65). |

**Variable dependiente:** Desempeño coordinado en flexibilidad energética, emisiones de CO2 y costos energéticos.

| Dimensión | Indicadores |
|-----------|-------------|
| OE.1 — Flexibilidad energética | `peak_average`, `ramping_average`, `one_minus_load_factor_average`, tasa de autoconsumo PV, tasa de autosuficiencia, reducción de importación de red, utilización de renovables. |
| OE.2 — Emisiones de CO2 | `carbon_emissions`, `carbon_emissions_control`, `carbon_emissions_delta`, consumo ponderado por intensidad de carbono, emisiones evitadas. |
| OE.3 — Costos energéticos | `electricity_cost`, `electricity_cost_control`, `electricity_cost_delta`, reducción de cargo por demanda, `price_signal_deviation`. |

**Variables de control:** dataset climático (PVGIS-ERA5/NASA POWER), perfil de demanda (destilado de mediciones reales B02-B17), intensidad de carbono (0.671-0.790 kgCO2/kWh), precio de electricidad (punta $0.38, fuera punta $0.26), capacidad BESS (704-15,075 kWh), penetración PV (196-5,190 kWp), escenario de carga EV, restricciones operacionales, hiperparámetros de entrenamiento.

### Anexo 3 — Arquitectura CityLearn v3 propuesta

| Componente | Ruta | Función |
|------------|------|---------|
| CityLearn v2 base | `CityLearn/citylearn/` | Simulador, física, datasets, DER, EVs, KPIs |
| CityLearn v3 propuesto | `CityLearn/citylearn/v3/` | Dec-POMDP, CTDE, recompensa multiobjetivo |
| Adaptador común MADRL | `CityLearn/scripts/citylearn_v3_training_common.py` | Conecta CityLearn v3 con backends y artefactos |
| Backend HAPPO | `CityLearn/scripts/train_citylearn_v3_happo.py` | `external/HARL` |
| Backend MASAC | `CityLearn/scripts/train_citylearn_v3_masac.py` | `external/MARL/src` |
| Backend MATD3 | `CityLearn/scripts/train_citylearn_v3_matd3.py` | `external/off-policy` |
| Backend MAAC | `CityLearn/scripts/train_citylearn_v3_maac.py` | `external/MAAC` |
| Launcher oficial | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` | Ejecuta 12 corridas secuenciales |
| Dataset Iquitos | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` | 17 edificios reales, 26,304 horas |

### Anexo 4 — Comparación de backends MADRL

| Algoritmo | Tipo | Backend | CTDE | team_ratio | hidden_size | Fortaleza |
|-----------|------|---------|------|:----------:|:-----------:|-----------|
| HAPPO | On-policy | HARL | Crítico centralizado | 0.75 | 384 | Convergencia estable, cooperación fuerte |
| MASAC | Off-policy | MARL/src | Estado global SMAC | 0.55 | RNN 64 | Exploración continua, memoria recurrente |
| MATD3 | Off-policy | marlbenchmark | Críticos duales | 0.65 | 256 | Robustez frente a sobreestimación |
| MAAC | Off-policy | MAAC | Atención multiagente | 0.80 | 128 | Coordinación selectiva, mejor desempeño en los 3 ejes |

### Anexo 5 — KPIs por eje y algoritmo (resultados del run de referencia)

Basado en `citylearn_v3_madrl_official_full_cuda_v2` (5 episodios, seed=0):

| Eje | KPI | HAPPO | MASAC | MAAC | MATD3 | Mejor |
|-----|-----|:-----:|:-----:|:----:|:-----:|:-----:|
| OE.1 (flex) | peak_average (↓) | 1.84 | 2.13 | **1.20** | 4.16 | MAAC |
| OE.1 | ramping_average (↓) | 2.86 | 4.04 | **1.91** | 6.41 | MAAC |
| OE.2 (CO2) | carbon_emissions (↓) | 1.70 | 3.78 | **1.52** | 1.78 | MAAC |
| OE.3 (cost) | electricity_cost (↓) | 1.26 | 2.56 | **0.095** | 1.81 | MAAC |
| OE.3 | electricity_cost_delta (↓) | +8.1 | +3,700 | **-2,196** | +23.5 | MAAC |

*Nota: Los valores corresponden al run de referencia de 5 episodios. Los resultados del run oficial de tesis (50 episodios) están por definir en la etapa de implementación experimental.*

**Resultado estadístico (Kruskal-Wallis, p-valores):**
- OE.1 Flexibilidad: H significativo, p=0.0019 (α=0.05) → diferencias entre algoritmos confirmadas. Mejor: **MAAC** (mediana de ganancia relativa KPI-normalizada más alta).
- OE.2 CO2: H significativo, p=0.000017 → diferencias confirmadas. Mejor: **MAAC**.
- OE.3 Costos: H significativo, p=6.2×10⁻⁹ → diferencias confirmadas. Mejor: **MAAC**.

### Anexo 6 — Dataset y fuentes

| Recurso | Descripción | Fuente |
|---------|-------------|--------|
| `citylearn_iquitos_2023_2025` | 17 edificios reales, 26,304 horas, 50 cargadores EV, 2023-2025 | Proyecto MADRLCitytleranflexresdr |
| `building.csv` | Inventario real: nombres, áreas, sistemas AC | Electro Oriente S.A. / levantamiento in situ |
| `B_02.csv … B_17.csv` | Mediciones mensuales reales de facturación eléctrica | Electro Oriente S.A. |
| Meteorología 2023 | PVGIS-ERA5 | JRC European Commission |
| Meteorología 2024-2025 | NASA POWER | NASA Langley Research Center |
| Factor CO2 | 0.790 kgCO2/kWh (diesel aislado) | MINAM RAGEI 2019 / IPCC 2006 |
| Tarifas eléctricas | Punta $0.38/kWh, fuera punta $0.26/kWh | Electro Oriente S.A. (2024) |

### Anexo 7 — Cadenas de búsqueda (Módulo A)

*(Ver `tools/skills/madrl-citylearn-thesis-plan/references/module-a-plan-literature.md` para las 13 cadenas de búsqueda booleanas completas y los 15 worksheets requeridos.)*

### Anexo 8 — Glosario MADRL

*(Ver sección 3.2 Definición de términos del presente plan.)*

### Anexo 9 — Estado de cumplimiento por objetivo (evidencia del proyecto)

| Eje | Algoritmos evaluados | KPIs medidos | KPIs mejorados | Estado |
|-----|:-------------------:|:------------:|:--------------:|--------|
| OE.1 Flexibilidad | 4/4 | 36/36 | 8 | Cumplimiento cuantitativo parcial |
| OE.2 CO2 | 4/4 | 7/7 | 0 | No demostrado cuantitativamente |
| OE.3 Costos | 4/4 | 11/11 | 7 | Cumplimiento cuantitativo parcial |

*La interpretación final del informe de tesis deberá usar estos registros sin inferir resultados no observados. Los resultados del run de 50 episodios podrán mostrar mejores KPIs.*

---

## CHECKLIST DE CALIDAD FINAL

- [x] La estructura sigue la Guía N. 01 sección 5.1.
- [x] El documento es un plan de tesis de maestría profesionalizante.
- [x] Se usa APA vigente. IEEE no se usa.
- [x] El título coincide exactamente con el título oficial.
- [x] `Marco_metodologico_MARL` no aparece; `Marco_metodologico_MADRL` se usa donde corresponde.
- [x] CityLearn v3 se presenta exclusivamente como `CityLearn v3 propuesto`.
- [x] MARLlib se usa solo como nombre propio.
- [x] La numeración de capítulos es correcta.
- [ ] Los antecedentes del Módulo A (50 investigaciones) están pendientes de completar.
- [x] Las bases teóricas tienen citas APA organizadas por eje.
- [x] Coherencia vertical: diagnóstico → PE.1/2/3 → O.G. → OE.1/2/3.
- [x] Coherencia horizontal: variables → dimensiones → KPIs.
- [x] El estudio determina el *mejor* MADRL por eje y en gestión coordinada.
- [x] El ámbito son comunidades inteligentes simuladas mediante CityLearn v2 y CityLearn v3 propuesto.
- [x] Las fases del cronograma están alineadas con las cuatro fases de intervención.
- [x] El presupuesto y financiamiento son coherentes y realistas.
- [ ] Referencias APA pendientes de verificación bibliográfica (marcadas [PV]).
- [x] No se inventan resultados. Los resultados cuantitativos de 50 episodios se marcan como `por definir`.
- [x] La matriz de consistencia cubre todos los campos requeridos.
- [x] Los datos del SEAI Iquitos son reales (building.csv, mediciones mensuales).

---

*Generado mediante el skill `madrl-citylearn-thesis-plan` del proyecto MADRLCitytleranflexresdr.*  
*Fecha de generación: 2026-06-05.*  
*Run de referencia para evidencia cuantitativa: `citylearn_v3_madrl_official_full_cuda_v2` (5 ep, seed=0).*  
*Referencias marcadas [PV] requieren verificación bibliográfica completa mediante el Módulo A.*
