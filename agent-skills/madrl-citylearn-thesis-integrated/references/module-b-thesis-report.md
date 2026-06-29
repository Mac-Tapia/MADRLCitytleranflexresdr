# Module B: Informe final de tesis doctoral

Use Module A outputs as mandatory input. Do not draft the report in isolation.

**Documento canónico de referencia:** `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`

**Borradores por capítulo (Markdown):** `docs/tesis_capitulos/` (`Capitulo_1_Introduccion.md` … `Capitulo_6_Conclusiones.md`, `Referencias_APA.md`, `00_INDICE.md`).

The final thesis report must follow the **six-chapter doctoral structure** defined in the canonical DOCX above. Guide N. 02 is **not** the governing structure for this project; use it only if the institution explicitly requires it in a separate submission.

## Thesis Title (official)

> MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN COORDINADA DE LA FLEXIBILIDAD ENERGÉTICA, LAS EMISIONES DE CARBONO Y LOS COSTOS ENERGÉTICOS EN COMUNIDADES INTELIGENTES

**Subtítulo de caso de estudio (carátula):**

> Caso de estudio experimental: Sistema Eléctrico Aislado de Iquitos (SEAI) — 17 edificios institucionales y comerciales reales, Loreto, Perú (2023–2025)

## Carátula — datos obligatorios

- Universidad: Universidad Nacional de Ingeniería (UNI)
- Unidad: Escuela de Posgrado
- Programa: Doctorado en Ingeniería — Inteligencia Artificial aplicada a Sistemas Eléctricos Inteligentes
- Grado académico: Doctor en Ingeniería
- Autor: Mac Tapia
- Asesor: `[por definir]` hasta confirmación institucional
- Lugar: Lima — Iquitos, Perú
- Año: 2026

## Epistemological frame — diseño experimental causa-efecto

The thesis is framed as a **simulation-based cause-and-effect experiment**:

- **Variable independiente (VI):** algoritmo MADRL aplicado a la comunidad, manipulado en dos dimensiones:
  - **D-VI.1 Tipo de algoritmo:** HAPPO, MASAC, MATD3, MAAC
  - **D-VI.2 Escenario de ponderación:** E1, E2, E3
- **Variable dependiente (VD):** desempeño coordinado de la comunidad, medido en tres dimensiones con **54 KPI oficiales** de CityLearn v2:
  - **D-VD.1 Flexibilidad:** `peak_average`, `ramping_average`, `one_minus_load_factor_average`, autoconsumo, autosuficiencia
  - **D-VD.2 Emisiones CO₂:** `carbon_emissions_total`, `carbon_emissions_delta`
  - **D-VD.3 Costos:** `electricity_cost_total`, `electricity_cost_delta`, `price_signal_deviation`
- **Variables de control (constantes):** dataset `citylearn_iquitos_2023_2025`, clima, intensidad de carbono, tarifa TOU, perfil de recompensa `unified_comparable_v4`, semilla

**Diseño factorial completo:** 4 × 3 = **12 tratamientos** (unidades experimentales).

## Problem, objective, and hypothesis block (use exactly)

**Problema general (PG):**

> ¿En qué medida el algoritmo Multi-Agente de Aprendizaje por Refuerzo Profundo aplicado a una comunidad inteligente (variable independiente) produce un efecto diferenciado sobre la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos (variable dependiente), y cuál de los algoritmos comparados genera el mayor efecto?

**Problemas específicos:**

> **PE.1:** ¿En qué medida el algoritmo MADRL (VI) produce un efecto sobre la dimensión de flexibilidad energética de la comunidad (D-VD.1), y cuál algoritmo genera el mayor efecto?
>
> **PE.2:** ¿En qué medida el algoritmo MADRL (VI) produce un efecto sobre la dimensión de emisiones de CO₂ de la comunidad (D-VD.2), y cuál algoritmo genera el mayor efecto?
>
> **PE.3:** ¿En qué medida el algoritmo MADRL (VI) produce un efecto sobre la dimensión de costos energéticos de la comunidad (D-VD.3), y cuál algoritmo genera el mayor efecto?

**Objetivo general (OG):**

> Determinar el efecto del algoritmo MADRL aplicado a una comunidad inteligente (VI) sobre la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos (VD), e identificar el algoritmo que produce el mayor efecto coordinado.

**Objetivos específicos:**

