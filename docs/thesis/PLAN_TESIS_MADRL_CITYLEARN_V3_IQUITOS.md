# PLAN DE TESIS DE MAESTRÍA DE ESPECIALIZACIÓN O PROFESIONALIZANTE

> **Nota de vigencia 2026-06-06:** los valores DER/dataset vigentes para entrenamiento estan validados en `docs/INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md`, `outputs/dataset_audit/training_dataset_validation.csv` y `outputs/dataset_audit/der_sizing_audit.csv`. Si alguna tabla historica de este documento conserva 50 EV, BESS antiguos, PV anterior o estado/IDs EV antiguos, debe tratarse como referencia previa y no como fuente de entrenamiento.

---

## CARÁTULA

**Universidad:** Universidad Nacional de Ingeniería (UNI)
**Unidad de Posgrado:** [Unidad de Posgrado — por confirmar con el graduando: e.g. Sección de Posgrado FIEE o FISI]
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
5. **Lugar o institución donde se desarrolla el proyecto:** Universidad Nacional de Ingeniería (UNI) / Sistema Eléctrico Aislado de Iquitos (SEAI) — Electro Oriente S.A., Loreto, Perú.
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

La revisión bibliográfica sistemática del Módulo A comprende 50 investigaciones verificadas, organizadas en cuatro ejes temáticos alineados con los objetivos específicos de la tesis. Los antecedentes a continuación provienen de la Matriz bibliográfica MODULO_A_Matriz_50_investigaciones del proyecto. Las referencias marcadas con `[PV]` son pendientes de verificación bibliográfica completa de datos secundarios (volumen, número de página, URL definitiva).

---

**Eje 1 — Flexibilidad energética con MADRL:**

Antecedentes sobre MADRL para respuesta a la demanda, reducción de picos, desplazamiento de cargas, autoconsumo, comunidades grid-interactive, CityLearn v2 y KPIs de flexibilidad energética.

- Vázquez-Canteli y Nagy (2019a) introducen CityLearn v1.0 como entorno OpenAI Gym para evaluación estandarizada de agentes de aprendizaje por refuerzo en respuesta a la demanda multiedificio, demostrando que SAC supera al control basado en reglas con una reducción de pico de demanda de aproximadamente 20%. Este trabajo constituye la base del entorno de simulación utilizado en la tesis (Vázquez-Canteli & Nagy, 2019a).
- Vázquez-Canteli et al. (2020) extienden CityLearn para estandarizar la investigación en aprendizaje por refuerzo multiagente (MARL) para la respuesta a la demanda y la gestión energética urbana, introduciendo KPIs comparables de `peak_average`, `ramping_average` y `one_minus_load_factor_average` (Vázquez-Canteli et al., 2020).
- Nweye et al. (2024) desarrollan CityLearn v2 como entorno de simulación oficial para gestión multiagente de energía en comunidades grid-interactive. El simulador integra vehículos eléctricos (EV/V2G), intensidad de carbono dinámica, BESS, PV y control de confort de ocupantes, con un conjunto completo de KPIs de flexibilidad, CO2 y costos energéticos. Este entorno constituye la base tecnológica directa de CityLearn v3 propuesto en la tesis (Nweye et al., 2024).
- Nweye et al. (2022) identifican nueve desafíos del mundo real para el aprendizaje por refuerzo multiagente (MARL) en edificios grid-interactive, incluyendo generalización, escalabilidad, seguridad, observabilidad parcial y no-estacionariedad. Este trabajo motiva la formulación Dec-POMDP adoptada en la tesis (Nweye et al., 2022).
- Nweye et al. (2023a) desarrollan MERLIN, el primer sistema de MARL offline y por transferencia para la operación centrada en ocupantes de comunidades grid-interactive de 17 edificios reales, demostrando la viabilidad del control multiagente en comunidades de escala equivalente al SEAI Iquitos (Nweye et al., 2023a).
- Nweye et al. (2023b) evalúan HAPPO (HARL) para la gestión energética heterogénea en comunidades grid-interactive usando CityLearn, siendo el primer estudio que aplica HAPPO en este entorno y a escala de 17 edificios heterogéneos comparable al SEAI Iquitos (Nweye et al., 2023b).
- Yao et al. (2023) proponen LSD-MADDPG, un framework MARL de estrategia local descentralizada para la gestión energética coordinada en comunidades inteligentes con PV, BESS y EV, obteniendo reducciones de pico de ~15% y de costo de ~18% frente a agentes no cooperativos (Yao et al., 2023).
- Xie et al. (2023) demuestran que un mecanismo de atención en MARL para respuesta a la demanda en edificios grid-responsive supera a MADDPG en coordinación DR con una mejora de ~25%, validando el enfoque del backend MAAC de la tesis (Xie et al., 2023).
- Hribar et al. (2025) demuestran que MADRL mejora la autonomía energética de distritos de energía positiva (PED) europeos con PV, BESS y EV en ~20% frente a control basado en reglas, validando el enfoque multiagente cooperativo para comunidades con DER en sistemas con alta penetración renovable (Hribar et al., 2025).
- Nweye et al. (2024b) presentan un benchmark multiobjetivo en el entorno CityLearn Gymnasium para control de edificios grid-interactive, estableciendo métricas comparables para evaluación de algoritmos de control en comunidades inteligentes [PV — verificar datos completos de publicación] (Nweye & Nagy, 2024b).
- Kathirgamanathan et al. (2020) proponen un enfoque SAC centralizado para la gestión de la respuesta a la demanda en distritos a través de CityLearn, demostrando la viabilidad de las políticas centralizadas para optimización de flexibilidad energética (Kathirgamanathan et al., 2020).
- Felicetti et al. (2024) combinan programación entera y aprendizaje por refuerzo para la maximización del autoconsumo y el recorte de picos en sistemas con almacenamiento de energía, obteniendo resultados relevantes para los KPIs de OE.1 de la tesis [PV] (Felicetti et al., 2024).
- Li et al. (2024) presentan un enfoque de aprendizaje por refuerzo profundo para la programación en línea de sistemas PV con BESS, con resultados aplicables a la optimización de autoconsumo en el contexto del SEAI Iquitos [PV] (Li et al., 2024).
- Zhao et al. (2024) proponen un framework MARL seguro para la gestión de edificios inteligentes en redes de distribución, con aplicación directa a los KPIs de flexibilidad y costos energéticos (OE.1/OE.3) de la tesis [PV] (Zhao et al., 2024).
- Wu et al. (2025) presentan un enfoque MARL basado en datos para control de voltaje bajo Dec-POMDP en redes eléctricas débiles, validando la formulación Dec-POMDP para sistemas eléctricos con restricciones de observabilidad [PV] (Wu et al., 2025).

---

**Eje 2 — Reducción de emisiones de CO2 con MADRL:**

Antecedentes sobre MADRL consciente de la intensidad de carbono, reducción de emisiones de CO2 en escenarios multiedificio, respuesta a la demanda baja en carbono y métricas de consumo ponderado por emisiones.

