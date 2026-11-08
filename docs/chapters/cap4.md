# Capítulo 4. Desarrollo de la Propuesta

> **Documento de tesis doctoral — desarrollo de la propuesta.** Describe la arquitectura ejecutable, el entorno CityLearn, la formulación Dec-POMDP/CTDE, los algoritmos MADRL, la recompensa multiobjetivo E1/E2/E3 y el diseño experimental de la corrida canónica `madrl_v3_20260627_164047`. Fuentes: `docs/architecture/flujo.md`, `docs/workflow_manifest.json`, `CityLearn/citylearn/v3/`, `data/dataset_audit/der_sizing_audit.csv`, `reward_function.py` y scripts `train_citylearn_v3_*.py`. **No inventar datos.** Este capítulo **no** responde hipótesis, **no** declara algoritmo ganador y **no** interpreta significancia estadística de resultados (Cap. 5).

---

## 4.1 Arquitectura general del sistema

La propuesta implementa un sistema de **coordinación energética multiobjetivo** mediante aprendizaje por refuerzo profundo multiagente (MADRL: HAPPO, MASAC, MATD3 y MAAC) sobre una **comunidad inteligente heterogénea de Iquitos**. El flujo de datos y control es lineal y reproducible:

**datos → CityLearn → comunidad heterogénea → Dec-POMDP → agentes → CTDE → MADRL → recursos controlables → recompensas E1/E2/E3 → entrenamiento → evaluación → artefactos.**

```mermaid
flowchart LR
  A[Datos SEAI / PVGIS / NASA / TOU] --> B[CityLearn v2 + fork A1–A4]
  B --> C[Comunidad heterogénea 17 edificios]
  C --> D[Dec-POMDP N=17]
  D --> E[Agentes edificio]
  E --> F[CTDE]
  F --> G[MADRL HAPPO/MASAC/MATD3/MAAC]
  G --> H[BESS / EV-V2G / cargas desplazables]
  H --> I[Reward E1/E2/E3]
  I --> J[Entrenamiento 4×3]
  J --> K[Evaluación + baseline v2]
  K --> L[Artefactos outputs/]
```

### 4.1.1 Frontera heredada frente a aportes de la tesis

| Componente | Frontera | Rol |
|---|---|---|
| Física CityLearn v2 (edificios, BESS, PV, EV, KPIs `evaluate_v2`) | **Heredada** (Nweye et al., 2024) | Simulador base; baseline `baseline` / `hour_rbc` |
| Dataset `citylearn_iquitos_2023_2025` | **Aporte tesis** (`tools/dataset/`) | 17 edificios SEAI, 26 304 h, 222 CSV |
| Extensiones A1–A4 (Arrhenius, PV IEC, pico OSINERGMIN, `CarbonIntensityModel`) | **Aporte tesis** (fork) | Realismo tropical / red aislada |
| Capa v3 Dec-POMDP + wrappers CTDE | **Aporte tesis** (`citylearn/v3/`, `dec_pomdp.py`) | Observabilidad parcial y estado centralizado |
| `CityLearnV3MADRLRewardFunction` (E1/E2/E3) | **Aporte tesis** | Operacionalización OE.1–OE.3 |
| Backends HARL / MARL / off-policy / MAAC | **Heredados** (`external/`) | Algoritmos; no se editan |
| Wrappers + `train_citylearn_v3_*.py` + adaptador común | **Aporte tesis** | Puente CityLearn ↔ backends |
| Orquestación Colab / validadores / tesis Word | **Aporte tesis** (`scripts/`, `tools/`) | Reproducibilidad y evidencia |

El paquete `uc3m/` (BACT, HPHI, `EmpiricalProtocol`) constituye **sustento de diseño**; las doce corridas canónicas no pasan por esa fachada.

---

## 4.2 Comunidad inteligente heterogénea

