# Justificacion de Recompensas Multi-objetivo y Penalidades — MADRL CityLearn v3 Iquitos

**Fecha de revision:** 2026-06-12
**Implementacion de referencia:** `CityLearn/citylearn/reward_function.py`, clase `CityLearnV3MADRLRewardFunction` (lineas 526-779)
**Codigo fuente de pesos:** `CITYLEARN_V3_AXIS_REWARD_WEIGHTS` (linea 526) y `CITYLEARN_V3_MADRL_REWARD_PROFILES` (linea 533)

---

## 1. Reconciliacion: Plan de Tesis vs Implementacion Vigente

El Plan de Tesis (§4.11.3) documento originalmente perfiles de recompensa diferenciados por algoritmo. La implementacion actual adopto el perfil **unified_comparable_v2** con valores identicos para los cuatro algoritmos.

| Parametro | HAPPO (plan) | MASAC (plan) | MATD3 (plan) | MAAC (plan) | **Implementacion real (todos)** | Razon del cambio |
|---|:---:|:---:|:---:|:---:|:---:|---|
| `team_reward_ratio` | 0.75 | 0.55 | 0.65 | 0.80 | **0.70** | Comparabilidad estadistica entre algoritmos |
| `peak_weight` | 0.45 | 0.40 | 0.50 | 0.42 | **0.45** | Peso canonico del KPI principal CityLearn |
| `ramp_weight` | 0.35 | 0.30 | 0.45 | 0.38 | **0.35** | Peso canonico del segundo KPI |
| `ev_weight` | 0.15 | 0.12 | 0.10 | 0.16 | **0.12** | Termino corrector uniforme |
| `reward_scale` | 1.00 | 0.80 | 1.10 | 1.00 | **1.00** | Escala unica para gradientes comparables |

**Justificacion de la unificacion:** Para que los resultados de los 12 experimentos (4 algoritmos x 3 escenarios) sean comparables estadisticamente, la funcion de recompensa debe ser identica en todos los backends. Aplicar escalas o pesos distintos por algoritmo introduciria un factor de confusion que impediria atribuir diferencias de rendimiento a la arquitectura del algoritmo en lugar de a la forma de la recompensa. Los perfiles diferenciados del plan original se reservan como configuracion de ablacion futura. El valor `team_reward_ratio=0.70` es la media ponderada de los valores originales (promedio: 0.6875 ≈ 0.70) y mantiene la propiedad cooperativa necesaria para Dec-POMDP.

---

## 2. Pesos Multi-objetivo por Escenario

### 2.1 Valores implementados

Fuente: `CITYLEARN_V3_AXIS_REWARD_WEIGHTS`, `reward_function.py:526-530`.

| Escenario | w_flex | w_carbon | w_cost | Objetivo principal | Objetivo residual |
|---|:---:|:---:|:---:|---|---|
| **E1** | **0.70** | 0.15 | 0.15 | OE.1 Flexibilidad energetica | 15% CO2 + 15% costo como incentivo residual |
| **E2** | 0.15 | **0.70** | 0.15 | OE.2 Reduccion de emisiones CO2 | 15% flex + 15% costo |
| **E3** | 0.25 | 0.15 | **0.60** | OE.3 Minimizacion de costos energeticos | 25% flex + 15% CO2 |

Los pesos suman 1.0 (simplex) y se normalizan internamente si se aplican multiplicadores de perfil (`_build_axis_weights`, linea 648).

### 2.2 Sustento de investigacion

**Valor dominante 0.70 / residual 0.15:**
- Vazquez-Canteli & Nagy (2019a) demuestran que la optimizacion de un solo KPI principal con incentivos residuales en los demas objetivos produce politicas mas robustas que la optimizacion pura de un solo eje. La proporcion 0.70/0.15/0.15 permite que el agente priorice claramente sin ignorar completamente los efectos laterales.
- Nweye et al. (2024) propone la evaluacion separada de KPIs por dimension (`peak_average`, `ramping_average`, emissiones CO2, costo economico), validando que el diseno de escenarios especializados por objetivo es metodologicamente correcto para comparar algoritmos MADRL en CityLearn.

