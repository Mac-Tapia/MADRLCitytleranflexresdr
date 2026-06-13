# Cooperación, Coordinación y Control Distrital MADRL

**Fecha:** 2026-06-12
**Proyecto:** MADRLCitytleranflexresdr
**Sección tesis:** Capítulo III §3.2.4, §3.2.5, §3.3.2, §3.3.3

---

## 1. KPIs por Escenario de Entrenamiento

Cada escenario evalúa **todos los KPIs** del entorno CityLearn al final del episodio, aunque el entrenamiento priorice uno. Los KPIs son computados a nivel **distrital** (suma o promedio sobre los 17 edificios y 8 760 pasos del episodio), no por edificio individual.

| Escenario | OE | w_eje | KPI primario de evaluación | KPIs secundarios evaluados |
| --------- | -- | :---: | -------------------------- | -------------------------- |
| **E1** | OE.1 Flexibilidad | 0.70 | `peak_average` · `ramping_average` · `1−load_factor_average` | `carbon_emissions_total` · `electricity_cost_total` |
| **E2** | OE.2 Emisiones CO₂ | 0.70 | `carbon_emissions_total` · `carbon_emissions_from_electrical_consumption` | `peak_average` · `electricity_cost_total` |
| **E3** | OE.3 Costos | 0.60 | `electricity_cost_total` · `electricity_cost_from_electrical_consumption` | `peak_average` · `carbon_emissions_total` |

> **Distinción crítica:** los KPIs de evaluación son los del entorno CityLearn (computados independientemente de la función de recompensa), no las componentes del reward. Esto garantiza comparabilidad entre escenarios aunque los pesos de entrenamiento sean distintos.

### KPI de recompensa (seguimiento de entrenamiento, no de evaluación)

Extraídos de `live_progress.json` y `trace.csv` durante el entrenamiento:

```
reward_mean           ← retorno promedio del episodio
flex_component_mean   ← componente flex de la recompensa
co2_component_mean    ← componente carbono
cost_component_mean   ← componente costo
ev_component_mean     ← componente EV
team_reward_mean      ← promedio distrital de recompensas
```

Estos se usan para seguimiento de convergencia, no para el ranking inter-algoritmo final.

---

## 2. Qué ES el MADRL — Definición Operativa

```
Edificio (agente)  ≠  MADRL

Edificio  →  quién decide (la entidad que actúa)
MADRL     →  cómo aprendió a decidir, y cómo los 17 aprenden coordinadamente
```

El **edificio es el agente**: tiene una red neuronal πᵢ que mapea su observación local a su acción local. En ejecución, solo corre esa política — MADRL ya no "corre".

El **MADRL es el framework algorítmico** que entrena las 17 políticas simultáneamente con mecanismos de coordinación. Cuando el entrenamiento termina, MADRL produjo 17 redes neuronales calibradas para trabajar juntas.

### Qué tiene cada edificio-agente

```
Observación local oᵢ(t):
  [mes, hora, tipo_día, T_interior, demanda_enfriamiento, DHW,
   carga_no_desplazable, generación_solar,
   BESS_SOC, P_BESS_acción,
   EV_estado_k, EV_salida_k, EV_SOC_requerido_k, EV_llegada_estimada_k,
   intensidad_carbono, precio_electricidad,
   GHI, T_ambiente, HR]
  → dimensiones: 54–327 por edificio según cantidad de cargadores EV

Acción local aᵢ(t):
  [P_BESS ∈ [−P_max, +P_max] kW,
   P_EV_cargador_k ∈ [0, P_nominal_k] kW por toma,
   acción_lavadora ∈ {operar, diferir}]
  → dimensiones: 2–44 por edificio

Red neuronal πᵢ: oᵢ → aᵢ   (MLP o RNN según el backend)
```

### Qué añade MADRL sobre 17 DRL independientes