La unidad experimental es la comunidad de **17 edificios** institucionales/comerciales del SEAI (Iquitos), tipológicamente heterogénea en área, demanda, PV, BESS y flota EV. Dimensionamiento auditado en `data/dataset_audit/der_sizing_audit.csv` (totales distritales: PV **48 790,9 kWp**; BESS **26 266 kWh / 6 648 kW**; **185** cargadores EV).

### 4.2.1 Inventario cuantitativo de los 17 edificios

| ID | Edificio (abreviado) | Tipo | Área m² | Demanda MWh | PV kWp | BESS kWh/kW | EV n / kW | Máq. ctrl. |
|---|---|---|---:|---:|---:|---|---|:---:|
| B01 | ELECTRO ORIENTE S.A. | Office | 14 000 | 17 378,1 | 3 360,2 | 6 747 / 1 609 | 4 / 21,8 | Sí |
| B02 | Mun. San Juan Bautista | Office | 8 000 | 247,5 | 1 920,0 | 244 / 50 | 6 / 24,4 | Sí |
| B03 | Aeropuerto Internacional | Assembly | 6 000 | 3 155,2 | 1 440,2 | 2 363 / 511 | 8 / 37,8 | Sí |
| B04 | Hipermercados Tottus | Retail | 2 500 | 4 131,9 | 600,2 | 454 / 409 | 6 / 24,4 | Sí |
| B05 | Hotel Plaza S.A. | MultiFamily_Hotel | 1 141,89 | 3 000,1 | 274,1 | 234 / 124 | 3 / 14,4 | Sí |
| B06 | Mall Aventura S.A. | Commercial_Mall | 20 637 | 34 622,6 | 4 952,9 | 2 541 / 835 | 32 / 119,6 | Sí |
| B07 | UNAP Biología | Education | 8 103,45 | 1 314,1 | 1 944,9 | 984 / 240 | 42 / 153,2 | Sí |
| B08 | PNP Escuela Técnica | Assembly_Military | 21 000 | 873,7 | 5 040,2 | 601 / 129 | 17 / 73,6 | Sí |
| B09 | GORE Loreto — COER | Office_Critical | 4 479,67 | 234,8 | 1 075,3 | 138 / 30 | 10 / 37,4 | Sí |
| B10 | Gobierno Regional Loreto | Office | 14 295,73 | 3 838,1 | 3 431,1 | 2 353 / 591 | 6 / 36,6 | Sí |
| B11 | Hospital Regional Loreto | Healthcare_Hospital | 42 649,33 | 3 018,9 | 10 236,1 | 1 901 / 424 | 3 / 14,4 | Sí |
| B12 | EsSalud | Healthcare | 18 197,48 | 7 120,6 | 4 367,5 | 4 346 / 960 | 3 / 14,4 | Sí |
| B13 | UNAP Cs. Contables y Eco. | Education | 2 723 | 388,6 | 653,8 | 272 / 69 | 11 / 41,4 | Sí |
| B14 | Autoridad Portuaria Nacional | Industrial_Port | 17 761 | 327,9 | 4 262,9 | 229 / 48 | 4 / 21,8 | Sí |
| B15 | DREL — Colegio Nacional | Education | 9 889,92 | 683,7 | 2 373,8 | 500 / 104 | 8 / 31,4 | Sí |
| B16 | SIMA — Iquitos | Industrial | 10 294 | 2 134,6 | 2 470,8 | 1 622 / 357 | 11 / 41,4 | Sí |
| B17 | Asoc. Civil Selva Amazónica | Laboratory | 1 611,23 | 1 406,4 | 386,9 | 737 / 158 | 11 / 41,4 | Sí |
| **Σ** | | | | | **48 790,9** | **26 266 / 6 648** | **185 / 749,4** | **17** |

*Fuente:* `data/dataset_audit/der_sizing_audit.csv` (columnas `PV_schema_kWp`, `BESS_schema_*`, `EV_schema_*`, `Carga_total_MWh`, `Maquina_controlada_count`). Demanda redondeada a 1 decimal; potencias EV = `EV_schema_kW`.

