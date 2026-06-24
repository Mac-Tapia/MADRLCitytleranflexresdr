# Arquitectura y Flujo de Trabajo — MADRL CityLearn v3
## Sustentacion de Tesis

**Proyecto:** Multi-agente de aprendizaje por refuerzo profundo para gestion coordinada de
flexibilidad energetica, emisiones de carbono y eficiencia economica en comunidades inteligentes.

**Caso de estudio:** 17 edificios institucionales/comerciales reales de Iquitos, Peru (2023-2025).

**Resultado principal (corrida v4):** MATD3 es el mejor MADRL global
(Kruskal-Wallis p = 0.0459, Mann-Whitney MATD3 vs HAPPO p = 0.0182).

---

## Diagrama 1 — Vision General del Proyecto (inicio a fin)

Este diagrama es la lectura completa del proyecto de izquierda a derecha: desde el problema de
investigacion hasta la determinacion del mejor algoritmo MADRL.

```mermaid
flowchart LR
    subgraph ORIGEN["① Origen del proyecto"]
        direction TB
        PROB(["Problema de investigacion\n¿Que MADRL optimiza mejor\nflexibilidad + CO2 + costos\nen comunidades inteligentes?"])
        OBJ["Objetivos especificos\nOE1 Flexibilidad\nOE2 Emisiones CO2\nOE3 Costos energeticos"]
        PROB --> OBJ
    end

    subgraph DATOS["② Dataset Iquitos"]
        direction TB
        RAW["Facturas electricas reales\nCityLearn/data/buildingcsv/\n17 edificios B01-B17"]
        PIPE["Pipeline destilacion\nNSL residual + EV + BESS\ngenerate_iquitos_dataset.py"]
        DS[("citylearn_iquitos_2023_2025\nschema.json\n26 304 pasos horarios\n222 CSV activos")]
        RAW --> PIPE --> DS
    end

    subgraph SIM["③ Simulador"]
        direction TB
        V2["CityLearn v2 base\nFisica edificios\nBESS + PV + EV\nKPIs oficiales"]
        V3["CityLearn v3 propuesto\nDec-POMDP 17 agentes\nCTDE: critic centralizado\nRecompensa multiobjetivo"]
        V2 -->|"se extiende con\ncapa experimental"| V3
    end

    subgraph MADRL_BLOQUE["④ Entrenamiento MADRL"]
        direction TB
        ALGS["4 algoritmos\nHAPPO · MASAC\nMATD3 · MAAC"]
        EJES["3 escenarios\nE1 Flex · E2 CO2 · E3 Costo"]
        GPU["Colab A100 oficial (two_phase_happo_masac_v3)\n50 ep x 8 760 pasos = 438 000 steps/corrida\n12 jobs: Fase1 HAPPO+MASAC · Fase2 MATD3+MAAC\n~20 h wall (6 paralelos/fase, sin stagger)"]
        ALGS --> EJES --> GPU
    end

    subgraph EVAL["⑤ Evaluacion y seleccion"]
        direction TB
        KPIS["KPIs CityLearn\npeak_average\ncarbon_emissions\nelectricity_cost"]
        STAT["Pruebas estadisticas\nShapiro-Wilk\nKruskal-Wallis\nMann-Whitney U\nWilcoxon SR"]
        RANK["Ranking inter-algoritmo\nScore ponderado global\nEfect size: Cliff delta\nHedges g · Bootstrap CI"]
        KPIS --> STAT --> RANK
    end

    subgraph RESULT["⑥ Resultado"]
        direction TB
        MEJOR(["Mejor MADRL: MATD3\nScore global: E1=0.75 E2=0.75 E3=0.73\nKW p=0.0459 · MWU p=0.0182"])
        TESIS["Evidencia para tesis\nTablas + graficas + conclusiones\ngenerate_thesis_objective_evidence.py"]
        MEJOR --> TESIS
    end

    ORIGEN --> DATOS
    DATOS --> SIM
    SIM --> MADRL_BLOQUE
    MADRL_BLOQUE --> EVAL
    EVAL --> RESULT

    classDef origen fill:#fef3c7,stroke:#d97706,color:#1c1917,stroke-width:2px
    classDef datos fill:#dbeafe,stroke:#2563eb,color:#1c1917,stroke-width:2px
    classDef sim fill:#e0e7ff,stroke:#4f46e5,color:#1c1917,stroke-width:2px
    classDef madrl fill:#fae8ff,stroke:#a21caf,color:#1c1917,stroke-width:2px
    classDef eval fill:#dcfce7,stroke:#16a34a,color:#1c1917,stroke-width:2px
    classDef result fill:#ffedd5,stroke:#ea580c,color:#1c1917,stroke-width:3px

    class ORIGEN origen
    class DATOS datos
    class SIM sim
    class MADRL_BLOQUE madrl
    class EVAL eval
    class RESULT result
```

