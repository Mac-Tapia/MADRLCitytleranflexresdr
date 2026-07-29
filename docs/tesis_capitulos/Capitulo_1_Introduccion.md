# Capítulo 1. Introducción

> **Documento de tesis — borrador integral alineado para Perplexity.** Construido a partir de la documentación y el **código real** del proyecto `MADRLCitytleranflexresdr`: Plan de Tesis UNI, `docs/workflow_manifest.json`, `CityLearn/configs/citylearn_v3_madrl_training.yaml`, scripts de entrenamiento `train_citylearn_v3_{happo,masac,matd3,maac}.py`, `reward_function.py` (`CityLearnV3MADRLRewardFunction`), `scenario_manager.py`, y artefactos de `outputs/citylearn_v3_madrl_full_20260615_074011_v4/`. Los datos inexistentes en el proyecto se marcan con `[Pendiente: ...]`. No inventar cifras.

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Actúa como redactor académico experto en aprendizaje por refuerzo multiagente (MADRL) y sistemas energéticos. Estás puliendo el **Capítulo 1 (Introducción)** de una **tesis de maestría profesionalizante de la Universidad Nacional de Ingeniería (UNI), Perú**, titulada *"Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes"*. Autor: Mac Tapia (mac.tapia.c@uni.pe). Caso de estudio: **Sistema Eléctrico Aislado de Iquitos (SEAI)**, Electro Oriente S.A., Loreto, Perú: 17 edificios institucionales/comerciales reales, simulados en **CityLearn v2 extendido con una capa propia CityLearn v3** (Dec-POMDP + CTDE). Se comparan cuatro algoritmos MADRL: **HAPPO, MASAC, MATD3 y MAAC**, sobre tres objetivos: **OE.1 flexibilidad energética, OE.2 reducción de CO₂, OE.3 reducción de costos**.

**Objetivo del prompt:** Convertir el borrador siguiente en una versión final de calidad académica, en español formal, con:
1. Redacción fluida y coherencia argumentativa entre problema → objetivos → hipótesis → justificación.
2. **Citas APA (autor, año)** consistentes con `Referencias_APA.md`. No añadir referencias inexistentes sin marcarlas.
3. Completar `[Pendiente: ...]` solo si la información se infiere del documento; si no, dejarlos señalados.
4. **No alterar cifras reales** (0.790 kgCO₂/kWh; tarifas 0.26/0.38 USD/kWh; 17 edificios; 26 304 horas; 185 cargadores EV; BESS 26 266 kWh; PV 48 790.9 kWp).

**Instrucciones específicas:** (a) reforzar el problema con evidencia del estado del arte; (b) verificar coherencia vertical PG→OG, PE.i→OE.i→HE.i; (c) afinar la justificación en sus seis dimensiones; (d) precisar alcances/limitaciones sin sobre-prometer (estudio de simulación, no despliegue real).

---

## 1.1 Problema de investigación

### 1.1.1 Contexto y diagnóstico

Las comunidades inteligentes (*smart communities*) son entornos energéticos complejos que integran recursos de energía distribuida (DER): generación solar fotovoltaica (PV), sistemas de almacenamiento en baterías (BESS) y estaciones de carga de vehículos eléctricos (EV). La coordinación multiagente de estos recursos bajo observabilidad parcial es un problema de decisión secuencial no resuelto que afecta simultáneamente la **flexibilidad energética**, las **emisiones de carbono** y los **costos energéticos**.

El caso de estudio es el **Sistema Eléctrico Aislado de Iquitos (SEAI)**, operado por Electro Oriente S.A. en Loreto, Perú. A diferencia de las redes interconectadas, el SEAI **no está conectado al SEIN** y se abastece principalmente con generación diésel, con penetración solar creciente (~15 % en 2022-2023) y un factor de emisión base de **0.790 kgCO₂/kWh** (MINAM RAGEI 2019). Sobre 17 edificios institucionales y comerciales reales se compara cuál de cuatro algoritmos MADRL gestiona mejor, de forma coordinada, las tres dimensiones objetivo.

El problema se descompone en tres dimensiones:

- **Flexibilidad energética (OE.1):** la ausencia de gestión coordinada de DER limita la modulación de demanda, el desplazamiento de cargas y el aprovechamiento renovable, derivando en comportamiento *grid-interactive* subóptimo y razones pico-promedio elevadas. No existe un estudio comparativo que determine cuál MADRL logra el mejor desempeño de flexibilidad coordinada.
- **Emisiones de carbono (OE.2):** bajo señales de intensidad de carbono variables (diésel + PV), la falta de control coordinado impide desplazar el consumo hacia periodos de baja intensidad. La intensidad de carbono dinámica del SEAI varía en **CI ∈ [0.6715, 0.790] kgCO₂/kWh** según la generación solar horaria.
- **Costos energéticos (OE.3):** la tarifa por uso horario (TOU) de Electro Oriente S.A. —**0.38 USD/kWh en punta (18:00-22:59) y 0.26 USD/kWh fuera de punta**— crea incentivos económicos para la flexibilidad, pero las respuestas no coordinadas a nivel de edificio generan resultados colectivos subóptimos.

