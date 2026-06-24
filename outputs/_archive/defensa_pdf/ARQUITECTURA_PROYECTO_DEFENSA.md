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

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-1.png)

---

## Diagrama 2 — Pipeline del Dataset Iquitos 2023-2025

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-2.png)

---

## Diagrama 3 — Arquitectura Dec-POMDP y CTDE de los 17 Agentes

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-3.png)

---

## Diagrama 4 — Los 4 Algoritmos MADRL: Taxonomia y Diferencias

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-4.png)

---

## Diagrama 5 — Flujo de Entrenamiento: 12 Corridas (4 Algoritmos x 3 Escenarios)

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-5.png)

---

## Diagrama 6 — Recompensa Multiobjetivo por Escenario

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-6.png)

---

## Diagrama 7 — Pipeline de Evaluacion y Seleccion del Mejor MADRL

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-7.png)

---

## Diagrama 8 — Infraestructura de Despliegue: Local y AWS EC2

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-8.png)

---

## Diagrama 9 — Estructura de Capas del Software

![diagram](./png\ARQUITECTURA_PROYECTO_DEFENSA-9.png)

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