---

## Diagrama 2 — Pipeline del Dataset Iquitos 2023-2025

```mermaid
flowchart TD
    subgraph INSUMOS["Insumos primarios (reales)"]
        FAC["Facturas electricas\nB02-B17.csv\nkWh punta / fuera punta\nGastos reales 2023-2025"]
        MET["Datos meteorologicos\nOpen-Meteo API\nGHI, T_amb, HR\nIquitos -3.74 lat"]
        AUD["Auditoria tecnica\nAreas techadas\nTipos HVAC\nFlota EV por edificio"]
    end

    subgraph PIPELINE["Pipeline de generacion (tools/)"]
        DEST["distill_building_loads.py\nNSL residual = E_medido - cooling/COP - DHW/COP\nBalance mensual < 0.1 percent error"]
        GEN["generate_iquitos_dataset.py\nInterpolacion horaria\nPronostico meses faltantes\ncalendar_month_mean_overlap_scaled"]
        SCHEMA["fix_schema_cooling.py\nAutosize safety factor\nchiller agua / multi-chiller\nprecision AC / ultra-freezers -80C"]
        VALID["orchestrate_citylearn_dataset.py\nIntegridad 222 CSV\n26 304 filas x edificio\ncharger NaN check"]
    end

    subgraph DATASET["Dataset final (CityLearn/data/datasets/)"]
        direction LR
        BUILD["Building_X.csv x17\nNSL + cooling + DHW\n26 304 pasos horarios"]
        WEATH["weather.csv\nGHI, T, HR, presion\nIquitos tropical"]
        CARBON["carbon_intensity.csv\n0.671-0.790 kgCO2/kWh\nMINAM RAGEI 2019"]
        PRICE["pricing.csv\nPunta 18-22h: 0.38 USD/kWh\nFuera punta: 0.26 USD/kWh"]
        EV["charger_X_Y.csv x185\n96 equipos Modo 3\n1 850 EV en pool"]
        SC["schema.json\n17 edificios registrados\nBESS + PV + EV por edificio"]
        BUILD --- WEATH --- CARBON --- PRICE --- EV --- SC
    end

    subgraph EDIFICIOS["17 edificios reales de Iquitos"]
        B["B01 ELECTRO ORIENTE 6747 kWh BESS\nB03 AEROPUERTO 2363 kWh BESS\nB06 MALL AVENTURA 2541 kWh BESS\nB07 UNAP BIOLOGIA 984 kWh BESS\nB11 HOSPITAL REGIONAL 1901 kWh BESS\n... 12 edificios mas"]
    end

    FAC --> DEST
    MET --> GEN
    AUD --> SCHEMA
    DEST --> VALID
    GEN --> VALID
    SCHEMA --> VALID
    VALID --> DATASET
    DATASET --> EDIFICIOS

    classDef ins fill:#fef3c7,stroke:#d97706,color:#1c1917
    classDef pipe fill:#e0f2fe,stroke:#0284c7,color:#1c1917
    classDef ds fill:#dbeafe,stroke:#2563eb,color:#1c1917
    classDef edif fill:#f0fdf4,stroke:#16a34a,color:#1c1917
    class INSUMOS ins
    class PIPELINE pipe
    class DATASET ds
    class EDIFICIOS edif
```

---

## Diagrama 3 — Arquitectura Dec-POMDP y CTDE de los 17 Agentes