### 1.1.2 Limitaciones del estado del arte

La literatura reporta evaluaciones aisladas de algoritmos individuales sobre dimensiones únicas. **No existe un marco comparativo unificado** que cubra HAPPO, MASAC, MATD3 y MAAC bajo una misma formulación Dec-POMDP y esquema CTDE, aplicado simultáneamente a flexibilidad, CO₂ y costos. Esta brecha impide determinar el mejor agente MADRL para la gestión coordinada en comunidades inteligentes, particularmente en redes aisladas como el SEAI.

### 1.2.1 Formulación del problema

#### 1.2.1.1 Formulación del problema general

¿En qué medida el algoritmo MADRL (aprendizaje por refuerzo profundo multiagente) impacta en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño a nivel global?

#### 1.2.1.2 Formulación de los problemas específicos

PE.1: ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E1?

PE.2: ¿En qué medida el algoritmo MADRL impacta en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E2?

PE.3: ¿En qué medida el algoritmo MADRL impacta en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E3?

---

## 1.3 Objetivos e hipótesis

### 1.3.1 Objetivos

#### 1.3.1.1 Objetivo general

OG. - Determinar el impacto de los algoritmos aprendizaje por refuerzo profundo multiagente (MADRLs) en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, e identificar cuál de los algoritmos presenta el mejor desempeño a nivel global.

#### 1.3.1.2 Objetivos específicos

OE.1: Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E1.

OE.2: Determinar el impacto de los algoritmos MADRLs en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E2.

OE.3: Determinar el impacto de los algoritmos MADRLs en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E3.

**Coherencia vertical:** cada OE responde a su PE, se operacionaliza con un escenario (E1, E2, E3) cuyos pesos de recompensa priorizan el eje correspondiente, y se evalúa con KPI-gains frente al baseline CityLearn v2 y con KPIs físicos de distrito y de edificio. Contrastación en Cap. 5 (§§5.2–5.5).

#### 1.3.1.3 Criterios de determinación del impacto (cumplimiento completo)

Para cumplir el OG y los OE.1–OE.3, y para demostrar las hipótesis, se exige el conjunto **completo** de criterios C1–C5 (sin parciales). **C5 (control de recursos)** es obligatorio. Cada eje se reporta a **nivel distrito** y a **nivel edificio**.

| Id | Criterio | Medida / prueba | Rol |
|---|---|---|---|
| **C1** | Impacto vs baseline | Wilcoxon KPI-gains vs cero + Holm | Inferencial HE |
| **C2** | Diferencias entre algoritmos | Kruskal–Wallis / Friedman + Holm | Inferencial HE |
| **C3** | KPIs físicos de distrito por eje | flex_composite / ΔCO₂ / Δcosto | Descriptivo distrito |
| **C4** | KPIs desagregados por edificio por eje | 17 edificios × E1/E2/E3 | Descriptivo edificio |
| **C5** | Control de recursos | BESS, EV/V2G, carga desplazable (acciones y éxito EV) | Obligatorio (atribuibilidad) |

Evidencia Cap. 5: §§5.1.1, 5.2 (C3–C4), 5.3–5.5 (C1–C2), 5.4.5 (C5).

### 1.3.2 Hipótesis

> **Nota metodológica:** estudio cuantitativo, aplicado, cuasiexperimental factorial 4×3 (algoritmo × escenario), basado en simulación. Puerta paramétrica (Shapiro–Wilk); si se rechaza normalidad, solo batería no paramétrica decide las hipótesis (α = 0,05). Unidad primaria: KPI-gains orientados. Corrida canónica madrl_v3_20260627_164047.

#### 1.3.2.1 Hipótesis general

H0G.-El algoritmo MADRL no impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas en el desempeño global de los algoritmos.

H1G.- El algoritmo MADRL impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y el desempeño global difiere entre los algoritmos.

#### 1.3.2.2 Hipótesis específicas

HE10.- El algoritmo MADRL no impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E1.

HE11.- El algoritmo MADRL impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E1.

HE20.- El algoritmo MADRL no impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E2.

HE21.- El algoritmo MADRL impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E2.

HE30.-El algoritmo MADRL no impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E3.

HE31.-El algoritmo MADRL impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E3.

#### 1.3.2.3 Resumen de contrastación (Cap. 5)