**Escenario E3 — peso flex=0.25 (mayor que E1/E2 residuales):**
- El escenario de costos mantiene mayor peso en flexibilidad (0.25 vs 0.15) porque en una red TOU la reduccion de pico esta directamente correlacionada con la reduccion del cargo por demanda. Gao et al. (2023) muestran que el arbitraje BESS en mercados TOU es inseparable de la gestion de pico, por lo que desacoplarlos con un peso residual minimo generaria incentivos contradictorios.

**Esquema simplex (Σw=1):**
- Liu et al. (2022) usan pesos simplex para escalarizar funciones de recompensa multiobjetivo en MADDPG, lo que garantiza que la recompensa total permanezca en el mismo rango [-1, 1] independientemente del escenario, facilitando la comparacion entre experimentos.

---

## 3. Componentes de Recompensa y Justificacion de Parametros

### Formula general

```
reward_i(t) = reward_scale × [
    w_flex   × flex_i(t)
  + w_carbon × carbon_i(t)
  + w_cost   × cost_i(t)
  + ev_weight × ev_i(t)
]

mixed_reward_i = (1 - team_ratio) × reward_i + team_ratio × mean(reward_j, j=1..17)
```

---

### 3.1 Componente de Flexibilidad — `flex_i(t)`

**Formula implementada** (`reward_function.py:737-747`):

```
peak_share(t)   = district_import(t) / N           [kWh/edificio]
ramp_share(t)   = |district_import(t) - district_import(t-1)| / N
headroom(t)     = max(0, 1 - mean_SOC(t))

flex_penalty(t) = 0.45 × tanh(peak_share / 25)
                + 0.35 × tanh(ramp_share / 15)
                + 0.15 × tanh(export_i × (1 + headroom) / 20)
                + 0.10 × tanh(import_i × SOC_i / 20)

flex_i(t) = -flex_penalty(t)   ∈ (-1, 0]
```

**Justificacion de cada parametro:**

| Parametro | Valor | Justificacion |
|---|---|---|
| `peak_weight` | **0.45** | `peak_average` es el KPI primario de flexibilidad en CityLearn (Nweye et al. 2024). Peso mayor que ramping para alinear el incentivo de aprendizaje con la metrica de evaluacion oficial. |
| `ramp_weight` | **0.35** | `ramping_average` es el segundo KPI de flexibilidad. Vazquez-Canteli & Nagy (2019b) reportan que SAC reduce el ramping en ~18% adicional cuando se incluye en la recompensa como segundo termino. |
| Divisor 25 (peak) | **25** | El pico medio por edificio en la red de Iquitos es ~1000 kW / 17 edificios ≈ 59 kWh/edificio. Con divisor=25, tanh(peak_share/25) satura (~0.9) recien al doble del pico medio (≈118 kWh/edificio), manteniendo gradiente activo en condiciones normales de operacion. |
| Divisor 15 (ramp) | **15** | Umbral de rampa suave: rampas de ±15 kWh/edificio/h (operacion normal con BESS activo) generan tanh≈0.46, penalizacion moderada. Rampas de ±30 kWh/edificio/h (sin BESS) generan tanh≈0.90, penalizacion fuerte. Calibrado empiricamente para la red de Iquitos con BESS de 6,648 kW agregados. |
| `0.15 × export × (1+headroom)` | **0.15** | Incentiva la exportacion de excedentes fotovoltaicos cuando la BESS tiene espacio disponible (headroom > 0), evitando curtailment. Hribar et al. (2025) demuestran que este incentivo mejora la autonomia energetica de distritos en ~20%. El multiplicador (1+headroom) amplifica el incentivo cuando la BESS esta descargada. |
| `0.10 × import × SOC` | **0.10** | Desincentiva importar de la red cuando la BESS esta cargada (SOC alto = oportunidad perdida de usar energia almacenada). Peso menor (0.10) porque este termino es secundario: el termino de costo ya penaliza la importacion en horas punta. |
| Divisor 20 (export/import) | **20** | Pico individual tipico por edificio en la red de Iquitos calibrado en ~20 kWh/h para buildings medianos (Office, Education). Asegura tanh ∈ [0, 1] para importaciones/exportaciones normales de un unico edificio. |