### 4.2.2 Señales controlables frente a exógenas

| Clase | Variables | Naturaleza |
|---|---|---|
| **Controlables (acción MADRL)** | `electrical_storage` (BESS), `electric_vehicle_storage` × \(n_i^{\mathrm{ch}}\) (EV/V2G), `washing_machine` (carga desplazable) | Setpoints en \([-1,1]\) por canal |
| **Exógenas (no actuadas)** | Precio TOU/RTP (`pricing.csv`), intensidad de carbono CI ∈ [0,6715; 0,790] kgCO₂/kWh (`carbon_intensity.csv`), meteorología (`weather.csv`: T, RH, irradiancia, viento), carga no desplazable residual | Observables; entran en \(o_i\) y en \(R\), no en \(a_i\) |

La generación PV es física determinista condicionada por GHI/temperatura (aporte A2); el agente no fija potencia PV, solo reacciona vía almacenamiento, EV y carga desplazable.

---

## 4.3 Datos y preprocesamiento

### 4.3.1 Origen y periodo

El dataset `citylearn_iquitos_2023_2025` se construye desde datos primarios del **SEAI** (facturación Electro Oriente S.A.), meteorología **PVGIS-ERA5** (2023, vía `pvlib`) y **NASA POWER** (2024–2025), e incentivos tarifarios **TOU** locales (0,38 USD/kWh en punta 18:00–22:59; 0,26 USD/kWh fuera de punta). Periodo: **2023–2025**; horizonte tabular: **26 304 horas**; artefactos activos auditados: **222 CSV**.

Pipeline canónico: `tools/dataset/generate_iquitos_dataset.py` / `orchestrate_citylearn_dataset.py` → `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` (`schema.json`, `Building_*.csv`, `charger_*.csv`, `Washing_Machine_*.csv`, `weather.csv`, `carbon_intensity.csv`, `pricing.csv`).

### 4.3.2 Limpieza, fugas temporales y compuerta NaN/Inf

1. Destilación de cargas mensuales a horarias (`distill_building_loads.py`) con balance residual NSL y error mensual de cierre < 0,1 %.
2. Series meteorológicas cacheadas (`.cache/weather/{year}.parquet`) sin remezcla futuro→pasado: el episodio de entrenamiento usa el schema completo en orden temporal horario.
3. Dimensionamiento DER/EV/lavadoras antes del `schema.json`; sin imputación ad hoc en el bucle MADRL.
4. **Compuerta de calidad:** `check_training_dataset_ready.py`, `audit_citylearn_csv_integrity.py`, `audit_der_sizing.py` → manifiestos en `outputs/dataset_audit/`. Criterio de aceptación: `status=ready`, **0 NaN / 0 Inf**, sin cargadores ni máquinas huérfanos.

No se adopta un dataset CityLearn upstream como caso empírico: los barrios/challenges retenidos en el submódulo sirven solo a integridad y reproducibilidad del paquete (Cap. 3 §3.4.6).

---

## 4.4 Entorno CityLearn y extensiones

### 4.4.1 Capa heredada CityLearn v2

Se conserva la física de edificios, almacenamiento, PV, EV/V2G y la batería de KPIs vía `env.evaluate_v2()`. El baseline de contraste (`baseline`, `hour_rbc`) proviene de esta capa. La propuesta **extiende** el simulador; no lo sustituye.

### 4.4.2 Aportes A1–A4 del fork (tesis)

| Código | Aporte | Archivo | Función |
|---|---|---|---|
| **A1** | Degradación BESS C-rate + Arrhenius (LiFePO₄) | `energy_model.py` | Realismo térmico tropical |
| **A2** | Corrección PV IEC 61215 | `energy_model.py` | Derating tropical ≈ 10,9–14,4 % vs STC |
| **A3** | Pico con ventana de facturación | `cost_function.py` | Alineación OSINERGMIN MT-3/MT-4 |
| **A4** | `CarbonIntensityModel` | `energy_model.py` | CI dinámica diésel+PV: \(CI(t)=0{,}790\times(1-0{,}15\times\min(GHI/1000,1))\) |