> **OE.1:** Determinar el efecto del algoritmo MADRL (VI) sobre la flexibilidad energética (D-VD.1) e identificar el algoritmo de mayor efecto en esta dimensión.
>
> **OE.2:** Determinar el efecto del algoritmo MADRL (VI) sobre las emisiones de CO₂ (D-VD.2) e identificar el algoritmo de mayor efecto en esta dimensión.
>
> **OE.3:** Determinar el efecto del algoritmo MADRL (VI) sobre los costos energéticos (D-VD.3) e identificar el algoritmo de mayor efecto en esta dimensión.

**Hipótesis general (HG):**

> La aplicación del algoritmo MADRL a la comunidad inteligente (VI) produce un efecto estadísticamente significativo y diferenciado sobre la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos (VD), siendo MATD3 el algoritmo que genera el mayor efecto coordinado.

**Hipótesis específicas:**

> **HE.1:** El algoritmo MADRL (VI) produce un efecto significativo sobre la flexibilidad energética (D-VD.1); el mayor efecto corresponde al algoritmo con menor variabilidad en los KPI de pico y rampa.
>
> **HE.2:** El algoritmo MADRL (VI) produce un efecto significativo sobre las emisiones de CO₂ (D-VD.2); el mayor efecto corresponde a MATD3.
>
> **HE.3:** El algoritmo MADRL (VI) produce un efecto significativo sobre los costos energéticos (D-VD.3); el mayor efecto corresponde a MATD3.

Each specific hypothesis has a corresponding null hypothesis (no significant differences between algorithm levels), tested with Kruskal-Wallis and pair-wise Mann-Whitney U / Wilcoxon (Colas et al., 2019; Agarwal et al., 2021).

## Mandatory six-chapter structure

Preserve this structure exactly. Do not replace it with Guide N. 02, an engineering log, or a dataset audit.

### Front matter

- Carátula (datos anteriores)
- Índice
- Resumen (español)
- Abstract (inglés)

### Capítulo 1. Introducción

**1.1 Planteamiento y formulación del problema**

- Contexto SEAI Iquitos: sistema aislado diésel, CI base 0,790 kgCO₂/kWh, TOU 0,26 / 0,38 USD/kWh (18:00–22:59)
- Brecha metodológica: ausencia de benchmark unificado HAPPO/MASAC/MATD3/MAAC bajo Dec-POMDP/CTDE en tres ejes
- Modelo causal Figura 1.1: VI fija y manipulada; VD varía y se mide
- PG, PE.1–PE.3

**1.2 Objetivos**

- OG, OE.1–OE.3 con coherencia vertical PG→OG→HG

**1.3 Hipótesis**

- HG, HE.1–HE.3 y criterio inferencial (α = 0,05)

**1.4 Matriz de consistencia y operacionalización de variables**

- Tabla 1.1: problema → objetivo → hipótesis → dimensión VD
- Tabla 1.2: VI (D-VI.1, D-VI.2), VD (D-VD.1–3), variables de control

**1.5 Justificación**

- Técnica, ambiental, económica y metodológica (diseño factorial, operacionalización causal, protocolo estadístico reproducible)

**1.6 Alcances y limitaciones**

- Cuantitativa, aplicada, explicativa; 12 tratamientos; 54 KPI; SEAI Iquitos
- Limitaciones: sin red física, CityLearn v3 propuesto = extensión experimental, corrida de referencia 5 episodios / 1 semilla

### Capítulo 2. Marco teórico

**2.1 Antecedentes de la investigación** (literatura últimos 5 años; tesis doctorales, maestría y artículos arbitrados)

- 2.1.1 Flexibilidad energética con MADRL (D-VD.1): CityLearn v2, MERLIN, Charbonnier (2024), Bušić et al. (2023)
- 2.1.2 Emisiones de carbono con MADRL (D-VD.2): Zhang et al. (2024), Song et al. (2025), Keren et al. (2024)
- 2.1.3 Costos energéticos con MADRL (D-VD.3): Amer et al. (2023), Weber et al. (2024), Schaap (2024)
- 2.1.4 Marco técnico MADRL y sistemas aislados: CTDE, Dec-POMDP, HAPPO/MASAC/MATD3/MAAC, Domínguez Barbero (2026), Rosero Bernal (2024)

**2.2 Bases teóricas**

- 2.2.1 Flexibilidad energética
- 2.2.2 Emisiones de carbono (CI dinámica SEAI)
- 2.2.3 Costos energéticos (TOU)
- 2.2.4 Dec-POMDP, CTDE y los cuatro algoritmos — Tabla 2.1

**2.3 Definición de términos**

- comunidad inteligente, DER, KPI, tratamiento, MADRL, CityLearn v2, CityLearn v3 propuesto

### Capítulo 3. Metodología

**3.1 Tipo, enfoque y nivel de investigación**