```mermaid
flowchart TD
    subgraph ENV["Entorno CityLearn v3 (simulacion horaria)"]
        direction LR
        B1["Edificio 1\nBESS + PV + EV"]
        B2["Edificio 2\nBESS + PV + EV"]
        BN["... Edificio 17\nBESS + PV + EV"]
        GRID(["Red electrica\nElectro Oriente\nSistema aislado diesel"])
        B1 --- B2 --- BN
        B1 & B2 & BN --> GRID
    end

    subgraph OBS["Observaciones locales oᵢ(t) — 19 dimensiones"]
        direction LR
        TIME["Tiempo\nmes hora tipo_dia"]
        PHYS["Fisica edificio\nT_interior DHW\ncarga_no_desplazable\ngeneracion_solar"]
        BESS_OBS["Estado BESS\nSOC accion_previa"]
        EV_OBS["Estado EV\nSOC_k salida_k\nSOC_req_k llegada_k"]
        SIG["Senales globales\ncarbono precio\nGHI T_amb HR"]
    end

    subgraph POLICY["Politicas descentralizadas (ejecucion)"]
        P1["π₁(a₁|o₁)\nred neuronal\nedificio 1"]
        P2["π₂(a₂|o₂)\nred neuronal\nedificio 2"]
        PN["π₁₇(a₁₇|o₁₇)\nred neuronal\nedificio 17"]
    end

    subgraph ACTIONS["Acciones locales aᵢ(t)"]
        A1["a₁: BESS carga/descarga\nEV carga\nLavadora on/off"]
        A2["a₂: BESS · EV · Lavadora"]
        AN["a₁₇: BESS · EV · Lavadora"]
    end

    subgraph CRITIC["Critico centralizado (solo en entrenamiento CTDE)"]
        STATE["Estado global s = concat(o₁,...,o₁₇)\nV(s) o Q(s,a) centralizado"]
        REWARD["Recompensa mixta por agente\nr_i_mix = 0.30 * r_i + 0.70 * team_reward\nteam_reward = mean(r₁,...,r₁₇)"]
        STATE --> REWARD
    end

    subgraph UPDATE["Actualizacion de politicas (CTDE)"]
        GRAD["Gradiente con informacion global\nHAPPO: secuencial con trust region\nMASAC: Q-mix + SAC discreto\nMATD3: TD3 con critico centralizado\nMAC: attention sobre Q"]
    end

    ENV -->|"emite oᵢ(t)"| OBS
    OBS --> POLICY
    POLICY -->|"accion aᵢ"| ACTIONS
    ACTIONS -->|"aplica en entorno"| ENV
    ENV -->|"estado global\nsolo entrenamiento"| CRITIC
    CRITIC --> UPDATE
    UPDATE -->|"actualiza pesos"| POLICY

    classDef env fill:#f0fdf4,stroke:#16a34a,color:#1c1917
    classDef obs fill:#dbeafe,stroke:#2563eb,color:#1c1917
    classDef pol fill:#fae8ff,stroke:#a21caf,color:#1c1917
    classDef crit fill:#fef3c7,stroke:#d97706,color:#1c1917
    classDef act fill:#ffedd5,stroke:#ea580c,color:#1c1917
    class ENV env
    class OBS obs
    class POLICY,ACTIONS pol
    class CRITIC,UPDATE crit
```

---

## Diagrama 4 — Los 4 Algoritmos MADRL: Taxonomia y Diferencias

