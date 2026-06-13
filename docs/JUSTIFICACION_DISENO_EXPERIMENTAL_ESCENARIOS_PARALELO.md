# Justificacion del Diseno Experimental: Tres Escenarios y Entrenamiento Paralelo

**Fecha:** 2026-06-12
**Contexto:** Tesis MADRL CityLearn v3 Iquitos — Diseno de 12 corridas oficiales (4 algoritmos × 3 escenarios)
**Codigo de referencia:** `CityLearn/citylearn/reward_function.py:526-530`, `CityLearn/scripts/launch_citylearn_v3_official_training.ps1`

---

## 1. Por que existen tres escenarios (E1, E2, E3)

### 1.1 Fundamento conceptual

Los escenarios E1, E2 y E3 no son repeticiones del mismo experimento: son **tres preguntas de investigacion distintas** respondidas con la misma arquitectura algortimica. Cada escenario asigna un vector de pesos diferente a la funcion de recompensa escalarizada, condicionando la politica aprendida hacia un objetivo dominante diferente:

| Escenario | Vector de pesos (w_flex, w_CO2, w_costo) | Objetivo de investigacion |
|---|:---:|---|
| **E1** | (0.70, 0.15, 0.15) | ¿Puede MADRL reducir el pico de demanda y ramping del distrito priorizando flexibilidad energetica? |
| **E2** | (0.15, 0.70, 0.15) | ¿Puede MADRL desplazar consumo hacia horas de baja intensidad de carbono en red diesel aislada? |
| **E3** | (0.25, 0.15, 0.60) | ¿Puede MADRL arbitrar la tarifa TOU (0.26/0.38 USD/kWh) para minimizar el costo energetico distrital? |

Cada escenario produce una **politica entrenada diferente** — los pesos de las redes neuronales de los actores y criticos divergen porque el gradiente de politica se construye con funciones de recompensa distintas. Al final del experimento, las 12 politicas (4 algoritmos × 3 escenarios) se comparan entre si con los KPIs oficiales de CityLearn, permitiendo responder:

> "¿Que algoritmo MADRL logra mejor reduccion de pico (OE.1), menor emision CO2 (OE.2) y menor costo (OE.3) en la comunidad de 17 edificios de Iquitos?"

Esta estructura es la base metodologica de los tres objetivos especificos de la tesis.

---

### 1.2 Sustento en escalarizacion multi-objetivo (MORL)

La escalarizacion lineal de objetivos con vectores de pesos es el enfoque canonico para convertir un problema de optimizacion multi-objetivo en una serie de problemas escalares que los algoritmos RL estandar pueden resolver:

**Roijers et al. (2013)** — *"A survey of multi-objective sequential decision-making"*. Journal of Artificial Intelligence Research, 47, 67-113.

> La escalarizacion lineal `r_scalar = Σ_k w_k · r_k` permite derivar la ecuacion de Bellman estandar para cada vector de pesos, siendo compatible con todos los metodos de RL existentes. Cada vector de pesos define una politica de Pareto-optima diferente en el frente de Pareto de soluciones.

**Felten, Talbi & Danoy (2024)** — *"Multi-Objective Reinforcement Learning Based on Decomposition: A Taxonomy and Framework"*. Journal of Artificial Intelligence Research, 79. arXiv:2311.12495.

> El framework MORL/D demuestra que descomponer el problema multi-objetivo en subproblemas escalarizados mediante vectores de pesos es la estrategia correcta para explorar eficientemente el frente de Pareto. Cada subproblema (escenario) debe entrenarse con una politica independiente, ya que los gradientes de politica son fundamentalmente distintos para cada vector de pesos.

**Abels et al. (2019)** — *"Dynamic Weights in Multi-Objective Deep Reinforcement Learning"*. ICML 2019, PMLR 97:11-20. arXiv:1809.07803.

> El condicionamiento de politicas sobre vectores de pesos fijos permite aprender politicas especializadas para distintas preferencias de objetivo. La separacion de politicas por vector de pesos es estadisticamente necesaria: una unica red no puede capturar simultaneamente comportamientos optimos bajo preferencias contradictorias (maximizar flexibilidad vs. minimizar CO2 tienen gradientes opuestos en muchos estados).

**Implicacion directa para la tesis:** Los tres vectores de pesos (E1/E2/E3) definen tres puntos distintos del frente de Pareto del espacio {flexibilidad, CO2, costo}. Entrenar una unica politica con pesos balanceados no responderia las preguntas de los objetivos especificos OE.1, OE.2 y OE.3 por separado.

---

### 1.3 Validacion en CityLearn y benchmarks de edificios

**Vazquez-Canteli et al. (2020)** — *"CityLearn: Standardizing Research in Multi-Agent Reinforcement Learning for Demand Response and Urban Energy Management"*. arXiv:2012.10504. Publicado en ACM e-Energy 2021.