Documentación: `docs/thesis/aportes.md`; arquitectura: `docs/architecture/flujo.md` §4b.

---

## 4.5 Formulación Dec-POMDP

El control distrital se formula como Dec-POMDP cooperativo:

\[
\mathcal{M}=\langle\mathcal{S},\{\mathcal{A}_i\}_{i=1}^{17},\mathcal{T},R,\{\mathcal{O}_i\}_{i=1}^{17},\Omega,\gamma,T\rangle
\]

Implementación: `CityLearn/citylearn/dec_pomdp.py`, fábrica `citylearn/v3/`, adaptador `CityLearn/scripts/citylearn_v3_training_common.py`. Dimensiones medidas con `CityLearnEnv(schema Iquitos, central_agent=False)`.

| Símbolo | Mapeo físico | Valor Iquitos |
|---|---|---|
| \(N\) | Agentes-edificio | **17** |
| \(\mathcal{S}\) | Estado CTDE \(s=[o_1,\ldots,o_{17}]\) | \(\lvert\mathcal{S}\rvert=d_s=\mathbf{1\,856}\) |
| \(o_i\in\mathcal{O}_i\) | Observación local (calendario, meteo, carga, térmica, PV, SoC BESS, 7 canales EV/toma, precio, CI) | \(d_{o_i}\in[\mathbf{54},\mathbf{327}]\) |
| \(a_i\in\mathcal{A}_i\) | BESS + EV×\(n_i^{\mathrm{ch}}\) + lavadora | \(d_{a_i}=2+n_i^{\mathrm{ch}}\in[\mathbf{5},\mathbf{44}]\); \(\sum_i d_{a_i}=\mathbf{219}\) |
| \(R\) | Recompensa mixta cooperativa | `team_reward_ratio` \(r_{\mathrm{team}}=0{,}70\) |
| \(\gamma\) | Descuento | **0,9999** |
| \(T\) | Horizonte por episodio | **8 760** pasos (1 año horario) |
| \(\mathcal{T},\Omega\) | Física CityLearn + observación schema | Transición horaria; observabilidad parcial estricta |

Agregación cooperativa canónica (canal de las 12 corridas):

\[
\mathrm{mixed}_i=(1-r_{\mathrm{team}})\,\mathrm{reward}_i+r_{\mathrm{team}}\cdot\mathrm{mean}_j(\mathrm{reward}_j),\quad r_{\mathrm{team}}=0{,}70.
\]

El distrito **no** es un agente adicional: entra por el crítico CTDE (\(s\)) y por KPIs agregados `evaluate_v2`.

---

## 4.6 CTDE

**Entrenamiento centralizado / ejecución descentralizada:**

- **Centralizado (train):** el crítico (o mezcla Q, según backend) recibe información conjunta —en la práctica el estado CTDE \(s\in\mathbb{R}^{1856}\) o su equivalente por wrapper— para estabilizar el crédito multiagente.
- **Descentralizado (exec):** cada política \(\pi_i(a_i\mid o_i)\) actúa solo con \(o_i\); no hay comunicación entre edificios en despliegue.
- Post-entrenamiento solo persisten las políticas locales.

| Algoritmo | Lectura CTDE en esta tesis |
|---|---|
| HAPPO | On-policy; actor local continuo; crítico / valor con observación compartida CTDE (`CityLearnHARLEnv`) |
| MASAC | Off-policy entrópico; estado global tipo SMAC + mezcla cooperativa QMIX (`CityLearnSMACDiscreteEnv`) |
| MATD3 | Off-policy determinístico continuo; críticos centralizados / info conjunta (`CityLearnOffPolicyVecEnv`) |
| MAAC | Attention-critic CTDE; acciones discretas (`CityLearnMAACVecEnv`) |

