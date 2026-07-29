# Capítulo 6. Conclusiones

> **Documento de tesis — alineado a la corrida canónica Colab/Drive (`madrl_v3_20260627_164047`) y a la capa KPI-gains de Cap. 5.**  
> Fuente Word canónica: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` (espejo Informe: `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx`).  
> No inventar hallazgos no soportados por artefactos. **No** tratar ranking episódico, TOPSIS ni evaluate_v2 4/4 como decisión de HE.

---

## 6.1 Principales hallazgos

1. **Respuesta al OG:** entre los MADRL del canónico 3×3 (MATD3, MAAC, MASAC), **MATD3** obtiene el mejor desempeño coordinado **descriptivo** (score global **0,6667**; `best_madrl_report.json`). No hay dominador Pareto: MATD3 lidera flexibilidad física de distrito y CO₂; **MAAC** lidera costos. El ranking evaluate_v2 4/4 sitúa a MAAC primero (0,9538; HAPPO 0,0000) y es **descriptivo**, no veredicto de hipótesis.

2. **Respuesta a PE.1 / OE.1 (flexibilidad, E1):** descriptivamente, **MATD3** obtiene el mejor `flex_composite` de distrito (**1,0009**); por mediana de KPI-gain el líder es **MAAC**. Inferencialmente (KPI-gains Cap. 5), Kruskal–Wallis **p = 0,4685** → **HE10 no se rechaza**; **HE11 no se respalda**.

3. **Respuesta a PE.2 / OE.2 (CO₂, E2):** descriptivamente, **MATD3** obtiene el menor ΔCO₂ de distrito (**23 070 kg**). Inferencialmente, KW **p = 0,7648** → **HE20 no se rechaza**; **HE21 no se respalda**.

4. **Respuesta a PE.3 / OE.3 (costos, E3):** descriptivamente, **MAAC** obtiene el menor Δcosto de distrito (**9 515 EUR**). Inferencialmente, KW **p = 0,7357** → **HE30 no se rechaza**; **HE31 no se respalda**. Ranking TOPSIS/4/4 **no** sustituye HE31.

5. **Hipótesis general (H0G / H1G):** H0G se **rechaza de forma exploratoria** (Friedman integración **p = 0,0096** + impacto GLOBAL vs baseline Holm); KW ALL **p = 0,1554** (n.s.). H1G se respalda **exploratoriamente** (sin ganador único; **no** implica HE11∧HE21∧HE31).

6. **Cobertura HAPPO:** KPI-gains evaluate_v2 4/4 disponibles (peores que el trío); cobertura episódica **49/50** por escenario. Las HE de entrenamiento usan el trío MASAC/MATD3/MAAC. `best_madrl` 3×3 permanece MATD3 0,6667.

7. **Contribución metodológica:** benchmark reproducible Dec-POMDP/CTDE sobre 17 edificios del SEAI Iquitos (\(d_s=1\,856\); \(d_{o_i}\in[54,327]\); \(d_{a_i}\in[5,44]\); \(r_{\mathrm{team}}=0{,}70\)) con cuatro algoritmos MADRL bajo CityLearn v3 (extensión experimental de tesis; Caps. 2 y 4).

### 6.1.1 Veredicto de hipótesis (aceptación / rechazo)

Unidad de decisión = **KPI-gains** de los 50 episodios Drive (Cap. 4–5). α = 0,05. Semilla de campaña = 0 (decisiones **exploratorias**).

| Hipótesis | Decisión | Fundamento |
|-----------|----------|------------|
| **H0G** | **Se rechaza de forma exploratoria** | Friedman integración p = 0,0096 + impacto GLOBAL vs baseline (Holm) |
| **H1G** | **Se respalda de forma exploratoria** (sin ganador único) | Diferenciación débil; trade-off MATD3/MAAC; **no** implica HE11∧HE21∧HE31 |
| **HE10** | **No se rechaza** | KW p = 0,4685 |
| **HE11** | **No se respalda** | Sin conjunción impacto + diferencias en E1 |
| **HE20** | **No se rechaza** | KW p = 0,7648 |
| **HE21** | **No se respalda** | Sin impacto vs cero tras Holm; 0/15 KPI mejorados |
| **HE30** | **No se rechaza** | KW p = 0,7357 |
| **HE31** | **No se respalda** | MAAC gana costos/TOPSIS/4/4 solo descriptivo |

*Nota.* La nula no se «acepta»; se informa si se rechaza o no. Accuracy/precision/recall/F1 no intervienen (métricas no primarias del control continuo MADRL).

### 6.1.2 Cumplimiento de objetivos

| Objetivo | Líder descriptivo | Inferencia / H | Cumplimiento |
|----------|-------------------|----------------|--------------|
| **OE.1** | MATD3 (flex distrito); MAAC (mediana gain) | HE10 no rechazada; HE11 no respaldada | Cumplido descriptivo-exploratorio |
| **OE.2** | **MATD3** | HE20 no rechazada; HE21 no respaldada | Cumplido descriptivo |
| **OE.3** | **MAAC** | HE30 no rechazada; HE31 no respaldada | Cumplido descriptivo |
| **OG** | MATD3 (`best_madrl` 0,6667) / MAAC (score 4/4) | H0G rechazo exploratorio; H1G exploratoria | Cumplido; sin ganador único |

---

## 6.2 Limitaciones encontradas

- **Semilla única entrenada (seed = 0):** el diseño `n_seeds=12` y el runner están implementados; smoke n=3 ejecutado; no se entrenaron 12 semillas reales (H2).
- **HAPPO 49/50:** sin imputación; KPI-gains evaluate_v2 4/4 disponibles (peores); HE de entrenamiento sobre MASAC/MATD3/MAAC.
- **Capas de evidencia distintas:** KPI-gains (HE), `best_madrl` 3×3, evaluate_v2 4/4 y TOPSIS son planos **complementarios**; no se fusionan para inventar respaldo de HE11–HE31.
- **Sin ganador Pareto universal:** trade-off MATD3 (flex+CO₂) vs MAAC (costos).
- **Simulación, no despliegue físico** en red real; MADRL por debajo del baseline RBC en score HPHI global (matiza generalización, no el benchmark inter-algoritmo).

---

## 6.3 Trabajo pendiente

Pendientes de evidencia empírica: (1) homogenizar HAPPO a 50 episodios i.i.d. por escenario; (2) campaña multi-semilla real (≥3, ideal 12) con post-hoc entre semillas; (3) frontera de Pareto por eje y % vs baseline RBC/CityLearn v2 por KPI.

Pendientes de análisis opcional (no bloquean lectura descriptiva 50 ep): Optuna (TPE) por backend; contraste SB3 (PPO/SAC/A2C) bajo el mismo schema de Iquitos.

Pendientes editoriales e institucionales: pasada ortográfica RAE; actualizar índices Word (F9); metadatos de asesor solo con dato real; PDF final y paquete de reproducibilidad. **No** sincronizar ni citar documentos Word eliminados.

---

## 6.4 Plan para culminar la tesis

**Tabla 6.1. Plan para culminar la tesis (hitos H1–H7).**

| Hito | Entregable verificable | Estado |
|------|------------------------|--------|
| **H1. HAPPO KPI-gains / 50 ep** | KPI-gains evaluate_v2 4/4; 50 ep i.i.d. | KPI-gains 4/4; 49/50 ep |
| **H2. Robustez multi-semilla** | Protocolo n_seeds=12 + smoke + campaña seed=0 | Diseño+runner+smoke; 12-seed no entrenada |
| **H3. Inferencia Colab cerrada** | Tablas KW/Friedman/Wilcoxon + Cap. 5–6 sincronizados | Ejecutada (H0G exploratoria; HE11/21/31 no respaldadas) |
| **H4. Pareto y % vs baseline** | Tablas/figuras OE.1–OE.3 vs RBC/CityLearn v2 | Parcial |
| **H5. HPO Optuna** | Estudio TPE por algoritmo | Pendiente (fuera del alcance cerrado) |
| **H6. Redacción final APA** | Cap. 1–6 + referencias APA | En curso |
| **H7. Sustentación** | Documento oficial + defensa | Pendiente institucional |

Con **H1 (parcial), H3 y H6 en curso/ejecutados**, y **H2/H5 delimitados** como trabajo futuro, el manuscrito queda **presentable académicamente** bajo las restricciones declaradas. Solo **H7** permanece para el cierre formal institucional.

---

## 6.5 Criterios de cierre y control de calidad final

| Actividad | Propósito | Criterio de cierre |
|-----------|-----------|-------------------|
| **Revisión APA integral** | Citas ↔ referencias | Toda cita en texto tiene entrada; viceversa |
| **Campaña multi-semilla** | Validez externa | Seeds 0..11 con `--run-root` (trabajo futuro) |
| **Auditoría figuras/tablas** | Trazabilidad Drive | Cada figura/tabla → artefacto de `madrl_v3_20260627_164047` |
| **Coherencia vertical** | PE–OE–H–resultados–conclusiones | Misma capa KPI-gains para HE; descriptivo separado |

*Nota.* Los criterios documentales no sustituyen la evidencia experimental ya auditada.

---

### Estado del capítulo

**Actualizado (2026-07-29)** al veredicto Cap. 5 (KPI-gains): HE11/HE21/HE31 **no respaldadas**; OE descriptivos **sí**; H0G/H1G **exploratorios** (Friedman p = 0,0096; KW ALL p = 0,1554). Sin p-valores legacy 0,281/0,546/0,388 como veredicto de HE.