```mermaid
flowchart LR
    subgraph HAPPO_BOX["HAPPO — Heterogeneous-Agent PPO"]
        direction TB
        HAPPO_T["Tipo: On-policy\nActualizacion secuencial\nTrust region por agente"]
        HAPPO_C["Critico: Centralizado V(s)\nActor: π(a|o) local\nBackend: HARL/external/HARL"]
        HAPPO_P["Parametros A100 Colab\nhidden_size=512\nn_rollout_threads=1\nlog_interval=1"]
    end

    subgraph MASAC_BOX["MASAC — Multi-Agent SAC Discreto"]
        direction TB
        MASAC_T["Tipo: Off-policy\nEntropy regularization\nAcciones discretas por eje"]
        MASAC_C["Critico: Q-mix centralizado\nActor: π(a|o) + temperatura\nBackend: MARL/external/MARL/src"]
        MASAC_P["Parametros A100 Colab\naction_bins=3 axis mode\nbuffer_size=8 ep · max 11 GiB GPU\ncritic_batch_size=512 · cuda_frac=0.26"]
    end

    subgraph MATD3_BOX["MATD3 — Multi-Agent TD3"]
        direction TB
        MATD3_T["Tipo: Off-policy\nDoble critico (anti-overest)\nPolicy delay + target noise"]
        MATD3_C["Critico: Par Q₁ Q₂ centralizado\nActor: μ(o) deterministico\nBackend: off-policy/external"]
        MATD3_P["Parametros A100 Colab\nbatch_size=1024\nbuffer_size=2M\nhidden_size=1024\ntrain_interval=100"]
    end

    subgraph MAAC_BOX["MAAC — Multi-Agent Attention Critic"]
        direction TB
        MAAC_T["Tipo: Off-policy\nAtencion sobre agentes\nSAC con Q de atencion"]
        MAAC_C["Critico: Attention SAC Q(s,a)\nActor: π(a|o) estocastico\nBackend: MAAC/external/MAAC"]
        MAAC_P["Parametros A100 Colab\nbatch_size=1024\nbuffer_length=1M\nhidden_size=1024\nnum_updates=16"]
    end

    HAPPO_BOX -->|"12/12 corridas\nv3+v4"| COMP(["Comparacion\nKPIs CityLearn\npor escenario"])
    MASAC_BOX --> COMP
    MATD3_BOX --> COMP
    MAAC_BOX --> COMP

    COMP -->|"ranking global"| WINNER(["Mejor: MATD3\nScore E1=0.75 E2=0.75 E3=0.73\nKW p=0.0459"])

    classDef happo fill:#dbeafe,stroke:#2563eb,color:#1c1917,stroke-width:2px
    classDef masac fill:#fae8ff,stroke:#a21caf,color:#1c1917,stroke-width:2px
    classDef matd3 fill:#dcfce7,stroke:#16a34a,color:#1c1917,stroke-width:2px
    classDef maac fill:#fef3c7,stroke:#d97706,color:#1c1917,stroke-width:2px
    classDef winner fill:#ffedd5,stroke:#ea580c,color:#1c1917,stroke-width:3px
    class HAPPO_BOX happo
    class MASAC_BOX masac
    class MATD3_BOX matd3
    class MAAC_BOX maac
    class WINNER winner
```

---

## Diagrama 5 — Flujo de Entrenamiento: 12 Corridas (two_phase_happo_masac_v3)

```mermaid
flowchart TD
    START(["Colab A100-SXM4-80GB · protocolo two_phase_happo_masac_v3\ncolab_a100_official_launcher.py --execution-mode two_phase_happo_masac\n--scenario ALL --episodes 50 --episode-time-steps 8760\n438 000 steps/corrida · --skip-completed · OOM retry"])

    subgraph PHASE1["FASE 1 — HAPPO + MASAC (6 jobs en paralelo, sin stagger) · ~10 h"]
        direction LR
        subgraph P1_H["HAPPO x3 (on-policy)"]
            H_E1["E1 flex\nw: 0.70/0.15/0.15"]
            H_E2["E2 CO2\nw: 0.15/0.70/0.15"]
            H_E3["E3 costo\nw: 0.25/0.15/0.60"]
        end
        subgraph P1_M["MASAC x3 (off-policy, buffer GPU)"]
            M_E1["E1\nbuf 8 ep · 11 GiB"]
            M_E2["E2\ncuda_frac 0.26"]
            M_E3["E3\npreload cuda"]
        end
    end

    subgraph PHASE2["FASE 2 — MATD3 + MAAC (6 jobs en paralelo, tras Fase 1) · ~10 h"]
        direction LR
        subgraph P2_T["MATD3 x3"]
            T_E1["E1\nbatch 1024"]
            T_E2["E2\nbuf 2M"]
            T_E3["E3\nhidden 1024"]
        end
        subgraph P2_A["MAAC x3"]
            A_E1["E1\nbatch 1024"]
            A_E2["E2\nbuf 1M"]
            A_E3["E3\nupdates 16"]
        end
    end

    subgraph ARTEFACTOS["Artefactos por corrida (algorithm-first layout)"]
        direction LR
        PATH["outputs/<ts>/<algo>/<Escenario>_seed_0/"]
        CHK["checkpoints/\nmodelos .pt"]
        DATA["data/\nresults.json · timeseries.csv\ntrace.csv · training_summary.json"]
        FIG["figures/\n13 graficas PNG"]
        LOG["logs/\nE?_algo.log · stderr"]
        PATH --- CHK --- DATA --- FIG --- LOG
    end

    subgraph STATUS["Protocolo, estado y monitoreo"]
        G1["colab_protocol_guard.py\nbloquea layout legacy 9+3"]
        S1["official_full_status.json\nofficial_full_manifest.json"]
        S2["live_progress.json\nepisodio · paso · reward · GPU"]
        MON["colab_a100_live_monitor.py\nprotocol=two_phase_happo_masac_v3"]
        G1 --- S1 --- S2 --- MON
    end

    START --> PHASE1
    PHASE1 -->|"6/6 completados"| PHASE2
    PHASE2 --> ARTEFACTOS
    PHASE1 & PHASE2 -->|"escribe en tiempo real"| STATUS

    classDef p1 fill:#dbeafe,stroke:#2563eb,color:#1c1917
    classDef p2 fill:#dcfce7,stroke:#16a34a,color:#1c1917
    classDef art fill:#f8fafc,stroke:#64748b,color:#1c1917
    classDef stat fill:#fff7ed,stroke:#ea580c,color:#1c1917
    class PHASE1,P1_H,P1_M p1
    class PHASE2,P2_T,P2_A p2
    class ARTEFACTOS art
    class STATUS stat
```