---

## 4.7 Algoritmos MADRL

Los backends residen en `external/`; la tesis aporta wrappers y scripts de entrenamiento. Sustento teórico de la adecuación: Cap. 2.

| Algoritmo | Wrapper | Backend | Paradigma | Acción |
|---|---|---|---|---|
| HAPPO | `CityLearnHARLEnv` | `external/HARL` | on-policy CTDE | continua |
| MASAC | `CityLearnSMACDiscreteEnv` | `external/MARL/src` | entropy-regularized + QMIX | discreta (`bins=3`, modo eje) |
| MATD3 | `CityLearnOffPolicyVecEnv` | `external/off-policy` | off-policy determinístico | continua |
| MAAC | `CityLearnMAACVecEnv` | `external/MAAC` | attention-critic CTDE | discreta (`bins=3`) |

### 4.7.1 HAPPO

Actualización secuencial con región de confianza para agentes heterogéneos. Script: `train_citylearn_v3_happo.py`. Acciones continuas en \([-1,1]^{d_{a_i}}\).

### 4.7.2 MASAC

Regularización de entropía multiagente con mezcla tipo QMIX. Script: `train_citylearn_v3_masac.py`. Discretización tractable (`action_bins=3`, no producto cartesiano \(3^{d_{a_i}}\)).

### 4.7.3 MATD3

Doble crítico, *policy delay* y ruido sobre el target; control continuo BESS/EV. Script: `train_citylearn_v3_matd3.py` (backend PyTorch `external/off-policy`).

### 4.7.4 MAAC

Crítico con atención multi-cabeza sobre los 17 agentes. Script: `train_citylearn_v3_maac.py`.

### Tabla comparativa de hiperparámetros canónicos (50 episodios)

Fuente: notebook `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` (celda 6.1, `HYPERPARAMS`), protocolo `two_phase_happo_masac_v3`.

| Parámetro | HAPPO | MASAC | MATD3 | MAAC |
|---|:---:|:---:|:---:|:---:|
| Episodios × pasos | 50 × 8 760 | 50 × 8 760 | 50 × 8 760 | 50 × 8 760 |
| `gamma` (\(\gamma\)) | 0,9999 | 0,9999 | 0,9999 | 0,9999 |
| `hidden_size` | [512, 512] | rnn 64 / qmix 32 | 768 | 768 |
| Buffer | on-policy | 2 ep (CPU) | 2 000 000 | 1 000 000 |
| Batch | rollout | 512 | 1 024 | 512 |
| LR actor / crítico | 1e-4 / 5e-4 | 3e-4 / 5e-4 | 3e-4 / 3e-4 | 3e-4 / 1e-3 |

La validación local (p. ej. 5 episodios, RTX 4060 8 GB) comprueba el pipeline; **no** sustituye la corrida canónica Colab `madrl_v3_20260627_164047`.

---

## 4.8 Recursos controlables

Las acciones del schema Iquitos son exactamente tres familias (§2.2.6.3):

\[
a_{i,t}=\big(a_i^{\mathrm{BESS}}(t),\,a_{i,1}^{\mathrm{EV}}(t),\ldots,a_{i,n_i^{\mathrm{ch}}}^{\mathrm{EV}}(t),\,a_i^{\mathrm{WM}}(t)\big)\in[-1,1]^{d_{a_i}}.
\]

### 4.8.1 BESS

- **Modelo:** batería CityLearn v2 + degradación A1 (C-rate y Arrhenius).
- **Límites:** capacidad/potencia por edificio (Tabla 4.2.1); SoC acotado por la física del `Battery`.
- **Acción:** `electrical_storage` ∈ \([-1,1]\) (carga/descarga normalizada).
- **Inventario distrital:** 26 266 kWh / 6 648 kW.

### 4.8.2 EV / V2G

