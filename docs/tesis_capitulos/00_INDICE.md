# Índice — Informe de Tesis por Capítulos (MADRL · CityLearn v3 · Iquitos)

**Tesis:** *Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes.*
**Autor:** Mac Tapia (mac.tapia.c@uni.pe) · **Universidad:** UNI (Maestría profesionalizante)
**Caso de estudio:** Sistema Eléctrico Aislado de Iquitos (SEAI) — 17 edificios reales, Electro Oriente S.A., Loreto, Perú.
**Algoritmos:** HAPPO, MASAC, MATD3, MAAC · **Ejes:** OE.1 flexibilidad, OE.2 CO₂, OE.3 costos.

> Cada archivo es autocontenido e incluye, al inicio, un bloque **"PROMPT PARA PERPLEXITY (versión final)"** para pulir el capítulo a versión académica final con citas APA. Los datos inexistentes en el proyecto se marcan con `[Pendiente: ...]`. Construido leyendo `docs/`, el código real (`CityLearn/citylearn/v3/`, `reward_function.py`, `train_citylearn_v3_*.py`), configuración (`workflow_manifest.json`, YAML/JSON) y artefactos de `outputs/`.

---

## Archivos

| # | Archivo | Contenido | Estado |
|---|---|---|---|
| 0 | `00_INDICE.md` | Este índice | Completo |
| 1 | `Capitulo_1_Introduccion.md` | Problema, objetivos (OG/OE.1-3), hipótesis (HG/HE.1-3), justificación (6 dim.), alcances y limitaciones | Completo · placeholders menores |
| 2 | `Capitulo_2_Marco_Teorico.md` | Estado del arte (4 ejes), bases teóricas (Dec-POMDP, CTDE, 4 algoritmos), tabla de trabajos relacionados, *gap analysis* | Completo · placeholders menores |
| 3 | `Capitulo_3_Metodologia.md` | Tipo/diseño, variables, muestreo, **dataset Iquitos** (17 edificios, 222 CSV, 26 304 h, DER), técnicas, instrumentos, procedimiento (12 corridas) | Completo · placeholders menores |
| 4 | `Capitulo_4_Desarrollo_Propuesta.md` | Arquitectura 6 capas, Dec-POMDP, CTDE, recompensa multiobjetivo (ecuaciones + pesos), hiperparámetros reales por algoritmo (v4 y canónico), 4 aportes al motor | Completo · placeholders menores |
| 5 | `Capitulo_5_Resultados.md` | 12 corridas v4, métricas, ranking (MATD3 0.7445), comparación con baseline, estadística (KW p=0.0459), figuras, discusión | Con placeholders pendientes (corrida canónica) |
| 6 | `Capitulo_6_Conclusiones.md` | Hallazgos por OG/OE, limitaciones, trabajo pendiente, plan de culminación (H1-H7) | Completo · placeholders de cierre |
| R | `Referencias_APA.md` | ~55 referencias APA (A-F), marcas ✓ / `[PV]` | Consolidado · ~10 `[PV]` por verificar |

---

## Resumen de cada capítulo