---

## Diagrama 6 — Recompensa Multiobjetivo por Escenario

```mermaid
flowchart LR
    subgraph REW_FUNC["CityLearnV3MADRLRewardFunction"]
        direction TB
        COMP1["Componente FLEX\npeak_penalty + ramping_penalty\n+ load_factor + ev_service"]
        COMP2["Componente CO2\ncarbon_emissions\n* carbon_intensity_signal"]
        COMP3["Componente COSTO\nelectricity_cost\n* price_signal"]
        COMP4["Componente EV\nEV SOC deficit\n* urgencia_salida\n1 / horas_restantes"]
        COMP5["Componente BESS v4\nC-rate penalty\nArrhenius LiFePO4\ndegradacion ciclica"]
    end

    subgraph PESOS["Pesos por escenario (w_eje)"]
        direction TB
        PE1["E1 Flexibilidad\nflex=0.70 co2=0.15 cost=0.15"]
        PE2["E2 CO2\nflex=0.15 co2=0.70 cost=0.15"]
        PE3["E3 Costos\nflex=0.25 co2=0.15 cost=0.60"]
    end

    subgraph MIX["Recompensa mixta (CTDE)"]
        TEAM["team_reward = mean(r₁...r₁₇)\ncooperacion distrital"]
        MIXED["r_i_mix = 0.30 * r_i + 0.70 * team_reward\nteam_ratio=0.70"]
        TEAM --> MIXED
    end

    subgraph PERFILES["Perfiles por algoritmo (v4)"]
        PH["happo_unified_comparable_v4\npeak_weight=0.45 ramp_weight=0.35\nev_weight=0.25 reward_scale=1.00"]
        PM["masac_unified_comparable_v4"]
        PT["matd3_unified_comparable_v4"]
        PA["maac_unified_comparable_v4"]
    end

    REW_FUNC --> PESOS
    PESOS --> MIX
    MIX --> PERFILES

    PERFILES -->|"mismos pesos base\ndiferente backend"| TRAIN(["Entrenamiento\nuniforme y comparable\npara todos los algoritmos"])

    classDef rw fill:#fef3c7,stroke:#d97706,color:#1c1917
    classDef pe fill:#e0e7ff,stroke:#4f46e5,color:#1c1917
    classDef mx fill:#fae8ff,stroke:#a21caf,color:#1c1917
    classDef pf fill:#f0fdf4,stroke:#16a34a,color:#1c1917
    class REW_FUNC rw
    class PESOS pe
    class MIX mx
    class PERFILES pf
```

---

## Diagrama 7 — Pipeline de Evaluacion y Seleccion del Mejor MADRL