| Problema sin MADRL | Solución MADRL |
| ------------------ | -------------- |
| Todos los edificios descargan BESS al mismo tiempo (misma señal de precio) → pico de exportación | Crítico centralizado aprende que la acción individual es mala cuando el distrito está en ese estado |
| Agente que mejora localmente puede perjudicar al distrito | `mixed_reward_i = 0.30·reward_i + 0.70·team_reward` — 70% del gradiente es señal distrital |
| Sin garantía de que mejoras individuales sean compatibles | HAPPO: actualización secuencial garantiza mejora monótona de la política conjunta |
| Sin ponderación de influencia entre agentes | MAAC: atención aprende cuánto influye cada edificio en el valor distrital |

---

## 3. Cooperación, Coordinación y Comunicación — Dónde Ocurre Cada Cosa

### 3.1 Durante entrenamiento — aquí está TODA la cooperación real

| Mecanismo | Qué hace | Algoritmo |
| --------- | -------- | --------- |
| **Crítico centralizado** `Q(s, a₁,…,a₁₇)` o `V(s)` | Ve estado global `s = [o₁,…,o₁₇]` — evalúa si la acción conjunta es buena para el distrito | HAPPO, MATD3, MAAC |
| **QMIX mixing network** | Combina Q-values individuales en Q global con propiedad IGM: `argmax Q_total = (argmax Q₁,…,argmax Q₁₇)` — la acción distrital óptima coincide con cada agente maximizando su propio Q | MASAC |
| **team_reward** `= (1/N) Σᵢ reward_i` | Señal colectiva del desempeño distrital | Todos |
| **mixed_reward_i = 0.30·reward_i + 0.70·team_reward** | 70% del gradiente de cada agente refleja el rendimiento del distrito | Todos |
| **Actualización secuencial (HAPPO)** | Actualiza π₁, luego π₂ condicionado al nuevo π₁, ..., π₁₇ al final. Garantiza que ninguna actualización individual deteriora la política conjunta | HAPPO |
| **Mecanismo de atención (MAAC)** | Crítico de cada agente pondera contribuciones de los otros 16 con 4 cabezas de atención | MAAC |

### 3.2 Durante ejecución — NO hay comunicación

```
Ejecución: πᵢ(aᵢ | oᵢ)  ←  solo observación local del edificio i
```

Los 17 agentes actúan **completamente independientes** en tiempo de inferencia. No hay red de comunicación, no hay mensajes entre edificios, no hay acceso al estado de otros agentes. La coordinación fue **internalizada** en los pesos de la red neuronal durante el entrenamiento CTDE.

Esta propiedad es la que hace el sistema desplegable en edificios reales sin infraestructura de comunicación especial.

### 3.3 Coordinación implícita a través del entorno físico

Tres fuentes de coordinación que no requieren mensajes explícitos:

1. **Señales compartidas**: todos los edificios observan el mismo `electricity_price(t)` y `carbon_intensity(t)`. En hora punta todos tienen incentivo a descargar BESS → reducción colectiva sin coordinación explícita.

2. **Internalización CTDE**: durante 43 800 pasos de entrenamiento el crítico centralizado evaluó miles de combinaciones de acciones conjuntas. La política aprendida tiene codificado implícitamente "qué hacen los otros en este contexto de precio/clima".

3. **Física del entorno** (único canal implícito en ejecución):
```
district_import(t) = Σᵢ max(0, net_load_i(t))
peak_share(t)      = district_import(t) / 17
ramp_share(t)      = |district_import(t) − district_import(t−1)| / 17
```
Si 16 edificios descargan BESS y reducen `district_import(t)`, el edificio 17 recibe menor penalización flex vía `team_reward`. Este es el único "mensaje" entre agentes en ejecución: el estado compartido de la red eléctrica.

---

## 4. Control a Nivel Distrito — Cómo los 17 Agentes Producen Control Emergente

### 4.1 No existe un agente distrital

No hay controlador central, no hay maestro enviando setpoints, no hay jerarquía de control. El control distrital es un **comportamiento emergente** de los 17 agentes descentralizados actuando en el mismo entorno físico.

### 4.2 Loop de control distrital en cada paso horario t

