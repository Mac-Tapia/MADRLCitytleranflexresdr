# INFORME DE TESIS — GUÍA N.º 02 (Sección 5.1)

> Documento redactado siguiendo el skill local `madrl-citylearn-thesis-integrated`. La estructura corresponde exactamente a la Guía N.º 02, sección 5.1. Toda la evidencia cuantitativa proviene únicamente de la sesión de entrenamiento vigente `citylearn_v3_madrl_full_20260615_074011_v4` y de las auditorías de dataset del repositorio. No se incorporan resultados históricos, externos ni inventados. Los valores no observados se marcan como `resultado no verificado` o `pendiente`.

---

## CARÁTULA

**UNIVERSIDAD NACIONAL DE INGENIERÍA**

Escuela de Posgrado / Facultad de Ingeniería Eléctrica y Electrónica

**MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS ENERGÉTICOS EN COMUNIDADES INTELIGENTES**

Tesis para optar el grado académico de Maestro (Maestría de especialización / profesionalizante)

Autor: [dato pendiente de verificación]

Asesor: [dato pendiente de verificación]

Lima, Perú — 2026

---

## DATOS GENERALES

### Dedicatoria

[Dato pendiente de verificación por el tesista.]

### Agradecimientos

[Dato pendiente de verificación por el tesista.]

### Copia de documentos

[Dato pendiente de verificación: constancias institucionales, autorizaciones y licencias del proyecto.]

### Índice de contenidos

1. Capítulo I. Planteamiento del problema
2. Capítulo II. Marco teórico
3. Capítulo III. Desarrollo del trabajo de tesis
4. Capítulo IV. Conclusiones y recomendaciones
5. Referencias
6. Anexos

### Lista de tablas, ilustraciones y cuadros

- Tabla 1. KPIs de flexibilidad energética por algoritmo × escenario E1 (OE.1).
- Tabla 2. KPI de emisiones de CO2 por algoritmo × escenario E2 (OE.2).
- Tabla 3. KPI de costos energéticos por algoritmo × escenario E3 (OE.3).
- Tabla 4. Ranking integrado MADRL (O.G.) — normalización min-max, Score_OG y Borda.
- Tabla 5. Backends MADRL comparados y configuración vigente `local4060_fast`.
- Tabla 6. Pruebas estadísticas no paramétricas por eje y global.
- Cuadro A1. Matriz de consistencia.
- Cuadro A2. Matriz de operacionalización de variables.

### Resumen

Las comunidades inteligentes integran recursos energéticos distribuidos —generación fotovoltaica (PV), almacenamiento en baterías (BESS) y carga de vehículos eléctricos (EV)— cuya operación no coordinada limita la reducción simultánea de picos de demanda, emisiones de carbono y costos eléctricos (Nweye et al., 2022; Vázquez-Canteli & Nagy, 2019b). El problema abordado es la ausencia de una determinación del mejor Multi-Agente de Aprendizaje por Refuerzo Profundo (MADRL) para la gestión coordinada de las tres dimensiones bajo condiciones idénticas y reproducibles. El objetivo general fue determinar el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes. La metodología es cuantitativa, aplicada y de simulación computacional no experimental: se empleó CityLearn v2 (Nweye et al., 2024) como entorno base y una capa experimental denominada CityLearn v3 propuesto que formula el problema como un proceso de decisión de Markov parcialmente observable descentralizado (Dec-POMDP) con entrenamiento centralizado y ejecución descentralizada (CTDE) (Oliehoek & Amato, 2016). Se compararon cuatro backends MADRL —HAPPO (Kuba et al., 2021; Zhong et al., 2023), MASAC (Haarnoja et al., 2018; Gao et al., 2023), MATD3 (Lowe et al., 2017) y MAAC (Iqbal & Sha, 2019)— sobre un dataset de 17 edificios del Sistema Eléctrico Aislado de Iquitos (SEAI). Se ejecutaron 12 corridas (3 escenarios × 4 algoritmos) de 5 episodios y 8 760 pasos horarios cada una, sobre GPU NVIDIA RTX 4060 con PyTorch 2.8.0+cu126. Los resultados, evaluados por ganancia relativa con signo frente al baseline `evaluate_v2`, muestran que ningún algoritmo superó el baseline en términos absolutos en la mayoría de los KPIs, por lo que la evidencia caracteriza el desempeño relativo entre algoritmos: MATD3 obtuvo la mejor mediana de ganancia en flexibilidad (OE.1) y de forma global (O.G.), MASAC la mejor mediana en emisiones (OE.2) y MAAC la mejor mediana en costos (OE.3). La prueba global de Kruskal-Wallis fue significativa (p = 0,0459) mientras que las pruebas por eje no lo fueron (α = 0,05). Se concluye que, con la evidencia vigente y bajo el método de agregación inter-eje, MATD3 es el MADRL mejor posicionado para la gestión coordinada, aunque el cumplimiento cuantitativo frente al baseline es parcial y requiere replicación con múltiples semillas.

**Palabras clave:** MADRL, CityLearn, Dec-POMDP, CTDE, flexibilidad energética, emisiones de CO2, costos energéticos, comunidades inteligentes.

### Abstract

Smart communities integrate distributed energy resources —photovoltaic generation (PV), battery energy storage (BESS), and electric-vehicle (EV) charging— whose uncoordinated operation limits the simultaneous reduction of demand peaks, carbon emissions, and electricity costs (Nweye et al., 2022; Vázquez-Canteli & Nagy, 2019b). The problem addressed is the absence of a determination of the best Multi-Agent Deep Reinforcement Learning (MADRL) approach for the coordinated management of these three dimensions under identical and reproducible conditions. The general objective was to determine the best MADRL that coordinately manages energy flexibility, CO2 emissions, and energy costs in smart communities. The methodology is quantitative, applied, and based on non-experimental computational simulation: CityLearn v2 (Nweye et al., 2024) was used as the base environment and an experimental layer named CityLearn v3 propuesto formulates the problem as a decentralized partially observable Markov decision process (Dec-POMDP) with centralized training and decentralized execution (CTDE) (Oliehoek & Amato, 2016). Four MADRL backends were compared —HAPPO (Kuba et al., 2021; Zhong et al., 2023), MASAC (Haarnoja et al., 2018; Gao et al., 2023), MATD3 (Lowe et al., 2017), and MAAC (Iqbal & Sha, 2019)— over a dataset of 17 buildings from the Iquitos Isolated Power System (SEAI). Twelve runs (3 scenarios × 4 algorithms) of 5 episodes and 8,760 hourly steps each were executed on an NVIDIA RTX 4060 GPU with PyTorch 2.8.0+cu126. Results, evaluated by signed relative gain against the `evaluate_v2` baseline, show that no algorithm beat the baseline in absolute terms across most KPIs; therefore the evidence characterizes the relative performance among algorithms: MATD3 achieved the best median gain in flexibility (OE.1) and globally (O.G.), MASAC the best median in emissions (OE.2), and MAAC the best median in costs (OE.3). The global Kruskal-Wallis test was significant (p = 0.0459) while per-axis tests were not (α = 0.05). It is concluded that, with current evidence and under the inter-axis aggregation method, MATD3 is the best-positioned MADRL for coordinated management, although quantitative compliance against the baseline is partial and requires replication with multiple seeds.

**Keywords:** MADRL, CityLearn, Dec-POMDP, CTDE, energy flexibility, CO2 emissions, energy costs, smart communities.

### Introducción