```mermaid
flowchart TD
    subgraph ARTIFACTS_IN["Entrada: artefactos de 12 corridas (50 ep · two_phase)"]
        direction LR
        R_J["results.json\npor cada algo/escenario"]
        TS["timeseries.csv\npor cada algo/escenario"]
        TR["trace.csv\npor cada algo/escenario"]
    end

    subgraph BENCHMARK["Benchmark CityLearn v2 (linea base)"]
        direction TB
        RBC["Agente RBC\nRule-Based Control\noriginal CityLearn v2"]
        SAC_V2["SAC v2\noriginal CityLearn v2"]
        BENCH_OUT["baseline_kpis.csv\npor escenario"]
        RBC & SAC_V2 --> BENCH_OUT
    end

    subgraph KPIS_CALC["Calculo de KPIs por escenario"]
        direction TB
        E1_KPI["E1 KPIs (OE1)\npeak_average\nramping_average\n1-load_factor_average"]
        E2_KPI["E2 KPIs (OE2)\ncarbon_emissions_total\ncarbon_emissions_from_elec"]
        E3_KPI["E3 KPIs (OE3)\nelectricity_cost_total\nelectricity_cost_from_elec"]
    end

    subgraph DELTA["Gain relativo vs baseline"]
        GAIN["gain_i = (KPI_v2 - KPI_v3) / abs(KPI_v2)\nvalor positivo = mejora\npor cada KPI, escenario y algoritmo"]
    end

    subgraph STAT_TEST["Suite de pruebas estadisticas (4 tests)"]
        direction LR
        SW["Shapiro-Wilk\n¿Distribucion normal?\npor algoritmo y eje"]
        KW["Kruskal-Wallis\n¿Diferencia global?\n4 grupos simultaneos"]
        MWU["Mann-Whitney U\n¿Cual par difiere?\nmuestras independientes\n+ Cliff delta + Hedges g"]
        WC["Wilcoxon SR\n¿Diferencia sistematica?\nmuestras pareadas"]
        SW --> KW --> MWU --> WC
    end

    subgraph RANKING["Ranking inter-algoritmo"]
        direction TB
        SCORE_E1["Score E1\nponderado por KPIs flex"]
        SCORE_E2["Score E2\nponderado por KPIs CO2"]
        SCORE_E3["Score E3\nponderado por KPIs costo"]
        GLOBAL["Score global\nHAPPO MASAC MATD3 MAAC"]
        SCORE_E1 & SCORE_E2 & SCORE_E3 --> GLOBAL
    end

    subgraph RESULT_BOX["Resultado final corrida v4"]
        direction TB
        MATD3_WIN["MATD3 es el mejor MADRL global\nE1=0.7486 E2=0.7515 E3=0.7333\nKW p=0.0459 → Significativo α=0.05"]
        PAIRS["Diferencias significativas\nMATD3 vs HAPPO: MWU p=0.0182\nMATD3 vs HAPPO: Wilcoxon p=2.62e-6"]
        MATD3_WIN --> PAIRS
    end

    ARTIFACTS_IN --> KPIS_CALC
    BENCHMARK --> KPIS_CALC
    KPIS_CALC --> DELTA
    DELTA --> STAT_TEST
    STAT_TEST --> RANKING
    RANKING --> RESULT_BOX

    subgraph OUTPUT_FILES["Archivos de salida (outputs/thesis_objective_evidence/)"]
        OF1["analisis_estadistico_madrl.csv\nSW + KW por eje"]
        OF2["comparaciones_mwu_madrl.csv\nMWU + effect sizes"]
        OF3["comparaciones_wilcoxon_madrl.csv\nWilcoxon SR pareado"]
        OF4["hipotesis_estadisticas_madrl.csv\n4 tests unificados"]
        OF5["scores_kpi_algoritmo_madrl.csv\nranking final"]
    end

    RESULT_BOX --> OUTPUT_FILES

    classDef inp fill:#dbeafe,stroke:#2563eb,color:#1c1917
    classDef bench fill:#f0fdf4,stroke:#16a34a,color:#1c1917
    classDef kpi fill:#e0e7ff,stroke:#4f46e5,color:#1c1917
    classDef stat fill:#fae8ff,stroke:#a21caf,color:#1c1917
    classDef rank fill:#fef3c7,stroke:#d97706,color:#1c1917
    classDef res fill:#ffedd5,stroke:#ea580c,color:#1c1917,stroke-width:3px
    classDef out fill:#f8fafc,stroke:#64748b,color:#1c1917
    class ARTIFACTS_IN inp
    class BENCHMARK bench
    class KPIS_CALC,DELTA kpi
    class STAT_TEST stat
    class RANKING rank
    class RESULT_BOX res
    class OUTPUT_FILES out
```

---