```
1. Cada edificio i observa oᵢ local
2. πᵢ(aᵢ | oᵢ) → acción local (BESS, EV, lavadora)
3. Entorno ejecuta las 17 acciones simultáneamente
4. Entorno computa:
     net_load_i(t)       = import_i(t) − export_i(t)
     district_import(t)  = Σᵢ max(0, net_load_i(t))   ← señal distrital
     peak_share(t)       = district_import(t) / 17
     ramp_share(t)       = |district_import(t) − district_import(t−1)| / 17
5. reward_function computa reward_i(t)
     → flex_component usa peak_share y ramp_share      ← efecto distrital entra aquí
6. team_reward(t) = mean(reward_i(t))                  ← promedia los 17
7. mixed_reward_i = 0.30·reward_i + 0.70·team_reward
8. [entrenamiento] gradiente actualiza πᵢ usando mixed_reward_i
9. t+1: cada edificio actúa de nuevo
```

### 4.3 Mecanismo distrital por algoritmo

**HAPPO — garantía matemática de mejora distrital:**

El Surrogate Objective garantiza `J(π_new) ≥ J(π_old)` sobre la política **conjunta**. Cada actualización individual de πᵢ está condicionada a que no deteriore el rendimiento conjunto. El crítico centralizado `V(s)` donde `s = [o₁,...,o₁₇]` evalúa el valor del estado completo del distrito.

**MASAC + QMIX — descomposición distrital:**

```
Q_total(s, a₁,...,a₁₇) = f( Q₁(o₁,a₁), ..., Q₁₇(o₁₇,a₁₇), s )
con ∂Q_total/∂Qᵢ ≥ 0   (monotónica)
```

Propiedad IGM: `argmax Q_total = (argmax Q₁,..., argmax Q₁₇)`. En ejecución, cada edificio actúa greedy local y el resultado es globalmente óptimo — sin comunicación. El razonamiento distrital queda codificado en los pesos de la red de mezcla.

**MATD3 — doble crítico conjunto:**

Dos críticos `Q1(s, a₁,...,a₁₇)` y `Q2(s, a₁,...,a₁₇)` evalúan la acción conjunta de los 17 edificios. El estimador pesimista `min(Q1, Q2)` evita sobreestimar el valor distrital. El gradiente del actor de cada edificio i es:
```
∇_{θᵢ} J = E[ ∇_{aᵢ} Q1(s, a₁,...,aᵢ,...,a₁₇) · ∇_{θᵢ} πᵢ(oᵢ) ]
```
El edificio i aprende a mejorar el Q **distrital**, no su Q individual.

**MAAC — atención distrital dinámica:**

```
Vᵢ = f( encode(oᵢ, aᵢ),  attention-pool({ encode(oⱼ, aⱼ) : j≠i }) )
```
El crítico de cada edificio aprende a ponderar la influencia de los otros 16. Edificios con mayor impacto distrital (B01 BESS 6 747 kWh, B06 32 cargadores, B07 42 cargadores) recibirán mayor peso de atención de los demás.

### 4.4 Comportamiento distrital emergente

```
Sin MADRL (baseline):                    Con MADRL entrenado:
  Pico = Σᵢ pico_i (todos sincronizan)   Pico < Σᵢ pico_i (descarga escalonada)
  Ramping violento (17 sinc)             Ramping suavizado
  EV carga al llegar                     EV carga en valle / solar disponible
  BESS reactivo                          BESS anticipa pico distrital

Por escenario:
  E1 → crítico penaliza peak_share      → agentes aprenden a coordinar descarga en punta
  E2 → crítico penaliza import × CI     → agentes aprenden a importar cuando CI es baja
  E3 → crítico penaliza import × precio → agentes aprenden arbitraje TOU
```

---

## 5. Determinación del Mejor MADRL Global (O.G.)

### 5.1 Problema de la determinación global

Los escenarios E1/E2/E3 entrenan con vectores de peso distintos. El algoritmo que "gana" E1 fue entrenado para maximizar flex — no es un ganador justo en los otros ejes. La determinación de O.G. requiere un método de agregación inter-eje que no favorezca el eje de entrenamiento de ningún algoritmo.

### 5.2 Score_OG — ranking integrado multiobjetivo

**Paso 1 — Extracción de KPIs por eje y algoritmo:**