- Cuantitativa, aplicada, explicativa; diseño experimental de simulación; validez interna por control de variables

**3.2 Diseño experimental**

- Factorial 4×3; Figura 3.1; Tabla 3.1 escenarios E1/E2/E3 con pesos [flex, CO₂, costo]

| Escenario | Pesos | Objetivo dominante | Asociado a |
|-----------|-------|-------------------|------------|
| E1 | [0,70; 0,15; 0,15] | Flexibilidad | OE.1 / HE.1 |
| E2 | [0,15; 0,70; 0,15] | Emisiones CO₂ | OE.2 / HE.2 |
| E3 | [0,25; 0,15; 0,60] | Costos | OE.3 / HE.3 |

**3.3 Unidad de análisis, población y muestra**

- Unidad: tratamiento (algoritmo × escenario)
- Muestra: diseño factorial completo (12 tratamientos)

**3.4 Datos: dataset `citylearn_iquitos_2023_2025`**

- Pipeline 10 etapas; Figura 3.2; Tabla 3.2 (17 edificios, 26 304 h, 222 CSV, PV 48 790,9 kWp, BESS 26 266 kWh / 6 648 kW, 185 tomas EV, CI 0,672–0,790, TOU 0,26/0,38)

**3.5 Variables y operacionalización**

- Referencia Tabla 1.2; 54 KPI oficiales

**3.6 Técnicas e instrumentos de recolección**

- Artefactos por corrida: `results.json`, `training_summary.json`, `timeseries.csv`, `trace.csv`, checkpoints, figuras

**3.7 Técnicas de análisis estadístico**

Protocolo de comparación experimental de algoritmos MADRL, fundamentado en los estándares vigentes de comparación rigurosa de RL (Colas et al., 2019; Agarwal et al., 2021; Patterson et al., 2024; Demšar, 2006):

- **Nivel descriptivo:** por tratamiento, media, desviación estándar, valores extremos y coeficiente de variación (CV) de los KPI por dimensión. La estocasticidad del entrenamiento se trata como error de medición, por lo que se reporta tendencia central con su incertidumbre, no solo estimadores puntuales (Agarwal et al., 2021).
- **Réplicas y potencia estadística:** cada tratamiento debe ejecutarse con **múltiples semillas independientes**. La literatura advierte que menos de 5 corridas es insuficiente para conclusiones causales sólidas y recomienda análisis de potencia (idealmente ≥ 20 semillas para efectos moderados) (Colas et al., 2019; Patterson et al., 2024). La corrida de referencia (1 semilla, 5 episodios) se declara explícitamente como **limitación de validez** y se consolida con la corrida canónica multi-semilla.
- **Nivel inferencial (α = 0,05):**
  1. **Shapiro-Wilk** — normalidad por grupo (justifica el uso de pruebas no paramétricas).
  2. **Kruskal-Wallis** — diferencia global entre los 4 niveles del factor algoritmo por escenario (equivalente no paramétrico de ANOVA de una vía).
  3. **Post-hoc de Dunn con corrección Bonferroni/Holm** — comparaciones por pares tras un Kruskal-Wallis significativo, controlando el error family-wise (Dunn, 1964). Mann-Whitney U y Wilcoxon se reportan como pruebas complementarias par-a-par y pareadas; recordar que Mann-Whitney U contrasta **dominancia estocástica**, no estrictamente medianas, salvo igualdad de forma y dispersión.
  4. **Wilcoxon de rangos con signo** — diferencias pareadas por indicador dentro del mismo escenario.
