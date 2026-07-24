# Bateria no parametrica MADRL (HAPPO, MAAC, MASAC, MATD3)

alpha=0.05, complementary=False
expected_n_seeds=12, sample_unit=seed
TOPSIS weights: {'OE.1': 0.3333333333333333, 'OE.2': 0.3333333333333333, 'OE.3': 0.3333333333333333}
TOPSIS criteria kinds: {'OE.1': 'benefit', 'OE.2': 'cost', 'OE.3': 'cost'}

### OE.1 — bateria no parametrica

Orientacion: mayor es mejor.
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 12, 'MAAC': 12, 'MASAC': 12, 'MATD3': 12} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9844549894332886, p=0.9956896901130676, normalidad_rechazada=False [ok]
- MAAC: W=0.9715715050697327, p=0.9265492558479309, normalidad_rechazada=False [ok]
- MASAC: W=0.9649982452392578, p=0.8520521521568298, normalidad_rechazada=False [ok]
- MATD3: W=0.9359277486801147, p=0.44718310236930847, normalidad_rechazada=False [ok]

**Fligner-Killeen**: estadistico=2.6852144628673806, p=0.4427457920844141, heterocedasticidad=False.

**Kruskal-Wallis**: H=34.758503401360514, p=1.3701014656385446e-07, epsilon^2=0.739542625560862, significativo=True.
Rangos medios: {'HAPPO': 41.5, 'MAAC': 23.666666666666668, 'MASAC': 7.833333333333333, 'MATD3': 25.0}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=3.1201833628309528, p_raw=0.0018073849422994967, p_holm=0.009036924711497484, sig=True, Cliff d=0.9305555555555556 (large)
- HAPPO vs MASAC: z=5.8904396195500235, p_raw=3.851695863872266e-09, p_holm=2.3110175183233594e-08, sig=True, Cliff d=1.0 (large)
- HAPPO vs MATD3: z=2.8868986254230316, p_raw=0.003890595620885816, p_holm=0.011671786862657449, sig=True, Cliff d=0.9027777777777778 (large)
- MAAC vs MASAC: z=2.770256256719071, p_raw=0.005601220549520689, p_holm=0.011671786862657449, sig=True, Cliff d=0.875 (large)
- MAAC vs MATD3: z=-0.23328473740792152, p_raw=0.8155403094707532, p_holm=0.8155403094707532, sig=False, Cliff d=-0.08333333333333333 (negligible)
- MASAC vs MATD3: z=-3.0035409941269924, p_raw=0.0026685759492327808, p_holm=0.010674303796931123, sig=True, Cliff d=-0.9027777777777778 (large)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=0.9305555555555556 (large)
- HAPPO vs MASAC: d=1.0 (large)
- HAPPO vs MATD3: d=0.9027777777777778 (large)
- MAAC vs MASAC: d=0.875 (large)
- MAAC vs MATD3: d=-0.08333333333333333 (negligible)
- MASAC vs MATD3: d=-0.9027777777777778 (large)

**Ganador(es)**: ['HAPPO'] (primary=HAPPO, status=ok)
- Highest KW mean rank: HAPPO (Rmean=41.500).
- Dunn-Holm confirms HAPPO > MATD3 (p_holm=0.011671786862657449, alpha=0.05).

### OE.2 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 12, 'MAAC': 12, 'MASAC': 12, 'MATD3': 12} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9290335774421692, p=0.36998113989830017, normalidad_rechazada=False [ok]
- MAAC: W=0.9650163054466248, p=0.8522837162017822, normalidad_rechazada=False [ok]
- MASAC: W=0.921684741973877, p=0.300176203250885, normalidad_rechazada=False [ok]
- MATD3: W=0.947411835193634, p=0.5995089411735535, normalidad_rechazada=False [ok]

**Fligner-Killeen**: estadistico=0.23736311077768757, p=0.9713434799189016, heterocedasticidad=False.

**Kruskal-Wallis**: H=32.1658163265306, p=4.828819998438495e-07, epsilon^2=0.6843790707772469, significativo=True.
Rangos medios: {'HAPPO': 21.5, 'MAAC': 32.0, 'MASAC': 7.25, 'MATD3': 37.25}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-1.8371173070873836, p_raw=0.06619257972219345, p_holm=0.1323851594443869, sig=False, Cliff d=-0.5694444444444444 (large)
- HAPPO vs MASAC: z=2.4932306310471635, p_raw=0.012658659315810979, p_holm=0.03797597794743294, sig=True, Cliff d=0.875 (large)
- HAPPO vs MATD3: z=-2.7556759606310757, p_raw=0.005857099085284129, p_holm=0.023428396341136516, sig=True, Cliff d=-0.8055555555555556 (large)
- MAAC vs MASAC: z=4.3303479381345475, p_raw=1.4887392198145034e-05, p_holm=7.443696099072516e-05, sig=True, Cliff d=1.0 (large)
- MAAC vs MATD3: z=-0.9185586535436918, p_raw=0.35832646674888025, p_holm=0.35832646674888025, sig=False, Cliff d=-0.3194444444444444 (small)
- MASAC vs MATD3: z=-5.248906591678239, p_raw=1.53004627295281e-07, p_holm=9.180277637716859e-07, sig=True, Cliff d=-1.0 (large)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-0.5694444444444444 (large)
- HAPPO vs MASAC: d=0.875 (large)
- HAPPO vs MATD3: d=-0.8055555555555556 (large)
- MAAC vs MASAC: d=1.0 (large)
- MAAC vs MATD3: d=-0.3194444444444444 (small)
- MASAC vs MATD3: d=-1.0 (large)

