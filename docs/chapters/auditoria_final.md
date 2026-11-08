> **Resultados históricos retirados (propietario, 2026-11-01).** Las cifras inferenciales de este documento (p-valores, ganadores, rankings) vienen de corridas anteriores que ya no cuentan. La única fuente válida de cifras estadísticas será `tools/eval/build_campaign_statistical_report.py` sobre la campaña nueva (SPEC-009, módulo 4); hasta entonces no se citan.

# Matriz de auditoría final — Capítulos IV–VII (prompt maestro)

**Fecha:** 2026-08-07  
**Corrida canónica:** `madrl_v3_20260627_164047`  
**Fuente HE/H0G:** `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` (Capa A)  
**α = 0,05** · HAPPO excluido de HE (sin KPI-gains finales comparables)

Estados: **CUMPLIDO** | **INCOMPLETO** | **INCONSISTENTE**

---

## Matriz vertical PG/OG/HG y PE/OE/HE

| Problema | Objetivo | Hipótesis | Desarrollo Cap. IV | KPI | Resultado descriptivo | Prueba inferencial | p | Tamaño del efecto | Mejor MADRL | Conclusión Cap. VI | Recomendación Cap. VII | Estado |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| **PG** | **OG** | **H0G/H1G** | §4.9–4.15 integración E1+E2+E3; 12 tratamientos | KPI-gains GLOBAL (n=26); score `best_madrl`; TOPSIS descriptivo | Score escenario MAAC; mediana GLOBAL MATD3 (−0,00694); `best_madrl` MATD3 0,6667; TOPSIS MAAC C\*=0,9827 | Friedman pareado (principal); KW exploratorio | Friedman **0,0096**; KW 0,4044 | Kendall W = **0,1787** | Sin ganador único inferencial; compromiso descriptivo MATD3/`best_madrl` vs MAAC/TOPSIS–4/4 | Se rechaza H0G exploratoria; se respalda H1G exploratoria; alcance seed=0 | §7.7 compromiso bajo condiciones experimentales; multisemilla §7.1 | **CUMPLIDO** |
| **PE.1** | **OE.1** | **HE10/HE11** | §4.9 E1; reward E1; recursos flex | KPI-gains E1 (n=12); flex_composite | Mediana gain MAAC −0,00119; flex_composite MATD3 1,0009 | Friedman; Wilcoxon vs 0 + Holm; KW exploratorio | Friedman **0,0611**; MASAC Holm vs 0 **0,0483** (desfavorable) | W = **0,2329** | Descriptivo: MAAC (gain) / MATD3 (flex); **no** inferencial | HE10 no se rechaza; HE11 no se respalda | E1: MATD3 físico / MAAC gain (solo descriptivo) | **CUMPLIDO** |
| **PE.2** | **OE.2** | **HE20/HE21** | §4.9 E2; CI dinámica A4 | KPI-gains E2 (n=5); ΔCO₂ | Mediana MATD3 −0,0421; ΔCO₂ MATD3 23 070 kg | Friedman; Wilcoxon vs 0; KW exploratorio | Friedman **0,0498**; impacto Holm todos **0,1875** | W = **0,6000** | Descriptivo: **MATD3**; sin post hoc Holm | HE20 no se rechaza; HE21 no se respalda | E2: MATD3 (descriptivo) | **CUMPLIDO** |
| **PE.3** | **OE.3** | **HE30/HE31** | §4.9 E3; tarifas TOU; peak billing A3 | KPI-gains E3 (n=9); Δcosto | Mediana MAAC −0,00268; Δcosto MAAC 9 515 USD | Friedman; Wilcoxon vs 0; KW exploratorio | Friedman **0,1801**; impacto Holm ≥0,0586 | W = **0,1905** | Descriptivo: **MAAC**; sin omnibus ni impacto Holm | HE30 no se rechaza; HE31 no se respalda | E3: MAAC (descriptivo; no ahorro inferencial) | **CUMPLIDO** |

---

## Checklist por objetivo (8 criterios)