- **Tamaños de efecto e intervalos:** ε² (eta-cuadrado) de Kruskal-Wallis, rank-biserial para pares, e intervalos de confianza por bootstrap. Cuando sea aplicable, métricas agregadas robustas tipo media intercuartil (IQM) y performance profiles (`rliable`, Agarwal et al., 2021).
- **Corrección por comparaciones múltiples:** ante 6 pares de algoritmos, aplicar umbral ajustado (Bonferroni α' = 0,05/6 ≈ 0,0083 o Holm) para preservar garantías de error.
- KPIs expresados como **razón al baseline CityLearn v2** (1,0 = baseline; menor = mejor).

### Capítulo 4. Desarrollo de la propuesta

**4.1 Arquitectura del sistema experimental** — Tabla 4.1 (4 capas: CityLearn v2, v3 propuesto, backends, evaluación)

**4.2 Formulación Dec-POMDP**

- ℳ = ⟨S, {Aᵢ}, T, R, {Oᵢ}, Ω, γ, T⟩; N = 17 agentes
- Estado global concatenado: **1 856 dimensiones** (entorno cargado)
- Observaciones locales heterogéneas: 57–330 dims por edificio
- Acciones heterogéneas: 5–44 por edificio
- **γ = 0,9999**; T = 8 760 pasos

**4.3 Esquema CTDE y función de recompensa multiobjetivo**

- `CityLearnV3MADRLRewardFunction`; perfil activo **`unified_comparable_v4`** (idéntico en los 4 algoritmos)
- Tabla 4.2:

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| team_reward_ratio | 0,70 | Coordinación cooperativa Dec-POMDP |
| peak_weight / ramp_weight | 0,45 / 0,35 | KPI primario y secundario flexibilidad |
| ev_weight | 0,25 | Cumplimiento carga EV |
| bess_cycle_weight | 0,10 | Penalización oscilación BESS (v4) |
| ev_urgency_hours | 8,0 | Ventana urgencia ampliada (v4) |
| reward_scale | 1,00 | Gradientes comparables |

**4.4 Algoritmos e hiperparámetros** — Tabla 4.3

- Corrida canónica objetivo: 50 episodios × 8 760 pasos, GPU A100 80 GB (Colab, `two_phase_happo_masac`)
- Corrida de referencia local: 5 episodios, RTX 4060 8 GB
- Hiperparámetros comunes: hidden [256,256], actor_lr 3e-4, critic_lr 1e-3, gamma 0,9999, batch 256

**4.5 Aportes originales al motor de simulación** — Tabla 4.4 (A1–A4; commit 54b1938e)

**4.6 Implementación y entorno computacional**

- Python 3.9, PyTorch 2.8.0+cu126, adaptador común `citylearn_v3_training_common.py`

### Capítulo 5. Resultados y contrastación de hipótesis

Organize in two levels: **descriptive effect** then **inferential hypothesis testing**.

**5.1 Experimentos realizados**

- 12/12 tratamientos completados (corrida de referencia v4, 5 episodios)
- Tiempos orientativos: HAPPO 57–67 min/escenario; MASAC 2–2,5 h; MAAC ~5,5 h; MATD3 6–7,5 h

**5.2 Análisis descriptivo del efecto sobre la VD**

- Tabla 5.1: estadística descriptiva D-VD.1 por tratamiento (media, desv., mín., máx., CV %)
- Hallazgo clave preliminar: **MATD3 CV < 1,1 %** vs HAPPO **> 9 %**
- Figuras 5.0 (convergencia), 5.2 (flexibilidad E1), 5.4 (éxito partida EV), 5.5 (matriz KPI E1)

**5.3 Efecto coordinado: ranking ponderado por escenario**

- Puntuación global ponderada por eje (pesos 0,34 / 0,33 / 0,33)
- Tabla 5.2 preliminar (corrida 5 ep):

| Escenario | Mejor MADRL | Puntuación | 2.º | 3.º | 4.º |
|-----------|-------------|------------|-----|-----|-----|
| E1 flexibilidad | MATD3 | 0,487 | MAAC 0,440 | MASAC 0,395 | HAPPO 0,338 |
| E2 CO₂ | MATD3 | 0,751 | MAAC 0,536 | MASAC 0,428 | HAPPO 0,307 |
| E3 costos | MATD3 | 0,733 | MAAC 0,602 | MASAC 0,442 | HAPPO 0,395 |

- Figuras 5.1 (ranking global), 5.3 (radial por eje)
- Nota: CityLearn v2 baseline puede conservar ventaja global en E1 con presupuesto 5 episodios

**5.4 Contrastación inferencial de las hipótesis**

- Shapiro-Wilk → justifica el uso de pruebas no paramétricas
- Kruskal-Wallis global: **p = 0,0459** (< 0,05) → rechaza H₀ de ausencia de efecto del factor algoritmo; respalda HG. Reportar el tamaño de efecto ε² asociado.
- Post-hoc de Dunn (Bonferroni/Holm) tras el Kruskal-Wallis significativo, con su tabla de p ajustados y tamaños de efecto.
- Tabla 5.3 Wilcoxon pareado (α = 0,05): HAPPO difiere significativamente de MASAC, MATD3 y MAAC; MATD3 vs MASAC/MAAC sin diferencia sistemática en el agregado. Acompañar con rank-biserial e intervalos bootstrap.
- Contrastación HE.1–HE.3 y HG según evidencia disponible; declarar cada decisión (rechazo / no rechazo de H₀) con su prueba, p ajustado y tamaño de efecto.
- Figura 5.6 matriz de p-valores Wilcoxon
- **Validez:** las cifras provienen de 1 semilla / 5 episodios; los contrastes se reconfirman con la corrida canónica multi-semilla antes de elevar las conclusiones a definitivas (Colas et al., 2019; Agarwal et al., 2021).

**5.5 Discusión de resultados**

- Ventaja off-policy + crítico centralizado (MATD3)
- Limitación presupuesto entrenamiento vs baseline CityLearn v2 (Schaap, 2024)
- Robustez por baja variabilidad inter-indicador

Mark all values from the 5-episode reference run as **preliminares** until the canonical 50-episode Colab run replaces them. Use `[REEMPLAZAR con corrida canónica 50 ep]` when canonical artifacts are unavailable.

### Capítulo 6. Conclusiones y trabajo futuro

**6.1 Conclusiones**

- Respuesta a OG/OE con evidencia causa-efecto
- MATD3 = mayor efecto coordinado preliminar
- Aportes metodológicos: benchmark unificado + 4 extensiones motor CityLearn

**6.2 Limitaciones**

- 5 episodios, 1 semilla, GPU local, v3 propuesto experimental

**6.3 Trabajo futuro**

- Corrida canónica 50 ep × 12 tratamientos, multi-semilla
- Optuna recompensa/hiperparámetros
- Mann-Whitney U con effect sizes (Agarwal et al., 2021)
- Transferibilidad a otros sistemas aislados peruanos

**6.4 Cronograma de culminación**

- Figura 6.1 (24 meses)

### Referencias bibliográficas

- APA 7.ª edición
- Priorizar literatura últimos 5 años + obras seminales CTDE/Dec-POMDP
- Fuente consolidada: `docs/tesis_capitulos/Referencias_APA.md`

**Referencias metodológicas obligatorias (diseño experimental y estadística RL):**

- Colas, C., Sigaud, O., & Oudeyer, P.-Y. (2019). *A hitchhiker's guide to statistical comparisons of reinforcement learning algorithms.* arXiv:1904.06979. https://arxiv.org/abs/1904.06979
- Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., & Bellemare, M. G. (2021). *Deep reinforcement learning at the edge of the statistical precipice.* NeurIPS, 34, 29304–29320. https://arxiv.org/abs/2108.13264
- Patterson, A., Neumann, S., White, M., & White, A. (2024). *Empirical design in reinforcement learning.* Journal of Machine Learning Research, 25. https://arxiv.org/abs/2304.01315
- Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2018). *Deep reinforcement learning that matters.* AAAI, 32(1). https://doi.org/10.1609/aaai.v32i1.11694
- Demšar, J. (2006). *Statistical comparisons of classifiers over multiple data sets.* JMLR, 7, 1–30.
- Dunn, O. J. (1964). *Multiple comparisons using rank sums.* Technometrics, 6(3), 241–252. https://doi.org/10.1080/00401706.1964.10490181