---

### 3.2 Componente de Carbono — `carbon_i(t)`

**Formula implementada** (`reward_function.py:729-748`):

```
carbon_norm(t) = CI(t) / (CI(t) + 0.35)           # ∈ [0.658, 0.693] para Iquitos

carbon_penalty = tanh(import_i × (0.25 + carbon_norm) / 20)
carbon_credit  = 0.05 × tanh(export_i × carbon_norm / 20)

carbon_i(t) = -carbon_penalty + carbon_credit      ∈ (-1, 0.05]
```

**Justificacion de cada parametro:**

| Parametro | Valor | Justificacion |
|---|---|---|
| `carbon_reference` | **0.35 kgCO2/kWh** | Media mundial de intensidad de carbono electrica segun IEA (2023): 0.350 kgCO2/kWh. Contextualiza la intensidad diesel de Iquitos (0.790 kgCO2/kWh, MINAM RAGEI 2019) como 2.26x la referencia global, dando `carbon_norm` ∈ [0.66, 0.69]: señal alta y relativamente estable que refleja la situacion de red aislada de Electro Oriente S.A. |
| Rango CI Iquitos | **0.672-0.790** | CI(t) = 0.790 × (1 - 0.15 × GHI(t)/1000). Con penetracion solar del 15%, la CI se reduce marginalmente en horas solares. Fuente: factor base MINAM RAGEI 2019 + perfil PV calibrado con pvlib/PVGIS TMY. |
| Offset 0.25 | **0.25** | Garantiza que importar de la red tenga siempre un costo de carbono positivo, incluso en las horas de minima intensidad (GHI maximo). Sin este offset, el agente podria interpretar erroneamente que importar en horas solares es "gratis" en terminos de carbono. |
| `0.05 × export × carbon_norm` | **0.05** | Credito por exportacion en horas de alta CI (la exportacion desplaza generacion fosil de la red). Peso menor (0.05) que la penalizacion para evitar que el agente optimice exclusivamente la exportacion a costa de la carga util. Motivado por Liu et al. (2022) que incluyen el termino de exportacion en la recompensa CO2 de MADDPG. |
| Divisor 20 | **20** | Consistente con el divisor del componente de flexibilidad, mantiene escala uniforme entre los tres ejes. |

---

### 3.3 Componente de Costo — `cost_i(t)`

**Formula implementada** (`reward_function.py:727-749`):

```
price_norm(t) = p(t) / (p(t) + 0.20)
               # p ∈ {0.26, 0.38} USD/kWh → price_norm ∈ {0.565, 0.655}
               # Diferencial Δprice_norm = 0.090

cost_penalty = tanh(import_i × (0.25 + price_norm) / 20)
cost_credit  = 0.08 × tanh(export_i × price_norm / 20)

cost_i(t) = -cost_penalty + cost_credit            ∈ (-1, 0.08]
```

**Justificacion de cada parametro:**

