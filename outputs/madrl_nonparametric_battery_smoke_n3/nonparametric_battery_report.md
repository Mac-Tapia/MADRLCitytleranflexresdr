# Bateria no parametrica MADRL (HAPPO, MAAC, MASAC, MATD3)

alpha=0.05, complementary=False
expected_n_seeds=3, sample_unit=seed
TOPSIS weights: {'OE.1': 0.3333333333333333, 'OE.2': 0.3333333333333333, 'OE.3': 0.3333333333333333}
TOPSIS criteria kinds: {'OE.1': 'benefit', 'OE.2': 'cost', 'OE.3': 'cost'}

### OE.1 — bateria no parametrica

Orientacion: mayor es mejor.
Unidad de analisis: seed | n_esperado=3 | n_por_algoritmo={'HAPPO': 3, 'MAAC': 3, 'MASAC': 3, 'MATD3': 3} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9644598960876465, p=0.6377831101417542, normalidad_rechazada=False [ok]
- MAAC: W=0.9424962401390076, p=0.5375089049339294, normalidad_rechazada=False [ok]
- MASAC: W=0.8783940672874451, p=0.3196965157985687, normalidad_rechazada=False [ok]
- MATD3: W=0.9999017119407654, p=0.9810585975646973, normalidad_rechazada=False [ok]

**Fligner-Killeen**: estadistico=1.4396592514234787, p=0.6962652768157677, heterocedasticidad=False.

**Kruskal-Wallis**: H=9.358974358974365, p=0.024879945028018657, epsilon^2=0.8508158508158513, significativo=True.
Rangos medios: {'HAPPO': 11.0, 'MAAC': 8.0, 'MASAC': 3.6666666666666665, 'MATD3': 3.3333333333333335}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=1.0190493307301363, p_raw=0.308179547467054, p_holm=0.616359094934108, sig=False, Cliff d=1.0 (large)
- HAPPO vs MASAC: z=2.491009475118111, p_raw=0.012738072274857463, p_holm=0.06369036137428731, sig=False, Cliff d=1.0 (large)
- HAPPO vs MATD3: z=2.60423717853257, p_raw=0.009207901182984923, p_holm=0.05524740709790954, sig=False, Cliff d=1.0 (large)
- MAAC vs MASAC: z=1.4719601443879748, p_raw=0.1410316405207163, p_holm=0.451694642863715, sig=False, Cliff d=1.0 (large)
- MAAC vs MATD3: z=1.585187847802434, p_raw=0.11292366071592876, p_holm=0.451694642863715, sig=False, Cliff d=1.0 (large)
- MASAC vs MATD3: z=0.11322770341445948, p_raw=0.9098500327472846, p_holm=0.9098500327472846, sig=False, Cliff d=0.1111111111111111 (negligible)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=1.0 (large)
- HAPPO vs MASAC: d=1.0 (large)
- HAPPO vs MATD3: d=1.0 (large)
- MAAC vs MASAC: d=1.0 (large)
- MAAC vs MATD3: d=1.0 (large)
- MASAC vs MATD3: d=0.1111111111111111 (negligible)

**Ganador(es)**: ['HAPPO', 'MAAC'] (primary=HAPPO, status=cowinners_cliff_tiebreak)
- Highest KW mean rank: HAPPO (Rmean=11.000).
- Dunn-Holm vs 2nd (MAAC, Rmean=8.000) not significant (p_holm=0.616359094934108) -> co-winners.
- Tie-break Cliff's delta(HAPPO,MAAC)=1.0 (large); oriented medians HAPPO=-0.5450, MAAC=-0.6158.
- Cliff's delta prefers HAPPO (report as primary among co-winners).

### OE.2 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=3 | n_por_algoritmo={'HAPPO': 3, 'MAAC': 3, 'MASAC': 3, 'MATD3': 3} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9997968673706055, p=0.9727783203125, normalidad_rechazada=False [ok]
- MAAC: W=0.9969347715377808, p=0.8942059278488159, normalidad_rechazada=False [ok]
- MASAC: W=0.9980037212371826, p=0.9146393537521362, normalidad_rechazada=False [ok]
- MATD3: W=0.9999996423721313, p=0.9988566637039185, normalidad_rechazada=False [ok]

**Fligner-Killeen**: estadistico=3.052874193710429, p=0.3835446417044587, heterocedasticidad=False.

**Kruskal-Wallis**: H=6.589743589743598, p=0.08618964081900728, epsilon^2=0.5990675990675999, significativo=False.
Rangos medios: {'HAPPO': 7.0, 'MAAC': 8.666666666666666, 'MASAC': 2.0, 'MATD3': 8.333333333333334}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-0.5661385170722977, p_raw=0.5712996214994488, p_holm=1.0, sig=False, Cliff d=-0.3333333333333333 (medium)
- HAPPO vs MASAC: z=1.6984155512168937, p_raw=0.08942935902899353, p_holm=0.3577174361159741, sig=False, Cliff d=1.0 (large)
- HAPPO vs MATD3: z=-0.45291081365783853, p_raw=0.6506129639327535, p_holm=1.0, sig=False, Cliff d=-0.3333333333333333 (medium)
- MAAC vs MASAC: z=2.2645540682891916, p_raw=0.023540058261177933, p_holm=0.1412403495670676, sig=False, Cliff d=1.0 (large)
- MAAC vs MATD3: z=0.11322770341445917, p_raw=0.9098500327472848, p_holm=1.0, sig=False, Cliff d=0.1111111111111111 (negligible)
- MASAC vs MATD3: z=-2.1513263648747323, p_raw=0.03145044869191862, p_holm=0.1572522434595931, sig=False, Cliff d=-1.0 (large)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-0.3333333333333333 (medium)
- HAPPO vs MASAC: d=1.0 (large)
- HAPPO vs MATD3: d=-0.3333333333333333 (medium)
- MAAC vs MASAC: d=1.0 (large)
- MAAC vs MATD3: d=0.1111111111111111 (negligible)
- MASAC vs MATD3: d=-1.0 (large)