```
KPI_flex(a)  ← peak_average            de a/E1_seed_0/data/results.json   (↓ mejor)
KPI_co2(a)   ← carbon_emissions_total  de a/E2_seed_0/data/results.json   (↓ mejor)
KPI_cost(a)  ← electricity_cost_total  de a/E3_seed_0/data/results.json   (↓ mejor)
```

**Paso 2 — Normalización min-max inter-algoritmo (invirtiendo a "mayor = mejor"):**

```
KPI_flex_norm(a) = 1 − [KPI_flex(a) − min_a KPI_flex] / [max_a KPI_flex − min_a KPI_flex]
KPI_co2_norm(a)  = 1 − [KPI_co2(a)  − min_a KPI_co2]  / [max_a KPI_co2  − min_a KPI_co2]
KPI_cost_norm(a) = 1 − [KPI_cost(a) − min_a KPI_cost] / [max_a KPI_cost − min_a KPI_cost]
```

**Paso 3 — Score global con pesos iguales [1/3, 1/3, 1/3]:**

```
Score_OG(a) = (1/3)·KPI_flex_norm(a) + (1/3)·KPI_co2_norm(a) + (1/3)·KPI_cost_norm(a)
```

Justificación de pesos iguales: el O.G. exige gestión *coordinada* sin preferencia a priori por ningún eje (Roijers et al., 2013, JAIR; Felten et al., 2024, JAIR arXiv:2311.12495).

### 5.3 Análisis de dominancia de Pareto (complementario)

El algoritmo `a` **domina de Pareto** al algoritmo `b` si:
```
KPI_flex_norm(a) ≥ KPI_flex_norm(b)  Y
KPI_co2_norm(a)  ≥ KPI_co2_norm(b)   Y
KPI_cost_norm(a) ≥ KPI_cost_norm(b)  Y
∃ eje k : KPI_k_norm(a) > KPI_k_norm(b)
```
Si existe un algoritmo no dominado → es el ganador inequívoco de O.G. Si ninguno domina (frente de Pareto) → el Score_OG decide.

### 5.4 Ranking de Borda (verificación no paramétrica)

Para cada eje e, asignar rango r_e(a) ∈ {1,2,3,4} donde rango 1 = mejor KPI:
```
Borda(a) = r_flex(a) + r_co2(a) + r_cost(a)
```
El algoritmo con menor Borda score es el mejor coordinado (O.G.). El ranking Borda y el Score_OG deben coincidir; si divergen, reportar ambos y discutir en §3.4.

### 5.5 Protocolo estadístico para O.G.

- **Kruskal-Wallis** sobre Score_OG de los 5 episodios por algoritmo: H₀ = todos equivalentes; si p < 0.05 existe diferencia significativa global.
- **Mann-Whitney U** par-a-par (6 pares) sobre Score_OG con corrección Bonferroni α' = 0.05/6 = 0.0083.
- **Effect size** ε² (eta-cuadrado de Kruskal-Wallis): pequeño ≥0.01, mediano ≥0.06, grande ≥0.14.

---

## 6. Desagregación por Edificio — Control Individual y Contribución al Distrito

### 6.1 KPIs por edificio i

Extraídos de `{algo}/{scenario}_seed_0/data/timeseries.csv`:

```
peak_i        = max_t ( net_load_i(t) )
co2_i         = Σ_t max(0, import_i(t)) · CI(t)
cost_i        = Σ_t max(0, import_i(t)) · p(t)
self_suff_i   = 1 − Σ_t import_i(t) / Σ_t non_shiftable_load_i(t)
bess_util_i   = Σ_t |P_bess_i(t)| / (T · P_bess_max_i)
ev_served_i   = Σ_t EV_sessions_completed_i(t) / EV_sessions_total_i
```

### 6.2 Métricas de coordinación distrital

```
district_import(t) = Σᵢ max(0, net_load_i(t))
peak_district      = max_t district_import(t)
peak_share_i(t)    = net_load_i(t) / district_import(t)
ramp_district(t)   = |district_import(t) − district_import(t−1)|
```

### 6.3 Contribución individual — análisis counterfactual

```
Δpeak_i  = peak_district_sin_i − peak_district_con_i
Δco2_i   = co2_district_sin_i  − co2_district_con_i
Δcost_i  = cost_district_sin_i − cost_district_con_i
```
"sin_i" = política ganadora con el agente i en modo pasivo (sin BESS, sin control EV). Cuantifica cuánto aporta cada edificio a la coordinación distrital.