La transición energética de las comunidades inteligentes depende cada vez más de la coordinación de recursos energéticos distribuidos como la generación fotovoltaica, el almacenamiento en baterías y la carga de vehículos eléctricos (Lund et al., 2017). Cuando estos recursos operan de forma independiente, la comunidad pierde oportunidades de aplanar su perfil de demanda, de desplazar consumo hacia horas de menor intensidad de carbono y de aprovechar señales tarifarias dinámicas (Vázquez-Canteli & Nagy, 2019b; Nweye et al., 2022). El control mediante aprendizaje por refuerzo profundo de un solo agente enfrenta dificultades de escalabilidad y de observabilidad parcial cuando el número de edificios crece, lo que motiva el uso de esquemas multiagente cooperativos (Lowe et al., 2017; Oliehoek & Amato, 2016).

El presente trabajo aborda esta brecha mediante un Multi-Agente de Aprendizaje por Refuerzo Profundo (MADRL) cooperativo formulado como un proceso de decisión de Markov parcialmente observable descentralizado (Dec-POMDP) con entrenamiento centralizado y ejecución descentralizada (CTDE) (Oliehoek & Amato, 2016). Como entorno base se emplea CityLearn v2 (Nweye et al., 2024; Nweye et al., 2023c), simulador estandarizado de gestión energética de comunidades conectadas a la red; sobre él se construye una capa experimental denominada CityLearn v3 propuesto, que implementa la formulación Dec-POMDP/CTDE y la función de recompensa multiobjetivo cooperativa de la investigación. CityLearn v3 propuesto es una extensión experimental de esta tesis y no constituye una versión oficial del paquete CityLearn.

Sobre esta base se comparan, bajo condiciones idénticas de entorno, cuatro backends MADRL representativos de familias algorítmicas distintas: HAPPO, de tipo on-policy con garantía de mejora monótona cooperativa (Kuba et al., 2021; Zhong et al., 2023); MASAC, de tipo off-policy basado en máxima entropía (Haarnoja et al., 2018; Gao et al., 2023); MATD3, de tipo off-policy determinístico con doble crítico (Lowe et al., 2017); y MAAC, de tipo off-policy con mecanismo de atención (Iqbal & Sha, 2019). MARLlib (Hu et al., 2023) se utiliza únicamente como marco de referencia conceptual y terminológico para patrones CTDE. El ajuste de hiperparámetros se concibe con Optuna (Akiba et al., 2019).

El informe se organiza según la Guía N.º 02: el Capítulo I plantea el problema, los objetivos y el alcance; el Capítulo II desarrolla los antecedentes, las bases teóricas y la definición de términos; el Capítulo III presenta y desarrolla la propuesta de solución (la capa CityLearn v3 propuesto y los cuatro backends), analiza los datos y resultados de la sesión vigente, los discute e interpreta, y estima el impacto; el Capítulo IV expone conclusiones y recomendaciones alineadas con el objetivo general y los objetivos específicos.

---

## CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA

### 1.1 Diagnóstico

El diagnóstico se organiza en las tres dimensiones del estudio, alineadas con los objetivos específicos OE.1, OE.2 y OE.3, más una brecha metodológica transversal.

**Flexibilidad energética (OE.1).** En comunidades inteligentes con alta penetración de PV, BESS y EV, la falta de coordinación entre edificios produce picos de demanda agregada, rampas pronunciadas y baja utilización del almacenamiento (Nweye et al., 2022). El control de un solo agente no escala bien al número de edificios y no explota la cooperación entre activos (Lowe et al., 2017). Existe una brecha en la determinación de cuál MADRL coordina mejor la flexibilidad.

**Emisiones de CO2 (OE.2).** En sistemas con intensidad de carbono variable, la operación insensible al carbono desaprovecha las ventanas de menor emisión (Sarkar et al., 2024; Ma et al., 2025). En sistemas aislados con generación diésel dominante, como el SEAI Iquitos, la intensidad de carbono es alta y relativamente estable (0,6715–0,7900 kgCO2/kWh según MINAM, 2019), por lo que la reducción de emisiones depende sobre todo de reducir y desplazar la importación neta de red. Hay una brecha en determinar cuál MADRL reduce mejor las emisiones.

**Costos energéticos (OE.3).** Bajo tarifas dinámicas, la respuesta de demanda no coordinada no minimiza el costo eléctrico de la comunidad (Xiong et al., 2024; Chen et al., 2024). Existe una brecha en determinar cuál MADRL optimiza mejor los costos.

**Brecha metodológica transversal.** No se dispone de un benchmark unificado que compare HAPPO, MASAC, MATD3 y MAAC bajo condiciones idénticas de Dec-POMDP/CTDE sobre los tres ejes simultáneamente, con protocolo estadístico y datos reproducibles (Hu et al., 2023; Nweye & Nagy, 2024b).

### 1.2 Identificación y descripción del problema de estudio

El problema central es la **ausencia de una determinación del mejor MADRL para la gestión coordinada** de flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes. Sus síntomas son perfiles de demanda con picos elevados, emisiones no minimizadas y costos no optimizados. Sus causas técnicas y metodológicas son la observabilidad parcial por edificio, la ausencia de un estado global compartido para coordinar, y la falta de un protocolo de comparación homogéneo entre algoritmos. Sus consecuencias operativas, ambientales y económicas son la subutilización de los recursos distribuidos, mayores emisiones y mayores costos.

- **Variable independiente:** la capa MADRL colaborativa implementada sobre CityLearn v2 (CityLearn v3 propuesto).
- **Variable dependiente:** el desempeño del despacho óptimo bajo restricciones eléctricas y operación segura, medido por KPIs de flexibilidad, emisiones, costos, operación segura y aprendizaje MADRL.
- **Alcance espacial:** comunidades inteligentes representadas por el dataset de 17 edificios del SEAI Iquitos en CityLearn v2.
- **Alcance temporal:** literatura 2015–2026; horizonte de simulación de un año (8 760 pasos horarios).

### 1.3 Formulación del problema

#### 1.3.1 Formulación del problema general

¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes?

#### 1.3.2 Formulación de los problemas específicos

- **PE.1:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes?
- **PE.2:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes?
- **PE.3:** ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes?

### 1.4 Objetivos

#### 1.4.1 Objetivo general

Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes.

#### 1.4.2 Objetivos específicos

- **OE.1:** Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes.
- **OE.2:** Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes.
- **OE.3:** Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes.

### 1.5 Justificación del estudio

- **Técnica:** la investigación entrega un benchmark reproducible de cuatro backends MADRL sobre un entorno común, con artefactos versionados (resúmenes, series de tiempo, trazas, KPIs y checkpoints) que permiten auditar el desempeño (Hu et al., 2023; Nweye & Nagy, 2024b).
- **Ambiental:** al evaluar el eje de emisiones de CO2 con intensidad de carbono real del SEAI, el estudio cuantifica el potencial de operación sensible al carbono en un sistema aislado con generación diésel (MINAM, 2019; Ma et al., 2025).
- **Económica:** al evaluar el eje de costos bajo tarifas dinámicas, el estudio caracteriza el potencial de ahorro mediante respuesta de demanda coordinada (Xiong et al., 2024).
- **Metodológica:** la formulación Dec-POMDP/CTDE y el protocolo estadístico no paramétrico aportan un marco de comparación homogéneo (Oliehoek & Amato, 2016).
- **Científica:** se contribuye con la capa CityLearn v3 propuesto como artefacto experimental abierto sobre CityLearn v2 (Nweye et al., 2024).
- **Social:** la aplicabilidad a comunidades de un sistema aislado peruano (SEAI Iquitos) vincula el trabajo con necesidades reales de electrificación sostenible.

