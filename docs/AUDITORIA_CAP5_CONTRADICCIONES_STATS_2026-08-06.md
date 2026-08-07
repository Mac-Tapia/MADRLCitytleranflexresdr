# Auditoría Cap. V — contradicciones estadísticas (2026-08-06)

**Corrida canónica:** `madrl_v3_20260627_164047` (50 episodios Drive).  
**Fuente única para HE/H0G:** `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` (Capa A).  
**α = 0,05.** HAPPO excluido de la inferencia HE (sin KPI-gains finales comparables).

## Capas incompatibles

| Capa | Ruta | Unidad / n | Algoritmos | Emparejamiento | Rol Cap. V |
|------|------|------------|------------|----------------|------------|
| **A (canónica HE)** | `problemas_objetivos_hipotesis/` | KPI-gains; OE1=12, OE2=5, OE3=9, GLOBAL=26 por algoritmo | MAAC, MASAC, MATD3 | Pareado por KPI (Friedman/Wilcoxon); KW independiente | **Única contrastación HE** |
| B (prohibida HE) | `analisis_estadistico_madrl.csv`, `hipotesis_estadisticas_madrl.csv`, `thesis_objective_evidence/` | KPI poolados; OE1=36, OE2=15, OE3=26, ALL=77 | Trio | Pareado por índice; KW independiente | Excluir de HE |
| C (complementaria) | `madrl_nonparametric_battery/`, `episode_inferential_by_oe.csv` | Métricas episódicas ~49–50 | +HAPPO | Independiente (KW/Dunn) | Solo sensibilidad |
| D (descriptiva) | `analisis_cuantitativo_completo_50_episodios/` | Primary % / building | +HAPPO | Friedman sobre bloques distintos | No HE |

## Contradicciones C1–C14

### C1 — Shapiro OE.1 magnitudes
- **Fuentes:** Cap. V §5.3.2 (p ≈ 10⁻⁷–10⁻⁸) vs `normalidad_shapiro_por_problema.csv` vs `analisis_estadistico_madrl.csv`
- **Variable / unidad / n:** KPI-gains OE1; n A=12, B=36
- **Algoritmos / emparejamiento / prueba:** MAAC, MASAC, MATD3; por grupo; Shapiro–Wilk
- **Conflicto:** Cap. V cita orden de Capa B; Capa A: MAAC W=0,7152 p=0,00118; MASAC W=0,5997 p=1,07×10⁻⁴; MATD3 W=0,7160 p=0,00121
- **Preferir:** Capa A

### C2 — Shapiro OE.2 / OE.3
- **Fuentes:** Cap. V §5.3.3–§5.3.4 vs Capa A vs Capa B
- **n:** A OE2=5 / OE3=9; B OE2=15 / OE3=26
- **Conflicto:** Cap. V OE2 “10⁻⁴–10⁻⁵” vs A p≈0,0094–0,0098; OE3 “10⁻⁷–10⁻⁸” vs A p≈2,2×10⁻⁵–6,9×10⁻⁵
- **Preferir:** Capa A (rechazo de normalidad idéntico; magnitudes distintas)

### C3 — Kruskal–Wallis A vs B
- **Fuentes:** `pruebas_omnibus_problemas_objetivos.csv` vs `analisis_estadistico_madrl.csv`
- **Conflicto:** OE1 H=1,5164 p=0,4685 (A) vs H=2,5415 p=0,2806 (B); OE2 0,7648 vs 0,5457; OE3 0,7357 vs 0,3881; GLOBAL 0,4044 vs ALL 0,1554
- **Preferir:** Capa A (escenario filtrado)

### C4 — Cap. V §5.3.1 mezcla KW GLOBAL (A) con KW ALL (B)
- **Conflicto:** “KW global (scores) 0,4044” + “KW ALL 0,1554”; scores reales KW p=0,1133 (`statistical_run_manifest.json`)
- **Preferir:** KW GLOBAL KPI-gains p=0,4044; no citar 0,1554 en HE

### C5 — Friedman / Kendall W / decisiones A vs D
- **Conflicto:** OE2 A χ²=6,00 p=0,0498 W=0,600 vs D χ²=39,35 p=1,46×10⁻⁸ (D rechaza HE20); OG A p=0,0096 vs D p=0,086
- **Preferir:** Capa A para HE/H0G

### C6 — KW episódica (C) vs HE (A)
- **Conflicto:** C OE1 p≈1,96×10⁻¹¹ vs A p=0,4685 (significancia opuesta)
- **Preferir:** A para HE; C solo complementaria

### C7 — Friedman OG A vs C
- **Conflicto:** A χ²=9,2911 p=0,0096 W=0,1787 vs C χ²=3,40 p=0,334 W=0,378
- **Preferir:** A