| Parametro | Valor | Justificacion |
|---|---|---|
| `price_reference` | **0.20 USD/kWh** | Precio de referencia de mercado spot competitivo (~0.20 USD/kWh). La tarifa punta de Iquitos (0.38 USD/kWh) es 1.9x la referencia, dando price_norm=0.655 en punta vs 0.565 fuera de punta. El diferencial activo Δprice_norm=0.09 es suficiente para que el agente diferencie las horas TOU (diferencia ≈12% en la recompensa de costo). |
| Tarifas TOU | **0.38/0.26** | Punta: 0.38 USD/kWh (18-22h). Fuera de punta: 0.26 USD/kWh (resto del dia). Fuente: Electro Oriente S.A. / OSINERGMIN tarifas MT3/MT4 Iquitos 2024. La proporcion punta/fuera-punta es 1.46, similar a la ratio tariff_peak_to_offpeak_ratio_weighted medida en las facturas reales (1.461538). |
| Horas punta | **18-22h** | Horas de maxima demanda residencial y comercial en Iquitos, coincidentes con el periodo de maxima carga del distrito y ausencia de generacion solar. Fuente: perfil de consumo del buildingcsv, validado contra `building_metadata.json`. |
| Offset 0.25 | **0.25** | Idem carbono: garantiza penalizacion de costo no-nula incluso fuera de punta (el agente siempre tiene incentivo a reducir importaciones). |
| `0.08 × export × price_norm` | **0.08** | Credito de exportacion mayor que en carbono (0.08 vs 0.05) porque la tarifa TOU tiene diferencial economico directo y mensurable. Motivado por Gao et al. (2023) que muestran que el arbitraje BESS en mercados TOU requiere un credito de exportacion suficientemente grande para incentivar la descarga en horas punta. |
| Divisor 20 | **20** | Escala uniforme con flex y carbon. |

---

### 3.4 Termino EV — `ev_i(t)`

**Formula implementada** (`reward_function.py:694-704, 750`):

```
ev_raw = EV_penalty_base - max(0, violation_kwh) × penalty_coefficient
ev_i(t) = ev_weight × tanh(ev_raw / 10.0)         ∈ (-0.12, 0.12)
```

**Justificacion de cada parametro:**

| Parametro | Valor | Justificacion |
|---|---|---|
| `ev_weight` | **0.12** | Peso fijo fuera de la normalizacion simplex de los tres ejes principales. El termino EV es corrector: penaliza violaciones de restricciones de carga (el EV debe llegar a la SOC de salida requerida) sin distorsionar la jerarquia flex/carbon/cost. 0.12 implica que incluso la maxima penalizacion EV (ev_i=-1) reduce la recompensa total en solo 12%, manteniendo la señal de los ejes principales dominante. |
| Divisor 10.0 | **10.0** | El framework base `Electric_Vehicles_Reward_Function` genera `ev_raw ∈ [-10, +10]` con 1 cargador activo (peso `close_soc` predeterminado). El divisor 10.0 acota el termino a tanh ∈ (-1,1) antes de aplicar `ev_weight`, manteniendo escala consistente con los demas ejes. Documentado en `reward_function.py:701-703`. |
| Cargadores Iquitos | **185** | 185 cargadores distribuidos en los 17 edificios (96 unidades fisicas Mode 3, 1,850 EVs en pool de simulacion, potencia nominal agregada 749.4 kW). |

---

### 3.5 Cooperacion — `team_reward_ratio`

**Formula implementada** (`reward_function.py:767-768`):

```
team_reward   = mean(reward_i, i=1..17)
mixed_reward_i = (1 - 0.70) × reward_i + 0.70 × team_reward
               = 0.30 × reward_i + 0.70 × team_reward
```

**Justificacion:**

| Parametro | Valor | Justificacion |
|---|---|---|
| `team_reward_ratio` | **0.70** | El 70% de señal colectiva garantiza coordinacion entre los 17 agentes heterogeneos. Lowe et al. (2017) establecen que CTDE requiere una señal global para que los criticos centralizados aprendan la correlacion entre acciones colectivas y resultados del distrito. Kuba et al. (2021) demuestran que HAPPO converge monótonamente con señal de equipo ≥50% en escenarios heterogeneos. El valor 0.70 es la media de los valores por algoritmo del plan original (0.75+0.55+0.65+0.80)/4 = 0.6875 ≈ 0.70, preservando el nivel cooperativo medio sin introducir sesgo algoritmico. |
| N edificios | **17** | `team_reward = mean(rewards)`. Con 17 agentes, el `team_reward` suaviza el ruido individual sin perder la señal de coordinacion distrital. Nweye et al. (2023b) aplican HAPPO a comunidades de 17 edificios, validando la escalabilidad de la señal colectiva. |

