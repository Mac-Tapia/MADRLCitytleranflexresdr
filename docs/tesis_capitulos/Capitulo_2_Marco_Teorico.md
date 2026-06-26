# Capítulo 2. Marco Teórico

> **Documento de tesis — borrador integral alineado para Perplexity.** Basado en la matriz bibliográfica de 50 antecedentes del Plan de Tesis UNI (organizada en Eje 1 flexibilidad, Eje 2 CO₂, Eje 3 costos y Eje transversal MADRL) y en las bases teóricas del proyecto (Dec-POMDP, CTDE, los cuatro algoritmos y sus backends reales en `external/`). Las referencias marcadas `[PV]` en el plan son pendientes de verificación bibliográfica secundaria. No inventar referencias.

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres un investigador experto en MADRL y gestión energética de edificios. Pules el **Capítulo 2 (Marco teórico)** de la tesis de maestría UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC; ejes OE.1 flexibilidad, OE.2 CO₂, OE.3 costos).

**Objetivo del prompt:** Llevar el borrador a versión final académica en español con:
1. Estado del arte actualizado y crítico (no solo enumerativo): agrupar por ejes, contrastar métodos y resaltar la brecha que motiva la tesis.
2. **Citas APA** consistentes con `Referencias_APA.md`; verificar y completar los datos marcados `[PV]` (volumen, número, DOI) usando Scopus/IEEE/ScienceDirect.
3. Bases teóricas rigurosas: definiciones formales de Dec-POMDP y CTDE, y descripción técnica precisa de HAPPO, MASAC, MATD3 y MAAC.
4. Cerrar con una **tabla de trabajos relacionados** y un párrafo explícito de *gap analysis*.

**Instrucciones específicas:** (a) verificar primeros autores reales de papers arXiv; (b) homogenizar nomenclatura (MARLlib ≠ MARL); (c) no eliminar las cifras de mejora reportadas por la literatura (~15-25 %); (d) mantener la distinción CityLearn v2 (oficial) vs CityLearn v3 (extensión de tesis).

---

## 2.1 Estado del arte actualizado

La revisión sistemática del proyecto (Módulo A) comprende 50 investigaciones verificadas, organizadas en cuatro ejes alineados con los objetivos.

### 2.1.1 Eje 1 — Flexibilidad energética con MADRL

El entorno base proviene de la línea CityLearn: Vázquez-Canteli y Nagy (2019a) introducen CityLearn v1.0 como entorno OpenAI Gym para respuesta a la demanda multiedificio, mostrando que SAC supera al control basado en reglas con reducción de pico de ~20 %. Vázquez-Canteli et al. (2020) estandarizan los KPIs `peak_average`, `ramping_average` y `one_minus_load_factor_average`. Nweye et al. (2024) consolidan **CityLearn v2** integrando EV/V2G, intensidad de carbono dinámica, BESS, PV y confort, constituyendo la base tecnológica directa de CityLearn v3 propuesto. Nweye et al. (2022) identifican nueve desafíos del MARL en edificios *grid-interactive* (generalización, escalabilidad, observabilidad parcial, no-estacionariedad) que motivan la formulación Dec-POMDP.

Aplicaciones de coordinación: Nweye et al. (2023a, MERLIN) demuestran MARL offline/transfer en **17 edificios reales**, escala equivalente al SEAI; Nweye et al. (2023b) aplican HAPPO en CityLearn a 17 edificios heterogéneos; Yao et al. (2023, LSD-MADDPG) obtienen reducciones de pico ~15 % y costo ~18 %; Xie et al. (2023) muestran que la atención en MARL supera a MADDPG en coordinación DR (~25 %); Hribar et al. (2025) mejoran la autonomía energética de distritos de energía positiva ~20 % frente a reglas.

### 2.1.2 Eje 2 — Reducción de emisiones de CO₂ con MADRL

