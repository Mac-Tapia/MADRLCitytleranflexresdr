# Capítulo 6. Conclusiones

> **Documento de tesis — alineado a la corrida canónica Colab/Drive (`madrl_v3_20260627_164047`).**  
> Validación 2026-07-15: `docs/VALIDACION_SECCIONES_6_3_6_4_6_5_2026-07-15.md`. No inventar hallazgos no soportados por artefactos.

---

## 6.1 Principales hallazgos

1. **Respuesta al OG:** entre los MADRL evaluables con KPIs auditados (MATD3, MAAC, MASAC), **MATD3** obtiene el mejor desempeño coordinado descriptivo (score global **0,6667**; fuente `best_madrl_report.json`). No existe dominancia universal en los tres ejes: MATD3 lidera flexibilidad y CO₂; MAAC lidera costos.

2. **Respuesta al OE.1 (flexibilidad):** **MATD3** registra la mejor flexibilidad compuesta en E1 (**1,0009**). En la muestra episódica completa (597 filas), **MAAC** obtiene la mejor media de `reward_mean_average`; Kruskal–Wallis sobre MAAC/MASAC/MATD3 es significativo (**p = 1,305×10⁻⁸**).

3. **Respuesta al OE.2 (CO₂):** **MATD3** logra el menor delta de emisiones en E2 (**23 070 kg** vs MAAC 70 654 kg y MASAC 77 649 kg). Kruskal–Wallis episódico: **p = 0,043866** (efecto pequeño, ε² ≈ 0,029).

4. **Respuesta al OE.3 (costos):** **MAAC** obtiene el menor delta de costo en E3 (**9 515 EUR**). Kruskal–Wallis episódico: **p = 0,251421** (no significativo a α = 0,05).

5. **Cobertura HAPPO:** corpus definitivo **49 episodios por escenario** (147 filas); no se imputó el episodio ausente. MAAC, MASAC y MATD3: **50 episodios por escenario** (450 filas). Total muestra episódica: **597 filas** (`gdrive_episode_kpis_used_for_statistics.csv`).

6. **Contribución metodológica:** benchmark reproducible Dec-POMDP/CTDE sobre 17 edificios del SEAI Iquitos con cuatro algoritmos MADRL bajo CityLearn v3.

### 6.1.1 Veredicto de hipótesis (aceptación / rechazo)

Diseño adoptado: **cuasiexperimental factorial 4×3**; formulación PG/OG tipo ranking–Pareto; contraste H₀/H₁ por eje con **dos capas** (A = episódica OE-alineada; B = KPI-gains). α = 0,05.

| Hipótesis | Decisión | Fundamento |
|-----------|----------|------------|
| **HG (ranking / Pareto)** | **Aceptada** como ranking multiobjetivo sin dominador universal (MATD3 score 0,6667; MAAC lidera costos). Superioridad omnibus en KPI-gains: **H₀ no rechazada** (p = 0,155). | Cap. 1 §1.3; `best_madrl_report.json`; capa B |
| **HE.1 (flexibilidad)** | **H₀ rechazada en capa A** (p = 1,305×10⁻⁸); **H₀ no rechazada en capa B** (p = 0,281). Cumplimiento de OE.1: **sí** (comparativo). | `gdrive_objective_aligned_statistics.csv`; `hipotesis_estadisticas_madrl.csv` |
| **HE.2 (CO₂)** | **H₀ rechazada en capa A** (p = 0,0439, ε² ≈ 0,029); **H₀ no rechazada en capa B** (p = 0,546). Cumplimiento de OE.2: **sí** (descriptivo + inferencia episódica débil). | Idem |
| **HE.3 (costos)** | **H₀ no rechazada** en capas A (p = 0,251) ni B (p = 0,388). Liderazgo MAAC: **descriptivo**. Cumplimiento de OE.3: **sí** a nivel identificación comparativa; **no** a nivel superioridad omnibus. | Idem |

*Nota.* No se fusionan capas A y B. Accuracy/precision/recall/F1 no intervienen en este veredicto (métricas no primarias del control continuo MADRL).

---

## 6.2 Limitaciones encontradas