- **Modelo:** tomas Mode 3; 185 cargadores schema; subconjunto V2G bidireccional documentado en Cap. 3 (31 tomas de camionetas).
- **Límites:** potencia por toma (`EV_schema_kW`); SoC, llegada/salida y ventana operativa en observación (7 canales/toma).
- **Acción:** `electric_vehicle_storage` por cargador ∈ \([-1,1]\).
- **Potencia nominal simultánea auditada:** 749,4 kW.

### 4.8.3 Cargas desplazables

- **Modelo:** una lavadora controlada por edificio (`washing_machine`; 17 máquinas).
- **Límites:** ciclos y potencia pico en CSV `Washing_Machine_*.csv` / columnas de auditoría `Maquina_controlada_*`.
- **Acción:** canal binario/continuo normalizado en el espacio de acción del agente.
- Las cargas residuales no desplazables permanecen **exógenas**.

---

## 4.9 Función de recompensa E1/E2/E3

Clase `CityLearnV3MADRLRewardFunction`:

\[
\mathrm{reward}_i(t)=\mathrm{reward\_scale}\cdot\big[w_{\mathrm{flex}}\mathrm{flex}_i+w_{\mathrm{carbon}}\mathrm{carbon}_i+w_{\mathrm{cost}}\mathrm{cost}_i+w_{\mathrm{ev}}\mathrm{ev}_i\big].
\]

Agregación cooperativa: \(r_{\mathrm{team}}=0{,}70\). Perfil unificado de comparabilidad `*_unified_comparable_v4`: `peak_weight=0,45`, `ramp_weight=0,35`, `ev_weight=0,25` (constantes entre algoritmos para no confundir VI con cambios de \(R\)).

| Escenario | OE | \(w_{\mathrm{flex}}\) | \(w_{\mathrm{carbon}}\) | \(w_{\mathrm{cost}}\) | KPI primario de diseño |
|---|---|:---:|:---:|:---:|---|
| **E1** | OE.1 Flexibilidad | **0,60** | 0,15 | 0,25 | `peak_average` / flex_composite |
| **E2** | OE.2 CO₂ | 0,25 | **0,60** | 0,15 | `carbon_emissions_total` |
| **E3** | OE.3 Costos | 0,15 | 0,25 | **0,60** | `electricity_cost_total` |

Los niveles principal/secundario/residual (0,60/0,25/0,15) rotan entre los tres ejes y cada fila suma uno. Esta formulación es una **suma ponderada jerarquizada compensatoria**, no una optimización lexicográfica: los términos secundarios permanecen activos y pueden compensar parcialmente el principal.

**Nota metodológica:** la recompensa de estado (señal de entrenamiento) **no** es el KPI final de contrastación. Los efectos diferenciales se miden en Cap. 5 con KPIs físicos / KPI-gains frente al baseline CityLearn v2.

---

## 4.10 Diseño experimental

Diseño factorial **4 × 3 = 12** tratamientos (algoritmo × eje), corrida canónica **`madrl_v3_20260627_164047`**.

| # | Algoritmo | Eje | Episodios | Seed | Horizonte | Config / salida |
|---:|---|---|---:|---:|---:|---|
| 1 | HAPPO | E1 | 50 | 0 | 8 760 | `happo/E1_seed_0` |
| 2 | HAPPO | E2 | 50 | 0 | 8 760 | `happo/E2_seed_0` |
| 3 | HAPPO | E3 | 50 | 0 | 8 760 | `happo/E3_seed_0` |
| 4 | MASAC | E1 | 50 | 0 | 8 760 | `masac/E1_seed_0` |
| 5 | MASAC | E2 | 50 | 0 | 8 760 | `masac/E2_seed_0` |
| 6 | MASAC | E3 | 50 | 0 | 8 760 | `masac/E3_seed_0` |
| 7 | MATD3 | E1 | 50 | 0 | 8 760 | `matd3/E1_seed_0` |
| 8 | MATD3 | E2 | 50 | 0 | 8 760 | `matd3/E2_seed_0` |
| 9 | MATD3 | E3 | 50 | 0 | 8 760 | `matd3/E3_seed_0` |
| 10 | MAAC | E1 | 50 | 0 | 8 760 | `maac/E1_seed_0` |
| 11 | MAAC | E2 | 50 | 0 | 8 760 | `maac/E2_seed_0` |
| 12 | MAAC | E3 | 50 | 0 | 8 760 | `maac/E3_seed_0` |