- Liu et al. (2022) proponen MADDPG para la gestión coordinada de sistemas energéticos con renovables en edificios con PV y BESS en China, logrando una reducción de costos de ~20% y de emisiones de CO2 de ~15% frente a control basado en reglas. Este antecedente es relevante para los ejes OE.2 y OE.3 de la tesis (Liu et al., 2022).
- Hribar et al. (2025) incluyen la reducción de emisiones de CO2 como KPI primario en la evaluación de MADRL para distritos de energía positiva, con mejoras de autonomía energética directamente correlacionadas con la reducción de carbono en el sistema (Hribar et al., 2025).
- Ye, T. et al. (2025) proponen un MADRL seguro para operación de baja emisión de carbono en redes de distribución activas y multi-microgrids, estableciendo restricciones de seguridad en el marco de optimización para reducción de CO2, con aplicabilidad directa al SEAI Iquitos con factor de emisión 0.790 kgCO2/kWh [PV] (Ye, T. et al., 2025).
- Sarkar et al. (2024) desarrollan un sistema en tiempo real para la reducción de la huella de carbono en centros de datos mediante MARL, con técnicas de desplazamiento de carga temporal hacia períodos de baja intensidad de carbono directamente transferibles al OE.2 de la tesis [PV] (Sarkar et al., 2024).
- Ahmed et al. (2025) proponen un framework MARL para la integración óptima de fuentes de energía renovable distribuida con baja emisión de CO2, con aplicabilidad al SEAI Iquitos dado su creciente penetración solar [PV] (Ahmed et al., 2025).
- Ren et al. (2025) proponen MARL para el diseño conjunto de mercados P2P de baja emisión y estrategias de pujas en microgrids, integrando restricciones de carbono en la función de recompensa cooperativa [PV] (Ren et al., 2025).
- Ma et al. (2025) presentan un MARL seguro para el intercambio de energía entre microgrids heterogéneos bajo restricciones de cap de carbono, relevante para el OE.2 de la tesis dado el contexto del SEAI Iquitos con factor de emisión del sistema diésel aislado [PV] (Ma et al., 2025).
- Shojaeighadikolaei et al. (2022) presentan un framework MADRL para la gestión distribuida de energía y la respuesta a la demanda en smart grids, con reducción de costos de ~22% frente a configuraciones no cooperativas y métricas indirectas de emisiones aplicables a OE.2 (Shojaeighadikolaei et al., 2022).
- Multiagent reinforcement learning para la integración óptima de fuentes de energía renovable distribuida aborda la reducción de emisiones en sistemas con alta penetración solar, condición directamente extrapolable al SEAI Iquitos donde la penetración solar llega a ~15% [PV] (Ahmed et al., 2025).

---

**Eje 3 — Optimización de costos energéticos con MADRL:**

Antecedentes sobre optimización de costos eléctricos con MADRL, respuesta a precios dinámicos, estrategias de tarifas por uso horario y KPIs de costos en comunidades inteligentes.

- Yao et al. (2023) obtienen una reducción de costo de ~18% con LSD-MADDPG frente a agentes no cooperativos en comunidades inteligentes con tarifas dinámicas, validando el enfoque cooperativo para OE.3 (Yao et al., 2023).
- Liu et al. (2022) demuestran que MADDPG reduce costos energéticos en ~20% en edificios con PV y BESS, con función de recompensa que integra costo y emisiones de CO2 de forma multiobjetivo (Liu et al., 2022).
- Shojaeighadikolaei et al. (2022) obtienen reducciones de costo operacional de ~22% frente a configuraciones no cooperativas en smart grids, validando el esquema CTDE para respuesta coordinada a precios dinámicos (Shojaeighadikolaei et al., 2022).
- Fang et al. (2021) proponen MARL para la gestión de energía distribuida y la optimización de estrategias en mercados de microgrids, con KPIs de costo eléctrico y respuesta a precios aplicables a OE.3 [PV] (Fang et al., 2021).
- Shojaeighadikolaei et al. (2024) realizan una evaluación comparativa de MARL centralizado versus descentralizado para redes de carga EV, identificando los trade-offs entre coordinación global y escalabilidad local en contextos de tarifas por uso horario (Shojaeighadikolaei et al., 2024).
- Zhang, Y. et al. (2023) proponen DRL jerárquico para coordinación V2G multiagente con condicionamiento de baterías, relevante para los cargadores EV del dataset `citylearn_iquitos_2023_2025` (185 tomas controlables, 96 unidades físicas Mode 3, 749.4 kW) (Zhang, Y. et al., 2023).
- Kim et al. (2025) proponen MARL para respuesta a la demanda residencial de electrodomésticos bajo incertidumbre de precio y solar, con validación en escenarios de tarifas por uso horario directamente aplicables al contexto tarifario del SEAI Iquitos ($0.38/kWh punta, $0.26/kWh fuera punta) [PV] (Kim et al., 2025).
- Xiong et al. (2024) presentan DRL para gestión de sistemas de energía doméstica (HEMS) con tarifa TOU y control de BESS en tiempo real, con resultados de reducción de costos relevantes para la estructura tarifaria del SEAI Iquitos ($0.38/kWh punta, $0.26/kWh fuera punta) (Xiong et al., 2024).
- Rezazadeh y Bartzoudis (2022) proponen DRL federado para control de energía en micro-grids inteligentes con privacidad de datos, técnica extrapolable a escenarios de respuesta a la demanda distribuida con restricciones de privacidad [PV] (Rezazadeh & Bartzoudis, 2022).
- Gao et al. (2023) proponen un algoritmo MASAC multi-microgrid mejorado para la programación colaborativa de optimización con respuesta a precios, publicado en Energies 16(7), 3248, validando MASAC como backend adecuado para optimización de costos cooperativos en OE.3 (Gao et al., 2023).
- Wang et al. (2025) realizan una evaluación de MARL cooperativo para gestión de carga EV con conciencia de la red, con KPIs de costo eléctrico y pico de demanda aplicables a OE.1 y OE.3 de la tesis [PV] (Wang et al., 2025).
- Chen et al. (2025) proponen MADRL para gestión segura de energía en edificios inteligentes con restricciones probabilísticas, integrando control de costos y confort en la función de recompensa cooperativa [PV] (Chen et al., 2025).

---

**Eje transversal — Marco técnico MADRL:**

