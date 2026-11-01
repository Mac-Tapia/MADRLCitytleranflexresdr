# Capítulo 7. Recomendaciones

> **Documento de tesis — recomendaciones.** Derivadas exclusivamente de los hallazgos de Cap. 5 y de las limitaciones de Cap. 6. Tercera persona. **No** se inventan resultados ni se elevan rankings descriptivos a superioridad estadística. Toda recomendación algorítmica se formula **bajo las condiciones experimentales estudiadas** (corrida canónica `madrl_v3_20260627_164047`, seed = 0, Capa A).

---

## 7.1 Recomendaciones estadísticas

Se recomienda completar una campaña **multisemilla** confirmatoria con 10–20 semillas independientes cuando el presupuesto computacional lo permita; el diseño `n_seeds=12` ya instrumentado satisface ese rango. Cada semilla debe tratarse como réplica experimental y los episodios de una sola corrida no deben sustituirla.

Se recomienda aumentar el número efectivo de réplicas y estimar **potencia** a priori/post hoc para los contrastes Friedman y Wilcoxon–Holm, reportando **intervalos de confianza** y **tamaños de efecto** (Kendall W, Cliff’s δ) de forma sistemática en todos los ejes.

Se recomienda evaluar **robustez** de las decisiones H0G/H1G y HE10–HE31 frente a variación de semilla, exclusión de KPI sensibles y sensibilidad de capas, manteniendo la Capa A como única fuente de veredicto de hipótesis.

---

## 7.2 Recomendaciones algorítmicas

**HAPPO.** Bajo las condiciones experimentales estudiadas, HAPPO dispone de 49 episodios históricos y un episodio post-resume para la curva descriptiva, pero carece de KPI-gains finales comparables para HE. Se recomienda completar una evaluación homogénea y generar esos KPI-gains antes de reincorporarlo a la contrastación inferencial; los episodios no deben denominarse i.i.d. ni usarse como sustitutos de semillas.

**MASAC.** En OE.1, MASAC es el único algoritmo con impacto Holm significativo vs baseline, en dirección de **deterioro**. Se recomienda revisar recompensa, exploración y estabilización de políticas antes de priorizarlo para flexibilidad.

**MATD3.** Bajo las condiciones experimentales estudiadas, MATD3 lidera descriptivamente la flexibilidad física de distrito y el eje CO₂ (OE.2). Se recomienda conservarlo como candidato preferente cuando el criterio de selección privilegie KPIs físicos de flexibilidad/emisiones, sin interpretarlo como ganador inferencial único.

**MAAC.** Bajo las condiciones experimentales estudiadas, MAAC lidera descriptivamente costos (OE.3), medianas de KPI-gain en E1 y los planos TOPSIS/4/4. Se recomienda conservarlo cuando el criterio privilegie costo o score multicriterio descriptivo, sin elevarlo a HE31 ni a ganador global estadístico.

---

## 7.3 Recomendaciones energéticas

A partir de la heterogeneidad documentada en Cap. 5 (throughput BESS, éxito EV y trade-offs por eje), se recomienda:

- **BESS:** calibrar señales de carga/descarga para que mayor actuación no se confunda con mejor KPI-gain.
- **EV / V2G:** mejorar la atribución del éxito de carga EV por escenario; el perfil actual muestra fuerte heterogeneidad entre algoritmos.
- **Cargas controlables:** mantener evaluación separada de flexibilidad de demanda respecto de storage/EV.
- **Carbono:** reforzar señales carbon-aware coherentes con el liderazgo descriptivo de MATD3 en ΔCO₂.
- **Tarifas:** preservar TOU explícito en el eje de costos, coherente con el liderazgo descriptivo de MAAC.
- **Flexibilidad:** reportar de forma conjunta `flex_composite` físico y KPI-gains, dado el liderazgo mixto MAAC/MATD3 en OE.1.

---

## 7.4 Validación externa

Se recomienda validar la generalización de los perfiles MATD3/MAAC/MASAC en:

- otros **períodos** temporales del dataset Iquitos;
- condiciones **climáticas** distintas;
- estructuras de **precios** y señales de carbono alternativas;
- otras **comunidades** o tipologías de edificios;
- **perturbaciones** de demanda, disponibilidad de DER y fallas parciales de agentes.

Toda extrapolación fuera del SEAI simulado debe tratarse como hipótesis de transferencia, no como resultado ya demostrado.

---

## 7.5 Validación preoperacional

Se recomienda una secuencia de madurez evidencia → operación:

1. simulación canónica (ya ejecutada);
2. campaña **multisemilla**;
3. evaluación **out-of-sample** (OOS);
4. pruebas de **stress** (perturbaciones);
5. validación **HIL/SIL** cuando exista bancada;
6. **piloto** controlado;
7. eventual **operación** asistida.

Bajo las condiciones experimentales estudiadas, el estudio permanece en simulación; no se recomienda despliegue operativo directo a partir del veredicto exploratorio actual.

---

## 7.6 Seguridad, privacidad y operación

Antes de cualquier piloto se recomienda aplicar privacidad por diseño y un modelo de amenazas para el flujo observación–política–acción–recompensa. El despliegue deberá minimizar datos identificables por edificio, segregar las redes OT/IT, autenticar agentes y operadores, proteger la integridad de telemetría, modelos y checkpoints, cifrar datos en tránsito y reposo, conservar registros auditables y definir respuesta ante incidentes. La política operativa deberá imponer límites seguros de acción, fallback a control RBC, monitoreo de deriva y rollback. Estas medidas son requisitos propuestos para una fase posterior; no se consideran implementadas ni validadas por la simulación actual (NIST, 2014; Casagrande, 2024; Sun et al., 2024).

---

## 7.7 Trabajo futuro

Se propone como trabajo futuro, sin afirmar resultados no obtenidos:

- **Safe MADRL** (restricciones de seguridad operativa y satisfacción de confort/energía);
- **GNN-MARL** solo si se justifica por topología de red o interacciones espaciales no capturadas por el Dec-POMDP actual;
- **transferencia** entre escenarios E1–E3 y entre comunidades;
- **robustez** a ruido de observación y a deriva de señales precio/carbono;
- **generalización** temporal y climática;
- modelado de **degradación** de BESS/EV;
- ampliación de **V2G**;
- **carbono dinámico** de mayor resolución;
- **multiobjetivo adaptativo** (pesos o preferencias no estacionarias) sin confundir ranking descriptivo con prueba de hipótesis.

---

## 7.8 Recomendación algorítmica final

Bajo las condiciones experimentales estudiadas:

| Eje | Recomendación descriptiva | Alcance |
|---|---|---|
| **E1 (flexibilidad)** | **MATD3** (KPI físico / flex de distrito) / **MAAC** (KPI-gain) | Liderazgo **descriptivo** únicamente |
| **E2 (CO₂)** | **MATD3** | Liderazgo **descriptivo** únicamente |
| **E3 (costos)** | **MAAC** | Liderazgo **descriptivo** únicamente |
| **Compromiso global** | Reportar **ambos**: MATD3 (`best_madrl` 0,6667) y MAAC (TOPSIS C\* = 0,9827 / evaluate_v2 4/4) | **Sin ganador estadístico único** |

**Síntesis.** Bajo las condiciones experimentales estudiadas, no existe un único algoritmo MADRL con superioridad estadística global concluyente. La recomendación de compromiso es reportar el dual descriptivo MATD3–MAAC y mantener las nulas específicas (HE10/HE20/HE30) como no rechazadas, de acuerdo con Cap. 5 y Cap. 6.

---