Liu et al. (2022) aplican MADDPG en edificios PV+BESS logrando reducción de costos ~20 % y CO₂ ~15 %. Ye et al. (2025) y Ma et al. (2025) proponen MARL seguro con restricciones de carbono para redes de distribución y multi-microgrids. Sarkar et al. (2024) reducen la huella de carbono en centros de datos mediante desplazamiento temporal de carga hacia periodos de baja intensidad, técnica directamente transferible al OE.2 con el CI dinámico de Iquitos.

### 2.1.3 Eje 3 — Optimización de costos energéticos con MADRL

Yao et al. (2023) y Shojaeighadikolaei et al. (2022) reportan reducciones de costo ~18-22 % con esquemas cooperativos. Gao et al. (2023) validan **MASAC** multi-microgrid para programación colaborativa con respuesta a precios. Xiong et al. (2024) y Kim et al. (2025) aplican DRL/MARL con tarifas TOU directamente análogas a la estructura de Electro Oriente S.A. ($0.38 punta / $0.26 fuera de punta). Zhang et al. (2023) y Chen et al. (2024) abordan coordinación V2G jerárquica con restricciones SOC y degradación, pertinentes a los 185 cargadores del dataset Iquitos.

### 2.1.4 Brecha (gap analysis)

A pesar de la riqueza de antecedentes, **ningún trabajo compara HAPPO, MASAC, MATD3 y MAAC bajo condiciones idénticas** (mismo Dec-POMDP, mismo CTDE, misma función de recompensa multiobjetivo y mismo dataset) para los tres ejes simultáneamente. Esta es la contribución central de la tesis. `[Pendiente: añadir 2-3 referencias 2025-2026 de benchmarks comparativos de MADRL para reforzar la novedad.]`

---

## 2.2 Bases teóricas

### 2.2.1 Aprendizaje por refuerzo y multiagente

El RL se formaliza como un MDP ⟨S, A, T, R, γ⟩ (Sutton & Barto, 2018). SAC (Haarnoja et al., 2018) introduce maximización de entropía off-policy, base conceptual de MASAC y MAAC. En entornos multiagente, el aprendizaje independiente sufre **no-estacionariedad** porque la política de cada agente cambia el entorno percibido por los demás.

### 2.2.2 Dec-POMDP

El **Decentralized Partially Observable Markov Decision Process** (Oliehoek & Amato, 2016) modela la decisión cooperativa bajo observabilidad parcial como la tupla:

> **ℳ = ⟨𝒮, {𝒜ᵢ}ᵢ₌₁ᴺ, 𝒯, R, {𝒪ᵢ}ᵢ₌₁ᴺ, Ω, γ, T⟩**

donde 𝒮 es el estado global, 𝒜ᵢ las acciones locales, 𝒯 la transición, R la recompensa cooperativa común, 𝒪ᵢ las observaciones locales, Ω la función de observación, γ el descuento y T el horizonte. En esta tesis: **N = 17** edificios, **γ = 0.9999** (configurado en los scripts para episodios de 8 760 pasos), **T = 8 760** pasos horarios.

### 2.2.3 CTDE

El esquema **Centralized Training, Decentralized Execution** (Lowe et al., 2017) entrena un crítico centralizado con acceso al estado global s = [o₁,…,o₁₇], mientras cada actor πᵢ(aᵢ|oᵢ) ejecuta usando solo su observación local. Tras el entrenamiento, el crítico se descarta. Este esquema corrige la no-estacionariedad y es el paradigma común a los cuatro algoritmos evaluados.

### 2.2.4 Los cuatro algoritmos MADRL

| Algoritmo | Tipo | Característica central | Crítico | Backend real del proyecto |
|---|---|---|---|---|
| **HAPPO** | On-policy | Actualización **secuencial** por agente con *trust region*; garantías de mejora monótona para agentes heterogéneos (Kuba et al., 2021; Zhong et al., 2023) | V(s) centralizado | `external/HARL` (PKU-MARL) |
| **MASAC** | Off-policy | SAC con regularización de entropía + mezcla cooperativa tipo **QMIX**; acciones discretizadas | Q-mix centralizado | `external/MARL/src` (puyuan1996) |
| **MATD3** | Off-policy | TD3 multiagente: **doble crítico** (anti-sobreestimación), *policy delay* y *target noise* | Par Q₁/Q₂ centralizado | `external/off-policy` (marlbenchmark) |
| **MAAC** | Off-policy | Actor-Attention-Critic: **atención multi-cabeza** que selecciona qué agentes observar (Iqbal & Sha, 2019) | Crítico con atención (SAC) | `external/MAAC` (shariqiqbal2810) |