- Lowe et al. (2017) introducen MADDPG con el esquema CTDE (Centralized Training, Decentralized Execution) para entornos cooperativos-competitivos, estableciendo el paradigma base de todos los backends de la tesis: HAPPO, MASAC, MATD3 y MAAC. Su demostración de que el crítico centralizado con estado global y la política descentralizada basada en observaciones locales mejoran la coordinación en entornos multiagente fundamenta el diseño de CityLearn v3 propuesto (Lowe et al., 2017).
- Oliehoek y Amato (2016) proveen el marco teórico del Dec-POMDP (Decentralized Partially Observable Markov Decision Process) —definido formalmente como la tupla ⟨S, A₁,…,Aₙ, T, R, O₁,…,Oₙ, Z⟩— que constituye el modelo formal de la tesis para la toma de decisiones cooperativa descentralizada bajo observabilidad parcial (Oliehoek & Amato, 2016).
- Kuba et al. (2021) presentan HAPPO (Heterogeneous-Agent Proximal Policy Optimization) con garantías de mejora monótona para agentes heterogéneos bajo el esquema CTDE, implementado en el repositorio HARL. HAPPO supera a MAPPO e IPPO en ~85% de las tareas MARL benchmark y es el primer algoritmo MARL on-policy con garantías teóricas para heterogeneidad de agentes (Kuba et al., 2021).
- Iqbal y Sha (2019) introducen MAAC (Multi-Agent Actor-Critic with Attention) con mecanismo de atención multi-cabeza en el crítico centralizado, permitiendo coordinación selectiva entre los 17 agentes del SEAI Iquitos. MAAC supera a MADDPG y COMA con mejoras de recompensa de ~15-30% en entornos cooperativos (Iqbal & Sha, 2019).
- Hu et al. (2023) presentan MARLlib como biblioteca escalable y eficiente de aprendizaje por refuerzo multiagente compatible con Ray/RLlib, unificando más de 20 algoritmos incluyendo HAPPO, MAAC, MADDPG y otros bajo una interfaz estandarizada. MARLlib se usa como referencia técnica de integración en la tesis (Hu et al., 2023).
- Akiba et al. (2019) presentan Optuna como framework de optimización automática de hiperparámetros (HPO) con API define-by-run basada en TPE (Tree-structured Parzen Estimator), que se usa en la tesis para ajustar los hiperparámetros de los cuatro backends MADRL (Akiba et al., 2019).
- Sutton y Barto (2018) proveen el marco teórico fundamental del aprendizaje por refuerzo (RL) como base conceptual de todos los algoritmos DRL y MADRL evaluados en la tesis (Sutton & Barto, 2018).
- Haarnoja et al. (2018) proponen SAC (Soft Actor-Critic) con maximización de entropía como algoritmo off-policy de referencia, base conceptual de los backends MASAC y MAAC evaluados en la tesis (Haarnoja et al., 2018).
- Nweye et al. (2023b) evalúan HAPPO (HARL) en comunidades grid-interactive heterogéneas usando CityLearn, siendo el primer antecedente directo del backend HAPPO de la tesis aplicado al entorno base CityLearn con 17 edificios heterogéneos (Nweye et al., 2023b).
- Gao et al. (2023) proponen un algoritmo MASAC multiagente mejorado para la programación colaborativa de múltiples microgrids, validando MASAC como backend adecuado para escenarios cooperativos de gestión energética (Gao et al., 2023).
- Oliehoek et al. (2013) presentan un algoritmo de clústering incremental para planificación óptima más rápida en Dec-POMDPs, estableciendo la complejidad computacional y los límites teóricos del modelo formal utilizado en la tesis (Oliehoek et al., 2013).
- Vázquez-Canteli y Nagy (2019b) realizan una revisión sistemática de algoritmos de aprendizaje por refuerzo y técnicas de modelado para la respuesta a la demanda en edificios, identificando la coordinación multiagente como el principal desafío abierto, directamente motivador del presente trabajo (Vázquez-Canteli & Nagy, 2019b).
- Zhu et al. (2024) presentan una revisión de los mecanismos de atención en aprendizaje por refuerzo multiagente, validando el mecanismo de atención del backend MAAC como estado del arte en coordinación selectiva entre agentes (Zhu et al., 2024).
- Dolatyabi et al. (2025) presentan un enfoque con HAPPO heterogéneo para el restablecimiento de sistemas de distribución de potencia, demostrando que HAPPO supera a PPO, QMIX y Mean-Field RL en restauración de carga en sistemas eléctricos bajo restricciones operativas similares al SEAI Iquitos [PV-parcial: verificar coautores] (Dolatyabi et al., 2025).
- Wang et al. (2022) evalúan MARL cooperativo para la integración óptima de redes eléctricas con fuentes renovables distribuidas, relevante para el contexto de generación PV del SEAI Iquitos [PV] (Wang et al., 2022).
- Chen et al. (2024b) proponen DRL bi-nivel para sistemas de energía integrados con EVs como almacenamiento móvil, relevante para la función EV/V2G del dataset `citylearn_iquitos_2023_2025` con 185 tomas controlables, 96 unidades físicas Mode 3 y 749.4 kW instalados (Chen et al., 2024b).
- Chen, X. et al. (2024) proponen MARL con restricciones SOC y degradación de batería para coordinación jerárquica de múltiples agregados EV entre múltiples partes interesadas, con resultados de control EV directamente aplicables a los cargadores del dataset Iquitos (Chen, X. et al., 2024).
- Zhong et al. (2023) presentan HARL v2 con mejora monótona extendida para algoritmos heterogéneos, validando la aplicabilidad de HAPPO a escenarios de 17 agentes heterogéneos [PV] (Zhong et al., 2023).

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

**MASAC (Multi-Agent Soft Actor-Critic con QMIX):** Algoritmo off-policy que combina SAC con redes RNN para observaciones parciales y QMIX como función de mezcla cooperativa. Implementado en el repositorio MARL/src (Wang et al., 2022 [PV-parcial — verificar referencia completa del artículo MASAC: Wang, J. et al., 2022]).

**MATD3 (Multi-Agent Twin Delayed Deep Deterministic Policy Gradient):** Algoritmo off-policy con doble crítico centralizado para reducir sobreestimación del valor. Backend PyTorch implementado en marlbenchmark/off-policy (Li et al., 2021 [PV]).

**MAAC (Multi-Agent Actor-Critic with Attention):** Algoritmo off-policy con mecanismo de atención multi-cabeza que selecciona dinámicamente qué agentes observar al calcular el valor de acción. Permite coordinación selectiva entre los 17 edificios (Iqbal & Sha, 2019 [PV]).

**MARLlib:** Biblioteca unificada de algoritmos MARL/MADRL compatible con Ray/RLlib 1.8.0, Gymnasium y PettingZoo. Se usa como referencia técnica de integración y adaptador de entorno (Hu et al., 2021 [PV]).

**CityLearn v2:** Entorno de simulación de código abierto para gestión energética multiagente en edificios grid-interactive. Provee datasets, física de edificios, DER, EVs, señales de carbono y precios, y KPIs estandarizados (Nweye et al., 2025 [PV]).

**CityLearn v3 propuesto:** Extensión experimental de tesis implementada sobre CityLearn v2. Agrega la formulación como Dec-POMDP ℳ = ⟨𝒮, {𝒜ᵢ}ᵢ₌₁¹⁷, 𝒯, R, {𝒪ᵢ}ᵢ₌₁¹⁷, Ω, γ=0.99, T=8,760⟩ con estado global 𝒮 ⊆ ℝ^(~680), observaciones locales 𝒪ᵢ ⊆ ℝ^(~40) por edificio y espacio de acción 𝒜ᵢ ⊆ ℝ^(2-5) para control de HVAC, BESS y EV. Implementa el esquema CTDE (Lowe et al., 2017) con crítico centralizado Qᵢ(s, a₁,…,a₁₇) durante entrenamiento y política local πᵢ(aᵢ|oᵢ) durante ejecución. Incorpora la función de recompensa multiobjetivo cooperativa `CityLearnV3MADRLRewardFunction` con tres ejes ponderados (flex, carbon, cost) más componente EV, con team_reward = (1/N) Σᵢ reward_i para alineación cooperativa. Los escenarios de entrenamiento E1/E2/E3 establecen pesos de eje [0.70,0.15,0.15], [0.15,0.70,0.15] y [0.25,0.15,0.60] respectivamente. Los adaptadores de entorno (CityLearnHARLEnv, CityLearnSMACDiscreteEnv, CityLearnOffPolicyVecEnv, CityLearnMAACVecEnv) conectan con los cuatro backends MADRL. La arquitectura completa se formaliza en las secciones 4.10-4.12 del presente plan. No constituye una versión oficial de CityLearn (Nweye et al., 2024).

**Dataset citylearn_iquitos_2023_2025:** Dataset de tesis construido desde datos primarios mediante la orquestacion vigente descrita en la sección 4.9. Cubre 17 edificios institucionales/comerciales reales del SEAI Iquitos actualizados desde `CityLearn/data/buildingcsv/building.csv`: Electro Oriente S.A., Municipalidad Distrital San Juan Bautista, Aeropuerto Internacional de Iquitos, Hipermercados Tottus Oriente, Hotel Plaza S.A., Mall Aventura Iquitos, UNAP Facultad de Biologia, PNP Escuela Tecnica Superior Iquitos, Gobierno Regional Loreto COER, Gobierno Regional de Loreto, Hospital Regional de Loreto, Seguro Social de Salud EsSalud, UNAP Facultad de Ciencias Economicas, Autoridad Portuaria Nacional Iquitos, DREL Colegio Nacional de Iquitos, SIMA Iquitos S.R.Ltda y Asociacion Civil Selva Amazonica. El dataset contiene 26,304 horas (2023-2025), 222 CSV auditados, 185 cargadores EV, 96 equipos fisicos modo 3, 17 maquinas controladas, BESS dimensionado por balance PV/EV/red/cargas con 26,266 kWh y 6,648 kW totales, generación PV modelada con pvlib/PVGIS TMY con 48,790.9 kWp totales, e intensidad de carbono CI ∈ [0.6715, 0.7900] kgCO₂/kWh calibrada con datos de Electro Oriente S.A. y MINAM RAGEI 2019. Datos meteorológicos: PVGIS-ERA5/PVGIS TMY y NASA POWER, ubicación: lat=-3.7491°, lon=-73.2538°. Precios horarios vigentes: 0.383220954-1.066918914 en `pricing.csv`. La auditoria vigente reporta 0 NaN, 0 Inf y ausencia de cargadores/maquinas huerfanos.

**Optuna:** Framework de optimización automática de hiperparámetros (HPO) basado en TPE (Tree-structured Parzen Estimator). Se utiliza para ajustar los hiperparámetros de cada backend MADRL (Akiba et al., 2019).

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

