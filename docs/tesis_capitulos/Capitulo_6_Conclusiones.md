# Capítulo 6. Conclusiones

> **Documento de tesis — alineado a la corrida canónica Colab/Drive (`madrl_v3_20260627_164047`).**  
> Validación 2026-07-15: `docs/VALIDACION_SECCIONES_6_4_6_5_2026-07-15.md`. No inventar hallazgos no soportados por artefactos.

---

## 6.1 Principales hallazgos

1. **Respuesta al OG:** entre los MADRL evaluables con KPIs auditados (MATD3, MAAC, MASAC), **MATD3** obtiene el mejor desempeño coordinado descriptivo (score global **0,6667**; fuente `best_madrl_report.json`). No existe dominancia universal en los tres ejes: MATD3 lidera flexibilidad y CO₂; MAAC lidera costos.

2. **Respuesta al OE.1 (flexibilidad):** **MATD3** registra la mejor flexibilidad compuesta en E1 (**1,0009**). En la muestra episódica completa (597 filas), **MAAC** obtiene la mejor media de `reward_mean_average`; Kruskal–Wallis sobre MAAC/MASAC/MATD3 es significativo (**p = 1,305×10⁻⁸**).

3. **Respuesta al OE.2 (CO₂):** **MATD3** logra el menor delta de emisiones en E2 (**23 070 kg** vs MAAC 70 654 kg y MASAC 77 649 kg). Kruskal–Wallis episódico: **p = 0,043866** (efecto pequeño, ε² ≈ 0,029).

4. **Respuesta al OE.3 (costos):** **MAAC** obtiene el menor delta de costo en E3 (**9 515 EUR**). Kruskal–Wallis episódico: **p = 0,251421** (no significativo a α = 0,05).

5. **Cobertura HAPPO:** corpus definitivo **49 episodios por escenario** (147 filas); no se imputó el episodio ausente. MAAC, MASAC y MATD3: **50 episodios por escenario** (450 filas). Total muestra episódica: **597 filas** (`gdrive_episode_kpis_used_for_statistics.csv`).

6. **Contribución metodológica:** benchmark reproducible Dec-POMDP/CTDE sobre 17 edificios del SEAI Iquitos con cuatro algoritmos MADRL bajo CityLearn v3.

---

## 6.2 Limitaciones encontradas

- **Semilla única (seed = 0):** la inferencia no cuantifica robustez multi-semilla; queda como trabajo futuro (H2).
- **HAPPO 49/50:** sin imputación del episodio faltante; HAPPO excluido de Kruskal–Wallis sobre KPI-gains por cobertura incompleta.
- **Dos niveles inferenciales:** contrastes episódicos (597 filas) vs KPI-gains de entrenamiento (231 filas, sin HAPPO) pueden divergir; la discusión los diferencia explícitamente.
- **Sin ganador Pareto universal:** trade-off MATD3 (flex+CO₂) vs MAAC (costos).
- **Simulación, no despliegue físico** en red real.

---

## 6.3 Trabajo futuro (no bloqueante para cierre del manuscrito)

- Campaña **multi-semilla** (≥3 seeds) con intervalos de confianza.
- **HPO con Optuna** y contrastes **PPO / SAC / A2C** (fuera de evidencia canónica).
- Sensibilidad de **pesos multiobjetivo** y frontera de Pareto ampliada.
- Re-evaluación técnica HAPPO si se corrige el error de evaluación post-entrenamiento.

---

## 6.4 Plan para culminar la tesis

El plan de culminación fue ejecutado diferenciando los hitos indispensables para cerrar el manuscrito de las ampliaciones experimentales que corresponden a trabajo futuro. La implementación se realizó sobre la corrida canónica `madrl_v3_20260627_164047`, sin inventar episodios, semillas, resultados ni artefactos no disponibles. El estado consolidado al **15 de julio de 2026** se presenta en la Tabla 6.1.

**Tabla 6.1. Ejecución e implementación del plan para culminar la tesis.**

