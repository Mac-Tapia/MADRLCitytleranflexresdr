## Seccion 6: Hiperparametros (A100 estable · 50 episodios/corrida · two_phase)

Perfil optimizado para `two_phase_happo_masac`: 6 jobs/fase en paralelo (sin stagger), A100-80GB + 167 GiB RAM.
La Seccion 6 (celda con `N_EPISODES`) es la **fuente unica de verdad**; el launcher aplica overrides de fase. Los hilos de CPU se **auto-ajustan** a las vCPU del runtime (A100 12 -> Fase1 torch=1/rollout=2, Fase2 torch=2; H100 ~26 -> Fase1 torch=2/rollout=4, Fase2 torch=4). MASAC replay en **CPU**; `critic_batch_size=1` **episodio** por update QMIX (Rashid et al. 2018 usan 32 ep x 60-120 pasos SMAC; CityLearn = 8760 pasos/ep).

| Algoritmo | Parametro clave | Valor A100 two_phase | OOM retry |
|---|---|---|---|
| **HAPPO** | hidden / n_rollout_threads | 512 / **auto (2 A100, 4 H100)** | hidden 256 |
| **MASAC** | buffer ep / max GiB / critic_batch | **2 / 8.0 / 1** | 2 / 6.0 / 1 (+ CPU replay) |
| **MASAC** | rnn / qmix / hyper hidden | **64 / 32 / 64** | 64 / 32 / 64 |
| **MATD3** | batch / buffer / hidden | **1280 / 2M / 768** | 768 / 1M / 512 |
| **MAAC** | batch / buffer / hidden / num_updates | **768 / 1M / 768 / 12** | 512 / 500K / 512 / 8 |

| Global | Valor |
|---|:---:|
| Episodios × pasos | 50 × 8 760 (por corrida, reanudable con --skip-completed) |
| Torch threads (two_phase) | 2 |
| CUDA fraction HAPPO/MATD3/MAAC (6-parallel) | **0.14-0.15** |
| CUDA fraction MASAC (6-parallel) | **0.16-0.22** (Blackwell 96 GiB -> ~21 GiB/job) |
| MASAC replay device | **cpu** (QMIX unroll 8760 pasos en GPU) |
| OOM retry | activo |
| Reanudacion | `--skip-completed` |