## Diagrama 8 — Infraestructura de Despliegue: Local, Colab A100 y AWS EC2

```mermaid
flowchart LR
    subgraph COLAB["Colab A100 Pro+ (canal oficial de entrenamiento)"]
        direction TB
        BADGE["Open in Colab\nMac-Tapia/CityLearn\ncodex/iquitos-distillation-madrl-docs"]
        SYNC["Celda 1.2 hard sync\n/content/MADRLCitytleranflexresdr"]
        LAUNCH_C["colab_a100_official_launcher.py\ntwo_phase_happo_masac_v3\n50 ep · 12 jobs"]
        DRIVE["Google Drive outputs\nMADRLCitytleranflexresdr/outputs"]
        MON_C["colab_a100_live_monitor.py\ncolab_protocol_guard.py"]
        BADGE --> SYNC --> LAUNCH_C --> DRIVE
        LAUNCH_C --> MON_C
    end

    subgraph DEV["Desarrollo local (Windows — RTX 4060)"]
        direction TB
        CODE["Codigo fuente\nCityLearn/ + uc3m/\nscripts/ + tools/"]
        VENV["Entorno .venv39-citylearn-v3\nPyTorch 2.8.0+cu126"]
        PS["Launcher local PS1\nsmoke test rapido"]
        MON_L["monitor_citylearn_v3_official_training.ps1"]
        CODE --> VENV --> PS --> MON_L
    end

    subgraph GIT["Repositorio GitHub"]
        REPO_P["Mac-Tapia/MADRLCitytleranflexresdr\ncodex/fix-madrl-traceability-docs"]
        REPO_CL["Mac-Tapia/CityLearn\ncodex/iquitos-distillation-madrl-docs"]
        REPO_P --- REPO_CL
    end

    subgraph AWS["Produccion AWS EC2 (opcional)"]
        direction TB
        DOCKER["Docker madrl-training\nrun_aws_training.sh"]
        VOL["bind mount outputs/"]
        DOCKER --> VOL
    end

    DEV -->|"git push"| GIT
    GIT -->|"clone + submodule"| COLAB
    GIT -->|"clone --recurse-submodules"| AWS
    COLAB -->|"artefactos Drive"| DEV

    classDef colab fill:#e0e7ff,stroke:#4f46e5,color:#1c1917
    classDef dev fill:#e0f2fe,stroke:#0284c7,color:#1c1917
    classDef git fill:#f0fdf4,stroke:#16a34a,color:#1c1917
    classDef aws fill:#fef3c7,stroke:#d97706,color:#1c1917
    class COLAB colab
    class DEV dev
    class GIT git
    class AWS aws
```

---

## Diagrama 9 — Estructura de Capas del Software