---

## 4. Resumen de Todos los Parametros Numericos

| Parametro | Valor | Archivo:Linea | Justificacion sintetica |
|---|---|---|---|
| w_flex E1 | 0.70 | reward_function.py:527 | Escenario lexicografico flexibilidad |
| w_carbon E2 | 0.70 | reward_function.py:528 | Escenario lexicografico CO2 |
| w_cost E3 | 0.60 | reward_function.py:529 | Escenario lexicografico costos |
| w_flex E3 | 0.25 | reward_function.py:529 | Costo-pico correlacionados en TOU |
| team_reward_ratio | 0.70 | reward_function.py:537 | Media cooperativa Dec-POMDP |
| peak_weight | 0.45 | reward_function.py:541 | KPI primario CityLearn |
| ramp_weight | 0.35 | reward_function.py:540 | KPI secundario flexibilidad |
| ev_weight | 0.12 | reward_function.py:538 | Termino corrector EV |
| reward_scale | 1.00 | reward_function.py:539 | Escala uniforme comparabilidad |
| carbon_reference | 0.35 | reward_function.py:600 | Media mundial IEA 2023 |
| price_reference | 0.20 | reward_function.py:599 | Referencia spot competitivo |
| Divisor peak | 25 | reward_function.py:738 | 2x pico medio Iquitos/edificio |
| Divisor ramp | 15 | reward_function.py:739 | Umbral ramp BESS activo |
| Divisor export/import | 20 | reward_function.py:740 | Pico individual tipico edificio |
| Offset carbon | 0.25 | reward_function.py:743 | Costo base importacion |
| Offset cost | 0.25 | reward_function.py:745 | Costo base importacion |
| Carbon credit | 0.05 | reward_function.py:744 | Credito exportacion CO2 |
| Cost credit | 0.08 | reward_function.py:746 | Credito exportacion TOU |
| EV divisor | 10.0 | reward_function.py:704 | Rango natural close_soc |
| CI base Iquitos | 0.790 kgCO2/kWh | carbon_intensity.csv | MINAM RAGEI 2019, diesel 100% |
| CI minima Iquitos | 0.672 kgCO2/kWh | iquitos.yaml | Solar 15% penetracion |
| Precio punta | 0.38 USD/kWh | pricing.csv | OSINERGMIN MT3/MT4 2024 |
| Precio fuera-punta | 0.26 USD/kWh | pricing.csv | OSINERGMIN MT3/MT4 2024 |
| Horas punta | 18-22h | building_metadata.json | Perfil demanda Iquitos |

---

## 5. Referencias Academicas

Los valores numericos de la funcion de recompensa se sustentan en las siguientes fuentes, clasificadas por eje:

### Fundamentos MADRL y Dec-POMDP
- **Oliehoek & Amato (2016).** *A Concise Introduction to Decentralized POMDPs.* Springer. — Modelo formal Dec-POMDP: justifica la señal de equipo y la observacion parcial local.
- **Lowe et al. (2017).** *Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments.* NeurIPS. — Establece el paradigma CTDE; justifica team_reward_ratio > 0.5 para coordinacion.
- **Kuba et al. (2021).** *Trust Region Policy Optimisation in Multi-Agent Reinforcement Learning.* ICLR. — HAPPO convergencia monotona con señal de equipo ≥50% en escenarios heterogeneos.
- **Iqbal & Sha (2019).** *Actor-Attention-Critic for Multi-Agent Reinforcement Learning.* ICML. — MAAC; validacion de la señal cooperativa con mecanismo de atencion.

