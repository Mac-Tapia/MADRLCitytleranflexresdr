# Capítulo 4. Desarrollo de la Propuesta

> **Documento de tesis — borrador integral alineado para Perplexity.** Basado en el código real: `CityLearn/citylearn/v3/` (`environment.py`, `objectives.py`, `config.py`, `backends.py`), `dec_pomdp.py`, `scenario_manager.py`, `madrl_kpis.py`, `official_madrl.py`, `reward_function.py` (`CityLearnV3MADRLRewardFunction`), `CityLearn/scripts/train_citylearn_v3_{happo,masac,matd3,maac}.py` + `citylearn_v3_training_common.py`, `CityLearn/configs/citylearn_v3_madrl_training.{yaml,json}`, `docs/workflow_manifest.json`, `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md` y el notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (celda 6.1 `HYPERPARAMS`, Secciones 4-7, modo `two_phase_happo_masac`). Hiperparámetros de la corrida v4 verificados contra la corrida real; hiperparámetros canónicos tomados del notebook. No inventar datos.

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres arquitecto de software de IA y experto en MADRL. Pules el **Capítulo 4 (Desarrollo de la propuesta)** de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC).

**Objetivo del prompt:** Versión final académica y técnicamente precisa en español, con:
1. Descripción de la arquitectura por capas, el Dec-POMDP, el esquema CTDE y la función de recompensa multiobjetivo (ecuaciones).
2. Tablas de **hiperparámetros reales** por algoritmo (sin redondear) y descripción de los wrappers/backends.
3. **Citas APA** consistentes con `Referencias_APA.md`.
4. Mantener la distinción entre la configuración canónica (50 ep) y la corrida ejecutada v4 (5 ep).

**Instrucciones específicas:** (a) no alterar valores de pesos de recompensa ni hiperparámetros; (b) explicitar dimensiones de observación/acción; (c) describir los 4 aportes al motor con sus ecuaciones; (d) marcar `[Pendiente: ...]` donde el proyecto no fije un valor.

---

## 4.1 Visión general del sistema

El sistema implementa el problema de gestión coordinada de 17 edificios como un **Dec-POMDP cooperativo** resuelto bajo **CTDE**, comparando cuatro backends MADRL. La arquitectura se organiza en seis capas:

| Capa | Componente | Ruta |
|---|---|---|
| 1. Simulador base | CityLearn v2 (física edificios, BESS, PV, EV, KPIs) | `CityLearn/citylearn/*.py` |
| 2. Extensión v3 | Dec-POMDP, objetivos, config, recompensa | `CityLearn/citylearn/v3/`, `dec_pomdp.py`, `reward_function.py` |
| 3. Adaptador común | Normalización, KPIs, trazas, figuras, layout | `CityLearn/scripts/citylearn_v3_training_common.py` |
| 4. Backends MADRL | HARL, MARL/src, off-policy, MAAC | `external/` |
| 5. Launchers | Scripts de entrenamiento y orquestación | `CityLearn/scripts/train_citylearn_v3_*.py`, `*.ps1` |
| 6. Evaluación/evidencia | Benchmark v2, comparador, evidencia tesis | `CityLearn/scripts/{benchmark,compare,generate_thesis}*.py` |

## 4.2 Formulación Dec-POMDP

> **ℳ = ⟨𝒮, {𝒜ᵢ}ᵢ₌₁¹⁷, 𝒯, R, {𝒪ᵢ}ᵢ₌₁¹⁷, Ω, γ, T⟩**

- **N = 17** agentes (edificios).
- **𝒮**: estado global = concatenación de observaciones locales (`ctde_state="concatenated_local_observations"`). La evaluación del dataset reporta un **state dim = 1856** por escenario con 17 agentes (incluye señales EV y de red).
- **𝒪ᵢ**: observación local **heterogénea** por edificio, cuya dimensión depende del número de cargadores EV. Según el notebook `madrl_citylearn_v3_tutorial.ipynb` (Sección 4), cada observación combina tiempo (mes, hora, `day_type`), física del edificio (`non_shiftable_load`, `dhw_demand`, `cooling_demand`, `solar_generation`), estado del BESS (SOC, potencia nominal, acciones previas), estado de cada cargador EV (SOC_k, hora de salida_k, SOC requerido_k, llegada estimada_k, estado_k) y señales globales (intensidad de carbono, precio, temperatura exterior, irradiancia difusa/directa), con un rango aproximado de **57–330 dimensiones** por agente. `[Pendiente: documentar la composición exacta de las 1856 dimensiones del estado global y el desglose por edificio.]`
- **𝒜ᵢ**: acción local **heterogénea** del edificio i — potencia BESS (carga/descarga), potencia de carga EV por cargador y control de carga desplazable (lavadora); la dimensión varía con el número de cargadores EV, en un rango aproximado de **5–44 acciones** por edificio (notebook, Sección 4). Los edificios con flota EV extensa (p. ej. B06 con 32 cargadores y B07 con 42) concentran las acciones de mayor dimensión.
- **𝒯**: transición estocástica (balance energético, modelo RC de temperatura, BESS con η_RT = 0.9025, llegada/salida EV estocástica).
- **R**: recompensa cooperativa `CityLearnV3MADRLRewardFunction` con `reward_aggregation = team_mean`.
- **γ = 0.9999** (configurado en los cuatro scripts para horizonte de 8 760 pasos); **T = 8 760**.
- **Observabilidad parcial estricta:** cada edificio observa solo su estado local; no accede a la temperatura, SOC ni EV de los demás durante la ejecución.