- **HAPPO** (Heterogeneous-Agent PPO): primer MARL on-policy con garantías teóricas para heterogeneidad; supera a MAPPO/IPPO en ~85 % de tareas benchmark (Kuba et al., 2021).
- **MASAC**: combina la estabilidad de SAC con mezcla de valores QMIX; en este proyecto se discretiza la acción continua de CityLearn en `action_bins=3` con `discrete_action_mode=axis` para evitar el crecimiento cartesiano exponencial.
- **MATD3**: hereda de TD3 los dos críticos y el retardo de política; backend activo `external/off-policy` por compatibilidad con Python 3.9 (sustituye a `MATD3implementation`).
- **MAAC**: la atención permite coordinación selectiva entre los 17 agentes, relevante por la heterogeneidad de tipos de edificio.

### 2.2.5 Herramientas de soporte teórico

- **MARLlib** (Hu et al., 2023): biblioteca unificada de >20 algoritmos MARL; referencia técnica de integración (no es el launcher oficial).
- **Optuna** (Akiba et al., 2019): HPO basado en TPE; previsto como mejora experimental posterior.
- **CityLearn v2** (Nweye et al., 2024): simulador base; **CityLearn v3 propuesto**: extensión experimental de tesis (Dec-POMDP, CTDE, recompensa multiobjetivo).

### 2.2.6 Bases teóricas de los ejes

- **Flexibilidad:** capacidad de modificar la curva de demanda vía desplazamiento de cargas, BESS, autoconsumo PV y carga/descarga EV. KPIs: `peak_average`, `ramping_average`, `one_minus_load_factor_average`, autoconsumo, autosuficiencia.
- **CO₂:** intensidad de carbono variable según mezcla horaria; KPIs de emisiones totales, emisiones de control vs baseline y delta.
- **Costos:** tarifas TOU/RTP; KPIs de costo total, costo de control vs baseline y desviación frente a la señal de precio.

---

## 2.3 Trabajos relacionados (síntesis)

| Trabajo | Método | Entorno/Escala | Eje principal | Mejora reportada |
|---|---|---|---|---|
| Vázquez-Canteli & Nagy (2019a) | SAC | CityLearn v1, multiedificio | Flexibilidad | ~20 % pico |
| Nweye et al. (2023a) MERLIN | MARL offline/transfer | 17 edificios reales | Flex/ocupante | Viabilidad a escala |
| Nweye et al. (2023b) | HAPPO | CityLearn, 17 edif. heterog. | Flexibilidad | Primer HAPPO en CityLearn |
| Yao et al. (2023) | LSD-MADDPG | Comunidad PV+BESS+EV | Flex/Costo | ~15 % pico, ~18 % costo |
| Xie et al. (2023) | Attention MARL | Edificios DR | Flexibilidad | ~25 % vs MADDPG |
| Liu et al. (2022) | MADDPG | Edificios PV+BESS | CO₂/Costo | ~15 % CO₂, ~20 % costo |
| Gao et al. (2023) | MASAC | Multi-microgrid | Costo | Programación colaborativa |
| Hribar et al. (2025) | MADRL | Distritos energía positiva | CO₂/Autonomía | ~20 % |
| **Esta tesis** | **HAPPO/MASAC/MATD3/MAAC** | **CityLearn v3, 17 edif. SEAI Iquitos** | **Flex+CO₂+Costo (3 ejes)** | **Comparación unificada (Cap. 5)** |

---

### Estado del capítulo
**Completo con placeholders menores.** Pendientes: verificar datos `[PV]` (volumen/número/DOI) de ~15 referencias; añadir 2-3 benchmarks comparativos 2025-2026.