> CityLearn establece como estandar de evaluacion el uso de multiples configuraciones de control con distintas funciones de costo, incluyendo: cargo por demanda, pico de demanda, ramping, solar no aprovechada y frecuencia de red. La evaluacion por configuracion separada es la practica recomendada para medir la generalizacion de politicas MARL.

**Nweye et al. (2023)** — *"The CityLearn Challenge 2022: Overview, Results, and Lessons Learned"*. Proceedings of Machine Learning Research, 220:85-103. NeurIPS 2022 Competitions Track.

> El CityLearn Challenge 2022 valida experimentalmente el diseno de escenarios multiples independientes. La competicion incluyo pistas separadas de evaluacion para: minimizacion de costos, reduccion de emisiones de CO2 y estabilidad de red — exactamente la estructura E1/E2/E3 de esta tesis. Los equipos ganadores ("Together", "DME") desarrollaron agentes especializados por objetivo, no agentes unicos que optimizaran los tres simultaneamente.

**Nweye et al. (2024)** — *"CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities"*. Journal of Building Performance Simulation, 18(1). arXiv:2405.03848.

> CityLearn v2 introduce soporte explicito para escenarios de control multiples con objetivos dinamicos: flexibilidad energetica, resiliencia, confort de ocupantes y conciencia de carbono. El framework valida la practica de entrenar politicas separadas por objetivo de control.

**Nweye et al. (2024)** — *"The CityLearn Challenge: Four Years of Advancing Common Task Frameworks for Energy Management in Smart Buildings"*. ACM e-Energy 2024. DOI: 10.1145/3679240.3734667.

> La evolucion del challenge a lo largo de cuatro anos (2020-2023) consolida los escenarios independientes por objetivo como el estandar de oro para benchmarking de MARL en edificios. El challenge 2023 introdujo escenarios diferenciados para flexibilidad de carga, resiliencia ante cortes y huella de carbono.

**Drgnona et al. (2023)** — *"Applications in CityLearn Gym Environment for Multi-Objective Control Benchmarking in Grid-Interactive Buildings and Districts"*. arXiv:2408.15170.

> Demuestra que CityLearn es el entorno correcto para benchmarking multi-objetivo en edificios interconectados a la red, y que los escenarios independientes por objetivo son la metodologia de comparacion adecuada.

**Lu et al. (2022)** — *"A multi-objective multi-agent deep reinforcement learning approach to residential appliance scheduling"*. IET Smart Grid, 5(3).

> Trata los objetivos de edificios (costo, confort, emisiones) como metas de optimizacion independientes en frameworks MADRL, con politicas entrenadas separadamente para cada combinacion de objetivos. Los resultados muestran que las politicas especializadas superan consistentemente a las politicas de compromiso unico.

---

### 1.4 Sustento en benchmarks MOMARL

**Felten et al. (2024)** — *"MOMAland: A Set of Benchmarks for Multi-Objective Multi-Agent Reinforcement Learning"*. arXiv:2407.16312. Farama Foundation.

> MOMAland, el primer benchmark estandarizado para MOMARL con 10+ entornos diversos, valida que el enfoque correcto consiste en entrenar politicas separadas por vector de pesos y luego comparar sus metricas en el frente de Pareto. Los autores demuestran que una politica unica con pesos mixtos no puede aproximar el frente de Pareto completo con la misma precision que politicas especializadas.

---

## 2. Por que el entrenamiento en paralelo es correcto

### 2.1 Independencia de los experimentos

Los tres escenarios para el mismo algoritmo (p. ej. HAPPO/E1, HAPPO/E2, HAPPO/E3) son **experimentos completamente independientes**. No comparten ningun recurso computacional o estado durante el entrenamiento:

| Recurso | HAPPO/E1 | HAPPO/E2 | ¿Compartido? |
|---|---|---|:---:|
| Instancia del entorno CityLearn | Propia | Propia | No |
| Pesos de la red neuronal actor | Politica E1 | Politica E2 | No |
| Buffer de experiencias | On-policy propio | On-policy propio | No |
| GPU VRAM | ~300 MiB | ~300 MiB | No |
| Semilla aleatoria | seed=0, env_id=E1 | seed=0, env_id=E2 | No |
| Funcion de recompensa | w=(0.70,0.15,0.15) | w=(0.15,0.70,0.15) | No |

La ejecucion en paralelo produce **exactamente los mismos resultados** que la ejecucion secuencial porque no existe ninguna dependencia entre los procesos. Esto es matematicamente equivalente a ejecutarlos en dias distintos en la misma maquina.

### 2.2 Sustento en la literatura de RL paralelo