Orquestación canónica: notebook `madrl_citylearn_v3_tutorial.ipynb` + `colab_a100_official_launcher.py` (`two_phase_happo_masac_v3`). Validación de plan: `tools/training/validate_launch_config.py`. Raíz de artefactos: `outputs/madrl_v3_20260627_164047/`.

---

## 4.11 Entrenamiento

| Fase | Contenido |
|---|---|
| **Inicialización** | Schema Iquitos; escenario E1/E2/E3; seed = 0; wrapper del algoritmo; hiperparámetros §4.7; verificación de contexto `scripts/verify_project_context.ps1` |
| **Interacción** | Rollout horario \(T=8760\); observación local \(o_i\); acción \(a_i\); transición física; recompensa mixta |
| **Actualización** | Gradientes según paradigma (on-policy HAPPO; off-policy MASAC/MATD3/MAAC) sobre batch/rollout |
| **Checkpoint** | Persistencia periódica + reanudación `--skip-completed` / manifests de checkpoint |
| **Terminación** | Cupo de episodios (objetivo 50) o parada por error/OOM con reintento del launcher |
| **Almacenamiento** | Por job: `results.json`, `training_summary.json`, `timeseries.csv`, `trace.csv`, `core_kpis.csv`, `figures/`, checkpoints bajo `{algo}/E*_seed_0/` |

Adaptador común: `citylearn_v3_training_common.py`. Guardas: tensores finitos, heartbeats, auditoría `episodes_recorded`.

---

## 4.12 Evaluación

| Elemento | Especificación |
|---|---|
| **Baseline** | CityLearn v2: `baseline` y `hour_rbc` (`benchmark_citylearn_v2_agents.py`) |
| **Periodo / horizonte** | Mismo schema horario; episodio de evaluación alineado a 8 760 pasos |
| **KPI** | `env.evaluate_v2()` (flexibilidad, carbono, costo, EV, etc.); KPI-gains orientados vs baseline como unidad de contraste Cap. 5 |
| **Unidad de análisis** | Tratamiento algoritmo × escenario (seed = 0); reportes a nivel distrito y edificio |
| **Artefactos** | Comparador `compare_citylearn_v2_vs_v3_madrl.py`; `best_madrl_report.json`; carpeta `resumen_comparativo/`; puente multicriterio en `outputs/madrl_multicriteria_selection/` (metodología; interpretación en Cap. 5) |

Este capítulo fija el **contrato de evaluación**; no reporta tablas de ranking ni decisiones de hipótesis.

---

## 4.13 Reproducibilidad

