# MADRL CityLearn v3 — Tutorial Completo (Google Colab · A100)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/codex/iquitos-distillation-madrl-docs/examples/madrl_citylearn_v3_tutorial.ipynb)

**Proyecto:** Multi-Agente de Aprendizaje por Refuerzo Profundo para gestion coordinada
de flexibilidad energetica, emisiones de CO2 y eficiencia economica en comunidades inteligentes.

**Caso de estudio:** 17 edificios reales de Iquitos, Peru · Dataset 2023-2025 · 26 304 pasos horarios.

| Parametro | Valor |
|---|---|
| Algoritmos | HAPPO · MASAC · MATD3 · MAAC |
| Escenarios | E1 (Flexibilidad) · E2 (CO2) · E3 (Costos) |
| Episodios | 50 por corrida (reanudable con --skip-completed) · 8 760 pasos/episodio |
| Total steps | 438 000 por corrida · 5 256 000 en los 12 jobs |
| GPU objetivo | NVIDIA H100 (~26 vCPU) primario · A100-SXM4-80GB compatible · 167 GiB RAM (Colab Pro+ High-RAM) |
| Ejecucion | two_phase_happo_masac (6+6 paralelo), recuperable, monitor y reintento OOM |

> **Requisito:** Seleccionar A100 en *Runtime -> Change runtime type -> A100 GPU*. El notebook falla temprano si Colab entrega otra GPU.

### Fuentes cientificas y de tesis usadas para el diseno

- CityLearn estandariza la evaluacion RL/MARL para demanda respuesta urbana: https://arxiv.org/abs/2012.10504
- CityLearn v2 y CityLearn Challenge documentan KPIs de flexibilidad, carbono y costo: https://escholarship.org/content/qt5t48x8xk/qt5t48x8xk.pdf y https://proceedings.mlr.press/v220/nweye23a.html
- HAPPO/HATRPO justifica actualizacion secuencial y trust region en MARL: https://openreview.net/forum?id=EcGGFkNTxdJ
- MAAC usa criticos centralizados con atencion para escalar agentes: https://proceedings.mlr.press/v97/iqbal19a.html
- MATD3 reduce sobreestimacion mediante doble critico centralizado: https://arxiv.org/abs/1910.01465
- MASAC se apoya en SAC y mezcla QMIX/CTDE: https://arxiv.org/abs/1812.05905 y https://arxiv.org/abs/1803.11485
- PyTorch CUDA y reproducibilidad: https://docs.pytorch.org/docs/stable/notes/cuda.html y https://docs.pytorch.org/docs/stable/notes/randomness.html
- Colab no garantiza tipo de GPU ni duracion; por eso se requiere checkpoint/estado recuperable: https://research.google.com/colaboratory/faq.html
- A100 40/80 GB, HBM y TF32: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-us-nvidia-1758950-r4-web.pdf
- Tesis consultadas sobre RL/MARL energetico: Ross May PhD Dalarna 2023, Oxford residential flexibility thesis, Politecnico di Torino MARL building-energy thesis.