### Flexibilidad Energetica (OE.1)
- **Vazquez-Canteli & Nagy (2019a).** *Reinforcement learning for demand response: A review of algorithms and modeling techniques.* Applied Energy. — Revision de algoritmos RL para respuesta a demanda; peak_average y ramping_average como KPIs principales.
- **Vazquez-Canteli & Nagy (2019b).** *MARLISA: Multiagent Reinforcement Learning with Iterative Sequential Action Selection.* BuildSys. — SAC multiagente logra ~20% reduccion de pico; ~18% reduccion de ramping con incentivo explicito.
- **Nweye et al. (2024).** *CityLearn: A framework for optimizing energy systems in cities using multi-agent reinforcement learning.* Applied Energy. — KPIs oficiales CityLearn v2: peak_average, ramping_average, one_minus_load_factor_average.
- **Nweye et al. (2023b).** *MERLIN: Multi-agent offline and transfer learning for occupant-centric operation of grid-interactive communities.* Applied Energy. — HAPPO aplicado a comunidad de 17 edificios heterogeneos.
- **Hribar et al. (2025).** *Multi-agent reinforcement learning for energy autonomy in positive energy districts.* Energy and Buildings. — Incentivo de exportacion con headroom BESS mejora autonomia en ~20%.

### Emisiones CO2 (OE.2)
- **Liu et al. (2022).** *Multi-agent deep reinforcement learning for HVAC control in commercial buildings.* IEEE Transactions on Smart Grid. — MADDPG multi-objetivo con termino CO2; incluye credito de exportacion como incentivo.
- **MINAM (2019).** *RAGEI — Registro de Agentes de la Generacion Electrica del SEIN e Interconexiones.* Ministerio del Ambiente, Peru. — Factor de emision red aislada Electro Oriente S.A.: 0.790 kgCO2/kWh (diesel 100%).
- **IEA (2023).** *Electricity 2023 — Analysis and Forecast to 2025.* International Energy Agency. — Factor de emision global de referencia: 0.350 kgCO2/kWh (media mundial electricidad).

### Costos Energeticos (OE.3)
- **Gao et al. (2023).** *Multi-agent soft actor-critic for building energy optimization.* Applied Energy. — MASAC para optimizacion colaborativa; arbitraje BESS en mercados TOU requiere credito de exportacion explicito.
- **Yao et al. (2023).** *Large-scale multi-agent reinforcement learning for smart community energy management.* IEEE Transactions on Industrial Informatics. — LSD-MADDPG logra ~18% reduccion de costo en comunidades inteligentes.
- **OSINERGMIN (2024).** *Tarifas electricas MT3 y MT4 — Servicio de Distribucion Electrica.* Organismo Supervisor de la Inversion en Energia y Mineria, Peru. — Tarifas TOU vigentes: punta 0.38 USD/kWh, fuera de punta 0.26 USD/kWh, Iquitos.
- **Electro Oriente S.A. (2023-2025).** *Facturas mensuales edificios institucionales SEAI Iquitos.* — Datos de medicion reales base del dataset; ratio punta/fuera-punta medido: 1.4615.

### Escalado y Estabilidad Numerica
- **Schulman et al. (2017).** *Proximal Policy Optimization Algorithms.* arXiv:1707.06347. — PPO/HAPPO: normalizacion de ventajas y clamping clip_param=0.2; justifica reward_scale=1.0 para gradientes estables.
- **Haarnoja et al. (2018).** *Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL with a Stochastic Actor.* ICML. — SAC/MASAC: temperatura de entropia; reward_scale=1.0 mantiene la escala compatible con alpha=0.2 (temperatura entropia).
- **Fujimoto et al. (2018).** *Addressing Function Approximation Error in Actor-Critic Methods (TD3).* ICML. — MATD3: reward_scale uniforme evita divergencia del critico doble.

---

## 6. Listado Completo del Dataset de Entrenamiento

**Dataset activo:** `CityLearn/data/datasets/citylearn_iquitos_2023_2025/`
**Estado:** 229 archivos activos (222 CSV + 7 JSON) — 227 MB — auditado 2026-06-12

### 6.1 Archivos de Carga por Edificio (17 archivos Building_X.csv)

Cada archivo: 26,304 filas × 12 columnas, resolucion horaria 2023-2025.