## 4.3 Esquema CTDE

- **Entrenamiento centralizado:** crítico Qᵢ(s, a₁,…,a₁₇) o V(s) accede al estado global s = [o₁,…,o₁₇] (`central_agent=false`, `centralized_training=true`).
- **Ejecución descentralizada:** política πᵢ(aᵢ|oᵢ) usa solo la observación local; sin comunicación entre edificios (`decentralized_execution=true`).
- **Post-entrenamiento:** el crítico se descarta; solo persisten las políticas locales.

## 4.4 Modelo de IA: función de recompensa multiobjetivo

La clase `CityLearnV3MADRLRewardFunction` (hereda de `Electric_Vehicles_Reward_Function`) calcula, por edificio i y paso t:

> **reward_i(t) = reward_scale · [ w_flex·flex_i + w_carbon·carbon_i + w_cost·cost_i + w_ev·ev_i ]**

**Componentes (forma del código):**

```
peak_share(t)   = district_import(t) / N
ramp_share(t)   = |district_import(t) − district_import(t−1)| / N
flex_i(t)       = −[ w_peak·tanh(peak_share/25) + w_ramp·tanh(ramp_share/15)
                     + 0.15·tanh(export_i·(1+headroom)/20) + 0.10·tanh(import_i·SOC_i/20) ]
carbon_norm(t)  = CI(t)/(CI(t)+0.35)
carbon_i(t)     = −tanh(import_i·(0.25+carbon_norm)/20) + 0.05·tanh(export_i·carbon_norm/20)
price_norm(t)   = p(t)/(p(t)+0.20)
cost_i(t)       = −tanh(import_i·(0.25+price_norm)/20) + 0.08·tanh(export_i·price_norm/20)
ev_i(t)         = clip( tanh(ev_penalty/10) + servicio_EV , −1, 1 )   # urgencia SOC/salida
```

**Agregación cooperativa (CTDE):**
```
team_reward    = (1/N) Σᵢ reward_i
mixed_reward_i = (1 − r)·reward_i + r·team_reward     con r = team_reward_ratio = 0.70
```

### 4.4.1 Pesos por escenario (axis weights)

| Escenario | OE | flex | carbon | cost | KPI primario |
|---|---|:---:|:---:|:---:|---|
| **E1** | OE.1 Flexibilidad | **0.70** | 0.15 | 0.15 | `peak_average` |
| **E2** | OE.2 CO₂ | 0.15 | **0.70** | 0.15 | `carbon_emissions_total` |
| **E3** | OE.3 Costos | 0.25 | 0.15 | **0.60** | `electricity_cost_total` |

Fuente: `scenario_manager.py` (`ScenarioConfig.reward_weights`) y `citylearn_v3_madrl_training.yaml` (`reward.axis_weights`).

### 4.4.2 Perfil de recompensa unificado (comparabilidad)

Todos los algoritmos usan el **mismo perfil** (`*_unified_comparable_v3/v4`) para garantizar comparabilidad estadística:

| Parámetro | Valor |
|---|:---:|
| `team_reward_ratio` (r) | 0.70 |
| `peak_weight` | 0.45 |
| `ramp_weight` | 0.35 |
| `ev_weight` | 0.25 |
| `reward_scale` | 1.00 |
| `axis_weight_multipliers` (flex/carbon/cost) | 1.00 / 1.00 / 1.00 |
| `ev_soc_tolerance` / `ev_soc_critical_deficit` | 0.05 / 0.25 |
| `ev_urgency_hours` | 4.0 |
| `ev_departure/urgency/idle_deficit_weight` | 0.55 / 0.30 / 0.15 |

> Razón de la unificación: con perfiles diferenciados, las diferencias de rendimiento no serían atribuibles solo a la arquitectura del algoritmo. Los perfiles diferenciados se conservan para ablación futura (no activos).

## 4.5 Algoritmos y wrappers

Cada algoritmo se conecta al entorno v3 mediante un wrapper específico definido en `citylearn_v3_training_common.py`:

| Algoritmo | Wrapper | Backend | Paradigma | Acción |
|---|---|---|---|---|
| HAPPO | `CityLearnHARLEnv` | `external/HARL` | on-policy cooperativo CTDE | continua |
| MASAC | `CityLearnSMACDiscreteEnv` | `external/MARL/src` | entropy-regularized discreto (QMIX) | discretizada (`axis`, bins=3) |
| MATD3 | `CityLearnOffPolicyVecEnv` | `external/off-policy` | off-policy determinístico CTDE | continua |
| MAAC | `CityLearnMAACVecEnv` | `external/MAAC` | attention-critic CTDE | discretizada (`axis`, bins=3) |

### 4.5.1 Hiperparámetros — corrida ejecutada v4 (real, `official_full_status.json`)

| Parámetro | HAPPO | MASAC | MATD3 | MAAC |
|---|:---:|:---:|:---:|:---:|
| Episodios × pasos | 5 × 8 760 | 5 × 8 760 | 5 × 8 760 | 5 × 8 760 |
| `gamma` | 0.9999 | 0.9999 | 0.9999 | 0.9999 |
| `hidden_size` | 256 | rnn 64 / qmix 32 / hyper 64 | 256 | 256 |
| Buffer | (on-policy) | `buffer_size` 2 ep (≤3 GiB) | 4 096 | 50 000 |
| Batch | — | `critic_batch_size` 1 | 256 | 256 |
| LR (actor/critic) | 1e-4 / 5e-4 | 3e-4 / 5e-4 (α 3e-4) | 3e-4 | π 3e-4 / Q 1e-3 |
| Específicos | `n_rollout_threads` 1, `action_aggregation` mean | `action_bins` 3 `axis`, `actor_sample_times` 2 | `train_interval` 100, `tau` 0.005, `target_noise` 0.2 | `attend_heads` 4, `tau` 0.005, `steps_per_update` 250, `num_updates` 4 |
| Reward profile | HAPPO unified | MASAC unified | MATD3 unified | MAAC unified |

### 4.5.2 Hiperparámetros — configuración canónica objetivo (50 ep, Colab A100)