### 4.9 Construcción del Dataset `citylearn_iquitos_2023_2025`

El dataset de tesis es construido íntegramente desde datos primarios mediante el script `tools/generate_iquitos_dataset.py`. No se adoptan datasets pre-existentes de CityLearn v2 (e.g., EULP USA) porque el SEAI Iquitos posee condiciones irrepresentables en esos datasets: sistema eléctrico aislado, generación diésel dominante, factor de emisión 0.790 kgCO₂/kWh, clima ecuatorial sin calefacción y tarifas TOU locales de Electro Oriente S.A.

#### 4.9.1 Los 17 Edificios del SEAI Iquitos

Los 17 edificios institucionales y comerciales reales de Iquitos (Loreto, Perú) constituyen los agentes del sistema multiagente. Sus nombres completos, tipos y áreas son los siguientes, conforme al levantamiento in situ y los registros de facturación de Electro Oriente S.A. (2023-2025):

| ID | Edificio actual | Tipo CityLearn | Area m2 | PV kWp | BESS kWh | BESS kW | EV kW | Cargadores EV | Carga controlada MWh |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| B01 | ELECTRO ORIENTE S.A. | Office | 14,000.00 | 3,360.2 | 6,747.0 | 1,609.0 | 21.8 | 4 | 11.6 |
| B02 | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | Office | 8,000.00 | 1,920.0 | 244.0 | 50.0 | 24.4 | 6 | 27.9 |
| B03 | AEROPUERTO INTERNACIONAL | Assembly | 6,000.00 | 1,440.2 | 2,363.0 | 511.0 | 37.8 | 8 | 104.1 |
| B04 | HIPERMERCADOS TOTTUS ORIENTE SAC | Retail | 2,500.00 | 600.2 | 454.0 | 409.0 | 24.4 | 6 | 24.3 |
| B05 | HOTEL PLAZA S.A. | MultiFamily_Hotel | 1,141.89 | 274.1 | 234.0 | 124.0 | 14.4 | 3 | 108.5 |
| B06 | MALL AVENTURA S.A. | Commercial_Mall | 20,637.00 | 4,952.9 | 2,541.0 | 835.0 | 119.6 | 32 | 192.9 |
| B07 | UNAP-FACULTAD DE BIOLOGIA-AULAS | Education | 8,103.45 | 1,944.9 | 984.0 | 240.0 | 153.2 | 42 | 30.7 |
| B08 | PNP- ESCUELA TECNICA SUPERIOR-IQUITOS | Assembly_Military | 21,000.00 | 5,040.2 | 601.0 | 129.0 | 73.6 | 17 | 77.8 |
| B09 | GOBIERNO REGIONAL DE LORETO - COER | Office_Critical | 4,479.67 | 1,075.3 | 138.0 | 30.0 | 37.4 | 10 | 13.3 |
| B10 | GOBIERNO REGIONAL DE LORETO | Office | 14,295.73 | 3,431.1 | 2,353.0 | 591.0 | 36.6 | 6 | 17.4 |
| B11 | HOSPITAL REGIONAL DE LORETO | Healthcare_Hospital | 42,649.33 | 10,236.1 | 1,901.0 | 424.0 | 14.4 | 3 | 80.0 |
| B12 | SEGURO SOCIAL DE SALUD - ESSALUD | Healthcare | 18,197.48 | 4,367.5 | 4,346.0 | 960.0 | 14.4 | 3 | 37.8 |
| B13 | UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO | Education | 2,723.00 | 653.8 | 272.0 | 69.0 | 41.4 | 11 | 11.6 |
| B14 | AUTORIDAD PORTUARIA NACIONAL | Industrial_Port | 17,761.00 | 4,262.9 | 229.0 | 48.0 | 21.8 | 4 | 51.5 |
| B15 | DREL- COLEGIO NACIONAL DE IQUITOS | Education | 9,889.92 | 2,373.8 | 500.0 | 104.0 | 31.4 | 8 | 18.3 |
| B16 | SIMA - IQUITOS S.R.LTDA | Industrial | 10,294.00 | 2,470.8 | 1,622.0 | 357.0 | 41.4 | 11 | 40.1 |
| B17 | ASOCIACION CIVIL SELVA AMAZONICA | Laboratory | 1,611.23 | 386.9 | 737.0 | 158.0 | 41.4 | 11 | 28.8 |

Totales vigentes auditados: PV=48,790.9 kWp; BESS=26,266.0 kWh / 6,648.0 kW; EV=185 cargadores / 749.4 kW; carga controlada=876.6 MWh.

Los edificios heterogéneos incluyen tipos de ocupación 24h (hospitales, hoteles, aeropuerto), horarios diurnos (educación, administración), usos industriales y deportivos. Esta heterogeneidad es un prerrequisito para la formulación Dec-POMDP del sistema multiagente y para justificar el uso de HAPPO (diseñado específicamente para agentes heterogéneos según Kuba et al., 2021).

#### 4.9.2 Flota de Vehículos Eléctricos y Cargadores (185 tomas controlables)

El dataset incorpora 185 tomas EV controlables distribuidas en los 17 edificios. El dimensionamiento vigente se calcula por edificio con área EV-ready, demanda de movilidad, afluencia diaria, permanencia, utilización objetivo y ventana operacional de recarga. La infraestructura física queda representada por 96 unidades Mode 3 con 192 sockets y 749.4 kW instalados. La asignación final se toma de `outputs/dataset_audit/ev_charger_sizing_audit.csv`, `outputs/dataset_audit/der_sizing_audit.csv` y del `schema.json` activo.

**Tiempos de carga Mode 3 validados:** motolineal ~80 min (3.2 kWh ÷ 2.76 kW efectivo × 1.15 taper), mototaxi ~1.2 h (carga parcial 35→82% SOC), camioneta ~2.0 h (50→85% SOC, 14 kWh ÷ 7.03 kW efectivo).

| B# | Edificio | Tomas controlables | Unidades Mode 3 | Sockets | Potencia EV kW | Uso área EV-ready |
|---|---|---:|---:|---:|---:|---:|
| B01 | Electro Oriente S.A. | 4 | 2 | 4 | 21.8 | 24.7% |
| B02 | Municipalidad Distrital San Juan Bautista | 6 | 3 | 6 | 24.4 | 29.3% |
| B03 | Aeropuerto Internacional de Iquitos | 8 | 4 | 8 | 37.8 | 7.4% |
| B04 | Hipermercados Tottus Oriente | 6 | 3 | 6 | 24.4 | 9.5% |
| B05 | Hotel Plaza S.A. | 3 | 2 | 4 | 14.4 | 97.2% |
| B06 | Mall Aventura Iquitos | 32 | 16 | 32 | 119.6 | 10.1% |
| B07 | UNAP Facultad de Biologia | 42 | 21 | 42 | 153.2 | 57.1% |
| B08 | PNP Escuela Tecnica Superior Iquitos | 17 | 9 | 18 | 73.6 | 16.4% |
| B09 | Gobierno Regional Loreto COER | 10 | 5 | 10 | 37.4 | 23.1% |
| B10 | Gobierno Regional de Loreto | 6 | 3 | 6 | 36.6 | 24.4% |
| B11 | Hospital Regional de Loreto | 3 | 2 | 4 | 14.4 | 3.2% |
| B12 | Seguro Social de Salud EsSalud | 3 | 2 | 4 | 14.4 | 7.3% |
| B13 | UNAP Facultad de Ciencias Economicas | 11 | 6 | 12 | 41.4 | 35.9% |
| B14 | Autoridad Portuaria Nacional Iquitos | 4 | 2 | 4 | 21.8 | 8.9% |
| B15 | DREL Colegio Nacional de Iquitos | 8 | 4 | 8 | 31.4 | 26.1% |
| B16 | SIMA Iquitos S.R.Ltda | 11 | 6 | 12 | 41.4 | 6.4% |
| B17 | Asociacion Civil Selva Amazonica | 11 | 6 | 12 | 41.4 | 8.0% |
| **Total vigente auditado** | 17 edificios | **185** | **96** | **192** | **749.4** | |