| Hipótesis | Decisión (KPI-gains, α = 0,05) | Líder descriptivo |
|---|---|---|
| **H0G / H1G** | Se rechaza H0G y se respalda H1G **exploratoriamente** (Friedman p = 0,0096); sin ganador global único | MAAC (score E1–E3) / MATD3 (mediana KPI / score 0,6667) |
| **HE10 / HE11** | No se rechaza HE10; no se respalda HE11 (KW p = 0,4685) | **MAAC** (E1) |
| **HE20 / HE21** | No se rechaza HE20; no se respalda HE21 (KW p = 0,7648) | **MATD3** (E2) |
| **HE30 / HE31** | No se rechaza HE30; no se respalda HE31 (KW p = 0,7357) | **MAAC** (E3) |

Fuente: `decisiones_problemas_objetivos_hipotesis.csv`. Detalle en Capítulos 5 y 6.

---

## 1.4 Justificación

- **Técnica:** primera evaluación comparativa unificada de HAPPO, MASAC, MATD3 y MAAC bajo Dec-POMDP y CTDE sobre un mismo dataset y función de recompensa.
- **Ambiental:** identificar el mejor MADRL para reducción de CO₂ contribuye a la descarbonización del SEAI (0.790 kgCO₂/kWh, generación diésel dominante).
- **Económica:** orientación accionable para reducir el gasto eléctrico bajo tarifas TOU de Electro Oriente S.A.
- **Metodológica:** Dec-POMDP + CTDE + benchmark unificado + **cuatro aportes originales al motor de simulación** (degradación BESS Arrhenius+C-rate; corrección PV tropical IEC 61215; KPI de pico con ventana de facturación OSINERGMIN MT-3/MT-4; clase `CarbonIntensityModel` para redes aisladas). Todo reproducible con artefactos versionados.
- **Científica:** la evaluación simultánea en tres ejes llena una laguna en la literatura comparativa de MADRL.
- **Social:** comunidades inteligentes flexibles y de bajo costo benefician a usuarios institucionales y residenciales y aportan a la transición energética amazónica.

---

## 1.5 Alcances y limitaciones

### 1.5.1 Alcances
- **Temático:** comparación de HAPPO, MASAC, MATD3 y MAAC en KPIs de flexibilidad, CO₂ y costos, frente a líneas base CityLearn v2 (`baseline`, `hour_rbc`) y comparadores SB3 (PPO/SAC/A2C de agente central).
- **Espacial:** comunidades inteligentes simuladas en CityLearn v2 / v3; aplicabilidad al SEAI Iquitos (17 edificios reales de Loreto).
- **Temporal:** dataset 2023-2025 (**26 304 pasos horarios**); literatura MADRL 2015-2026.
- **Metodológico:** cuantitativo, aplicado, comparativo, **cuasiexperimental factorial 4×3** (algoritmo × escenario E1/E2/E3), basado en simulación.
- **Computacional:** Python 3.9, PyTorch 2.8.0+cu126, CUDA 12.6; entrenamiento local en NVIDIA RTX 4060 Laptop 8 GB (perfil `local4060_fast`) y corridas en Colab A100.

### 1.5.2 Limitaciones y supuestos
- No se modela ninguna red eléctrica física; los resultados **no constituyen validación de despliegue real**.
- **CityLearn v3 es una extensión experimental de tesis, no una versión oficial de CityLearn.**
- El dataset de Iquitos se construye por **destilación** de facturación mensual real a perfiles horarios sintéticos que preservan la magnitud energética (Capítulo 3).
- Las corridas locales reportadas usan **5 episodios × 8 760 pasos = 43 800 pasos** por job (presupuesto de cómputo en 8 GB VRAM); la configuración canónica vigente apunta a **50 episodios = 438 000 pasos**. La corrida canónica usa **seed = 0** (semilla única); la robustez multi-semilla (≥3) queda como **trabajo futuro (H2)**, no como resultado de esta tesis.
- **Exclusiones:** despliegue en campo, sujetos humanos, despacho económico de generación física y análisis de estabilidad de red.

---

## 1.6 Estructura de la tesis

| Capítulo | Contenido |
|---|---|
| 1. Introducción | Problema, objetivos, hipótesis, justificación, alcances |
| 2. Marco teórico | Estado del arte, bases teóricas (Dec-POMDP, CTDE, 4 algoritmos), trabajos relacionados |
| 3. Metodología | Tipo y diseño, dataset Iquitos, variables, técnicas, herramientas, procedimiento |
| 4. Desarrollo de la propuesta | Arquitectura CityLearn v3, modelo de IA, algoritmos, recompensa multiobjetivo, implementación |
| 5. Resultados | Experimentos, métricas, resultados v3/v4, comparación con baseline, tablas, figuras, discusión |
| 6. Conclusiones preliminares | Hallazgos, limitaciones, trabajo pendiente, plan de culminación |

---

### Estado del capítulo
**Veredicto metodológico aplicado (2026-07-18):** diseño cuasiexperimental; PG/OG/HG tipo ranking–Pareto (Semilla C); H₀/H₁ por eje; dos capas de evidencia sincronizadas con Caps. 5–6. Pendientes institucionales: unidad de posgrado (FIEE/FISI), nombre completo del autor, multi-semilla experimental (H2).
