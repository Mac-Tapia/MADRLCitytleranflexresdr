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
| 5 | `Capitulo_5_Resultados.md` | Corrida Colab/Drive, métricas, ranking (MATD3 0.6667), KPIs OE.1–OE.3, comparación baseline, estadística (v4 + Colab pendiente), figuras, discusión | Integrado (cobertura parcial 40/11/12 ep) |
| 6 | `Capitulo_6_Conclusiones.md` | Hallazgos por OG/OE (Colab), limitaciones, trabajo pendiente, plan de culminación (H1-H7) | Actualizado · pendientes de cierre |
| R | `Referencias_APA.md` | ~55 referencias APA (A-F), marcas ✓ / `[PV]` | Consolidado · ~10 `[PV]` por verificar |

---

## Resumen de cada capítulo

- **Capítulo 1 — Introducción.** Plantea el problema de la gestión coordinada de DER en una red aislada diésel (0.790 kgCO₂/kWh; tarifas 0.26/0.38 USD/kWh). Define PG/PE, OG/OE, HG/HE y la justificación. Alcance: simulación (no despliegue real); CityLearn v3 = extensión experimental.
- **Capítulo 2 — Marco teórico.** Sintetiza 50 antecedentes en 4 ejes, formaliza Dec-POMDP y CTDE, y describe técnicamente HAPPO/MASAC/MATD3/MAAC con sus backends (`external/HARL`, `MARL/src`, `off-policy`, `MAAC`). Identifica la brecha: ausencia de benchmark unificado de los 4 algoritmos en 3 ejes.
- **Capítulo 3 — Metodología.** Estudio cuantitativo, aplicado, comparativo, no experimental. Detalla el dataset real de Iquitos (pipeline de 10 etapas, fuentes PVGIS/NASA POWER, destilación de facturación) y el procedimiento de 12 corridas con sus gates de validación y las 4 pruebas estadísticas.
- **Capítulo 4 — Desarrollo de la propuesta.** Arquitectura por capas; formulación Dec-POMDP (17 agentes, γ=0.9999, T=8 760; observaciones y acciones heterogéneas por edificio, 57-330 obs y 5-44 acciones según cargadores EV); recompensa multiobjetivo con pesos por escenario (E1 0.70/0.15/0.15; E2 0.15/0.70/0.15; E3 0.25/0.15/0.60) y perfil unificado (r=0.70, peak 0.45, ramp 0.35, ev 0.25); hiperparámetros reales (v4 local vs canónico de 50 ep en Colab H100/A100, protocolo `two_phase_happo_masac_v3`, tomados de la celda 6.1 del notebook); 4 aportes al motor (A1-A4).
- **Capítulo 5 — Resultados.** Corrida canónica Colab/Drive `madrl_v3_20260627_164047` (GPU RTX PRO 6000 Blackwell). **MATD3** es el mejor MADRL global entre algoritmos evaluables (score 0.6667; 40/50 ep con KPIs). MAAC lidera costos (OE.3); MASAC con 12 ep parcial. HAPPO sin KPIs finales (error evaluación). Corrida local v4 (5 ep) conservada como referencia (KW p=0.0459).
- **Capítulo 6 — Conclusiones.** Responde OG/OE con evidencia Colab; limitaciones (cobertura parcial, semilla única, HAPPO); trabajo pendiente (50 ep completos, re-eval HAPPO, estadística Colab, multi-semilla, Pareto); plan H1-H7.
- **Referencias APA.** Lista consolidada; pendiente completar entradas `[PV]`.

---

## Estado global

| Capítulo | ¿Completo? | Principales placeholders |
|---|---|---|
| 1 | Sí | H0/H1 según UNI; unidad de posgrado |
| 2 | Sí | datos `[PV]`; benchmarks 2025-2026 |
| 3 | Sí | nº semillas; episodios objetivo |
| 4 | Sí | composición de 1856 dims de estado |
| 5 | **Integrado** | 50 ep completos; HAPPO re-eval; estadística Colab; % mejora vs baseline; figuras Drive |
| 6 | Sí | confirmación con 50 ep + HAPPO |
| Ref. | Sí | ~10 entradas `[PV]` |

**Recomendación de uso:** abrir cada archivo en Perplexity, ejecutar el bloque "PROMPT PARA PERPLEXITY" para pulir a versión final, y completar los placeholders restantes del Capítulo 5 (50 ep completos, HAPPO, estadística Colab, figuras).

> **Resultados del Capítulo 5 (Colab/Drive).** Las cifras principales provienen de la corrida canónica `madrl_v3_20260627_164047` en Google Colab (protocolo `two_phase_happo_masac_v3`, GPU RTX PRO 6000 Blackwell). KPIs descargados a `outputs/_drive_madrl/kpis/` y agregados en `outputs/madrl_v3_20260627_164047/resumen_comparativo/best_madrl_report.json`. Cobertura parcial: MATD3 40/50 ep, MAAC 11/50, MASAC 12/50, HAPPO sin KPIs finales. La corrida local v4 (5 ep) se mantiene como referencia de validación y estadística preliminar (KW p=0.0459).