**Potencia EV vigente:** 749.4 kW instalados en 185 tomas controlables. La asignacion final se toma de `outputs/dataset_audit/ev_charger_sizing_audit.csv` y del `schema.json` activo, no de tablas preliminares.

#### 4.9.3 Fuentes de Datos de Entrada

La construcción del dataset integra tres categorías de datos:

**a) Datos meteorológicos horarios (2023-2025):**
- **2023**: PVGIS-ERA5 obtenido mediante la librería `pvlib` (Joint Research Centre, Comisión Europea). Variables: temperatura exterior (T2M), humedad relativa (RH2M), irradiancia solar difusa y directa, velocidad del viento (WS10M).
- **2024-2025**: NASA POWER REST API (NASA Langley Research Center). Mismas variables, misma ubicación: lat = −3.7491°, lon = −73.2538°, altitud = 106 m s.n.m., zona horaria America/Lima.
- Caché local: `.cache/weather/{year}.parquet` para reproducibilidad y eficiencia.

**b) Datos de consumo energético real:**
- Mediciones mensuales de facturación eléctrica de Electro Oriente S.A. (2023-2025) para los 17 edificios.
- Proceso de destilación (distillation) mediante `tools/distill_building_loads.py`: los perfiles mensuales se destilan en perfiles horarios sintéticos que preservan la magnitud real de la energía consumida y reproducen el patrón de demanda horaria y semanal de cada tipo de edificio.

**c) Señales regulatorias y de mercado:**
- **Intensidad de carbono**: calculada a partir del factor de emisión del sistema diésel del SEAI según MINAM RAGEI 2019 (0.790 kgCO₂/kWh), con modulación solar: CI[t] = 0.790 × (1 − 0.15 × GHI[t]/1,000) kgCO₂/kWh. Rango: 0.672–0.790 kgCO₂/kWh.
- **Precios eléctricos TOU**: Electro Oriente S.A. (2024). Tarifa punta (18:00–22:59): 0.38 USD/kWh; tarifa fuera de punta: 0.26 USD/kWh. Diferencia punta/fuera punta: 46%.

#### 4.9.4 Pipeline de Construcción (10 Etapas Secuenciales)

El proceso de construcción del dataset sigue 10 etapas implementadas en `tools/generate_iquitos_dataset.py`, ejecutadas de forma reproducible con control de semilla y validación en cada etapa:

**Etapa 1 — Descarga de datos meteorológicos.** Se descarga la serie horaria de 26,304 filas (2023-2025) desde PVGIS-ERA5 (2023) y NASA POWER (2024-2025). Los datos se almacenan en caché `.cache/weather/{year}.parquet` para garantizar reproducibilidad. La ubicación geográfica exacta es: lat = −3.7491°, lon = −73.2538°, tz = America/Lima, alt = 106 m.

**Etapa 2 — Selección del módulo fotovoltaico Sandia.** La clase `SandiaModelSelector` filtra módulos PV de la base de datos Sandia con criterios adaptados al clima tropical ecuatorial: eficiencia ≥ 18%, área unitaria 1.7–2.6 m², Pmp ≥ 300 W. El montaje es fijo: inclinación = 5°, azimuth = 0° (norte, hemisferio sur). El modelo térmico SAPM `open_rack_glass_glass` representa las condiciones tropicales de Iquitos. Se aplica restricción eléctrica IEC 61730: máximo 20 módulos por string para Voc ≤ 1,000 V. Factor de área útil de techo = 0.63 (0.70 × 0.90).

**Etapa 3 — Generación de la serie solar PV por edificio.** Se utiliza `pvlib.ModelChain` con el modelo SAPM para cada uno de los 17 edificios, calculando la potencia AC generada en cada paso horario. La generación típica en Iquitos es 4.2–4.8 kWh/kWp/día, con pérdida térmica de −3% a −5% respecto a STC (temperatura de celda ~32°C en condiciones de operación).

**Etapa 4 — Dimensionamiento del BESS por edificio.** Se aplica el método de balance energético acumulado de Hesse et al. (2017) con parámetros LFP: DoD = 0.80, η_carga = 0.95, η_descarga = 0.95, η_RT = 0.9025, self-discharge = 1×10⁻⁵/h, SOC₀ = 0.50, target de autoabastecimiento = 70%. La potencia nominal se fija como P_bess = max(déficit.quantile(0.99), excedente.quantile(0.99)).

**Etapa 5 — Generación de Building_X.csv.** Las clases `BuildingDataGenerator` y `DatasetValidator` producen 17 archivos con 12 columnas y 26,304 filas cada uno (formato oficial CityLearn v2): month, hour, day_type, daylight_savings_status (= 0 siempre, Perú tropical), indoor_dry_bulb_temperature, average_unmet_cooling_setpoint_difference, indoor_relative_humidity, non_shiftable_load, dhw_demand, cooling_demand, heating_demand (= 0.0 siempre), solar_generation.

**Etapa 6 — Generación y sincronizacion de 185 archivos charger_X_Y.csv.** La orquestacion ejecuta `tools/dimension_ev_chargers.py` para dimensionar cargadores EV por edificio con Peak Demand Factor, Ley de Little, afluencia diaria, permanencia, utilizacion objetivo y area EV-ready. El resultado vigente contiene 185 tomas controlables, 96 equipos fisicos modo 3, 192 sockets y 749.4 kW instalados. Cada archivo contiene 6 columnas: charger_state, vehicle_id, departure_time, required_soc_departure, estimated_arrival_time, estimated_soc_arrival.

**Etapa 7 — Generación de Washing_Machine_X.csv.** Se generan 17 archivos de maquinas controladas, uno por edificio, con 5 columnas y 26,304 filas, parametrizados por tipo de edificio.

**Etapa 8 — Generación de archivos de red (weather.csv, carbon_intensity.csv, pricing.csv).** Se producen los tres archivos de señales de red: `weather.csv` con 16 columnas (4 observadas + 12 predicciones +1h/+2h/+3h por variable); `carbon_intensity.csv` con la serie horaria de intensidad de carbono (0.672–0.790 kgCO₂/kWh); `pricing.csv` con 4 columnas (precio actual + 3 predicciones).

**Etapa 9 — Construcción y sincronizacion de schema.json.** `SchemaBuilder` y la cadena DER vigente generan el archivo de configuración del entorno CityLearn v2/v3 que referencia 17 edificios, 185 cargadores EV, 17 maquinas controladas, BESS, PV, clima, carbono y precios. Los campos `inactive_observations` e `inactive_actions` se mantienen vacíos para que los algoritmos MADRL accedan a la totalidad de señales.

**Etapa 10 — Validación con CityLearnEnv.** La clase `DatasetValidator` verifica rangos (month ∈ [1,12], hour ∈ [0,23], T_interior ∈ [15,45]°C, RH ∈ [20,100]%, cargas ≥ 0) e instancia `CityLearnEnv(schema="…/schema.json")` confirmando compatibilidad completa con CityLearn v2.

#### 4.9.5 Estructura del Dataset (222 CSV auditados, 26,304 filas)

El dataset `citylearn_iquitos_2023_2025` contiene 222 CSV auditados en el directorio `CityLearn/data/datasets/citylearn_iquitos_2023_2025/`:

| Tipo de Archivo | Cantidad | Filas | Columnas | Descripción |
|-----------------|:--------:|:-----:|:--------:|-------------|
| `Building_X.csv` | 17 | 26,304 | 12 | Perfil energético horario por edificio |
| `charger_X_Y.csv` | 185 | 26,304 | 6 | Estado horario por cargador EV |
| `weather.csv` | 1 | 26,304 | 16 | Meteorología observada + predicciones |
| `carbon_intensity.csv` | 1 | 26,304 | 1 | Intensidad de carbono horaria |
| `pricing.csv` | 1 | 26,304 | 4 | Precio eléctrico TOU + predicciones |
| `Washing_Machine_X.csv` | 17 | 26,304 | 5 | Maquina controlada por edificio |
| `schema.json` | 1 | — | — | Configuración del entorno CityLearn v2 |
| `carbon_intensity_metadata.json` | 1 | — | — | Metadatos de señal de carbono |