| Hito | Implementación realizada | Estado y evidencia de cierre |
|------|--------------------------|------------------------------|
| **H1. Cobertura HAPPO** | Corpus definitivo de **49 episodios por escenario** para HAPPO; no se imputó el episodio ausente. Sincronizado en metodología, resultados, discusión, conclusiones y limitaciones. MAAC, MASAC y MATD3 conservan 50 episodios por escenario (**597 filas episódicas**). | **Ejecutado.** Evidencia: `gdrive_episode_kpis_used_for_statistics.csv` (597 filas; HAPPO n=49; MAAC/MASAC/MATD3 n=50). |
| **H2. Robustez multi-semilla** | Inferencia delimitada a **una sola semilla** de la corrida canónica. No se afirma generalización universal. | **Implementado como delimitación metodológica.** No ejecutado experimentalmente; no bloquea el cierre del manuscrito. |
| **H3. Inferencia estadística** | Shapiro–Wilk, Kruskal–Wallis, Mann–Whitney con **corrección Holm**, tamaños de efecto; Capítulos 5 y 6 sincronizados. | **Ejecutado.** OE.1: p = 1,305×10⁻⁸; OE.2: p = 0,043866; OE.3: p = 0,251421 (`gdrive_objective_aligned_statistics.csv`; pares Holm: `gdrive_objective_pairwise_mannwhitney_holm.csv`). |
| **H4. Pareto y baseline** | Lectura multiobjetivo sin ganador universal; contraste CityLearn v2 / RBC / baseline. Discusión diferencia medias episódicas, muestra inferencial completa y KPI anual final. | **Ejecutado en Cap. 5.** Sensibilidad de pesos como trabajo futuro. |
| **H5. HPO y algoritmos adicionales** | Optuna y contrastes PPO/SAC/A2C **no** forman parte de la evidencia canónica. | **Delimitado → trabajo futuro.** |
| **H6. Cierre documental** | Caps. 2, 4, 5 y 6 reforzados; discusión 5.10; referencias depuradas; tablas APA 7; campos e índices Word al abrir (F9). | **Ejecutado.** Manuscrito integrado listo para revisión institucional. |
| **H7. Entrega y sustentación** | Secuencia: índices F9, revisión visual PDF, validación del asesor, registro institucional, preparación de defensa. | **Pendiente de gestión institucional.** |

*Nota.* «Ejecutado» abarca cierre documental, analítico o de delimitación metodológica sobre `madrl_v3_20260627_164047`. Multi-semilla, Optuna y algoritmos adicionales quedan como trabajo futuro.

Con **H1, H3, H4 y H6 ejecutados**, y con **H2 y H5 delimitados** como trabajo futuro, el manuscrito queda **culminado para presentación académica** bajo las restricciones declaradas (semilla única; HAPPO con 49 episodios por escenario). Solo **H7** permanece pendiente para el cierre formal institucional.

---

## 6.5 Criterios de cierre de la tesis y control de calidad final

Las conclusiones se consideran suficientemente sustentadas para responder las preguntas específicas desde la corrida Drive analizada. Tras el plan de la sección 6.4, el control de calidad final se centra en campos e índices Word, legibilidad PDF, correspondencia vertical entre PE–OE–hipótesis–resultados–conclusiones y aprobación del asesor.

**Tabla 6.2. Criterios de cierre y control de calidad final.**

| Actividad | Propósito | Criterio de cierre |
|-----------|-----------|-------------------|
| **Revisión APA integral** | Alinear citas, tablas, figuras y referencias al formato APA 7. | Todas las citas tienen entrada bibliográfica y viceversa; captions coherentes. |
| **Revisión multi-semilla opcional** | Mejorar validez externa de la comparación MADRL. | Réplicas documentadas **o** limitación de semilla única explicitada (**opción adoptada**). |
| **Auditoría de figuras y tablas** | Confirmar legibilidad y correspondencia con CSV/Drive canónicos. | Cada figura/tabla apunta a fuente verificable de `madrl_v3_20260627_164047`. |
| **Revisión de coherencia vertical** | Asegurar que PE, OE, hipótesis, resultados y conclusiones respondan lo mismo. | Matriz problema–objetivo–resultado–conclusión sin vacíos. |

*Nota.* Los criterios de calidad documental no sustituyen la evidencia experimental ya auditada. El cierre formal institucional (registro y sustentación) corresponde al hito **H7**.

---

### Estado del capítulo

**Actualizado y validado (2026-07-15)** contra artefactos de `madrl_v3_20260627_164047`. Fuente Word canónica: `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx`.