### 1.6 Alcance del estudio

- **Temático:** comparación de HAPPO, MASAC, MATD3 y MAAC sobre tres ejes de KPI (flexibilidad, emisiones, costos).
- **Espacial:** dataset de 17 edificios del SEAI Iquitos representados en CityLearn v2.
- **Temporal:** literatura 2015–2026; simulación de un año horario.
- **Metodológico:** cuantitativo, comparativo, basado en simulación.
- **Computacional:** Python, PyTorch 2.8.0+cu126, CityLearn v2, CityLearn v3 propuesto, GPU NVIDIA RTX 4060, ajuste con Optuna.
- **Límites y exclusiones:** la sesión vigente usa una sola semilla por algoritmo (seed = 0), por lo que los contrastes estadísticos son exploratorios; los resultados de simulación no sustituyen mediciones operativas reales del SEAI Iquitos; la transferencia al sistema real requiere calibración adicional.

---

## CAPÍTULO II. MARCO TEÓRICO

### 2.1 Antecedentes

Los antecedentes se organizan en cuatro ejes, alineados con OE.1, OE.2, OE.3 y el eje metodológico transversal. Provienen de la matriz bibliográfica del proyecto.

**Eje 1 — MADRL para flexibilidad energética (OE.1).** Liu et al. (2022) aplican MADRL a sistemas de edificios con energía renovable y muestran mejoras de flexibilidad respecto de líneas base no coordinadas. Fang et al. (2021) emplean MADRL para gestión energética distribuida y optimización de estrategias en mercados de microrredes. Hribar et al. (2025) mejoran la autonomía energética de distritos de energía positiva con MADRL. Nweye et al. (2022) documentan los retos reales del MADRL en edificios interactivos con la red usando CityLearn. Felicetti et al. (2024) combinan programación entera y aprendizaje por refuerzo para aplanamiento de picos y autoconsumo.

**Eje 2 — MADRL para reducción de emisiones de CO2 (OE.2).** Ma et al. (2025) proponen un esquema seguro de MADRL con asignación de crédito y actualización secuencial para compartir energía con tope de carbono entre microrredes. Sarkar et al. (2024) reducen la huella de carbono de centros de datos en tiempo real con aprendizaje por refuerzo sensible al carbono. Ye et al. (2025) aplican MADRL seguro a la operación descentralizada de baja emisión en redes de distribución activas y multi-microrredes. Ren et al. (2025) diseñan mercados P2P de bajo carbono con MADRL.

**Eje 3 — MADRL para optimización de costos energéticos (OE.3).** Xiong et al. (2024) optimizan el costo de sistemas de energía doméstica considerando tarifas time-of-use y control en tiempo real del almacenamiento. Chen et al. (2024) usan aprendizaje por refuerzo de dos niveles para gestión de sistemas integrados con vehículos eléctricos como almacenamiento móvil. Gao et al. (2023) optimizan el despacho colaborativo de microrredes con un MASAC mejorado. Yao et al. (2023) aplican MADRL a la gestión energética de comunidades inteligentes con foco en costos.

**Eje transversal — Dec-POMDP, CTDE, backends y benchmarks.** Oliehoek y Amato (2016) formalizan los Dec-POMDP. Lowe et al. (2017) introducen el actor-crítico multiagente para entornos mixtos (base de MADDPG/MATD3). Kuba et al. (2021) y Zhong et al. (2023) desarrollan HAPPO/HATRPO con garantías de mejora monótona heterogénea. Haarnoja et al. (2018) proponen Soft Actor-Critic, base de MASAC. Iqbal y Sha (2019) introducen el actor-attention-critic (MAAC). Hu et al. (2023) presentan MARLlib como librería escalable de MADRL. Vázquez-Canteli y Nagy (2019a, 2020) y Nweye et al. (2023c, 2024) desarrollan y consolidan CityLearn como entorno estándar de benchmarking.

Cada antecedente de la matriz incluye autor-año, objetivo, metodología, dataset/entorno, algoritmo, resultados principales, aporte a esta tesis y cita APA (ver Anexo — matriz bibliográfica).

### 2.2 Bases teóricas

**Aprendizaje por refuerzo profundo (DRL).** Un agente aprende una política que maximiza el retorno esperado mediante interacción con un entorno modelado como proceso de decisión de Markov (Sutton & Barto, 2018).

**Aprendizaje por refuerzo profundo multiagente cooperativo (MADRL).** Varios agentes aprenden políticas que maximizan una recompensa común o de equipo; la no estacionariedad inducida por el aprendizaje simultáneo se mitiga con esquemas de entrenamiento centralizado (Lowe et al., 2017).

**Dec-POMDP.** Modelo formal para decisión cooperativa con observabilidad parcial: cada agente observa solo información local y todos comparten una recompensa (Oliehoek & Amato, 2016).

**CTDE (entrenamiento centralizado, ejecución descentralizada).** Durante el entrenamiento, un crítico centralizado accede al estado global; durante la ejecución, cada actor decide solo con su observación local (Lowe et al., 2017; Iqbal & Sha, 2019).

**Backends MADRL.** HAPPO aplica actualizaciones secuenciales con garantía de mejora monótona cooperativa (Kuba et al., 2021; Zhong et al., 2023). MASAC extiende SAC al caso multiagente con máxima entropía (Haarnoja et al., 2018; Gao et al., 2023). MATD3 extiende TD3/MADDPG con doble crítico determinístico (Lowe et al., 2017). MAAC usa atención para que el crítico pondere selectivamente a otros agentes (Iqbal & Sha, 2019).

**CityLearn.** Entorno OpenAI Gym/Gymnasium para benchmarking de respuesta de demanda y gestión energética de comunidades interactivas con la red (Vázquez-Canteli & Nagy, 2019a; Nweye et al., 2024).

**Optuna.** Marco de optimización de hiperparámetros de nueva generación (Akiba et al., 2019).

### 2.3 Definición de términos

- **MADRL:** Multi-Agente de Aprendizaje por Refuerzo Profundo.
- **DRL:** aprendizaje por refuerzo profundo.
- **Agente:** entidad que aprende y decide acciones (en esta tesis, un edificio).
- **Entorno:** simulador CityLearn v2 con dinámica física, DER, EV y KPIs.
- **Dec-POMDP:** proceso de decisión de Markov parcialmente observable descentralizado.
- **CTDE:** entrenamiento centralizado con ejecución descentralizada.
- **HAPPO, MASAC, MATD3, MAAC:** backends MADRL comparados.
- **MARLlib:** librería de referencia de MADRL (nombre propio).
- **Optuna:** marco de ajuste de hiperparámetros.
- **CityLearn v2:** entorno base existente.
- **CityLearn v3 propuesto:** capa experimental de esta tesis sobre CityLearn v2.
- **Comunidad inteligente:** conjunto de edificios con DER coordinables.
- **Flexibilidad energética:** capacidad de modular la demanda neta (picos, rampas, factor de carga).
- **Intensidad de carbono:** emisiones de CO2 por kWh consumido.
- **Costos energéticos:** costo eléctrico bajo tarifa dinámica.
- **BESS, PV, EV:** almacenamiento en baterías, generación fotovoltaica y vehículos eléctricos.
- **KPI:** indicador clave de desempeño.

---

## CAPÍTULO III. DESARROLLO DEL TRABAJO DE TESIS

### 3.1 Presentación de la propuesta de solución