- **Capítulo 1 — Introducción.** Plantea el problema de la gestión coordinada de DER en una red aislada diésel (0.790 kgCO₂/kWh; tarifas 0.26/0.38 USD/kWh). Define PG/PE, OG/OE, HG/HE y la justificación. Alcance: simulación (no despliegue real); CityLearn v3 = extensión experimental.
- **Capítulo 2 — Marco teórico.** Sintetiza 50 antecedentes en 4 ejes, formaliza Dec-POMDP y CTDE, y describe técnicamente HAPPO/MASAC/MATD3/MAAC con sus backends (`external/HARL`, `MARL/src`, `off-policy`, `MAAC`). Identifica la brecha: ausencia de benchmark unificado de los 4 algoritmos en 3 ejes.
- **Capítulo 3 — Metodología.** Estudio cuantitativo, aplicado, comparativo, no experimental. Detalla el dataset real de Iquitos (pipeline de 10 etapas, fuentes PVGIS/NASA POWER, destilación de facturación) y el procedimiento de 12 corridas con sus gates de validación y las 4 pruebas estadísticas.
- **Capítulo 4 — Desarrollo de la propuesta.** Arquitectura por capas; formulación Dec-POMDP (17 agentes, γ=0.9999, T=8 760; observaciones y acciones heterogéneas por edificio, 57-330 obs y 5-44 acciones según cargadores EV); recompensa multiobjetivo con pesos por escenario (E1 0.70/0.15/0.15; E2 0.15/0.70/0.15; E3 0.25/0.15/0.60) y perfil unificado (r=0.70, peak 0.45, ramp 0.35, ev 0.25); hiperparámetros reales (v4 local vs canónico de 50 ep en Colab A100, modo `two_phase_happo_masac`, tomados de la celda 6.1 del notebook); 4 aportes al motor (A1-A4).
- **Capítulo 5 — Resultados.** Corrida v4 completada (12/12, ~39 h en RTX 4060). **MATD3** es el mejor MADRL global (score 0.7445; KW p=0.0459; MATD3>HAPPO MWU p=0.0182, Wilcoxon p=2.62e-6). HAPPO lidera flexibilidad pura (OE.1); MATD3 lidera CO₂/costos (E2/E3). Resultados preliminares (5 episodios, semilla única).
- **Capítulo 6 — Conclusiones preliminares.** Responde OG/OE con evidencia; limitaciones (cómputo, semilla única, servicio EV); trabajo pendiente (corrida canónica de 50 ep en Colab —en curso—, reemplazo de los resultados preliminares de 5 ep, multi-semilla, Pareto, Optuna); plan H1-H7.
- **Referencias APA.** Lista consolidada; pendiente completar entradas `[PV]`.

---

## Estado global

| Capítulo | ¿Completo? | Principales placeholders |
|---|---|---|
| 1 | Sí | H0/H1 según UNI; unidad de posgrado |
| 2 | Sí | datos `[PV]`; benchmarks 2025-2026 |
| 3 | Sí | nº semillas; episodios objetivo |
| 4 | Sí | composición de 1856 dims de estado |
| 5 | **Parcial** | scores exactos por algoritmo; KPIs OE normalizados; % mejora vs baseline; MWU/Wilcoxon pares restantes; figuras |
| 6 | Sí | confirmación con corrida canónica |
| Ref. | Sí | ~10 entradas `[PV]` |

**Recomendación de uso:** abrir cada archivo en Perplexity, ejecutar el bloque "PROMPT PARA PERPLEXITY" para pulir a versión final, y completar primero los placeholders del Capítulo 5 tras la corrida canónica de 50 episodios.

> **Aviso sobre los resultados del Capítulo 5 (preliminares).** Las cifras actuales del Capítulo 5 provienen de la corrida local preliminar de **5 episodios**. La **corrida canónica de 50 episodios** se está ejecutando en Google Colab (NVIDIA A100-SXM4-80GB, modo `two_phase_happo_masac`, `gamma=0.9999`, `hidden_size` 512/768; ver celda 6.1 del notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`). Al finalizar, se deben **reemplazar** los resultados preliminares de 5 episodios por los de 50 episodios, recalcular los KPIs normalizados, las pruebas estadísticas y los % de mejora vs baseline, e insertar las figuras `.png` definitivas.
>
> **Integración de resultados de Colab/Drive.** Los artefactos de la corrida canónica (results.json, training_summary.json, comparativas y figuras) se descargarán a `outputs/colab_50ep/` desde la carpeta de Google Drive del entrenamiento. A la fecha de esta edición, la carpeta de Drive **no es accesible automáticamente** (responde HTTP 401): requiere compartirla como "Cualquier persona con el enlace" o realizar una descarga manual. Mientras tanto, el Capítulo 5 mantiene los resultados preliminares de 5 episodios con marcadores explícitos `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`.