---

### 4.10 Arquitectura CityLearn v3 Propuesto y Formulación Dec-POMDP

CityLearn v3 propuesto es una extensión experimental sobre CityLearn v2 que implementa la capa MADRL cooperativa para el problema de gestión coordinada de comunidades inteligentes. No constituye una versión oficial del simulador. Su contribución central es la formalización del problema de gestión multiagente como un **Dec-POMDP** bajo esquema **CTDE**, con una función de recompensa multiobjetivo cooperativa.

#### 4.10.1 Formulación Dec-POMDP

El problema de gestión coordinada de los 17 edificios del SEAI Iquitos se formaliza como el Dec-POMDP:

> **ℳ = ⟨𝒮, {𝒜ᵢ}ᵢ₌₁ᴺ, 𝒯, R, {𝒪ᵢ}ᵢ₌₁ᴺ, Ω, γ, T⟩**

donde:

- **N = 17**: número de agentes (edificios del SEAI Iquitos).
- **𝒮 ⊆ ℝ^(d_s)**: espacio de estado global. d_s = Σᵢ₌₁^17 dim(oᵢ) ≈ 40 × 17 = 680 dimensiones. El estado global s = [o₁, o₂, …, o₁₇] concatena las observaciones locales de los 17 agentes y es accesible solo por el crítico centralizado durante el entrenamiento (no durante la ejecución).
- **𝒜ᵢ ⊆ ℝ^(d_aᵢ)**: espacio de acción local del edificio i. Las acciones incluyen: (a) scaling de potencia HVAC ∈ [0, 1]; (b) potencia BESS ∈ [−P_max,i, +P_max,i] kW; (c) potencia de carga EV ∈ [0, P_nominal] kW por cargador asignado al edificio i. La dimensionalidad varía de 2 (edificios educativos) a 5 (Electro Oriente S.A., B1).
- **𝒯: 𝒮 × 𝒜₁ × … × 𝒜_N → Δ(𝒮)**: función de transición estocástica. Modela la dinámica del balance energético por edificio, el modelo RC de temperatura interior, la carga/descarga BESS con eficiencia η_RT = 0.9025, y el perfil de llegada/salida EV estocástico.
- **R: 𝒮 × 𝒜₁ × … × 𝒜_N → ℝ**: función de recompensa cooperativa `CityLearnV3MADRLRewardFunction`. Scalar cooperativa: team_reward = (1/N) Σᵢ reward_i.
- **𝒪ᵢ ⊆ ℝ^(~40)**: observación local del edificio i. Incluye: 12 columnas Building_i, 4 columnas weather subset, 4 columnas pricing, 6 × n_chargers_i columnas EV, estado SOC del BESS. El edificio i no observa el estado de los demás edificios.
- **Ω**: función de observación. Mapea s → (o₁, …, o_N) de forma que oᵢ = proyección del estado sobre las variables del edificio i.
- **γ = 0.99**: factor de descuento para horizonte largo (8,760 pasos por episodio = 1 año horario de Iquitos).
- **T = 8,760**: horizonte de decisión (pasos horarios).

**Condición de observabilidad parcial estricta (Dec-POMDP válido):** La condición P(oᵢ | s, aᵢ) ≠ P(oᵢ | s, aⱼ) para i ≠ j se satisface porque cada edificio solo observa su propio estado local. El edificio i no tiene acceso a la temperatura interior, demanda, SOC del BESS ni perfil EV del edificio j durante la ejecución.

#### 4.10.2 Esquema CTDE

El esquema CTDE (Centralized Training, Decentralized Execution) de Lowe et al. (2017) organiza el aprendizaje de la siguiente forma:

- **Entrenamiento centralizado**: el crítico centralizado Qᵢ(s, a₁, …, a_N) o la función de valor V(s) de cada agente accede al estado global s = [o₁, …, o₁₇] durante el entrenamiento. Esto permite al crítico aprender a evaluar la calidad cooperativa de los perfiles de acción colectiva, corrigiendo el problema de no-estacionariedad que surge cuando cada agente aprende independientemente.
- **Ejecución descentralizada**: la política πᵢ(aᵢ | oᵢ) de cada edificio usa exclusivamente su observación local oᵢ durante la ejecución. No requiere comunicación entre edificios ni acceso al estado global.

#### 4.10.3 Clases de CityLearn v3 Propuesto

| Clase | Backend Asociado | Descripción |
|-------|-----------------|-------------|
| `CityLearnDecPOMDPEnv` | Todos (base) | Entorno Dec-POMDP; gestiona estado global y recompensa cooperativa |
| `CityLearnHARLEnv` | HAPPO (HARL) | Wrapper HARL; exporta estado global como tensor; compatible con `external/HARL` |
| `CityLearnSMACDiscreteEnv` | MASAC (MARL/src) | Wrapper SMAC; formato MARL/src con observaciones individuales + estado global |
| `CityLearnOffPolicyVecEnv` | MATD3 (marlbenchmark) | Wrapper vectorizado off-policy para MATD3 |
| `CityLearnMAACVecEnv` | MAAC (external/MAAC) | Wrapper MAAC; expone observaciones por agente para mecanismo de atención |
| `CityLearnV3MADRLRewardFunction` | Todos | Recompensa multiobjetivo: flex + CO₂ + costos + EV; hereda de `Electric_Vehicles_Reward_Function` |

#### 4.10.4 Aportes Originales al Motor de Simulación CityLearn v3 Propuesto

Como parte de las contribuciones metodológicas de esta tesis, se realizaron **cuatro extensiones originales** al motor de simulación del fork `github.com/Mac-Tapia/CityLearn.git`. Todos los cambios son **retrocompatibles** con el simulador CityLearn v2 base. Los archivos modificados son `CityLearn/citylearn/energy_model.py` y `CityLearn/citylearn/cost_function.py`. Commit de referencia: `54b1938e` (submodulo CityLearn).

| # | Aporte | Clase/Método | Modelo matemático incorporado | Justificación |
| --- | ------ | ------------ | ----------------------------- | ------------- |
| **A1** | Degradación BESS con C-rate y temperatura (Arrhenius) | `Battery.degrade(temperature_celsius=25.0)` | `ΔC = base × (C_rate)^{0.55} × exp[Ea/R × (1/T_ref − 1/T)]`, Ea=24 500 J/mol, T_ref=298.15 K | Degrada LiFePO₄ en función de temperatura y velocidad de carga; políticas MADRL aprenden ciclos más suaves en horas calurosas |
| **A2** | Corrección PV temperatura tropical (IEC 61215) | `PV.get_generation(dry_bulb_temperature, ghi)` | `T_cell = T_amb + (NOCT−20)/800 × G`; `P(T) = P_STC × [1 + γ × (T_cell − 25)]`, γ = −0.0035/°C | Iquitos T_max ≈ 35°C: paneles operan 8–12% bajo STC; mejora fidelidad física del entorno de simulación |
| **A3** | KPI pico de demanda con ventana de facturación configurable | `CostFunction.peak(billing_window_steps=1)` | Máximo rodante sub-horario antes de la agrupación diaria; `billing_window_steps=1` reproduce el original | OSINERGMIN Res. 0024-2024-OS/CD: cargo por demanda máxima en ventanas de 15 min (MT-3/MT-4, Electro Oriente S.A.) |
| **A4** | Clase `CarbonIntensityModel` para redes aisladas diesel+PV | `CarbonIntensityModel(base_ci=0.790, pv_displacement_factor=0.15)` | `CI(t) = CI_base × (1 − δ_PV × min(G(t)/1000, 1))` | Formaliza el CI dinámico del dataset Iquitos como componente del motor; reutilizable para otras redes aisladas amazónicas |

**Impacto en las políticas MADRL:**