La propuesta de solución es la evaluación comparativa de cuatro backends MADRL cooperativos bajo condiciones idénticas de Dec-POMDP/CTDE sobre los tres ejes de KPI. El soporte experimental es la capa **CityLearn v3 propuesto**, una extensión experimental de CityLearn v2 (Nweye et al., 2024) que implementa la formulación Dec-POMDP, el esquema CTDE y la función de recompensa multiobjetivo cooperativa de la investigación. La capa reside en `CityLearn/citylearn/v3/` y expone el adaptador común `CityLearn/scripts/citylearn_v3_training_common.py`, que estandariza el registro de artefactos, KPIs, figuras y tablas. La arquitectura propuesta y el rol de cada componente se resumen en el Anexo 5.

### 3.2 Desarrollo de la propuesta de solución

#### 3.2.1 Arquitectura CityLearn v3 propuesta

El entorno base `CityLearnEnv` (v2) se extiende con clases experimentales en `CityLearn/citylearn/v3/`: un entorno base Dec-POMDP, envoltorios específicos por backend (HAPPO/HARL, MASAC, MATD3, MAAC) y la función de recompensa `CityLearnV3MADRLRewardFunction`. Los scripts `CityLearn/scripts/train_citylearn_v3_*.py` ejecutan cada backend, conectados a fuentes de implementación externas tratadas como dependencias: `external/HARL` (HAPPO), `external/MARL/src` (MASAC), `external/off-policy` (MATD3) y `external/MAAC` (MAAC).

#### 3.2.2 Formulación Dec-POMDP

El problema se formula como ℳ = ⟨𝒮, 𝒜₁…𝒜_N, 𝒯, R, 𝒪₁…𝒪_N, Ω, γ, T⟩, donde N = 17 agentes (un edificio del SEAI Iquitos cada uno). El estado global 𝒮 se construye, para el esquema CTDE, a partir de las 17 observaciones locales normalizadas; cada agente observa únicamente su oᵢ. La acción 𝒜ᵢ controla el BESS, la carga de EV y las cargas controlables del edificio. Se emplea γ = 0,9999 y T = 8 760 pasos horarios (un año), según la configuración registrada de la sesión vigente. La condición Dec-POMDP (cada agente observa solo su oᵢ) y el esquema CTDE (crítico centralizado durante el entrenamiento, actor local en ejecución) se satisfacen por construcción.

#### 3.2.3 Función de recompensa multiobjetivo

La recompensa por agente combina los tres ejes:

`reward_i(t) = reward_scale × [w_flex·flex_i(t) + w_carbon·carbon_i(t) + w_cost·cost_i(t)]`

La recompensa cooperativa de equipo es `team_reward = (1/N) Σᵢ reward_i`, y la recompensa mixta `mixed_reward_i = (1−r_team)·reward_i + r_team·team_reward`. Los pesos por escenario alinean cada escenario con un objetivo específico: E1 prioriza flexibilidad (OE.1), E2 prioriza emisiones (OE.2) y E3 prioriza costos (OE.3). En la sesión vigente la agregación de recompensa es `team_mean` y la función activa es `citylearn.reward_function.CityLearnV3MADRLRewardFunction` (no se usan los pesos base de MARL). La justificación académica de todos los parámetros se documenta en `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`.

#### 3.2.4 Esquema CTDE

Los críticos son centralizados durante el entrenamiento (acceden al estado global o a observaciones/acciones conjuntas, según el backend) y los actores son locales y descentralizados en ejecución, de modo que cada edificio decide con su sola observación (Lowe et al., 2017; Iqbal & Sha, 2019).

#### 3.2.5 Backends MADRL comparados

Los cuatro backends se entrenaron bajo condiciones idénticas de entorno en una GPU NVIDIA GeForce RTX 4060 Laptop (8 188 MiB), con PyTorch 2.8.0+cu126, CUDA habilitado y perfil `local4060_fast`. La Tabla 5 resume su tipo, propiedad clave y configuración vigente.

**Tabla 5. Backends MADRL comparados y configuración vigente `local4060_fast`.**

| Algoritmo | Tipo | Propiedad clave | Configuración vigente | Fuente |
| --- | --- | --- | --- | --- |
| HAPPO | On-policy | Mejora monótona cooperativa | hidden_size = 256, n_rollout_threads = 1, γ = 0,9999 | `external/HARL` (Kuba et al., 2021; Zhong et al., 2023) |
| MASAC | Off-policy | Máxima entropía + estado tipo SMAC | rnn_hidden = 64, qmix_hidden = 32, hyper_hidden = 64, buffer = 2, critic_batch = 1, action_bins = 3 | `external/MARL/src` (Haarnoja et al., 2018; Gao et al., 2023) |
| MATD3 | Off-policy | Doble crítico determinístico | hidden_size = 256, batch = 256, buffer = 4096, train_interval = 100 | `external/off-policy` (Lowe et al., 2017) |
| MAAC | Off-policy | Mecanismo de atención | hidden_size = 256, batch = 256, buffer_length = 50 000, steps_per_update = 250, attend_heads = 4 | `external/MAAC` (Iqbal & Sha, 2019) |

Referencia de implementación conceptual: MARLlib (Hu et al., 2023). El entorno CityLearn avanza de forma secuencial para preservar la contabilidad por episodio; la GPU se usa en los backends neuronales.

#### 3.2.6 Ajuste de hiperparámetros con Optuna

El ajuste de hiperparámetros se concibe con Optuna (Akiba et al., 2019). En la sesión vigente se usaron las configuraciones del perfil `local4060_fast` registradas en `official_full_status.json`; la búsqueda sistemática con Optuna se mantiene como trabajo de ablación.

#### 3.2.7 Dataset `citylearn_iquitos_2023_2025`

El dataset representa 17 edificios reales del Sistema Eléctrico Aislado de Iquitos (SEAI), Loreto, Perú. Comprende 222 archivos CSV auditados (17 `Building_X.csv`, 185 `charger_X_Y.csv`, 17 `Washing_Machine_X.csv`, además de `weather.csv`, `carbon_intensity.csv` y `pricing.csv`), referenciados por `schema.json`. Los totales de recursos distribuidos vigentes son: PV 48 790,9 kWp; BESS 26 266 kWh / 6 648 kW; EV 749,4 kW con 185 cargadores en el schema. La intensidad de carbono se sitúa entre 0,6715 y 0,7900 kgCO2/kWh (MINAM, 2019), y el precio entre 0,383220954 y 1,066918914 USD/kWh. La auditoría integral del dataset reporta 0 celdas NaN y 0 celdas Inf, sin cargadores ni máquinas huérfanos o faltantes, con normalización permitida antes del entrenamiento (`outputs/dataset_audit/`). La regla operativa implementada prioriza la generación solar hacia recarga EV y carga del edificio, y el BESS prioriza recarga EV dentro de la ventana operativa antes de atender carga del edificio o corte de pico.

#### 3.2.8 KPIs por eje

Se emplean los nombres exactos del entorno CityLearn v2/v3 y la evaluación `evaluate_v2`:

- **OE.1 Flexibilidad:** `peak_average`, `ramping_average`, `one_minus_load_factor_average` (y KPIs de almacenamiento, importación/exportación de red y EV/V2G).
- **OE.2 Emisiones de CO2:** `carbon_emissions` y sus variantes baseline/control/delta.
- **OE.3 Costos:** `electricity_cost` y sus variantes, más `price_signal_deviation` y componentes de costo por pico/ramping.

Los KPIs se reportan como valores normalizados respecto del baseline `evaluate_v2`, donde el baseline equivale a 1,0 y, para indicadores en que «menor es mejor», un valor de control superior a 1,0 indica desempeño peor que el baseline.

