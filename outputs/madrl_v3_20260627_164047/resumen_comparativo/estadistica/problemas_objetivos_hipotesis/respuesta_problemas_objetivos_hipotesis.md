# Respuesta estadística a problemas, objetivos e hipótesis — madrl_v3_20260627_164047

Unidad primaria: ganancia relativa orientada de KPI frente al baseline (un valor positivo favorece al MADRL). Cada objetivo se restringe al escenario formulado: OE1/E1, OE2/E2 y OE3/E3.

Alcance: análisis exploratorio de una sola semilla. HAPPO conserva episodios descriptivos, pero no KPI-gains finales comparables; por ello los contrastes de KPI incluyen MAAC, MASAC y MATD3.

## OE1 / E1 — Flexibilidad energética

**Problema.** PE.1: ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E1?

**Objetivo.** OE.1: Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E1.

| Algoritmo | n KPI | Media | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| MAAC | 12 | -0.0888 | -0.0012 | 5 | 7 |
| MATD3 | 12 | -0.0868 | -0.0029 | 5 | 7 |
| MASAC | 12 | -0.2621 | -0.0136 | 2 | 10 |

**Diferencias entre algoritmos.** Kruskal-Wallis H=1.5164, p=0.4685, ε²=0.0000: no se rechaza igualdad global. Friedman pareado por KPI: χ²=5.5897, p=0.0611, Kendall W=0.2329.

**Impacto frente al baseline.** MAAC: mediana=-0.0012, p-Holm=0.6025; MATD3: mediana=-0.0029, p-Holm=0.6025; MASAC: mediana=-0.0136, p-Holm=0.0483.

**Decisión HE10/HE11.** no se rechaza HE10; no se reúne evidencia conjunta para HE11.

**Respuesta y cumplimiento.** El líder descriptivo por mediana de ganancia es MAAC; cumplido descriptivamente y contrastado de forma exploratoria; pendiente confirmación multisemilla.

## OE2 / E2 — Emisiones de CO₂

**Problema.** PE.2: ¿En qué medida el algoritmo MADRL impacta en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E2?

**Objetivo.** OE.2: Determinar el impacto de los algoritmos MADRLs en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E2.

| Algoritmo | n KPI | Media | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| MATD3 | 5 | -0.4101 | -0.0421 | 0 | 5 |
| MAAC | 5 | -0.4148 | -0.0470 | 0 | 5 |
| MASAC | 5 | -0.4171 | -0.0516 | 0 | 5 |

**Diferencias entre algoritmos.** Kruskal-Wallis H=0.5364, p=0.7648, ε²=0.0000: no se rechaza igualdad global. Friedman pareado por KPI: χ²=6.0000, p=0.0498, Kendall W=0.6000.

**Impacto frente al baseline.** MATD3: mediana=-0.0421, p-Holm=0.1875; MAAC: mediana=-0.0470, p-Holm=0.1875; MASAC: mediana=-0.0516, p-Holm=0.1875.

**Decisión HE20/HE21.** no se rechaza HE20; no se reúne evidencia conjunta para HE21.

**Respuesta y cumplimiento.** El líder descriptivo por mediana de ganancia es MATD3; cumplido descriptivamente y contrastado de forma exploratoria; pendiente confirmación multisemilla.

## OE3 / E3 — Costos energéticos

**Problema.** PE.3: ¿En qué medida el algoritmo MADRL impacta en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E3?

**Objetivo.** OE.3: Determinar el impacto de los algoritmos MADRLs en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E3.

| Algoritmo | n KPI | Media | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| MAAC | 9 | -0.2278 | -0.0027 | 1 | 8 |
| MATD3 | 9 | -0.2259 | -0.0092 | 1 | 8 |
| MASAC | 9 | -0.2355 | -0.0140 | 1 | 8 |

**Diferencias entre algoritmos.** Kruskal-Wallis H=0.6138, p=0.7357, ε²=0.0000: no se rechaza igualdad global. Friedman pareado por KPI: χ²=3.4286, p=0.1801, Kendall W=0.1905.

**Impacto frente al baseline.** MAAC: mediana=-0.0027, p-Holm=0.0781; MATD3: mediana=-0.0092, p-Holm=0.0586; MASAC: mediana=-0.0140, p-Holm=0.0781.

**Decisión HE30/HE31.** no se rechaza HE30; no se reúne evidencia conjunta para HE31.

**Respuesta y cumplimiento.** El líder descriptivo por mediana de ganancia es MAAC; cumplido descriptivamente y contrastado de forma exploratoria; pendiente confirmación multisemilla.

## Problema general, objetivo general e hipótesis general

**Problema.** PG: ¿En qué medida los algoritmos MADRLs impactan en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál presenta el mejor desempeño a nivel global?

**Objetivo.** OG: Determinar el impacto de los algoritmos MADRLs en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, e identificar el mejor desempeño global.

| Algoritmo | Score medio E1-E3 | Desv. |
|---|---:|---:|
| MAAC | 0.8066 | 0.1474 |
| MATD3 | 0.6323 | 0.3752 |
| MASAC | 0.1694 | 0.2028 |

Kruskal-Wallis global: H=1.8108, p=0.4044. Friedman pareado: χ²=9.2911, p=0.0096, Kendall W=0.1787.

**Decisión H0G/H1G.** se rechaza H0G y se respalda H1G de forma exploratoria para MAAC, MASAC y MATD3.

**Respuesta y cumplimiento del OG.** El score de escenarios con igual peso ubica primero a MAAC; la mediana robusta de KPI-gains ubica primero a MATD3. La inversión de ranking y la ausencia de significancia impiden declarar un ganador global único.