**Ganador(es)**: ['MATD3', 'MAAC'] (primary=MATD3, status=cowinners_cliff_tiebreak)
- Highest KW mean rank: MATD3 (Rmean=37.250).
- Dunn-Holm vs 2nd (MAAC, Rmean=32.000) not significant (p_holm=0.35832646674888025) -> co-winners.
- Tie-break Cliff's delta(MATD3,MAAC)=0.3194444444444444 (small); oriented medians MATD3=-836.6190, MAAC=-857.6200.
- Cliff's delta prefers MATD3 (report as primary among co-winners).

### OE.3 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 12, 'MAAC': 12, 'MASAC': 12, 'MATD3': 12} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9063951969146729, p=0.1917739063501358, normalidad_rechazada=False [ok]
- MAAC: W=0.9150462746620178, p=0.2474842369556427, normalidad_rechazada=False [ok]
- MASAC: W=0.9288262128829956, p=0.36783671379089355, normalidad_rechazada=False [ok]
- MATD3: W=0.7476391792297363, p=0.0025251840706914663, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=1.7281433272261317, p=0.6306951223476249, heterocedasticidad=False.

**Kruskal-Wallis**: H=38.62840136054419, p=2.0805506115928644e-08, epsilon^2=0.8218808800115784, significativo=True.
Rangos medios: {'HAPPO': 22.25, 'MAAC': 41.583333333333336, 'MASAC': 6.5, 'MATD3': 27.666666666666668}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-3.3826286924148654, p_raw=0.0007179563057028212, p_holm=0.0028718252228112848, sig=True, Cliff d=-1.0 (large)
- HAPPO vs MASAC: z=2.7556759606310757, p_raw=0.005857099085284129, p_holm=0.017571297255852387, sig=True, Cliff d=1.0 (large)
- HAPPO vs MATD3: z=-0.9477192457196822, p_raw=0.343272400574707, p_holm=0.343272400574707, sig=False, Cliff d=-0.375 (medium)
- MAAC vs MASAC: z=6.138304653045941, p_raw=8.340679347410911e-10, p_holm=5.004407608446547e-09, sig=True, Cliff d=1.0 (large)
- MAAC vs MATD3: z=2.4349094466951833, p_raw=0.014895516855698135, p_holm=0.02979103371139627, sig=True, Cliff d=0.8472222222222222 (large)
- MASAC vs MATD3: z=-3.703395206350758, p_raw=0.00021273308097789127, p_holm=0.0010636654048894563, sig=True, Cliff d=-1.0 (large)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-1.0 (large)
- HAPPO vs MASAC: d=1.0 (large)
- HAPPO vs MATD3: d=-0.375 (medium)
- MAAC vs MASAC: d=1.0 (large)
- MAAC vs MATD3: d=0.8472222222222222 (large)
- MASAC vs MATD3: d=-1.0 (large)

**Ganador(es)**: ['MAAC'] (primary=MAAC, status=ok)
- Highest KW mean rank: MAAC (Rmean=41.583).
- Dunn-Holm confirms MAAC > MATD3 (p_holm=0.02979103371139627, alpha=0.05).

### OG — sintesis global (E1+E2+E3 como bloques)

**Friedman**: chi2=5.800000000000004, p=0.12175661971125347, W=0.6444444444444449, significativo=False.
Rangos medios Friedman: {'HAPPO': 2.6666666666666665, 'MAAC': 3.0, 'MASAC': 1.0, 'MATD3': 3.3333333333333335}

**Nemenyi**: CD=2.707997260862172 (alpha=0.05)
- HAPPO vs MAAC: |dR|=0.3333333333333335, sig=False
- HAPPO vs MASAC: |dR|=1.6666666666666665, sig=False
- HAPPO vs MATD3: |dR|=0.666666666666667, sig=False
- MAAC vs MASAC: |dR|=2.0, sig=False
- MAAC vs MATD3: |dR|=0.3333333333333335, sig=False
- MASAC vs MATD3: |dR|=2.3333333333333335, sig=False

**TOPSIS (declaracion oficial de ganador)**
- #1 MAAC: C*=0.7609512738416977
- #2 MATD3: C*=0.6566239129395309
- #3 HAPPO: C*=0.6301508596523131
- #4 MASAC: C*=0.0

**Validacion TOPSIS vs Friedman-Nemenyi**
- DISCREPANCY: TOPSIS winner=MAAC, Friedman mean-rank winner=MATD3.
- Nemenyi does not separate TOPSIS vs Friedman winners; treat as co-leading.
- [!] Discrepancia reportada entre TOPSIS y Friedman.