La corrida canónica se ejecuta en Google Colab (NVIDIA A100-SXM4-80GB, High-RAM) bajo el modo de lanzamiento `two_phase_happo_masac` (Fase 1: HAPPO + MASAC en sus tres escenarios en paralelo; Fase 2: MATD3 + MAAC, también ×3), con seis trabajos por fase. La validación operacional fija el horizonte total en 50 episodios × 8 760 pasos = 438 000 pasos por corrida y 5 256 000 pasos para las doce corridas. Los valores siguientes corresponden a la celda 6.1 (`HYPERPARAMS`, declarada como fuente única de verdad) del notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`:

| Parámetro | HAPPO | MASAC | MATD3 | MAAC |
|---|:---:|:---:|:---:|:---:|
| Episodios × pasos | 50 × 8 760 | 50 × 8 760 | 50 × 8 760 | 50 × 8 760 |
| `num_env_steps` | 438 000 | 438 000 | 438 000 | 438 000 |
| `gamma` | 0.9999 | 0.9999 | 0.9999 | 0.9999 |
| `hidden_size` | [512, 512] | rnn 64 / qmix 32 / hyper 64 | 768 | 768 |
| Buffer | (on-policy, rollout) | 2 ep (≤8 GiB, replay en CPU) | 2 000 000 | 1 000 000 |
| Batch | rollout completo | 512 (`critic_batch` 1 ep QMIX) | 1 024 (GPU 1 280) | 512 (GPU 768) |
| LR (actor/crítico) | 1e-4 / 5e-4 | 3e-4 / 5e-4 (α 3e-4) | 3e-4 / 3e-4 | 3e-4 / 1e-3 |
| `tau` | — | 0.005 | 0.005 | 5e-3 |
| Específicos | clip 0.2, GAE 0.95, `update_epochs` 5, `n_rollout_threads` 2 (auto), `share_param` False | `action_bins` 3 `axis` (89 acciones discretas), `update_frequency` 2, `actor_sample_times` 10 | `policy_noise` 0.2, `noise_clip` 0.5, `policy_delay` 2, `train_interval` 50 | `attention_heads` 4, `steps_per_update` 50, `num_updates` 12, `reward_scale` 10.0, `action_bins` 3 |

> Nota: estos valores corresponden a la corrida canónica de 50 episodios en Colab A100 (celda 6.1 del notebook, modo `two_phase_happo_masac`) y difieren de la corrida v4 local (tabla 4.5.1), ajustada a los 8 GB de VRAM de una RTX 4060 Laptop. El Capítulo 5 todavía reporta resultados preliminares de la corrida v4 (5 episodios); se reemplazarán al concluir la corrida canónica, cuyos artefactos se integrarán desde `outputs/colab_50ep/` (o la carpeta de Google Drive del entrenamiento).

## 4.6 Aportes originales al motor de simulación (CityLearn fork)

Cuatro extensiones retrocompatibles (commit `54b1938e`), documentadas en `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md`:

| # | Aporte | Archivo · Clase/Método | Modelo |
|---|---|---|---|
| **A1** | Degradación BESS C-rate + Arrhenius | `energy_model.py` · `Battery.degrade(temperature_celsius=25.0)` | ΔC = base·(C_rate)^0.55·exp[Ea/R·(1/T_ref−1/T)], Ea=24 500 J/mol, T_ref=298.15 K; a 35 °C → +14 % degradación |
| **A2** | Corrección PV tropical (IEC 61215) | `energy_model.py` · `PV.get_generation(dry_bulb_temperature, ghi)` | T_cell = T_amb+(NOCT−20)/800·GHI; P=P_STC·[1+γ·(T_cell−25)], γ=−0.0035/°C; derating 10.9–14.4 % |
| **A3** | KPI pico con ventana de facturación | `cost_function.py` · `CostFunction.peak(billing_window_steps=1)` | Máximo rodante sub-horario; alinea con OSINERGMIN MT-3/MT-4 (15 min) |
| **A4** | `CarbonIntensityModel` (clase nueva) | `energy_model.py` | CI(t)=base_ci·(1−δ_PV·min(GHI/1000,1)); base_ci=0.790, δ_PV=0.15 → CI∈[0.6715,0.790] |

## 4.7 Escenarios y matriz de 12 corridas

Tres escenarios (E1/E2/E3) × cuatro algoritmos = **12 corridas oficiales** (seed 0), lanzadas por `launch_citylearn_v3_official_training.ps1 -Scenario ALL`.

|  | HAPPO | MASAC | MATD3 | MAAC |
|---|:---:|:---:|:---:|:---:|
| **E1 Flexibilidad** | happo/E1_s0 | masac/E1_s0 | matd3/E1_s0 | maac/E1_s0 |
| **E2 CO₂** | happo/E2_s0 | masac/E2_s0 | matd3/E2_s0 | maac/E2_s0 |
| **E3 Costos** | happo/E3_s0 | masac/E3_s0 | matd3/E3_s0 | maac/E3_s0 |

Artefactos por corrida: `results.json`, `training_summary.json`, `timeseries.csv`, `trace.csv`, `checkpoint_manifest.json`, `artifact_audit.json`, `figures/` (13 PNG).

## 4.8 Implementación y entorno

Una vez fijada la formulación, la implementación distingue dos planos de ejecución coherentes entre sí. El plano local sirvió para validar el pipeline completo y producir la corrida preliminar v4, mientras que el plano en la nube concentra la corrida canónica de 50 episodios; ambos comparten el mismo dataset, la misma función de recompensa y los mismos KPIs, lo que preserva la comparabilidad.

- **Lenguaje/stack:** Python 3.9 (`.venv39-citylearn-v3`), PyTorch 2.8.0+cu126, CUDA 12.6.
- **Hardware (corrida v4 local):** NVIDIA RTX 4060 Laptop, 8 188 MiB VRAM, driver 560.94; perfil `local4060_fast` (TF32, `cuda_memory_fraction≈0.812`, `max_split_size_mb:128`).
- **Cómputo canónico (Colab A100):** NVIDIA A100-SXM4-80GB con ~167 GiB de RAM (Colab Pro+ High-RAM), orquestado por `CityLearn/scripts/colab_a100_official_launcher.py` en modo `two_phase_happo_masac` (protocolo `two_phase_happo_masac_v3`). La Fase 1 entrena HAPPO y MASAC (6 jobs en paralelo) y la Fase 2 MATD3 y MAAC (otros 6 jobs); MASAC mantiene el replay en CPU y los hilos por fase se autoajustan a las vCPU del runtime. El monitoreo y la reanudación intra-job usan `colab_a100_live_monitor.py`, `live_progress.json` y `--skip-completed`. Fuente: notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (celdas 6.1 y 7.x).
- **Concurrencia (local):** `MaxConcurrentScenarioJobs=2`; MASAC/MAAC limitados a 1 (estabilidad de memoria); `torch_threads` 8-12.
- **Guardas de robustez:** filtros de gradientes/valores finitos (`install_finite_optimizer_step_guard`, `FiniteTensorBoardWriter`), heartbeats de progreso y reanudación por checkpoints (`discover_job_resume_plan`).

---

### Estado del capítulo
**Completo con placeholders menores.** Pendientes: composición exacta de las 1856 dimensiones de estado; consolidación de la configuración objetivo (50 ep) vs ejecutada (5 ep).