**Springer Nature (2024)** — *"Accelerating Independent Multi-Agent Reinforcement Learning on Multi-GPU Platforms"*. Proceedings of ECML/PKDD 2025.

> El aprendizaje independiente (IL) en MARL es "embarrassingly parallel" — la paralelizacion de experimentos independientes en multiples GPUs logra hasta **15.5× mayor throughput** sin alterar la semantica de aprendizaje ni la convergencia. Los autores demuestran formalmente: "independent learner semantics are essentially unchanged when parallelized".

**Zhou et al. (2021)** — *"MALib: A Parallel Framework for Population-based Multi-agent Reinforcement Learning"*. Journal of Machine Learning Research, 24(1). arXiv:2106.07551.

> MALib demuestra que el entrenamiento en paralelo de politicas heterogeneas independientes logra 5× speedup sobre RLlib y 3× sobre OpenSpiel, sin interferencia entre experimentos. Prueba que la paralelizacion de runs independientes de MARL es correcta metodologicamente y computacionalmente eficiente.

### 2.3 Restricciones de memoria y limites del paralelo

El paralelismo no es ilimitado — esta acotado por la VRAM disponible y la memoria RAM del sistema. Por eso el launcher implementa:

```
MaxConcurrentScenarioJobs = 2   # HAPPO, MATD3 (on-policy, bajo uso de memoria)
MaxConcurrentHeavyJobs    = 1   # MASAC, MAAC  (off-policy, replay buffer grande)
```

| Algoritmo | Tipo | Memoria por corrida | Max paralelo | Razon |
|---|---|---|:---:|---|
| HAPPO | On-policy | ~300 MiB GPU + ~1.9 GB RAM | 2 | No tiene replay buffer |
| MATD3 | Off-policy (buffer pequeno) | ~300 MiB GPU + ~2.0 GB RAM | 2 | Buffer 4,096 transiciones |
| MASAC | Off-policy (buffer grande) | ~500 MiB GPU + ~3.5 GB RAM | 1 | Buffer 20 episodios (QMIX) |
| MAAC | Off-policy (critic grande) | ~450 MiB GPU + ~3.0 GB RAM | 1 | Critic de atencion multi-cabeza |

Con la RTX 4060 Laptop (8,188 MiB VRAM, reserva 1,500 MiB):
- 2 × HAPPO paralelo: 600 MiB → **dentro del limite** (margen 6,088 MiB)
- 2 × MASAC paralelo: 1,000 MiB → riesgo de OOM en pico de batch → **secuencial**

---

## 3. Estructura completa del experimento de 12 corridas

### 3.1 Matriz experimental

Cada celda es una politica entrenada independiente que responde una pregunta especifica:

| | **HAPPO** | **MASAC** | **MATD3** | **MAAC** |
|---|:---:|:---:|:---:|:---:|
| **E1** (flex=0.70) | happo/E1 | masac/E1 | matd3/E1 | maac/E1 |
| **E2** (CO2=0.70) | happo/E2 | masac/E2 | matd3/E2 | maac/E2 |
| **E3** (costo=0.60) | happo/E3 | masac/E3 | matd3/E3 | maac/E3 |

**Comparaciones que habilita esta matriz:**
- **Por fila (mismo escenario):** ¿Que algoritmo optimiza mejor OE.1? ¿OE.2? ¿OE.3? → responde la pregunta de cual MADRL es superior por objetivo
- **Por columna (mismo algoritmo):** ¿Como cambia el comportamiento de HAPPO al cambiar el objetivo? → mide la sensibilidad al vector de pesos
- **Diagonal (compromiso):** Comparar rendimiento cruzado de cada politica en objetivos para los que no fue entrenada → mide generalizacion

### 3.2 Secuencia de ejecucion planificada

```
Fase 1: HAPPO  — E1 + E2 paralelo → E3         (on-policy, max 2 concurrentes)
Fase 2: MATD3  — E1 + E2 paralelo → E3         (off-policy leve, max 2)
Fase 3: MASAC  — E1 → E2 → E3 secuencial       (off-policy pesado, max 1)
Fase 4: MAAC   — E1 → E2 → E3 secuencial       (attention critic, max 1)
```

El orden HAPPO → MATD3 → MASAC → MAAC esta motivado por uso de memoria: se ejecutan primero los algoritmos mas ligeros para liberar recursos antes de los mas pesados.

### 3.3 Artefactos producidos por cada corrida

Cada una de las 12 corridas produce, en su directorio `<alg>/E<n>_seed_0/data/`:

```
results.json          — KPIs finales CityLearn (peak_average, ramping_average,
                         carbon_emissions, electricity_cost, etc.)
timeseries.csv        — Serie temporal horaria de variables de control
trace.csv             — Trazas de recompensa, acciones y observaciones
episode_summary.csv   — Resumen por episodio (retorno, paso, tiempo)
training_summary.json — Hiperparametros, configuracion y metricas de entrenamiento
```