- **Semilla única (seed = 0):** la inferencia no cuantifica robustez multi-semilla; queda como trabajo futuro (H2).
- **HAPPO 49/50:** sin imputación del episodio faltante; HAPPO excluido de Kruskal–Wallis sobre KPI-gains por cobertura incompleta.
- **Dos niveles inferenciales:** contrastes episódicos (597 filas) vs KPI-gains de entrenamiento (231 filas, sin HAPPO) pueden divergir; la discusión los diferencia explícitamente.
- **Sin ganador Pareto universal:** trade-off MATD3 (flex+CO₂) vs MAAC (costos).
- **Simulación, no despliegue físico** en red real.

---

## 6.3 Trabajo pendiente

El trabajo pendiente se declara con honestidad metodologica respecto de la corrida canonica madrl_v3_20260627_164047 (factorial 4×3: HAPPO, MAAC, MASAC y MATD3 × E1–E3). No se imputan episodios ni KPIs inexistentes; lo que sigue son huecos reales del pipeline y del manuscrito que deben cerrarse antes de la version de sustentacion.

Pendientes de evidencia empirica (bloqueantes Cap. 5 / Anexo A): (1) homogeneizar HAPPO a evaluate_v2/core_kpis y artefactos building_* comparables con MAAC/MASAC/MATD3 (hoy HAPPO aporta trazas y series distritales —49 episodios reales por escenario— pero queda incompleto en KPIs de edificio cuando faltan CSV locales); (2) cerrar checkpoint_manifest.json de HAPPO en la corrida canonica (conteo = 0 en Figura 5.1 / Anexo A.4 frente a MAAC 52, MASAC 12 y MATD3 34 archivos listados); (3) mantener la Figura 5.8e con fuentes mixtas auditadas (action_l2 desde full_data/trace.csv; EV/BESS desde building_behavior_summary), sin reutilizar columnas muertas ev_charge_kwh / electrical_storage_soc (=0 en trace.csv); (4) auditar celdas cero en Anexo A.4 y demas tablas/figuras para distinguir cero legitimo vs fallo de lectura.

Pendientes de analisis y robustez (no bloquean la lectura descriptiva 50 ep, pero si afirmaciones de generalizacion): corrida multi-semilla (≥3, ideal ≥5) con post-hoc alineado a la Tabla 3.4; frontera de Pareto por eje OE.1–OE.3 frente a baseline CityLearn/RBC; Optuna (TPE) por backend solo si se declara optimizacion hiperrametricas; contraste SB3 (PPO/SAC/A2C) bajo el mismo schema de Iquitos como extension opcional.

Pendientes editoriales e institucionales: pasada ortografica RAE (tildes, tipografia, concordancia) en Cap. 1–6; verificar citas marcadas [PV] y actualizar indices Word (F9); completar metadatos de asesor / [por definir] unicamente con dato real del programa (no inventar nombres); sincronizar ABRIR_ESTE y FINAL_COMPLETA sin regenerar masivamente el cuerpo; PDF final y paquete de reproducibilidad (scripts + CSV + manifiestos).

**Estado de cierre documental (2026-07-15).** (3) Figura 5.8e cerrada con fuentes mixtas auditadas; (4) ceros de Anexo A.4 auditados (HAPPO = 0 legítimo por manifiesto ausente, sin inventar checkpoints). (1)–(2) quedan declarados sin inventar CSV/KPIs/manifiestos inexistentes: HAPPO no aporta `building_behavior_summary`/`core_kpis` ni `.pt` reales en `madrl_v3_20260627_164047`. Multi-semilla, Optuna y SB3 → trabajo futuro (H2/H5). Editoriales F9/PDF/asesor → H7 institucional.

---

## 6.4 Plan para culminar la tesis

El plan de culminación fue ejecutado diferenciando los hitos indispensables para cerrar el manuscrito de las ampliaciones experimentales que corresponden a trabajo futuro. La implementación se realizó sobre la corrida canónica `madrl_v3_20260627_164047`, sin inventar episodios, semillas, resultados ni artefactos no disponibles. El estado consolidado al **15 de julio de 2026** se presenta en la Tabla 6.1.

**Tabla 6.1. Ejecución e implementación del plan para culminar la tesis.**