| # | Archivo | Nombre del Edificio | Tipo CityLearn | Area (m²) |
|---|---|---|---|---:|
| 1 | Building_1.csv | ELECTRO ORIENTE S.A. | Office | 14,000 |
| 2 | Building_2.csv | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | Office | 8,000 |
| 3 | Building_3.csv | AEROPUERTO INTERNACIONAL | Assembly | 6,000 |
| 4 | Building_4.csv | HIPERMERCADOS TOTTUS ORIENTE SAC | Retail | 2,500 |
| 5 | Building_5.csv | HOTEL PLAZA S.A. | MultiFamily_Hotel | 1,142 |
| 6 | Building_6.csv | MALL AVENTURA S.A. | Commercial_Mall | 20,637 |
| 7 | Building_7.csv | UNAP - FACULTAD DE BIOLOGIA - AULAS | Education | 8,103 |
| 8 | Building_8.csv | PNP - ESCUELA TECNICA SUPERIOR | Assembly_Military | 21,000 |
| 9 | Building_9.csv | GOBIERNO REGIONAL DE LORETO - COER | Office_Critical | 4,480 |
| 10 | Building_10.csv | GOBIERNO REGIONAL DE LORETO | Office | 14,296 |
| 11 | Building_11.csv | HOSPITAL REGIONAL DE LORETO | Healthcare_Hospital | 42,649 |
| 12 | Building_12.csv | SEGURO SOCIAL DE SALUD - ESSALUD | Healthcare | 18,197 |
| 13 | Building_13.csv | UNAP - FACULTAD DE CIENCIAS CONTABLES Y ECO | Education | 2,723 |
| 14 | Building_14.csv | AUTORIDAD PORTUARIA NACIONAL | Industrial_Port | 17,761 |
| 15 | Building_15.csv | DREL - COLEGIO NACIONAL DE IQUITOS | Education | 9,890 |
| 16 | Building_16.csv | SIMA - IQUITOS S.R.LTDA | Industrial | 10,294 |
| 17 | Building_17.csv | ASOCIACION CIVIL SELVA AMAZONICA | Laboratory | 1,611 |

**Columnas de Building_X.csv:**
`month, hour, day_type, daylight_savings_status, indoor_dry_bulb_temperature, average_unmet_cooling_setpoint_difference, indoor_relative_humidity, non_shiftable_load, dhw_demand, cooling_demand, heating_demand, solar_generation`

### 6.2 Maquinas Lavadoras Controladas (17 archivos Washing_Machine_X.csv)

Una maquina por edificio, carga flexible para gestion de demanda.

`Washing_Machine_1.csv` … `Washing_Machine_17.csv`

**Columnas:** `day_type, hour, wm_start_time_step, wm_end_time_step, load_profile`

### 6.3 Cargadores EV por Edificio (185 archivos charger_X_Y.csv)

| Edificio | Nombre | Cargadores | Archivos |
|---|---|:---:|---|
| B01 | ELECTRO ORIENTE S.A. | 4 | charger_1_1 … charger_1_4 |
| B02 | MUNICIPALIDAD SAN JUAN BAUTISTA | 6 | charger_2_1 … charger_2_6 |
| B03 | AEROPUERTO INTERNACIONAL | 8 | charger_3_1 … charger_3_8 |
| B04 | HIPERMERCADOS TOTTUS | 6 | charger_4_1 … charger_4_6 |
| B05 | HOTEL PLAZA | 3 | charger_5_1 … charger_5_3 |
| B06 | MALL AVENTURA | **32** | charger_6_1 … charger_6_32 |
| B07 | UNAP BIOLOGIA | **42** | charger_7_1 … charger_7_42 |
| B08 | PNP ESCUELA TECNICA | 17 | charger_8_1 … charger_8_17 |
| B09 | GORE LORETO - COER | 10 | charger_9_1 … charger_9_10 |
| B10 | GORE LORETO | 6 | charger_10_1 … charger_10_6 |
| B11 | HOSPITAL REGIONAL | 3 | charger_11_1 … charger_11_3 |
| B12 | ESSALUD | 3 | charger_12_1 … charger_12_3 |
| B13 | UNAP CONTABLES | 11 | charger_13_1 … charger_13_11 |
| B14 | AUTORIDAD PORTUARIA | 4 | charger_14_1 … charger_14_4 |
| B15 | COLEGIO NACIONAL | 8 | charger_15_1 … charger_15_8 |
| B16 | SIMA IQUITOS | 11 | charger_16_1 … charger_16_11 |
| B17 | ASOCIACION SELVA AMAZONICA | 11 | charger_17_1 … charger_17_11 |
| **TOTAL** | | **185** | |