Marcar como `dato bibliográfico pendiente de verificación` cualquier dato faltante (volumen, página, DOI).

## Evidence sources (current project only)

Primary:

- `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`
- `docs/tesis_capitulos/`
- `CityLearn/configs/citylearn_v3_madrl_training.yaml`
- `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`
- `docs/JUSTIFICACION_DISENO_EXPERIMENTAL_ESCENARIOS_PARALELO.md`
- `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md`

Training outputs (use latest completed v4 session):

- `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` (corrida local referencia 5 ep)
- Canonical target: `outputs/colab_50ep/` or new `citylearn_v3_madrl_full_*_v4` with 50 episodes

Dataset audit:

- `outputs/dataset_audit/`
- `docs/INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md`

Do **not** use archived sessions (`20260613_010234`, `_archive/`) as definitive thesis evidence unless explicitly labeled exploratory.

## Resumen / Abstract content requirements

Spanish Resumen and English Abstract must include:

- Experimental cause-effect framing (VI/VD, 12 treatments, 54 KPI)
- CityLearn v2 + v3 propuesto + dataset Iquitos (17 buildings, DER totals)
- Dec-POMDP/CTDE; four algorithms; unified v4 reward
- Statistical protocol (descriptive + Shapiro/KW/MWU/Wilcoxon)
- Preliminary finding: MATD3 largest and most stable coordinated effect; KW p = 0,0459
- Keywords: aprendizaje por refuerzo multiagente, diseño experimental, Dec-POMDP, CTDE, flexibilidad energética, emisiones CO₂, microrred aislada, Iquitos

## Quality rules

- Never invent DOI, results, p-values, or KPI values not present in current artifacts or the canonical DOCX
- Mark pending canonical-run values explicitly
- Keep MADRL terminology (not MARL) per project rules
- Distinguish CityLearn v2 (base) from CityLearn v3 propuesto (thesis extension)