- A1 introduce penalización implícita por degradación acelerada → agente aprende ciclos BESS más suaves en horas calurosas (E1/E3).
- A2 corrige el error sistemático de generación PV en clima tropical (3–12% derating) → episodios E1 y E3 más fieles al SEAI Iquitos.
- A3 alinea `peak_average` con la estructura tarifaria de OSINERGMIN → escenario E3 directamente comparable con facturación real.
- A4 provee el modelo de CI dinámico como clase configurable por schema → escenario E2 adaptable a otras redes aisladas peruanas.

**Documentación académica completa:** `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md` — 17 referencias bibliográficas (2019–2024), incluyendo IEC 61215-1:2021, OSINERGMIN Res. 0024-2024-OS/CD y MINAM RAGEI 2019.

---

### 4.11 Escenarios de Entrenamiento, Función de Recompensa Multiobjetivo y Pesos por Algoritmo

#### 4.11.1 Estructura de Escenarios

El experimento comparativo se organiza en **tres escenarios evaluativos** (E1, E2, E3) y un **modo global** de entrenamiento. Cada escenario se corresponde con un objetivo específico de la tesis y establece la distribución de pesos eje (w_flex, w_carbon, w_cost) en la función de recompensa:

| Escenario | Objetivo Específico | Prioridad | Pesos [flex, carbon, cost] | Eje dominante |
|-----------|--------------------|-----------|--------------------------:|---------------|
| **E1** | OE.1 — Flexibilidad energética | Reducir peak y ramping del distrito | [**0.70**, 0.15, 0.15] | Flexibilidad |
| **E2** | OE.2 — Emisiones de CO₂ | Desplazar demanda a horas de baja CI | [0.15, **0.70**, 0.15] | Carbono |
| **E3** | OE.3 — Costos energéticos | Explotar tarifa TOU punta/fuera punta | [0.25, 0.15, **0.60**] | Costos |
| **Global** | O.G. — Gestión coordinada | Balance multiobjetivo de 3 ejes | [0.50, 0.25, 0.25] | Coordinado |

#### 4.11.2 Función de Recompensa Multiobjetivo

La clase `CityLearnV3MADRLRewardFunction` calcula la recompensa de cada edificio i en el paso horario t como:

> **reward_i(t) = reward_scale × [ w_flex × flex_i(t) + w_carbon × carbon_i(t) + w_cost × cost_i(t) + w_ev × ev_i(t) ]**

**Componente de flexibilidad energética (flex_i):**

La flexibilidad se evalúa a nivel de **distrito** para capturar el efecto de coordinación. El pico de demanda y la rampa se calculan sobre la carga neta agregada de los 17 edificios:

```
peak_share(t)   = district_import(t) / N          [kWh/edificio]
ramp_share(t)   = |district_import(t) − district_import(t−1)| / N
headroom(t)     = max(0, 1 − mean_SOC(t))         [capacidad BESS disponible]
flex_penalty(t) = w_peak × tanh(peak_share/25)
                + w_ramp × tanh(ramp_share/15)
                + 0.15 × tanh(export_i × (1 + headroom)/20)
                + 0.10 × tanh(import_i × SOC_i/20)
flex_i(t)       = − flex_penalty(t)
```

**Componente de carbono (carbon_i):**

La señal de carbono opera sobre la importación de red del edificio i, ponderada por la intensidad de carbono horaria CI(t) ∈ [0.672, 0.790] kgCO₂/kWh:

```
carbon_norm(t)   = CI(t) / (CI(t) + 0.35)
carbon_i(t)      = −tanh(import_i × (0.25 + carbon_norm)/20)
                 + 0.05 × tanh(export_i × carbon_norm/20)
```

**Componente de costo (cost_i):**

La señal de costo refleja la tarifa TOU de Electro Oriente S.A., con incentivo para importar en horas fuera de punta (0.26 USD/kWh) y exportar o reducir importación en horas punta (0.38 USD/kWh):

```
price_norm(t)   = p(t) / (p(t) + 0.20)            donde p ∈ {0.26, 0.38} USD/kWh
cost_i(t)       = −tanh(import_i × (0.25 + price_norm)/20)
                + 0.08 × tanh(export_i × price_norm/20)
```

**Agregación cooperativa (team_reward):**

La recompensa individual se mezcla con la recompensa media del equipo según el parámetro `team_reward_ratio` (r):

```
team_reward      = (1/N) Σᵢ reward_i(t)
mixed_reward_i   = (1 − r) × reward_i + r × team_reward
```

#### 4.11.3 Perfiles de Recompensa por Algoritmo MADRL

> **RECONCILIACION (2026-06-14):** La implementacion vigente adopta el perfil **unified_comparable_v3** con valores idénticos para los cuatro algoritmos y penalidad SOC/EV reforzada (ver `reward_function.py` y `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`). Los perfiles diferenciados de la tabla original se conservan como referencia de ablacion futura pero NO son los valores activos en entrenamiento.

**Perfil activo (todos los algoritmos — unified_comparable_v3):**

| Algoritmo | r (team_ratio) | w_peak | w_ramp | ev_weight | reward_scale |
| --------- | :------------: | :----: | :----: | :-------: | :----------: |
| HAPPO | **0.70** | **0.45** | **0.35** | **0.25** | **1.00** |
| MASAC | **0.70** | **0.45** | **0.35** | **0.25** | **1.00** |
| MATD3 | **0.70** | **0.45** | **0.35** | **0.25** | **1.00** |
| MAAC | **0.70** | **0.45** | **0.35** | **0.25** | **1.00** |

Razón de la unificación: garantizar comparabilidad estadística entre los 12 experimentos (4 algoritmos × 3 escenarios). Con perfiles diferenciados, las diferencias de rendimiento no son atribuibles exclusivamente a la arquitectura del algoritmo.

**Perfiles diferenciados originales (ablación futura — NO activos):**

| Algoritmo | Tipo de entrenamiento | r (team_ratio) | w_peak | w_ramp | reward_scale | Justificación original |
|-----------|----------------------|:--------------:|:------:|:------:|:------------:|---------------|
| **HAPPO** | On-policy cooperativo CTDE | 0.75 | 0.45 | 0.35 | 1.00 | Alta cooperación para convergencia monótona |
| **MASAC** | Off-policy con entropía | 0.55 | 0.40 | 0.30 | 0.80 | Escala reducida para estabilidad de entrópica |
| **MATD3** | Off-policy determinístico | 0.65 | 0.50 | 0.45 | 1.10 | Mayor énfasis en pico-rampa para estabilidad TD3 |
| **MAAC** | Off-policy con atención | 0.80 | 0.42 | 0.38 | 1.00 | Máxima cooperación para mecanismo de atención |

#### 4.11.4 Matriz de 12 Corridas Oficiales

Las 12 corridas del experimento oficial se ejecutan mediante `CityLearn/scripts/launch_citylearn_v3_official_training.ps1 -Scenario ALL`. La ruta operativa normal usa monitor visible con `LiveOutput=false`, agrupa por algoritmo y permite escenarios concurrentes dentro de cada etapa: hasta 2 para HAPPO/MATD3 en RTX 4060 Laptop 8 GB, y 1 para MASAC/MAAC por seguridad de memoria. Las condiciones de entrenamiento para la run de referencia son: 5 episodios × 8,760 pasos = 43,800 pasos totales por algoritmo; seed = 0; CUDA habilitado; hardware: NVIDIA RTX 4060 Laptop 8 GB.

| | **HAPPO** | **MASAC** | **MATD3** | **MAAC** |
|-|:---------:|:---------:|:---------:|:--------:|
| **E1 Flexibilidad** | happo/E1_s0 | masac/E1_s0 | matd3/E1_s0 | maac/E1_s0 |
| **E2 CO₂** | happo/E2_s0 | masac/E2_s0 | matd3/E2_s0 | maac/E2_s0 |
| **E3 Costos** | happo/E3_s0 | masac/E3_s0 | matd3/E3_s0 | maac/E3_s0 |

Los artefactos generados por cada corrida incluyen: `live_progress.json`, `results.json`, `timeseries.csv`, `trace.csv`, `episode_summary.csv`.

---

### 4.12 Control a Nivel de Edificio y Coordinación CTDE a Nivel de Distrito