```mermaid
flowchart TD
    subgraph L1["Capa 1: Simulador base (CityLearn v2)"]
        direction LR
        CL2["CityLearn/citylearn/*.py\nFisica edificios + BESS + PV + EV\nKPIs oficiales del challenge"]
    end

    subgraph L2["Capa 2: Extension experimental (CityLearn v3 propuesto)"]
        direction LR
        ENV3["CityLearn/citylearn/v3/\nDec-POMDP environment\nObjectives + Config + Reward"]
        COMM["CityLearn/scripts/\ncitylearn_v3_training_common.py\nresolve_output_dir() + ensure_artifact_layout()"]
        ENV3 --- COMM
    end

    subgraph L3["Capa 3: Framework UC3M (wrapper universal)"]
        direction LR
        UC3M_E["uc3m/env/uc3m_env.py\nUC3MEnv: Dec-POMDP 11-aria\nCompatible HARL + MARLlib + RLlib"]
        UC3M_B["uc3m/env/bact.py\nBACTTensor 29D\nClima(7)+Geo(8)+Fisico(14)"]
        UC3M_R["uc3m/reward/axes.py\nRewardAxes 7 ejes\nflex+co2+cost+ev+bess+resil+acs"]
        UC3M_H["uc3m/reward/hphi.py\nHPHI: Holistic Pareto\nHypervolume Index 7D"]
        UC3M_K["uc3m/kpis/evaluator.py\nKPIEvaluator\nnormalizados contra RBC"]
        UC3M_E --- UC3M_B --- UC3M_R --- UC3M_H --- UC3M_K
    end

    subgraph L4["Capa 4: Backends MADRL externos"]
        direction LR
        HARL["external/HARL/\nHAPPO: on-policy\nsequential trust region"]
        MARL["external/MARL/src/\nMASAC: Q-mix + SAC discreto"]
        OFFP["external/off-policy/\nMATD3: doble critico TD3"]
        MAAC_B["external/MAAC/\nMAC: attention critic SAC"]
        HARL --- MARL --- OFFP --- MAAC_B
    end

    subgraph L5["Capa 5: Launchers y orquestacion"]
        direction LR
        TRAIN_S["CityLearn/scripts/train_citylearn_v3_*.py\n4 scripts de entrenamiento\nuno por algoritmo"]
        COLAB_L["CityLearn/scripts/colab_a100_official_launcher.py\ncolab_a100_live_monitor.py\ncolab_protocol_guard.py · two_phase_happo_masac_v3"]
        LAUNCH["scripts/ + deploy/aws/training/\nLaunchers locales PS + AWS bash\nMonitoreo + checkpointing"]
        TRAIN_S --- COLAB_L --- LAUNCH
    end

    subgraph L6["Capa 6: Evaluacion y evidencia"]
        direction LR
        GEN["CityLearn/scripts/generate_thesis_objective_evidence.py\nKPIs + estadisticas + figuras"]
        BENCH["CityLearn/scripts/benchmark_citylearn_v2_agents.py\nLinea base RBC + SAC v2"]
        COMP["CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py\nDelta + ranking + HPHI"]
        GEN --- BENCH --- COMP
    end

    L1 -->|"extiende"| L2
    L2 -->|"wrap universal"| L3
    L3 -->|"conecta"| L4
    L4 -->|"invocado por"| L5
    L5 -->|"genera artefactos para"| L6

    classDef l1 fill:#f1f5f9,stroke:#64748b,color:#1c1917
    classDef l2 fill:#e0e7ff,stroke:#4f46e5,color:#1c1917
    classDef l3 fill:#dbeafe,stroke:#2563eb,color:#1c1917
    classDef l4 fill:#fae8ff,stroke:#a21caf,color:#1c1917
    classDef l5 fill:#fef3c7,stroke:#d97706,color:#1c1917
    classDef l6 fill:#dcfce7,stroke:#16a34a,color:#1c1917
    class L1 l1
    class L2 l2
    class L3 l3
    class L4 l4
    class L5 l5
    class L6 l6
```

---

## Tabla de Resultados v4 — Corrida Definitiva

| Algoritmo | OE1 Flex Score | OE2 CO2 Score | OE3 Costo Score | Score Global | Rango |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **MATD3** | **0.7486** | **0.7515** | **0.7333** | **0.7445** | **1 (mejor)** |
| MASAC | 0.74 | 0.74 | 0.72 | ~0.73 | 2 |
| MAAC | 0.72 | 0.72 | 0.73 | ~0.72 | 3 |
| HAPPO | 0.70 | 0.70 | 0.70 | ~0.70 | 4 |

**Pruebas estadisticas (OE global):**

| Test | Resultado | p-valor | Conclusion |
|---|---|:---:|---|
| Shapiro-Wilk | Algunos grupos no normales | — | Justifica tests no parametricos |
| Kruskal-Wallis | Diferencia entre algoritmos | **0.0459** | **Significativo α=0.05** |
| Mann-Whitney U: MATD3 vs HAPPO | MATD3 superior | **0.0182** | Significativo |
| Wilcoxon SR: MATD3 vs HAPPO | Diferencia sistematica | **2.62e-6** | Muy significativo |

---

## Archivos de Documentacion y Referencia

| Documento | Contenido |
|---|---|
| `docs/architecture/ARQUITECTURA_PROYECTO_DEFENSA.md` | Este documento — 9 diagramas Mermaid |
| `docs/architecture/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md` | Flujo vigente y corridas oficiales |
| `docs/architecture/COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.md` | Dec-POMDP y CTDE detallado |
| `docs/architecture/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` | Arquitectura profesional completa |
| `ESTRATEGIA_3PILARES_MADRL.md` | Ejes OE1/OE2/OE3 y sustento cientifico |
| `docs/thesis/PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md` | Plan de tesis estructurado |
| `deploy/aws/README_TRAINING_AWS.md` | Manual completo de entrenamiento AWS |