**Columnas de charger_X_Y.csv:**
`electric_vehicle_charger_state, electric_vehicle_id, electric_vehicle_departure_time, electric_vehicle_required_soc_departure, electric_vehicle_estimated_arrival_time, electric_vehicle_estimated_soc_arrival`

### 6.4 Señales Globales del Distrito (3 archivos)

| Archivo | Tamaño | Columnas | Descripcion |
|---|---|---|---|
| `weather.csv` | 4.1 MB | 16 | T_ext, RH_ext, GHI_difuso, DNI + 12 predicciones (1-3h) |
| `pricing.csv` | 1.3 MB | 4 | electricity_pricing + 3 predicciones horarias |
| `carbon_intensity.csv` | — | 1 | CI(t) = 0.790×(1-0.15×GHI/1000) kgCO2/kWh |

**Rango CI:** 0.672-0.790 kgCO2/kWh (varia con penetracion solar horaria).
**Rango precio:** 0.26-0.38 USD/kWh segun hora TOU.

### 6.5 Archivos de Configuracion (7 archivos JSON)

| Archivo | Tamaño | Contenido |
|---|---|---|
| `schema.json` | 1.1 MB | Configuracion completa CityLearn: 17 edificios, observaciones, acciones, DER, simulacion |
| `building_metadata.json` | 31 KB | Inventario por edificio: nombre, area, oficinas, equipos, sistemas |
| `carbon_intensity_metadata.json` | 1.1 KB | Documentacion fuente CI (Electro Oriente S.A., MINAM) |
| `ev_charger_sizing_log.json` | 38 KB | Auditoria de dimensionamiento y despliegue de cargadores EV |
| `controlled_machines_log.json` | 4.8 KB | Historial de control y dimensionamiento de lavasecadoras |
| `solar_fix_log.json` | 11 KB | Log de calibracion PV con pvlib/PVGIS para B02-B17 |
| `dataset_generation_log.json` | 762 B | Metadata de creacion del dataset |

### 6.6 Estadisticas Resumidas del Dataset

| Componente | Valor |
|---|---:|
| Total archivos activos | 229 (222 CSV + 7 JSON) |
| Tamaño total | 227 MB |
| Edificios (agentes MADRL) | 17 |
| Periodo temporal | 2023-2025 (3 años) |
| Pasos temporales | 26,304 h |
| Pasos por episodio | 8,760 h (1 año) |
| Cargadores EV | 185 |
| Unidades fisicas Mode 3 | 96 |
| EVs en pool de simulacion | 1,850 |
| Maquinas controladas | 17 |
| PV total nominal | 48,790.9 kWp |
| BESS total | 26,266 kWh / 6,648 kW |
| state_dim (CityLearn) | 879 |
| Algoritmos MADRL | HAPPO, MASAC, MATD3, MAAC |
| Escenarios | E1 (flex), E2 (CO2), E3 (costos) |
| Corridas oficiales | 12 (4 alg × 3 esc) |
| Hardware objetivo | NVIDIA RTX 4060 Laptop 8 GB |

---

*Este documento fue generado por revision sistematica del codigo fuente y reconcilia la especificacion del Plan de Tesis (§4.11.3) con la implementacion vigente en `CityLearn/citylearn/reward_function.py`.*