### 3.3 Análisis de los datos y resultados

La sesión de entrenamiento vigente es `citylearn_v3_madrl_full_20260615_074011_v4`, iniciada el 2026-06-15 y completada el 2026-06-16 (`status = completed`). Las 12 corridas (3 escenarios × 4 algoritmos) finalizaron con `exit_code = 0`, 5 episodios y 8 760 pasos por episodio (43 800 pasos por corrida). La métrica de evaluación es la ganancia relativa con signo frente al baseline (`signed_relative_gain`, positivo = mejor que baseline), calculada sobre `citylearn_v2.evaluate_v2`. El paquete de evidencia consolidado se encuentra en `outputs/thesis_objective_evidence/`.

**Hallazgo transversal.** En la sesión vigente, los agentes MADRL no superaron al baseline en términos absolutos en la mayoría de los KPIs por eje (la mayoría de los valores de control resultaron iguales o superiores a 1,0 en indicadores de «menor es mejor»). Por ello, la evidencia se interpreta como una **caracterización del desempeño relativo entre algoritmos**, no como una demostración de mejora frente al baseline. Este hallazgo se reporta sin ajustes para preservar la no invención de resultados.

#### 3.3.1 Resultados por eje

**Tabla 1. KPIs de flexibilidad (OE.1), escenario E1, valores normalizados (baseline = 1,0; menor es mejor en `peak_average` y `ramping_average`).**

| Algoritmo | `peak_average` | `ramping_average` | `one_minus_load_factor_average` |
| --- | :---: | :---: | :---: |
| HAPPO | 1,1520 | 1,1057 | 0,9340 (mejora) |
| MASAC | 1,1166 | 1,0191 | 0,9852 (mejora) |
| MATD3 | **1,0135** | **1,0013** | 0,9903 (mejora) |
| MAAC | 1,0892 | 1,0215 | 0,9828 (mejora) |

MATD3 obtiene los valores de pico y rampa más cercanos al baseline (los mejores entre los cuatro), mientras que HAPPO logra el mejor factor de carga. El paquete de evidencia identifica a **MATD3 como mejor algoritmo de OE.1 por mediana de ganancia relativa**; la prueba de Kruskal-Wallis sobre OE.1 no detecta diferencias globales significativas (p = 0,4450; α = 0,05). Estado de cumplimiento de OE.1: `cumplimiento_cuantitativo_parcial` (17 de 48 registros KPI mejoraron frente al baseline).

**Tabla 2. KPI de emisiones de CO2 (OE.2), escenario E2, `carbon_emissions` normalizado (baseline = 1,0; menor es mejor).**

| Algoritmo | `carbon_emissions` | ¿Mejora vs. baseline? |
| --- | :---: | :---: |
| HAPPO | 1,4052 | No |
| MASAC | **1,0381** | No |
| MATD3 | 1,0745 | No |
| MAAC | 1,0547 | No |

Ningún algoritmo redujo las emisiones por debajo del baseline; MASAC quedó más cercano al baseline. El paquete de evidencia identifica a **MASAC como mejor algoritmo de OE.2 por mediana de ganancia relativa**; Kruskal-Wallis no es significativo (p = 0,1655). Estado de cumplimiento de OE.2: `no_demostrado_cuantitativamente` (0 de 20 registros KPI mejoraron). Este resultado es coherente con la naturaleza del SEAI: con intensidad de carbono alta y casi constante, la reducción de emisiones depende de reducir la importación neta, lo que no se logró en esta sesión.

**Tabla 3. KPI de costos energéticos (OE.3), escenario E3, `electricity_cost` normalizado (baseline = 1,0; menor es mejor).**

| Algoritmo | `electricity_cost` | ¿Mejora vs. baseline? |
| --- | :---: | :---: |
| HAPPO | 1,0436 | No |
| MASAC | **1,0033** | No |
| MATD3 | 1,0092 | No |
| MAAC | 1,0050 | No |

Sobre el KPI principal de costo, MASAC quedó más cercano al baseline, seguido de MAAC. No obstante, considerando el conjunto completo de KPIs de costo, el paquete de evidencia identifica a **MAAC como mejor algoritmo de OE.3 por mediana de ganancia relativa**; Kruskal-Wallis no es significativo (p = 0,0774). Estado de cumplimiento de OE.3: `cumplimiento_cuantitativo_parcial` (5 de 36 registros KPI mejoraron).

#### 3.3.2 Determinación del mejor MADRL global (O.G.) — ranking integrado multiobjetivo

Para responder al O.G. se aplica el método de agregación inter-eje del skill, que no favorece el eje de entrenamiento de ningún algoritmo. Se toman los KPIs principales por eje (`peak_average` para flexibilidad, `carbon_emissions` para emisiones, `electricity_cost` para costos), se normalizan por min-max inter-algoritmo invirtiendo a «mayor = mejor», y se agregan con pesos iguales [1/3, 1/3, 1/3], según el principio de comparación MORL sin función de utilidad especificada (Oliehoek & Amato, 2016, para la formalización cooperativa subyacente).

**Tabla 4. Ranking integrado MADRL (O.G.).**

| Algoritmo | KPI_flex_norm | KPI_co2_norm | KPI_cost_norm | Score_OG | Borda (Σ rangos) | Rango O.G. |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| HAPPO | 0,000 | 0,000 | 0,000 | 0,000 | 12 | 4 |
| MASAC | 0,256 | 1,000 | 1,000 | 0,752 | 5 | 3 |
| MATD3 | 1,000 | 0,901 | 0,854 | **0,918** | 7 | **1** |
| MAAC | 0,453 | 0,955 | 0,958 | 0,789 | 6 | 2 |

*Análisis de dominancia de Pareto:* HAPPO está dominado por los otros tres en los tres ejes. Entre MATD3, MASAC y MAAC ninguno domina a los demás en los tres ejes simultáneamente (forman un frente de Pareto): MATD3 lidera ampliamente en flexibilidad pero queda por debajo en emisiones y costos. Como no hay dominancia total, el Score_OG decide el ranking.

*Ranking escalar (Score_OG):* MATD3 (0,918) > MAAC (0,789) > MASAC (0,752) > HAPPO (0,000).

*Ranking de Borda (solo rangos):* MASAC (5) < MAAC (6) < MATD3 (7) < HAPPO (12), es decir, por conteo de posiciones MASAC encabeza, porque obtiene dos primeros lugares (OE.2 y OE.3). El Score_OG y el Borda **divergen**: se reportan ambos. La divergencia se interpreta en §3.4.

*Protocolo estadístico para O.G.:* sobre el conjunto agregado de todos los ejes, la prueba de Kruskal-Wallis es **significativa** (H = 8,006; p = 0,0459 < 0,05), con MATD3 como mejor mediana de ganancia relativa. La prueba de Brown-Forsythe no detecta heterocedasticidad (p = 0,9056). Shapiro-Wilk rechaza la normalidad en todos los grupos (p < 0,001), lo que justifica el uso de pruebas no paramétricas. La Tabla 6 resume los contrastes.

**Tabla 6. Pruebas estadísticas no paramétricas por eje y global (α = 0,05).**

| Ámbito | n | Kruskal-Wallis H | Kruskal-Wallis p | ¿Significativo? | Brown-Forsythe p | Mejor por mediana |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| OE.1 (E1) | 144 | 2,672 | 0,4450 | No | 0,9368 | MATD3 |
| OE.2 (E2) | 60 | 5,088 | 0,1655 | No | 0,9838 | MASAC |
| OE.3 (E3) | 104 | 6,832 | 0,0774 | No | 0,9969 | MAAC |
| Global (ALL) | 308 | 8,006 | **0,0459** | **Sí** | 0,9056 | MATD3 |

