### 7.6 Benchmarks comparativos CityLearn v2

#### Baseline principal integrado en `evaluate_v2`

El sistema de evaluacion de CityLearn v2 calcula la linea base RBC local en cada corrida y los artefactos MADRL guardan `objective_kpis`, `axis_baseline_comparison` y `baseline_gain_by_kpi` contra esa referencia.

#### PPO/SAC/A2C como benchmarks comparativos CityLearn v2

PPO, SAC y A2C se ejecutan solo como **benchmarks CityLearn v2 de agente central** con Stable-Baselines3 sobre el mismo schema local:

`CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`

| Agente | Script CityLearn v2 | Salida comparable |
|---|---|---|
| PPO | `CityLearn/scripts/benchmark_citylearn_v2_ppo.py` | `outputs/citylearn_v2_original_benchmark/ppo/<scenario>_seed_<seed>/` |
| SAC | `CityLearn/scripts/benchmark_citylearn_v2_sac.py` | `outputs/citylearn_v2_original_benchmark/sac/<scenario>_seed_<seed>/` |
| A2C | `CityLearn/scripts/benchmark_citylearn_v2_a2c.py` | `outputs/citylearn_v2_original_benchmark/a2c/<scenario>_seed_<seed>/` |

Estos scripts no crean agentes MADRL v3. Entrenan/evaluan un agente central CityLearn v2 (`central_agent=True`) y escriben el mismo layout de tablas/figuras que consume `compare_citylearn_v2_vs_v3_madrl.py`.

> Separacion clara: HAPPO/MASAC/MATD3/MAAC son los 4 algoritmos MADRL principales. PPO/SAC/A2C son benchmarks comparativos CityLearn v2 con el mismo dataset local Iquitos.

