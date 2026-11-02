# Capítulo 6. Conclusiones

> **Documento de tesis — conclusiones.** Alineado a la corrida canónica Colab/Drive (`madrl_v3_20260627_164047`) y a la Capa A de Cap. 5 (`problemas_objetivos_hipotesis/`). α = 0,05. Semilla de campaña = 0. HAPPO excluido de la contrastación HE. **No** se inventan hallazgos; **no** se cita Kruskal–Wallis ALL como veredicto de H0G/H1G; TOPSIS y evaluate_v2 4/4 son descriptivos y no sustituyen hipótesis.

---

## 6.1 Conclusión general

Respecto del objetivo general (OG) —determinar el impacto de los algoritmos MADRL en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de Iquitos, e identificar el algoritmo de mejor desempeño global—, la evidencia de Cap. 5 permite concluir lo siguiente.

**Efecto global.** A nivel integrado (KPI-gains GLOBAL, n = 26), se observan efectos diferenciales entre algoritmos y frente al baseline CityLearn v2: el contraste omnibus pareado detecta diferenciación agregada, y el impacto frente a cero tras corrección Holm resulta significativo para los tres algoritmos del canónico 3×3, en dirección **desfavorable** (no mejora agregada vs baseline).

**Valor y magnitud de la diferenciación.** La prueba de Friedman sobre la integración GLOBAL arroja χ² = 9,2911, p = 0,0096, con Kendall W = 0,1787 (concordancia débil). El post hoc Wilcoxon–Holm identifica un único par significativo: MAAC–MASAC (p-Holm = 0,0172). El impacto GLOBAL vs baseline (Holm) es desfavorable y significativo para MAAC, MASAC y MATD3.

**Mejor algoritmo global.** No existe ganador único inferencial. En el plano descriptivo coexisten dos liderazgos: MATD3 encabeza `best_madrl` 3×3 (score 0,6667), mientras que MAAC encabeza el ranking evaluate_v2 4/4 y TOPSIS (C\* = 0,9827). El frente de Pareto retiene a MATD3, MAAC y MASAC; el trade-off MATD3 (flexibilidad física / CO₂) frente a MAAC (costos) impide declarar un dominador universal.

**Limitación metodológica.** La unidad experimental es semilla única (`seed = 0`); los episodios de una sola corrida no constituyen réplicas experimentales independientes ni habilitan robustez multisemilla.

**Decisión HG.** Se **rechaza H0G**. Se **respalda H1G** (efectos diferenciales agregados sin ganador único). El respaldo de H1G **no** implica la conjunción HE11 ∧ HE21 ∧ HE31.

**Alcance.** Inferencia HE/H0G restringida a MASAC, MATD3 y MAAC. HAPPO dispone de una curva descriptiva reconstruida con 49 episodios históricos y uno post-resume, pero no de KPI-gains finales comparables; por ello queda fuera de la contrastación HE y solo aporta lectura descriptiva 4/4.

---

## 6.2 Conclusión OE.1 (flexibilidad energética)

Respecto de OE.1 —determinar el impacto de los MADRL en la flexibilidad energética e identificar el mejor desempeño en E1—, Cap. 5 establece lo siguiente.

**Efecto.** Los efectos diferenciales sobre flexibilidad se caracterizan descriptivamente (liderazgo mixto) y se contrastan inferencialmente sin alcanzar el umbral de la hipótesis alternativa conjunta.

**Magnitud.** Las medianas de KPI-gain en E1 son ≤ 0 (deterioro relativo al baseline en la métrica de gain orientada). Por mediana, MAAC (−0,00119) supera a MATD3 (−0,00289) y a MASAC (−0,01363). En el KPI físico de distrito, MATD3 obtiene el mejor `flex_composite` (1,0009).

**Significancia entre algoritmos.** Friedman (principal): p = 0,0611 (χ² = 5,5897; Kendall W = 0,2329). No se rechaza la igualdad pareada al α = 0,05. El post hoc Wilcoxon–Holm entre pares es no significativo. Kruskal–Wallis se menciona solo como sensibilidad exploratoria (p = 0,4685) y **no** fundamenta la decisión de HE.

**Baseline.** Tras Holm, solo MASAC muestra impacto significativo vs cero, en dirección desfavorable (p-Holm = 0,0483). MAAC y MATD3 no alcanzan impacto detectado vs baseline en OE.1.

**Mejor MADRL (descriptivo).** MAAC por mediana de KPI-gain; MATD3 por flexibilidad física de distrito (`flex_composite` / score OE1).

**Decisión HE.** **HE10 no se rechaza.** **HE11 no se respalda.**

---

## 6.3 Conclusión OE.2 (emisiones de CO₂)

Respecto de OE.2 —impacto MADRL sobre emisiones de CO₂ y mejor desempeño en E2—, Cap. 5 concluye lo siguiente.

**Efecto.** Se identifica un liderazgo descriptivo claro de MATD3; el efecto inferencial conjunto no alcanza a respaldar la alternativa.

**Magnitud.** Medianas de KPI-gain negativas y 0/5 KPI mejorados en los tres algoritmos. En delta físico de distrito, MATD3 minimiza ΔCO₂ (23 070 kg) frente a MAAC (70 654 kg) y MASAC (77 649 kg).

