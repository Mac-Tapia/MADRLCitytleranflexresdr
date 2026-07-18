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

### 1.1.3 Formulación del problema

**Problema general (PG):**
> ¿Qué algoritmo MADRL ofrece el mejor compromiso (ranking / frontera de Pareto) de gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes simuladas bajo CityLearn v3 en el SEAI Iquitos?

**Problemas específicos:**
- **PE.1:** ¿Qué MADRL lidera la flexibilidad energética (escenario E1) y con qué evidencia descriptiva e inferencial?
- **PE.2:** ¿Qué MADRL lidera la reducción de emisiones de CO₂ (escenario E2) y con qué evidencia descriptiva e inferencial?
- **PE.3:** ¿Qué MADRL lidera la optimización de costos energéticos (escenario E3) y con qué evidencia descriptiva e inferencial?

---

## 1.2 Objetivos

### 1.2.1 Objetivo general
> **OG.** Identificar el(los) MADRL recomendable(s) por eje y el ranking integrado de gestión coordinada de flexibilidad, CO₂ y costos en el SEAI Iquitos, **sin asumir dominancia Pareto universal**.

### 1.2.2 Objetivos específicos
> **OE.1.** Identificar el MADRL líder en flexibilidad energética (E1) y contrastar si la diferencia entre algoritmos es estadísticamente sustentable.
>
> **OE.2.** Identificar el MADRL líder en reducción de emisiones de CO₂ (E2) y contrastar si la diferencia entre algoritmos es estadísticamente sustentable.
>
> **OE.3.** Identificar el MADRL líder en costos energéticos (E3) y contrastar si la diferencia entre algoritmos es estadísticamente sustentable.

**Coherencia vertical:** cada OE responde a su PE, se operacionaliza con un escenario de entrenamiento (E1, E2, E3) cuyos pesos de recompensa priorizan el eje correspondiente, y se evalúa con los KPIs de CityLearn v2 (`peak_average`, `ramping_average`, `carbon_emissions`, `electricity_cost`, etc.) más la recompensa episódica. Las métricas primarias son KPIs energéticos y recompensa MADRL; accuracy/precision/recall/F1 no se usan como métricas centrales (solo serían auxiliares si se dicotomizara éxito vs baseline).

---

## 1.3 Hipótesis

> **Nota metodológica:** el estudio es *cuantitativo, aplicado y cuasiexperimental factorial 4×3 (algoritmo × escenario), basado en simulación*. Se formula H₀/H₁ por eje y se contrastan **dos capas de evidencia** que no deben fusionarse: (A) series episódicas alineadas a OE; (B) KPI-gains de entrenamiento.

**Hipótesis general (HG) — ranking multiobjetivo:**
> **H₁(G):** no existe un único MADRL que domine simultáneamente los tres ejes; el ranking integrado y los líderes por eje pueden diferir (trade-off Pareto).  
> **H₀(G):** las distribuciones de desempeño entre algoritmos son idénticas en el agregado de ejes (omnibus).

**Hipótesis específicas (contraste de efecto del algoritmo):**
- **HE.1:** H₁₁ = las distribuciones de desempeño de flexibilidad difieren entre algoritmos; H₀₁ = son idénticas.
- **HE.2:** H₁₂ = las distribuciones de emisiones de CO₂ difieren entre algoritmos; H₀₂ = son idénticas.
- **HE.3:** H₁₃ = las distribuciones de costo energético difieren entre algoritmos; H₀₃ = son idénticas.

**Contrastación (α = 0,05):** Shapiro–Wilk (normalidad) → Kruskal–Wallis (omnibus) → Mann–Whitney U con corrección Holm (pares) y Wilcoxon signed-rank (pareado por KPI, exploratorio). Corrida canónica `madrl_v3_20260627_164047` (seed = 0; ≈50 episodios; HAPPO n = 49).

| Hipótesis | Capa A (episódica, OE-alineada) | Capa B (KPI-gains) | Veredicto |
|-----------|----------------------------------|--------------------|-----------|
| **HG** | — (se decide por ejes + ranking) | KW p = 0,155 → **no se rechaza H₀** omnibus | Ranking descriptivo: **MATD3** (score 0,6667); **sin dominador Pareto**; HG de ranking/Pareto **aceptada**; superioridad omnibus KPI-gains **no confirmada** |
| **HE.1** | KW H = 36,31; p = 1,305×10⁻⁸; ε² = 0,233 → **rechazar H₀** | KW p = 0,281 → no rechazar H₀ | Diferencia episódica **sí**; KPI-gains **no**. Líder compuesto E1: **MATD3**; media episódica `reward_mean_average`: **MAAC** |
| **HE.2** | KW H = 6,25; p = 0,0439; ε² = 0,029 → **rechazar H₀** (efecto pequeño) | KW p = 0,546 → no rechazar H₀ | Diferencia episódica débil **sí**; KPI-gains **no**. Líder descriptivo CO₂: **MATD3** |
| **HE.3** | KW H = 2,76; p = 0,251 → **no rechazar H₀** | KW p = 0,388 → no rechazar H₀ | Liderazgo de **MAAC** (Δcosto 9 515 EUR en E3) es **descriptivo**, no inferencial omnibus |

Fuentes: `gdrive_objective_aligned_statistics.csv` (capa A); `hipotesis_estadisticas_madrl.csv` (capa B). Ver Capítulos 5 y 6.

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