La suite estadística aplicada incluye Shapiro-Wilk (normalidad por grupo), Kruskal-Wallis (omnibus), Mann-Whitney U y Wilcoxon signed-rank (por pares), tamaños de efecto (Cliff's delta, Vargha-Delaney A12, Cohen d, Hedges g), Levene/Brown-Forsythe (homogeneidad de varianza) y bootstrap (IC 95%). Los archivos de soporte son `analisis_estadistico_madrl.csv`, `comparaciones_mwu_madrl.csv`, `comparaciones_wilcoxon_madrl.csv`, `hipotesis_estadisticas_madrl.csv` y `scores_kpi_algoritmo_madrl.csv`.

**Limitación estadística:** los contrastes se calculan sobre KPIs normalizados de una sola semilla por algoritmo; son evidencia exploratoria y no sustituyen la replicación con múltiples semillas.

#### 3.3.3 Desagregación por edificio y contribución al distrito

El paquete de evidencia incluye la desagregación por edificio y por distrito (`kpis_por_edificio_y_agente.csv`, `comparativa_edificios_por_agente.csv`, `comparativa_distrito_por_agente.csv`). A nivel distrital, los indicadores de uso de almacenamiento muestran un comportamiento marcadamente distinto entre algoritmos: HAPPO presenta el mayor throughput y ciclos equivalentes de batería (≈175–193 ciclos equivalentes en E1–E3), mientras que MATD3 utiliza el BESS de forma mínima (≈0,2–0,55 ciclos equivalentes), lo que indica una política mucho más conservadora en el uso del almacenamiento. Este contraste es relevante para interpretar por qué MATD3 mantiene picos y rampas cercanos al baseline. El detalle por edificio (B01 Electro Oriente, B06 Mall Aventura, B07 UNAP Biología, B11 Hospital Loreto, entre otros) se reporta en los archivos citados.

### 3.4 Discusión e interpretación de los resultados

**Comportamiento por eje.** MATD3 lidera la flexibilidad (OE.1) con picos y rampas casi iguales al baseline; su doble crítico determinístico y su política conservadora en el uso del BESS evitan introducir oscilaciones que degraden el pico y la rampa, lo que explica su cercanía al baseline (Lowe et al., 2017). MASAC queda más cercano al baseline en emisiones (OE.2) y en el costo principal (OE.3): la regularización por máxima entropía favorece políticas estables que no se alejan demasiado del baseline (Haarnoja et al., 2018). MAAC obtiene la mejor mediana en el conjunto de KPIs de costo (OE.3), consistente con la capacidad del mecanismo de atención para ponderar selectivamente las interacciones relevantes entre edificios (Iqbal & Sha, 2019). HAPPO, pese a su garantía de mejora monótona cooperativa (Kuba et al., 2021; Zhong et al., 2023), presenta el peor desempeño relativo en los tres ejes en esta sesión, asociado a un uso intensivo del almacenamiento que incrementa picos y rampas; este resultado sugiere que su configuración on-policy requiere mayor presupuesto de muestras o reajuste de hiperparámetros para esta tarea.

**Gestión coordinada (O.G.).** Bajo el Score_OG con normalización min-max, MATD3 encabeza el ranking porque su amplia ventaja en flexibilidad domina la magnitud de las diferencias, mientras que las ventajas de MASAC en emisiones y costos son marginales. Bajo el ranking de Borda (solo posiciones), MASAC encabeza por acumular dos primeros lugares. La divergencia entre ambos criterios indica que la determinación del «mejor MADRL coordinado» depende de si se pondera la magnitud de la mejora (Score_OG, favorece a MATD3) o la consistencia de posiciones (Borda, favorece a MASAC). La prueba global de Kruskal-Wallis significativa (p = 0,0459) con MATD3 como mejor mediana refuerza la determinación de **MATD3 como el MADRL mejor posicionado para la gestión coordinada** con la evidencia vigente, manteniendo a MASAC como alternativa robusta por consistencia de rango.

**Desempeño frente al baseline.** Es central reconocer que, en términos absolutos, ningún algoritmo superó consistentemente al baseline `evaluate_v2`. Por tanto, la determinación es **relativa** entre algoritmos y debe leerse como caracterización del desempeño bajo el presupuesto de entrenamiento vigente (5 episodios, una semilla), no como evidencia de superioridad frente a un controlador no aprendido.

**Aplicabilidad a comunidades reales.** Los resultados son metodológicamente aplicables al SEAI Iquitos, pero la transferencia operativa requiere calibración con datos reales y restricciones eléctricas específicas (ver Anexo — aplicabilidad).

### 3.5 Estimación del impacto de la solución

- **Impacto técnico:** la capa CityLearn v3 propuesto y el adaptador común constituyen un benchmark reproducible que permite comparar backends MADRL bajo condiciones idénticas con artefactos auditables (Hu et al., 2023; Nweye & Nagy, 2024b).
- **Impacto ambiental:** el marco habilita la evaluación de operación sensible al carbono con intensidad real del SEAI; el potencial de reducción de CO2 queda como `resultado no verificado` en esta sesión, dado que ningún algoritmo redujo las emisiones bajo el baseline.
- **Impacto económico:** el marco cuantifica el potencial de respuesta a tarifas dinámicas; el ahorro de costos frente al baseline también queda como `resultado no verificado` en esta sesión.
- **Impacto científico:** se aporta una metodología de determinación inter-eje (Score_OG, Borda, dominancia de Pareto) acompañada de un protocolo estadístico no paramétrico, replicable en otros datasets de CityLearn.

---

## CAPÍTULO IV. CONCLUSIONES Y RECOMENDACIONES

### 4.1 Conclusiones

- **Conclusión general (O.G.):** Con la evidencia vigente de la sesión `citylearn_v3_madrl_full_20260615_074011_v4` y bajo el método de agregación inter-eje (Score_OG con pesos iguales), **MATD3 es el Multi-Agente de Aprendizaje por Refuerzo Profundo mejor posicionado para la gestión coordinada** de flexibilidad, emisiones y costos (Score_OG = 0,918; mejor mediana global; Kruskal-Wallis global significativo, p = 0,0459). Bajo el criterio de consistencia de posiciones (Borda), MASAC encabeza; ambos criterios se reportan por su divergencia. La determinación es relativa entre algoritmos, pues ninguno superó al baseline de forma consistente.
- **Conclusión OE.1 (flexibilidad):** MATD3 optimiza mejor la flexibilidad energética (picos y rampas más cercanos al baseline; mejor mediana de ganancia), con cumplimiento cuantitativo parcial.
- **Conclusión OE.2 (emisiones):** MASAC queda mejor posicionado por mediana de ganancia, pero el objetivo **no se demostró cuantitativamente**: ningún algoritmo redujo las emisiones por debajo del baseline en esta sesión.
- **Conclusión OE.3 (costos):** MAAC obtiene la mejor mediana de ganancia en el conjunto de KPIs de costo (MASAC es el más cercano en el KPI principal `electricity_cost`), con cumplimiento cuantitativo parcial.
- **Conclusión metodológica:** la formulación Dec-POMDP/CTDE y la capa CityLearn v3 propuesto permiten una comparación homogénea y auditable de cuatro backends MADRL sobre los tres ejes, con un protocolo estadístico no paramétrico adecuado a datos que no cumplen normalidad.
- **Conclusión técnica:** la capa CityLearn v3 propuesto funciona como benchmark reproducible sobre el dataset real del SEAI Iquitos (222 CSV auditados, 0 NaN/Inf).
- **Conclusión ambiental y económica:** los potenciales de reducción de CO2 y de costos quedan como `resultado no verificado` en esta sesión y requieren mayor presupuesto de entrenamiento y replicación.

### 4.2 Recomendaciones

- Replicar las 12 corridas con múltiples semillas y mayor número de episodios para convertir los contrastes exploratorios en evidencia estadística robusta y verificar el desempeño frente al baseline.
- Ejecutar la búsqueda sistemática de hiperparámetros con Optuna (Akiba et al., 2019), en particular para HAPPO, cuyo desempeño relativo fue el más bajo.
- Revisar la política de uso del BESS de HAPPO, que mostró el mayor throughput y peores picos/rampas, para acotar la oscilación del almacenamiento.
- Extender la evaluación a datasets adicionales de CityLearn v2 para validar la generalización del ranking inter-eje.
- Validar la transferencia al SEAI Iquitos con datos operativos reales y restricciones eléctricas específicas antes de cualquier despliegue.
- Explorar enfoques híbridos MADRL-MPC y publicar la capa CityLearn v3 propuesto como software abierto sobre CityLearn v2.

---

## REFERENCIAS

Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. En *Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining* (pp. 2623–2631). ACM. https://doi.org/10.1145/3292500.3330701

Chen, L., He, H., Jing, R., Xie, M., & Ye, K. (2024). Energy management in integrated energy system with electric vehicles as mobile energy storage: An approach using bi-level deep reinforcement learning. *Energy*, 307. https://doi.org/10.1016/j.energy.2024.132599

Fang, X., Zhao, Q., Wang, J., Han, Y., & Li, Y. (2021). Multi-agent deep reinforcement learning for distributed energy management and strategy optimization of microgrid market. *Sustainable Cities and Society*, 74, 103163. https://doi.org/10.1016/j.scs.2021.103163

Felicetti, R., Iarlori, S., Monteriù, A., et al. (2024). Peak shaving and self-consumption maximization in home energy management systems: A combined integer programming and reinforcement learning approach. *Computers & Electrical Engineering*, 117, 109217. https://doi.org/10.1016/j.compeleceng.2024.109217

Gao, J., Li, Y., Wang, B., & Wu, H. (2023). Multi-microgrid collaborative optimization scheduling using an improved multi-agent soft actor-critic algorithm. *Energies*, 16(7), 3248. https://doi.org/10.3390/en16073248

Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). Soft Actor-Critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. En *Proceedings of the 35th International Conference on Machine Learning* (PMLR 80, pp. 1861–1870). https://proceedings.mlr.press/v80/haarnoja18b.html