**Significancia.** Friedman p = 0,0498 (χ² = 6,0000; Kendall W = 0,6000) indica señal pareada global débil-moderada; el post hoc Wilcoxon–Holm entre pares es no significativo (p-Holm = 0,307). Sin impacto vs cero tras Holm (p-Holm = 0,1875 para los tres). Kruskal–Wallis exploratorio p = 0,7648; **no** fundamenta HE.

**Mejor MADRL (descriptivo).** **MATD3** (mediana gain, ΔCO₂ de distrito y score OE2).

**Decisión HE.** Pese a la señal omnibus de Friedman, la ausencia de post hoc significativo y de impacto vs baseline tras Holm implica: **HE20 no se rechaza**; **HE21 no se respalda**.

---

## 6.4 Conclusión OE.3 (costos energéticos)

Respecto de OE.3 —impacto MADRL sobre costos energéticos y mejor desempeño en E3—, Cap. 5 establece lo siguiente.

**Efecto.** Existe liderazgo descriptivo de MAAC en costos; no se establece superioridad ni impacto estadísticamente concluyentes.

**Magnitud.** MAAC obtiene la mejor mediana de KPI-gain (−0,00268) y el menor Δcosto de distrito (9 515 USD), frente a MASAC (19 793 USD) y MATD3 (44 399 USD). TOPSIS y score OE3 4/4 también sitúan a MAAC primero (C\* = 0,9827; score 1,0000), en plano descriptivo.

**Significancia.** Friedman p = 0,1801 (χ² = 3,4286; W = 0,1905) — no significativo. Post hoc n.s. Impacto vs cero tras Holm no significativo (dirección desfavorable). Kruskal–Wallis exploratorio p = 0,7357; **no** fundamenta HE.

**Distinción crítica.** El **menor costo observado** (descriptivo: MAAC) no equivale a un **ahorro estadísticamente demostrado** frente al baseline ni a una superioridad inter-algoritmo inferencial.

**Mejor MADRL (descriptivo).** **MAAC**.

**Decisión HE.** **HE30 no se rechaza.** **HE31 no se respalda.**

---

## 6.5 Contribuciones científicas

**Metodológica.** Se cierra un protocolo de contrastación vertical PG–OG–HG / PE–OE–HE sobre KPI-gains (Capa A), con puerta Shapiro–Wilk → Friedman pareado + Kendall W + Wilcoxon/Holm como batería principal, y Kruskal–Wallis / Mann–Whitney solo como sensibilidad exploratoria, sin mezclar capas B/C/D con la decisión de hipótesis.

**Algorítmica.** Se compara de forma homogénea el trío canónico MASAC, MATD3 y MAAC (e, en plano descriptivo, HAPPO) bajo el mismo esquema Dec-POMDP/CTDE y la misma función de recompensa multiobjetivo por escenario E1–E3.

**Energética.** Se operacionalizan tres ejes de gestión —flexibilidad, emisiones de CO₂ y costos— con KPIs físicos de distrito y KPI-gains orientados, frente a baseline CityLearn v2 / RBC.

**Multiobjetivo.** Se documenta el trade-off Pareto entre algoritmos (MATD3 en flexibilidad física/CO₂; MAAC en costos; MASAC en el frente sin liderar un eje) y se evita declarar un dominador único a partir de rankings complementarios (TOPSIS, 4/4, `best_madrl`).

**Computacional.** Se ejecuta y audita una campaña canónica de 50 episodios por escenario (`madrl_v3_20260627_164047`) con artefactos trazables en Drive/local para reproducir tablas y figuras de Cap. 5.

**Aplicada a Iquitos.** Se instancia el problema en una comunidad de 17 edificios del SEAI–Iquitos (Electro Oriente S.A.), con señales exógenas de clima, precio y carbono propias del caso de estudio.

**Reproducibilidad.** Se delimitan unidad experimental (algoritmo × escenario, seed = 0), cobertura episódica, exclusión de HAPPO de HE, n de KPI por eje (12/5/9) y la separación explícita entre evidencia descriptiva e inferencial, de modo que las decisiones HG/HE sean auditables contra Cap. 5.

---

## 6.6 Limitaciones

Las limitaciones verificadas, coherentes con Cap. 5, son únicamente las siguientes:

1. **Semilla única entrenada (`seed = 0`).** No se afirma robustez multisemilla; la generalización de las decisiones HG/HE queda limitada por esa unidad experimental.
2. **HAPPO sin KPI-gains finales comparables.** Su curva descriptiva reúne 49 episodios históricos y uno post-resume, pero esa cobertura no lo habilita como réplica inferencial homogénea. Queda excluido de HE; solo aporta lectura descriptiva 4/4.
3. **Tamaño muestral de KPI por eje.** n = 12 (OE.1), n = 5 (OE.2) y n = 9 (OE.3) en la Capa A.
4. **Simulación, no despliegue.** Los resultados corresponden a CityLearn / capa MADRL v3, no a operación en red real.
5. **Trade-off Pareto.** No hay dominador universal entre flexibilidad/CO₂ y costos.
6. **Capas B/C/D no deben mezclarse con la Capa A** para inventar respaldo de HE11–HE31 ni de H1G.
7. **No se entrenaron 12 semillas reales.** El diseño `n_seeds=12` y el runner existen; la campaña completa queda fuera del alcance cerrado de evidencia.

---