**Ganador(es)**: ['MAAC', 'MATD3'] (primary=MAAC, status=cowinners_median_tiebreak)
- Highest KW mean rank: MAAC (Rmean=8.667).
- Dunn-Holm vs 2nd (MATD3, Rmean=8.333) not significant (p_holm=1.0) -> co-winners.
- Tie-break Cliff's delta(MAAC,MATD3)=0.1111111111111111 (negligible); oriented medians MAAC=-828.2296, MATD3=-834.0604.
- Median tie-break prefers MAAC.

### OE.3 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=3 | n_por_algoritmo={'HAPPO': 3, 'MAAC': 3, 'MASAC': 3, 'MATD3': 3} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9999032616615295, p=0.9812083840370178, normalidad_rechazada=False [ok]
- MAAC: W=0.9884372353553772, p=0.7942326664924622, normalidad_rechazada=False [ok]
- MASAC: W=0.7938928008079529, p=0.09999964386224747, normalidad_rechazada=False [ok]
- MATD3: W=0.9937629699707031, p=0.8490105867385864, normalidad_rechazada=False [ok]

**Fligner-Killeen**: estadistico=2.4695390603298546, p=0.48082121804457956, heterocedasticidad=False.

**Kruskal-Wallis**: H=10.384615384615387, p=0.015564397458593152, epsilon^2=0.9440559440559443, significativo=True.
Rangos medios: {'HAPPO': 5.0, 'MAAC': 11.0, 'MASAC': 2.0, 'MATD3': 8.0}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-2.0380986614602725, p_raw=0.04154006700988516, p_holm=0.2077003350494258, sig=False, Cliff d=-1.0 (large)
- HAPPO vs MASAC: z=1.0190493307301363, p_raw=0.308179547467054, p_holm=0.924538642401162, sig=False, Cliff d=1.0 (large)
- HAPPO vs MATD3: z=-1.0190493307301363, p_raw=0.308179547467054, p_holm=0.924538642401162, sig=False, Cliff d=-1.0 (large)
- MAAC vs MASAC: z=3.0571479921904086, p_raw=0.0022345392261445187, p_holm=0.013407235356867112, sig=True, Cliff d=1.0 (large)
- MAAC vs MATD3: z=1.0190493307301363, p_raw=0.308179547467054, p_holm=0.924538642401162, sig=False, Cliff d=1.0 (large)
- MASAC vs MATD3: z=-2.0380986614602725, p_raw=0.04154006700988516, p_holm=0.2077003350494258, sig=False, Cliff d=-1.0 (large)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-1.0 (large)
- HAPPO vs MASAC: d=1.0 (large)
- HAPPO vs MATD3: d=-1.0 (large)
- MAAC vs MASAC: d=1.0 (large)
- MAAC vs MATD3: d=1.0 (large)
- MASAC vs MATD3: d=-1.0 (large)

**Ganador(es)**: ['MAAC', 'MATD3'] (primary=MAAC, status=cowinners_cliff_tiebreak)
- Highest KW mean rank: MAAC (Rmean=11.000).
- Dunn-Holm vs 2nd (MATD3, Rmean=8.000) not significant (p_holm=0.924538642401162) -> co-winners.
- Tie-break Cliff's delta(MAAC,MATD3)=1.0 (large); oriented medians MAAC=-308.5569, MATD3=-368.8843.
- Cliff's delta prefers MAAC (report as primary among co-winners).

### OG — sintesis global (E1+E2+E3 como bloques)

**Friedman**: chi2=6.600000000000001, p=0.08580108740012288, W=0.7333333333333335, significativo=False.
Rangos medios Friedman: {'HAPPO': 2.6666666666666665, 'MAAC': 3.6666666666666665, 'MASAC': 1.0, 'MATD3': 2.6666666666666665}

**Nemenyi**: CD=2.707997260862172 (alpha=0.05)
- HAPPO vs MAAC: |dR|=1.0, sig=False
- HAPPO vs MASAC: |dR|=1.6666666666666665, sig=False
- HAPPO vs MATD3: |dR|=0.0, sig=False
- MAAC vs MASAC: |dR|=2.6666666666666665, sig=False
- MAAC vs MATD3: |dR|=1.0, sig=False
- MASAC vs MATD3: |dR|=1.6666666666666665, sig=False

**TOPSIS (declaracion oficial de ganador)**
- #1 MAAC: C*=0.7841288492979923
- #2 HAPPO: C*=0.578813207888542
- #3 MATD3: C*=0.548304241628292
- #4 MASAC: C*=0.0

**Validacion TOPSIS vs Friedman-Nemenyi**
- TOPSIS and Friedman agree on winner: MAAC.