La arquitectura de control de CityLearn v3 propuesto opera en dos niveles: el nivel de edificio (control descentralizado local) y el nivel de distrito (coordinación centralizada durante entrenamiento). Esta separación corresponde exactamente al esquema CTDE de Lowe et al. (2017) y a la formulación Dec-POMDP de Oliehoek y Amato (2016).

#### 4.12.1 Control a Nivel de Edificio (Ejecución Descentralizada)

Cada edificio Bᵢ opera como un **agente autónomo** con política local πᵢ(aᵢ | oᵢ):

- **Observación local oᵢ ∈ ℝ^(~40)**: cada edificio recibe exclusivamente su propio estado. Las 40 dimensiones aproximadas incluyen: (i) 12 columnas de Building_i (carga no desplazable, demanda de enfriamiento, generación solar, temperatura interior, etc.); (ii) 4 columnas meteorológicas (T exterior, RH, GHI difuso, DNI); (iii) 4 columnas de precio (precio actual y predicciones +1h, +2h, +3h); (iv) 1 columna de intensidad de carbono; (v) 6 columnas por cargador EV asignado al edificio (n_chargers_i × 6); (vi) estado SOC del BESS.

- **Acción local aᵢ ∈ ℝ^(d_aᵢ)**: el edificio controla sus propios recursos DER. La dimensionalidad de acción varía:
  - Edificios educativos sin BESS/EV: 1-2 dimensiones (solo HVAC).
  - Edificios con BESS: +1 dimensión (carga/descarga BESS en [−P_max, +P_max] kW).
  - Edificios con cargadores EV: +n_chargers_i dimensiones (potencia de carga por cargador).
  - B1 (Electro Oriente S.A.): 5 dimensiones (2 HVAC + 1 BESS + 2 EV + 1 lavasecadora).

- **Ejecución en tiempo real**: la política πᵢ opera sin comunicación con otros edificios. No requiere acceso al estado global. Este diseño garantiza la escalabilidad del sistema a entornos con mayor número de edificios.

#### 4.12.2 Coordinación a Nivel de Distrito (Entrenamiento Centralizado)

A nivel de distrito, la coordinación opera durante el **entrenamiento** a través del crítico centralizado:

- **Estado global s = [o₁, …, o₁₇] ∈ ℝ^(~680)**: el crítico centralizado Qᵢ(s, a₁, …, a₁₇) de cada agente accede al estado completo del distrito durante el entrenamiento. Esto permite aprender la correlación entre las acciones colectivas y el resultado energético del distrito.

- **Métricas de coordinación distrital** (calculadas en la función de recompensa):
  - `district_import(t) = Σᵢ net_load_i(t)` [kWh/h]: importación neta total del distrito.
  - `peak_share(t) = district_import(t) / N`: pico promedio por agente.
  - `ramp_share(t) = |district_import(t) − district_import(t−1)| / N`: rampa promedio por agente.

- **Recompensa mixta**: la recompensa individual se pondera con la recompensa media del equipo (`team_reward = mean(rewards_i)`), alineando los incentivos individuales con el objetivo colectivo del distrito. El balance entre incentivo individual y cooperativo está controlado por `team_reward_ratio` (r), que varía por algoritmo: HAPPO = 0.75, MASAC = 0.55, MATD3 = 0.65, MAAC = 0.80.

- **Post-entrenamiento**: el crítico centralizado se descarta. Solo las políticas πᵢ locales (sin acceso al estado global) se utilizan en la evaluación final y en hipotéticos despliegues.

#### 4.12.3 Hiperparámetros Comunes del Entrenamiento

Los siguientes hiperparámetros son compartidos por los cuatro backends MADRL y configurados en `CityLearn/configs/`:

| Hiperparámetro | Valor | Aplicabilidad |
|----------------|:-----:|--------------|
| `hidden_sizes` | [256, 256] | Todos |
| `actor_lr` | 3×10⁻⁴ | Todos |
| `critic_lr` | 1×10⁻³ | Todos |
| `gamma` | 0.99 | Todos |
| `batch_size` | 256 | Todos |
| `replay_buffer_size` | 1,000,000 | MASAC, MATD3, MAAC |
| `tau` | 0.005 | MASAC, MATD3, MAAC |
| `ppo_clip` | 0.2 | Solo HAPPO |
| `matd3_policy_delay` | 2 | Solo MATD3 |
| `maac_attention_heads` | 4 | Solo MAAC |
| `masac_alpha` | "auto" | Solo MASAC |

La optimización automática de hiperparámetros mediante Optuna (Akiba et al., 2019) queda como mejora experimental posterior. La evidencia cuantitativa del proyecto debe tomarse solo de la corrida vigente indicada por `outputs/latest_visible_training_output_root.txt`.

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
| Servicios computacionales | Entrenamiento local en GPU NVIDIA RTX 4060 Laptop 8 GB | S/ 0 adicional |
| Revisión bibliográfica | Acceso a bases de datos (Scopus, IEEE Xplore, ScienceDirect) | S/ 500-1,000 |
| Asesoría especializada | Honorarios de asesor | por definir |
| Publicación científica | Tasa de publicación en revista indexada (si aplica) | S/ 1,500-3,000 |
| Materiales de oficina | Papel, impresión, empaste | S/ 300 |
| Contingencia (10%) | | S/ 230-430 |
| **Total estimado** | | **S/ 2,530-4,730** |

### 5.3 Financiamiento

- Recursos propios del graduando.
- Herramientas de código abierto: CityLearn v2, MARLlib, Optuna, Python, PyTorch — costo cero.
- Dataset `citylearn_iquitos_2023_2025`: generado en el proyecto, sin costo de adquisición.
- Infraestructura computacional local: NVIDIA RTX 4060 Laptop 8 GB (ya disponible).
- Apoyo institucional de UNI: por definir.

---

## Referencias bibliograficas (lista unica)

La bibliografia canónica del proyecto está unificada en:

- docs/tesis_capitulos/Referencias_APA.md (fuente Markdown, APA 7)
- Sección **Referencias bibliográficas** del informe final Word (docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx y espejo docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx)

No mantener listas duplicadas, «complementarias» ni bibliografías por capítulo o anexo en este plan.

---

*Generado mediante el skill `madrl-citylearn-thesis-plan` del proyecto MADRLCitytleranflexresdr.*
*Fecha de generación: 2026-06-04.*
*Actualización 2026-06-05a — Módulo A completado: 50 antecedentes en sección 1.2.1; 50 referencias APA; 18 primeros autores corregidos vía verificación web.*
*Actualización 2026-06-05b — Integración técnica completa: Secciones 4.9 (dataset pipeline, 17 edificios reales), 4.10 (Dec-POMDP doctoral, CityLearn v3 propuesto), 4.11 (escenarios E1/E2/E3/Global, función recompensa multiobjetivo, pesos por algoritmo), 4.12 (control edificio vs. distrito CTDE). Ampliación Marco Teórico sección 3.1. Nuevos Anexos 10 (17 edificios), 11 (pipeline técnico dataset), 12 (escenarios y pesos). SKILL.md actualizado con Módulos C, D, E, F.*
*Actualización 2026-06-13 — Sección 4.10.4 (nueva): 4 aportes originales al motor de simulación CityLearn (Battery C-rate+Arrhenius, PV IEC 61215, CostFunction peak OSINERGMIN, CarbonIntensityModel). Commit 54b1938e submodulo CityLearn. Documentados en `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md` (17 referencias, 2019–2024). SKILL.md actualizado con Módulo G.*
*Run de referencia para evidencia cuantitativa: `<OutputRoot>` leido desde `outputs/latest_visible_training_output_root.txt` (5 ep, seed=0, CUDA=True, perfil `local4060_fast`).*
*Referencias con [PV-parcial]: 9 referencias con autores secundarios pendientes de verificación vía Scopus/IEEE Xplore.*
*Run de referencia para evidencia cuantitativa: `<OutputRoot>` leido desde `outputs/latest_visible_training_output_root.txt` (5 ep, seed=0).*
*Referencias marcadas [PV] requieren verificación bibliográfica completa mediante el Módulo A.*