Hribar, J., Mohorčič, M., & Čampa, A. (2025). Improving energy autonomy of positive energy districts using multi-agent deep reinforcement learning. *Scientific Reports*, 15, 27798. https://doi.org/10.1038/s41598-025-12554-x

Hu, S., Zhong, Y., Gao, M., Wang, W., Dong, H., Liang, X., Li, Z., Chang, X., & Yang, Y. (2023). MARLlib: A scalable and efficient multi-agent reinforcement learning library. *Journal of Machine Learning Research*, 24(315), 1–23. https://www.jmlr.org/papers/v24/23-0378.html

Iqbal, S., & Sha, F. (2019). Actor-Attention-Critic for multi-agent reinforcement learning. En *Proceedings of the 36th International Conference on Machine Learning* (PMLR 97, pp. 2961–2970). https://proceedings.mlr.press/v97/iqbal19a.html

Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Yang, Y. (2021). Trust region policy optimisation in multi-agent reinforcement learning. arXiv. https://arxiv.org/abs/2109.11251

Liu, Y., Zhang, Q., & Guo, Y. (2022). Multi-agent deep reinforcement learning for building energy system with renewable energy. *Applied Energy*, 313, 118703. https://doi.org/10.1016/j.apenergy.2022.118703

Lowe, R., Wu, Y., Tamar, A., Harb, J., Abbeel, P., & Mordatch, I. (2017). Multi-agent actor-critic for mixed cooperative-competitive environments. En *Advances in Neural Information Processing Systems 30* (pp. 6382–6393). https://proceedings.neurips.cc/paper/2017/hash/68a9750337a418a86fe06c1991a1d64c-Abstract.html

Lund, H., Østergaard, P. A., Connolly, D., & Mathiesen, B. V. (2017). Smart energy and smart energy systems. *Energy*, 137, 556–565. https://doi.org/10.1016/j.energy.2016.12.003

Ma, Q., Ye, Y., Liu, Z., Liu, X., & Strbac, G. (2025). Carbon cap based multi-energy sharing among heterogeneous microgrids using multi-agent safe reinforcement learning method with credit assignment and sequential update. *Applied Energy*, 393, 126018. https://doi.org/10.1016/j.apenergy.2025.126018

MINAM. (2019). *INFOCARBONO — RAGEI 2019 Energía*. Ministerio del Ambiente del Perú. https://infocarbono.minam.gob.pe/

Nweye, K., Kaspar, R., Manweiler, A., Kalbfleisch, M., Amara, N., & Nagy, Z. (2024). CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities. *Journal of Building Performance Simulation*, 18(1). https://doi.org/10.1080/19401493.2024.2418813

Nweye, K., Liu, B., Stone, P., & Nagy, Z. (2022). Real-world challenges for multi-agent reinforcement learning in grid-interactive buildings. *Energy and AI*. https://doi.org/10.1016/j.egyai.2022.100202

Nweye, K., & Nagy, Z. (2024b). Applications in CityLearn Gym environment for multi-objective control benchmarking in grid-interactive buildings and districts. arXiv. https://arxiv.org/abs/2408.15170