| Criterio | OE.1 | OE.2 | OE.3 | OG |
|---|---|---|---|---|
| 1. DESARROLLO (Cap. IV) | CUMPLIDO | CUMPLIDO | CUMPLIDO | CUMPLIDO |
| 2. EFECTO cuantitativo | CUMPLIDO | CUMPLIDO | CUMPLIDO | CUMPLIDO |
| 3. SIGNIFICANCIA (prueba adecuada) | CUMPLIDO (Friedman; no rechaza) | CUMPLIDO (Friedman marginal sin post hoc) | CUMPLIDO (Friedman n.s.) | CUMPLIDO (Friedman p=0,0096) |
| 4. MAGNITUD (tamaño del efecto) | CUMPLIDO (W=0,2329) | CUMPLIDO (W=0,6000) | CUMPLIDO (W=0,1905) | CUMPLIDO (W=0,1787) |
| 5. DESEMPEÑO (mejor MADRL) | CUMPLIDO (descriptivo mixto) | CUMPLIDO (MATD3) | CUMPLIDO (MAAC) | CUMPLIDO (sin único inferencial) |
| 6. INFERENCIA del liderazgo | CUMPLIDO (no respaldado) | CUMPLIDO (no respaldado) | CUMPLIDO (no respaldado) | CUMPLIDO (exploratorio; sin ganador único) |
| 7. CONCLUSIÓN responde objetivo | CUMPLIDO (§6.2) | CUMPLIDO (§6.3) | CUMPLIDO (§6.4) | CUMPLIDO (§6.1) |
| 8. RECOMENDACIÓN deriva del hallazgo | CUMPLIDO (§7.7) | CUMPLIDO (§7.7) | CUMPLIDO (§7.7) | CUMPLIDO (§7.7) |

---

## Correspondencias estructurales verificadas

| Cadena | Cap. IV | Cap. V | Cap. VI | Cap. VII | Estado |
|---|---|---|---|---|---|
| PG ↔ OG ↔ HG ↔ IV ↔ V ↔ VI ↔ VII | §4.15 / 4.10 | §5.6–5.7 | §6.1 | §7.1/7.7 | **CUMPLIDO** |
| PE.1 ↔ OE.1 ↔ HE.1 ↔ E1 | §4.9 / 4.15 | §5.3 | §6.2 | §7.2/7.7 | **CUMPLIDO** |
| PE.2 ↔ OE.2 ↔ HE.2 ↔ E2 | §4.9 / 4.15 | §5.4 | §6.3 | §7.2/7.7 | **CUMPLIDO** |
| PE.3 ↔ OE.3 ↔ HE.3 ↔ E3 | §4.9 / 4.15 | §5.5 | §6.4 | §7.2/7.7 | **CUMPLIDO** |

---

## Ban list (no citar)

| Claim | Motivo |
|---|---|
| KW ALL p = 0,1554 | Capa B poolada; no HE |
| Shapiro OE1 ~10⁻⁷ | Capa B / residual |
| Wilcoxon OE3 p = 0,0333 como Holm | Capa B |
| TOPSIS / 4/4 como prueba HE | Solo descriptivo |
| «Se acepta H₀» | Regla de interpretación: solo «no se rechaza» |

---

## Elementos rectores

Título, PG/PE, OG/OE y H0G/H1G–HE10–HE31 **no** se modifican para resolver inconsistencias posteriores; cualquier ajuste se hace en Cap. IV–VII.

**Veredicto global de la matriz:** **CUMPLIDO** en markdown Cap. IV–VII bajo Capa A.

**Word (2026-08-07):** Cap. IV–VII inyectados atómicamente en ambos canónicos (`tools/thesis/rebuild_cap4_7_atomic_docx.py`). Estructura Cap4→5→6→7→Referencias verificada (bloques ≈127/187/51/38). Ban list `0,1554` eliminada del Resumen/Abstract. `verify_tesis_doctoral_docx.py --all-canons` → **ok=true** / doctoral **complete=true**.