### C8 — Wilcoxon vs cero A vs D
- **Conflicto:** A OE1 solo MASAC Holm p=0,0483 (desfavorable); D sin impacto OE1 significativo; OE2/OE3 direcciones distintas
- **Preferir:** A

### C9 — Wilcoxon OE3 p=0,0333 (B) vs Holm A
- **Conflicto:** Cap. V cita MASAC vs MAAC p=0,0333 (B n=26); A p_raw=0,176 p_Holm=0,527 (n=9)
- **Preferir:** A Holm

### C10 — MWU / Cliff’s δ A vs B
- **Conflicto:** p crudos distintos; ambos sin pares Holm-significativos en A
- **Preferir:** A

### C11 — Decisión H0G A vs D vs B
- **Conflicto:** A+Cap. V rechaza H0G exploratoria; D no rechaza; B KW no rechaza
- **Preferir:** A (Friedman preferido sobre KW para mismas unidades)

### C12 — Rankings descriptivos (no error de cálculo)
- KPI-gain mediana: OE1 MAAC, OE2 MATD3, OE3 MAAC
- Físicos: flex/CO₂ MATD3; costo/TOPSIS/4/4 MAAC
- **Regla:** HE usa medianas KPI-gain (A); físicos/TOPSIS en descriptivo

### C13 — Pipeline código
- `thesis_cap5_structured.py` hardcodea A; `thesis_doctoral_sections.py` helpers leen Capa B
- **Preferir:** A; corregir helpers

### C14 — TOPSIS C\*
- Cap. V citaba C\*=0,7828; canónico `topsis_ranking.csv` C\*=**0,9827** (MAAC)
- **Preferir:** CSV canónico

## Tabla canónica HE (Capa A)

| Eje | Hip. | Mejor descriptivo (mediana gain) | Shapiro | Impacto vs 0 (Holm) | Friedman (principal) | Kendall W | KW (exploratorio) | Post hoc Holm | Decisión |
|-----|------|----------------------------------|---------|---------------------|----------------------|-----------|-------------------|---------------|----------|
| OE.1 | HE10/HE11 | MAAC (−0,00119) | Rechazada (p≤0,00121) | Solo MASAC p=0,0483 desfavorable | χ²=5,5897 p=0,0611 | 0,2329 | H=1,5164 p=0,4685 | Pares n.s. (min Holm 0,110) | **No se rechaza HE10**; no se respalda HE11 |
| OE.2 | HE20/HE21 | MATD3 (−0,0421) | Rechazada (p≈0,0094–0,0098) | Todos Holm=0,1875 n.s. | χ²=6,0000 p=0,0498 | 0,6000 | H=0,5364 p=0,7648 | Pares n.s. | **No se rechaza HE20**; no se respalda HE21 |
| OE.3 | HE30/HE31 | MAAC (−0,00268) | Rechazada (p≤6,9×10⁻⁵) | Todos n.s. tras Holm | χ²=3,4286 p=0,1801 | 0,1905 | H=0,6138 p=0,7357 | Pares n.s. | **No se rechaza HE30**; no se respalda HE31 |
| OG | H0G/H1G | Score MAAC / mediana MATD3 | Rechazada | Tres algoritmos impacto desfavorable significativo | χ²=9,2911 p=0,0096 | 0,1787 | H=1,8108 p=0,4044 | MAAC–MASAC Holm p=0,0172 | **Se rechaza H0G** exploratoria; **sin ganador único** |

## Ban list (no citar como HE)

| Claim | Fuente | Motivo |
|-------|--------|--------|
| Rechazar HE20 / respaldar HE21 | Capa D | Estimando distinto + HAPPO |
| KW p≈1e-11 como HE | Capa C | Episódico independiente |
| KW p=0,1554 / 0,2806 / … | Capa B | Escenarios poolados |
| Shapiro OE1 ~1e-7 | Cap. V residual / B | n incorrecto |
| Wilcoxon OE3 p=0,0333 como Holm | Cap. V / B | n y corrección incorrectos |
| TOPSIS/4/4 como prueba HE | multicriteria / evaluate_v2 | Solo descriptivo |

## Artefactos de verificación

- `decisiones_problemas_objetivos_hipotesis.csv`
- `pruebas_omnibus_problemas_objetivos.csv`
- `normalidad_shapiro_por_problema.csv`
- `impacto_vs_baseline_wilcoxon.csv`
- `comparaciones_wilcoxon_pareado_holm.csv`
- `comparaciones_mwu_holm_problemas.csv`
- `outputs/madrl_multicriteria_selection/topsis_ranking.csv`