### 6.4 Edificios críticos para la coordinación

Edificios con mayor Δpeak_i esperado por tamaño de DER:

| Edificio | BESS kWh | EV tomas | Factor crítico |
| -------- | :------: | :------: | -------------- |
| B01 ELECTRO ORIENTE | 6 747 | 4 | BESS más grande del distrito |
| B06 MALL AVENTURA | 2 541 | 32 | Mayor concentración de cargadores EV |
| B07 UNAP BIOLOGÍA | 984 | 42 | Mayor número de tomas EV |
| B11 HOSPITAL LORETO | 1 901 | 3 | Carga base constante 24h (healthcare) |
| B12 ESSALUD | 4 346 | 3 | Segundo BESS más grande |

---

## 7. Resumen Conceptual

```
ENTRENAMIENTO (donde ocurre la cooperación):
  Crítico centralizado  → ve s = [o₁,...,o₁₇]
  QMIX (MASAC)          → mezcla Q-values con garantía IGM
  team_reward           → señal colectiva del distrito
  mixed_reward (70/30)  → 70% gradiente = señal de equipo
  Actualiz. secuencial  → HAPPO garantiza mejora conjunta
  Atención (MAAC)       → ponderación dinámica de agentes

EJECUCIÓN (donde NO hay comunicación):
  πᵢ(aᵢ | oᵢ)          → solo observación local
  Coordinación          → internalizada durante CTDE

ENTORNO (canal físico siempre activo):
  district_import(t)    → única "señal" compartida en ejecución
  team_reward           → propaga efecto colectivo a gradientes individuales

PREGUNTA DE TESIS:
  ¿Cuál algoritmo (HAPPO/MASAC/MATD3/MAAC) produce las 17 políticas
  que mejor coordinan flexibilidad, CO₂ y costos de forma simultánea?
  → Score_OG = mean(KPI_flex_norm, KPI_co2_norm, KPI_cost_norm)
  → Verificado con dominancia de Pareto, ranking de Borda y suite estadística
```

---

## 8. Referencias Académicas

- Roijers, D. M., Vamplew, P., Whiteson, S., & Farquhar, R. (2013). A survey of multi-objective sequential decision-making. *Journal of Artificial Intelligence Research, 48*, 67–113.
- Felten, F., Alegre, L. N., Nowe, A., Bazzan, A. L. C., Talbi, E.-G., Danoy, G., & Majeri, P. (2024). A toolkit for reliable benchmarking and research in multi-objective reinforcement learning. *Journal of Artificial Intelligence Research*. arXiv:2311.12495.
- Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Yang, Y. (2021). Trust region policy optimisation in multi-agent reinforcement learning. arXiv:2109.11251. [HAPPO]
- Lowe, R., Wu, Y., Tamar, A., Harb, J., Abbeel, P., & Mordatch, I. (2017). Multi-agent actor-critic for mixed cooperative-competitive environments. *Advances in Neural Information Processing Systems, 30*. [MADDPG/CTDE]
- Rashid, T., Samvelyan, M., de Witt, C. S., Farquhar, G., Foerster, J., & Whiteson, S. (2018). QMIX: Monotonic value function factorisation for deep multi-agent reinforcement learning. *Proceedings of ICML 2018*. [QMIX]
- Iqbal, S., & Sha, F. (2019). Actor-attention-critic for multi-agent reinforcement learning. *Proceedings of ICML 2019*. [MAAC]
- Nweye, K., Sankaranarayanan, S., & Nagy, Z. (2024). CityLearn v2: Energy-flexible, resilient, and occupant-centric control of grid-interactive communities. *Journal of Building Performance Simulation*. arXiv:2405.03848. [CityLearn v2 KPIs]
- Hu, J., Zhu, Y., Wang, H., Bhatt, A., Garg, A., & Wen, Y. (2023). HARL: Heterogeneous-agent reinforcement learning. *Journal of Machine Learning Research*. arXiv:2304.09870. [HAPPO implementación]