Nweye, K., Kaspar, K., Buscemi, G., Pinto, G., Li, H., Hong, T., Ouf, M., Capozzoli, A., & Nagy, Z. (2023c). CityLearn v2: An OpenAI Gym environment for demand response control benchmarking in grid-interactive communities. En *Proceedings of the 10th ACM International Conference on Systems for Energy-Efficient Buildings, Cities, and Transportation* (BuildSys '23). ACM. https://doi.org/10.1145/3600100.3626257

Oliehoek, F. A., & Amato, C. (2016). *A concise introduction to decentralized POMDPs*. Springer. https://doi.org/10.1007/978-3-319-28929-8

Ren, J., Gao, H., Wang, S., Zhao, L., Kang, Q., Ashan, A., Sun, Y., & Xiao, G. (2025). Multi-agent reinforcement learning-based joint design of low-carbon P2P market and bidding strategy in microgrids. arXiv. https://arxiv.org/abs/2604.02728

Sarkar, S., Naug, A., Luna, R., Guillen, A., Gundecha, V., Ghorbanpour, S., Mousavi, S., Markovikj, D., & Babu, A. R. (2024). Carbon footprint reduction for sustainable data centers in real-time. En *Proceedings of the AAAI Conference on Artificial Intelligence*, 38. https://arxiv.org/abs/2403.14092

Sutton, R. S., & Barto, A. G. (2018). *Reinforcement learning: An introduction* (2.ª ed.). MIT Press.

Vázquez-Canteli, J. R., & Nagy, Z. (2019a). CityLearn v1.0: An OpenAI Gym environment for demand response with deep reinforcement learning. En *Proceedings of the 6th ACM International Conference on Systems for Energy-Efficient Buildings, Cities, and Transportation* (pp. 356–357). ACM. https://doi.org/10.1145/3360322.3360998

Vázquez-Canteli, J. R., & Nagy, Z. (2019b). Reinforcement learning for demand response: A review of algorithms and modeling techniques. *Applied Energy*, 235, 1072–1089. https://doi.org/10.1016/j.apenergy.2018.11.028

Vázquez-Canteli, J. R., Dey, S., Henze, G., & Nagy, Z. (2020). CityLearn: Standardizing research in multi-agent reinforcement learning for demand response and urban energy management. arXiv. https://arxiv.org/abs/2012.10504

Xiong, S., Liu, D., Chen, Y., & Zhang, Y. (2024). A deep reinforcement learning approach based energy management strategy for home energy system considering the time-of-use price and real-time control of energy storage system. *Energy Reports*, 11, 3501–3508. https://doi.org/10.1016/j.egyr.2024.001501

Yao, Y., Wang, X., & Sun, J. (2023). Multi-agent reinforcement learning for smart community energy management. *Energies*, 17(20), 5211. https://doi.org/10.3390/en17205211

Ye, T., Huang, Y., Yang, W., Cai, G., Yang, Y., & Pan, F. (2025). Safe multi-agent deep reinforcement learning for decentralized low-carbon operation in active distribution networks and multi-microgrids. *Applied Energy*, 387. https://doi.org/10.1016/j.apenergy.2025.125339

Zhong, Y., Kuba, J. G., Feng, X., Hu, S., Ji, J., & Yang, Y. (2023). Heterogeneous-agent reinforcement learning. *Journal of Machine Learning Research*, 25. https://jmlr.org/papers/v25/23-0488.html

---

## ANEXOS

### Anexo 1 — Matriz de consistencia

| Campo | Contenido |
| --- | --- |
| Problema general | ¿Cuál es el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes? |
| PE.1 / PE.2 / PE.3 | Mejor MADRL para flexibilidad / emisiones de CO2 / costos energéticos. |
| O.G. | Determinar el mejor MADRL para la gestión coordinada de los tres ejes. |
| OE.1 / OE.2 / OE.3 | Determinar el mejor MADRL para flexibilidad / emisiones / costos. |
| Variable independiente | Capa MADRL colaborativa sobre CityLearn v2 (CityLearn v3 propuesto). |
| Variable dependiente | Desempeño del despacho óptimo bajo restricciones eléctricas y operación segura. |
| Dimensiones | Flexibilidad energética; emisiones de CO2; costos energéticos; operación segura; desempeño de aprendizaje MADRL. |
| Método | Simulación computacional no experimental con CityLearn v2 y capa CityLearn v3 propuesta. |
| Técnicas | Entrenamiento MADRL CTDE, extracción de KPIs, comparación contra baseline, Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon signed-rank. |
| Instrumentos | Scripts `train_citylearn_v3_*.py`, `objective_kpis.csv`, `axis_baseline_comparison.csv`, matrices estadísticas MADRL. |
| Resultados esperados | Caracterización/ranking de algoritmos por eje y global. |

### Anexo 2 — Matriz de operacionalización de variables

- **Variable independiente:** capa MADRL colaborativa implementada sobre CityLearn v2.
- **Variable dependiente:** desempeño del despacho óptimo bajo restricciones eléctricas y operación segura.
- **Dimensiones de la variable dependiente:** (1) flexibilidad energética; (2) emisiones de CO2; (3) costos energéticos; (4) operación segura; (5) desempeño de aprendizaje MADRL.
- **Variables de control:** dataset climático, perfil de demanda, intensidad de carbono, precio eléctrico, capacidad BESS, penetración PV, escenario de carga EV, restricciones operativas, hiperparámetros de entrenamiento.
- **Indicadores/KPIs:** flexibilidad (`peak_average`, `ramping_average`, `one_minus_load_factor_average`, autoconsumo, autosuficiencia, utilización BESS, flexibilidad EV/V2G); emisiones (`carbon_emissions` y variantes); costos (`electricity_cost` y variantes, `price_signal_deviation`); aprendizaje (recompensa media por episodio, pérdidas de actor/crítico, estabilidad).

### Anexo 3 — Matriz de antecedentes

Ver matriz bibliográfica de 50 investigaciones del workbook del skill (`outputs/thesis/madrl_citylearn_integrated_thesis_workbook.xlsx`) y la sección 2.1.

### Anexo 4 — Matriz de KPIs

Fuente: `outputs/thesis_objective_evidence/Matriz_KPIs.csv` y `matriz_kpis_tesis.csv`. Estado: definida metodológicamente, con valores observados de la sesión v4 en `scores_kpi_algoritmo_madrl.csv`.

### Anexo 5 — Arquitectura CityLearn v3 propuesta

| Componente | Ruta | Propósito | Rol en la tesis |
| --- | --- | --- | --- |
| CityLearn v2 base | `CityLearn/` | Simulador, dataset, dinámica física, edificios, DER, EV y KPIs `evaluate_v2` | Entorno base existente |
| CityLearn v3 propuesto | `CityLearn/citylearn/v3/` | Capa experimental Dec-POMDP, CTDE, OE.1/OE.2/OE.3 y wrappers MADRL | Extensión experimental propuesta |
| Adaptador de entrenamiento | `CityLearn/scripts/citylearn_v3_training_common.py` | Estandariza registros, artefactos, KPIs, figuras y tablas | Instrumento de recolección |
| Scripts MADRL | `CityLearn/scripts/train_citylearn_v3_*.py` | Ejecutan HAPPO, MASAC, MATD3 y MAAC | Intervención computacional |
| Paquete de evidencia | `CityLearn/scripts/generate_thesis_objective_evidence.py` | Consolida evidencia por objetivo específico | Puente resultados–redacción |

### Anexo 6 — Comparación de backends MADRL

Ver Tabla 5 (sección 3.2.5) y `outputs/thesis_objective_evidence/Backends_MADRL.csv`.

### Anexo 7 — Datasets y fuentes

Dataset `citylearn_iquitos_2023_2025` (17 edificios SEAI Iquitos; 222 CSV; PV 48 790,9 kWp; BESS 26 266 kWh / 6 648 kW; EV 749,4 kW). Auditorías en `outputs/dataset_audit/`. Código base CityLearn v2 y capa v3 propuesta en el repositorio.

### Anexo 8 — Configuración de hiperparámetros

Fuente: `outputs/citylearn_v3_madrl_full_20260615_074011_v4/official_full_status.json` y configs en `CityLearn/configs/`.

### Anexo 9 — Recompensa multiobjetivo

`CityLearnV3MADRLRewardFunction`; justificación en `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`.

### Anexo 10 — Resultados de simulación vigentes

Sesión `citylearn_v3_madrl_full_20260615_074011_v4` (12 corridas, `exit_code = 0`). Evidencia consolidada en `outputs/thesis_objective_evidence/`.

### Anexo 11 — Evidencias de GitHub / código

Repositorio del proyecto y submódulos `external/HARL`, `external/MARL`, `external/off-policy`, `external/MAAC`; MARLlib (Hu et al., 2023) como referencia.

### Anexo 12 — Glosario MADRL

Ver sección 2.3.

---

*Control de no invención: los valores cuantitativos provienen de archivos CSV/JSON del repositorio. Los resultados no observados se marcan como `resultado no verificado` o `pendiente`. Las afirmaciones de mejora frente al baseline se reportan solo cuando los registros las respaldan.*