| Hito | Implementación realizada | Estado y evidencia de cierre |
|------|--------------------------|------------------------------|
| **H1. Cobertura HAPPO** | Se adoptó como corpus definitivo la cobertura materializada de 49 episodios por escenario para HAPPO. No se imputó el episodio ausente y se sincronizó esta condición en metodología, resultados, discusión, conclusiones y limitaciones. MAAC, MASAC y MATD3 conservan 50 episodios por escenario (597 filas episódicas en total). | **Ejecutado.** Evidencia: `gdrive_episode_kpis_used_for_statistics.csv` (597 filas; HAPPO n=49; MAAC/MASAC/MATD3 n=50). |
| **H2. Robustez multi-semilla** | La inferencia se delimitó a una sola semilla de la corrida canónica. No se afirma generalización universal; la validación multi-semilla queda como trabajo futuro. | **Implementado como delimitación metodológica.** No ejecutado experimentalmente; no bloquea el cierre del manuscrito. |
| **H3. Inferencia estadística** | Se consolidaron Shapiro–Wilk, Kruskal–Wallis, Mann–Whitney con Holm y tamaños de efecto; Capítulos 5 y 6 sincronizados. | **Ejecutado.** OE.1: p = 1,305×10⁻⁸; OE.2: p = 0,043866; OE.3: p = 0,251421 (`gdrive_objective_aligned_statistics.csv`). |
| **H4. Pareto y baseline** | Se consolidó la lectura multiobjetivo sin ganador universal, con contraste CityLearn v2/RBC/baseline. La discusión diferencia medias episódicas, muestra inferencial completa y KPI anual final. | **Ejecutado en Cap. 5.** Sensibilidad de pesos como trabajo futuro. |
| **H5. HPO y algoritmos adicionales** | Optuna y contrastes PPO/SAC/A2C no forman parte de la evidencia canónica; se evita sesgo retrospectivo. | **Delimitado → trabajo futuro.** No requerido para los objetivos actuales. |
| **H6. Cierre documental** | Se reforzaron Cap. 2, 4, 5 y 6; discusión 5.10; referencias depuradas; tablas APA 7; campos e índices Word al abrir. | **Ejecutado.** |
| **H7. Entrega y sustentación** | Secuencia final: índices F9, revisión visual PDF, validación del asesor, registro institucional y preparación de defensa. | **Pendiente de gestión institucional.** |

*Nota.* Estado al 15 de julio de 2026. «Ejecutado» abarca cierre documental, analítico o de delimitación metodológica sobre `madrl_v3_20260627_164047`. Multi-semilla, Optuna y algoritmos adicionales quedan como trabajo futuro y no sustituyen la evidencia canónica.

Con **H1, H3, H4 y H6 ejecutados**, y con **H2 y H5 delimitados** como trabajo futuro, el manuscrito queda **culminado para presentación académica** bajo las restricciones declaradas (semilla única; HAPPO con 49 episodios por escenario). Solo **H7** permanece pendiente para el cierre formal institucional.

---

## 6.5 Criterios de cierre de la tesis y control de calidad final

Las conclusiones se consideran suficientemente sustentadas para responder las preguntas específicas desde la corrida Drive analizada. Tras el plan de la sección 6.4, el control de calidad final se centra en campos e índices Word, legibilidad PDF, correspondencia vertical entre PE–OE–hipótesis–resultados–conclusiones y aprobación del asesor. La extensión multi-semilla se mantiene como recomendación de trabajo futuro, no como resultado de esta tesis.

**Tabla 6.2. Criterios de cierre y control de calidad final.**

| Actividad | Propósito | Criterio de cierre |
|-----------|-----------|-------------------|
| **Revisión APA integral** | Alinear citas, tablas, figuras y referencias al formato APA 7. | Todas las citas tienen entrada bibliográfica y viceversa; captions coherentes. |
| **Revisión multi-semilla opcional** | Mejorar la validez externa de la comparación MADRL. | Réplicas documentadas o limitación de semilla única explicitada (opción adoptada). |
| **Auditoría de figuras y tablas** | Confirmar legibilidad y correspondencia con CSV/Drive canónicos. | Cada figura/tabla apunta a fuente verificable de `madrl_v3_20260627_164047`. |
| **Revisión de coherencia vertical** | Asegurar que PE, OE, hipótesis, resultados y conclusiones respondan lo mismo. | Matriz problema–objetivo–resultado–conclusión sin vacíos. |

*Nota.* Los criterios C de calidad documental no sustituyen la evidencia experimental ya auditada. El cierre formal institucional (registro y sustentación) corresponde al hito **H7**.

---

### Estado del capítulo

**Actualizado y validado (2026-07-15)** contra artefactos de `madrl_v3_20260627_164047`. Fuente Word canónica: `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx`.