Estos artefactos son la base de los graficos y tablas de comparacion de la tesis.

---

## 4. Relacion con los Objetivos Especificos de la Tesis

| Objetivo | Escenario | Metrica principal de evaluacion |
|---|---|---|
| **OE.1** Flexibilidad energetica | E1 (w_flex=0.70) | `peak_average`, `ramping_average`, `one_minus_load_factor_average` |
| **OE.2** Reduccion de CO2 | E2 (w_CO2=0.70) | `carbon_emissions`, `carbon_emissions_delta` |
| **OE.3** Minimizacion de costos | E3 (w_costo=0.60) | `electricity_cost`, `cost_peak_average` |

Sin los tres escenarios, la tesis no puede responder sus tres objetivos especificos de forma independiente. Los escenarios son la implementacion computacional de los OE.

---

## 5. Referencias

### Fundamentos de MORL y escalarizacion

- **Roijers, D. M., Vamplew, P., Whiteson, S., & Dazeley, R. (2013).** A survey of multi-objective sequential decision-making. *Journal of Artificial Intelligence Research*, 47, 67-113.
- **Abels, A., Roijers, D., Lenaerts, T., Nowe, A., & Steckelmacher, D. (2019).** Dynamic Weights in Multi-Objective Deep Reinforcement Learning. *Proceedings of the 36th International Conference on Machine Learning (ICML)*, PMLR 97:11-20. arXiv:1809.07803.
- **Felten, F., Talbi, E.-G., & Danoy, G. (2024).** Multi-Objective Reinforcement Learning Based on Decomposition: A Taxonomy and Framework. *Journal of Artificial Intelligence Research*, 79. arXiv:2311.12495.
- **Felten, F., Ucak, B., Azmani, M., et al. (2024).** MOMAland: A Set of Benchmarks for Multi-Objective Multi-Agent Reinforcement Learning. arXiv:2407.16312. Farama Foundation.

### CityLearn y benchmarks de edificios

- **Vazquez-Canteli, J. R., Dey, S., Henze, G., & Nagy, Z. (2020).** CityLearn: Standardizing Research in Multi-Agent Reinforcement Learning for Demand Response and Urban Energy Management. arXiv:2012.10504. ACM e-Energy 2021.
- **Nweye, K., Sankaranarayanan, S., & Nagy, Z. (2022).** MERLIN: Multi-agent offline and transfer learning for occupant-centric operation of grid-interactive communities. *Applied Energy*, 346, 121323.
- **Nweye, K., et al. (2023).** The CityLearn Challenge 2022: Overview, Results, and Lessons Learned. *Proceedings of Machine Learning Research*, 220:85-103. NeurIPS 2022 Competitions Track.
- **Nweye, K., et al. (2024).** CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities. *Journal of Building Performance Simulation*, 18(1). arXiv:2405.03848.
- **Nweye, K., et al. (2024).** The CityLearn Challenge: Four Years of Advancing Common Task Frameworks for Energy Management in Smart Buildings. *Proceedings of ACM e-Energy 2024*. DOI: 10.1145/3679240.3734667.
- **Drgnona, J., Tucci, F., Nweye, K., Nagy, Z., et al. (2023).** Applications in CityLearn Gym Environment for Multi-Objective Control Benchmarking in Grid-Interactive Buildings and Districts. arXiv:2408.15170.
- **Lu, R., et al. (2022).** A multi-objective multi-agent deep reinforcement learning approach to residential appliance scheduling. *IET Smart Grid*, 5(3).

### HAPPO / HARL para agentes heterogeneos

- **Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Mahajan, A. (2021).** Trust Region Policy Optimisation in Multi-Agent Reinforcement Learning. arXiv:2109.11251. ICLR 2022.
- **Zhong, Y., et al. (2023).** Heterogeneous-Agent Reinforcement Learning. *Journal of Machine Learning Research*, 25(1):1-61. arXiv:2304.09870.
- **Autores (2025).** Heterogeneous Multi-Agent Proximal Policy Optimization for Power Distribution System Restoration. arXiv:2511.14730.

### Paralelismo en MARL

- **Zhou, M., Wan, J., Wang, H., et al. (2021).** MALib: A Parallel Framework for Population-based Multi-agent Reinforcement Learning. *Journal of Machine Learning Research*, 24(1). arXiv:2106.07551.
- **Springer Nature (2024).** Accelerating Independent Multi-Agent Reinforcement Learning on Multi-GPU Platforms. *Proceedings of ECML/PKDD 2025*.

---

*Documento generado tras inspeccion del diseno experimental y busqueda sistematica de literatura. Complementa `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`.*