| Dimensión | Valor canónico |
|---|---|
| **Software** | Python 3.9 (`.venv39-citylearn-v3`), PyTorch 2.8.0+cu126, CUDA 12.6; pytest 8.4.2 (validación) |
| **Activación** | `scripts/activate_citylearn_v3.ps1` (`PYTHONPATH` = raíz + `CityLearn/`) |
| **Hardware local** | NVIDIA RTX 4060 Laptop 8 GB (validación de pipeline) |
| **Hardware canónico** | Google Colab Pro+ (A100 / H100 según runtime del notebook); protocolo `two_phase_happo_masac_v3` |
| **Semilla** | seed = 0 en las 12 corridas reportadas |
| **Rutas** | Dataset: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/`; run: `outputs/madrl_v3_20260627_164047/`; auditoría DER: `data/dataset_audit/der_sizing_audit.csv` |

---

## 4.14 Validación técnica

### 4.14.1 Suite automatizada (2026-07-29)

```text
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest tests/uc3m/ tests/citylearn_v3/ -v --tb=line
```

**Resultado:** **184 passed** (180 `tests/uc3m/` + 4 `tests/citylearn_v3/`), 1 warning no bloqueante; duración ≈ 91 s. Entorno: Python 3.9.25, raíz `D:\MADRLCitytleranflexresdr`, contexto verificado.

### 4.14.2 Controles de integridad operativa

- Acciones en rangos de actuadores; evolución de SoC BESS/EV bajo física CityLearn; filtros **NaN/Inf** en tensores y CSV del dataset.
- `tools/training/validate_launch_config.py`: **PASS** en construcción de **12 jobs** 4×3, hiperparámetros por algoritmo y dry-run del *scheduler* (concurrencia ≤ 6; fase 1 HAPPO+MASAC).

La validación de software **no** sustituye el entrenamiento Colab ni la batería estadística del Cap. 5.

---

## 4.15 Correspondencia OE.1→E1, OE.2→E2, OE.3→E3 y OG→E1+E2+E3

Se citan los elementos definitivos de investigación (sin reformular) y su operacionalización técnica. **Cap. IV no contrastará hipótesis.**

| Alcance | Texto rector (efectos diferenciales) | Escenario / pesos | Variables / KPI de diseño | Rutas |
|---|---|---|---|---|
| **OE.1** | Determinar y cuantificar los efectos diferenciales de HAPPO, MASAC, MATD3 y MAAC sobre la **flexibilidad energética (eje E1)** e identificar el algoritmo de mejor desempeño en la comunidad inteligente heterogénea de Iquitos | **E1:** 0,60 / 0,15 / 0,25 | `peak_average`, `ramping_average`, `one_minus_load_factor_average`, flex_composite | `*/E1_seed_0/`; `CityLearnV3MADRLRewardFunction` |
| **OE.2** | … sobre las **emisiones de CO₂ (eje E2)** … | **E2:** 0,25 / 0,60 / 0,15 | `carbon_emissions_total` (+ deltas vs baseline) | `*/E2_seed_0/`; `carbon_intensity.csv` |
| **OE.3** | … sobre los **costos energéticos (eje E3)** … | **E3:** 0,15 / 0,25 / 0,60 | `electricity_cost_total` (+ TOU/RTP) | `*/E3_seed_0/`; `pricing.csv` |
| **OG** | Determinar y cuantificar los efectos diferenciales … en la **coordinación energética multiobjetivo** … e identificar el algoritmo de mejor desempeño **global** | **E1+E2+E3** (integración) | Score de escenario / multicriterio (pesos iguales ⅓ por defecto en puente metodológico) | `outputs/madrl_v3_20260627_164047/resumen_comparativo/`; `outputs/madrl_multicriteria_selection/` |

Tema del título: **coordinación energética multiobjetivo**; mecanismo: **MADRL HAPPO/MASAC/MATD3/MAAC**; unidad: **comunidad inteligente heterogénea de Iquitos**. La identificación del mejor desempeño pertenece al objetivo y se resuelve con evidencia en Cap. 5; no se anticipa aquí.

---

### Estado del capítulo

Estructura **4.1–4.15 completa**: arquitectura (heredado vs aporte), comunidad 17 edificios, datos/preprocesamiento, CityLearn A1–A4, Dec-POMDP, CTDE, algoritmos e hiperparámetros, recursos BESS/EV/cargas, recompensa E1/E2/E3, diseño 4×3 (`madrl_v3_20260627_164047`), entrenamiento, evaluación, reproducibilidad, validación técnica (184 pytest) y correspondencia OE↔E / OG↔E1+E2+E3. Pendiente de consumo en Cap. 5: interpretación de artefactos y contrastación de hipótesis.
