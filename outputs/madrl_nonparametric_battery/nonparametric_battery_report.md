# Bateria no parametrica MADRL (HAPPO, MAAC, MASAC, MATD3)

alpha=0.05, complementary=False
TOPSIS weights: {'OE.1': 0.3333333333333333, 'OE.2': 0.3333333333333333, 'OE.3': 0.3333333333333333}
TOPSIS criteria kinds: {'OE.1': 'benefit', 'OE.2': 'cost', 'OE.3': 'cost'}

### OE.1 — bateria no parametrica

Orientacion: mayor es mejor.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.8819757103919983, p=0.01920420490205288, normalidad_rechazada=True [ok]
- MAAC: W=0.7605104446411133, p=0.00023565547598991543, normalidad_rechazada=True [ok]
- MASAC: W=0.7239064574241638, p=7.741466833977029e-05, normalidad_rechazada=True [ok]
- MATD3: W=0.7720008492469788, p=0.00034006821806542575, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=16.848141701158802, p=0.000759426223739126, heterocedasticidad=True.

**Kruskal-Wallis**: H=21.667423132377607, p=7.649502904148951e-05, epsilon^2=0.2742711788908558, significativo=True.
Rangos medios: {'HAPPO': 31.5, 'MAAC': 59.35, 'MASAC': 42.65, 'MATD3': 28.5}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-3.7901492961571837, p_raw=0.00015055676546665083, p_holm=0.0007527838273332541, sig=True, Cliff d=-0.6 (large)
- HAPPO vs MASAC: z=-1.5174206338295364, p_raw=0.12916051762124447, p_holm=0.25832103524248895, sig=False, Cliff d=-0.43 (medium)
- HAPPO vs MATD3: z=0.40827460999897847, p_raw=0.6830720775260473, p_holm=0.6830720775260473, sig=False, Cliff d=0.13 (negligible)
- MAAC vs MASAC: z=2.2727286623276473, p_raw=0.023042536296064575, p_holm=0.0921701451842583, sig=False, Cliff d=0.57 (large)
- MAAC vs MATD3: z=4.198423906156162, p_raw=2.6877913885150712e-05, p_holm=0.00016126748331090428, sig=True, Cliff d=0.715 (large)
- MASAC vs MATD3: z=1.9256952438285149, p_raw=0.05414243811897638, p_holm=0.16242731435692914, sig=False, Cliff d=0.355 (medium)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-0.6 (large)
- HAPPO vs MASAC: d=-0.43 (medium)
- HAPPO vs MATD3: d=0.13 (negligible)
- MAAC vs MASAC: d=0.57 (large)
- MAAC vs MATD3: d=0.715 (large)
- MASAC vs MATD3: d=0.355 (medium)

**Ganador(es)**: ['MAAC', 'MASAC'] (primary=MAAC, status=cowinners_cliff_tiebreak)
- Highest KW mean rank: MAAC (Rmean=59.350).
- Dunn-Holm vs 2nd (MASAC, Rmean=42.650) not significant (p_holm=0.0921701451842583) -> co-winners.
- Tie-break Cliff's delta(MAAC,MASAC)=0.57 (large); oriented medians MAAC=-0.6136, MASAC=-0.6211.
- Cliff's delta prefers MAAC (report as primary among co-winners).

### OE.2 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9515063166618347, p=0.3905356228351593, normalidad_rechazada=False [ok]
- MAAC: W=0.6611056327819824, p=1.356965094601037e-05, normalidad_rechazada=True [ok]
- MASAC: W=0.7578094005584717, p=0.0002164616307709366, normalidad_rechazada=True [ok]
- MATD3: W=0.688618004322052, p=2.8415404813131317e-05, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=11.498363718067175, p=0.009314845433479624, heterocedasticidad=True.

**Kruskal-Wallis**: H=13.371835297719254, p=0.0038977540506232727, epsilon^2=0.16926373794581334, significativo=True.
Rangos medios: {'HAPPO': 54.85, 'MAAC': 40.5, 'MASAC': 38.35, 'MATD3': 28.3}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=1.9572776605595887, p_raw=0.050314832491662076, p_holm=0.2012593299666483, sig=False, Cliff d=0.44 (medium)
- HAPPO vs MASAC: z=2.2505283205040563, p_raw=0.024415427819357974, p_holm=0.12207713909678987, sig=False, Cliff d=0.435 (medium)
- HAPPO vs MATD3: z=3.621304661174709, p_raw=0.00029312108401560174, p_holm=0.0017587265040936106, sig=True, Cliff d=0.56 (large)
- MAAC vs MASAC: z=0.29325065994446775, p_raw=0.7693305641903496, p_holm=0.7693305641903496, sig=False, Cliff d=0.08 (negligible)
- MAAC vs MATD3: z=1.6640270006151203, p_raw=0.0961070337161986, p_holm=0.28832110114859577, sig=False, Cliff d=0.36 (medium)
- MASAC vs MATD3: z=1.3707763406706526, p_raw=0.17044468846740946, p_holm=0.3408893769348189, sig=False, Cliff d=0.3 (small)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=0.44 (medium)
- HAPPO vs MASAC: d=0.435 (medium)
- HAPPO vs MATD3: d=0.56 (large)
- MAAC vs MASAC: d=0.08 (negligible)
- MAAC vs MATD3: d=0.36 (medium)
- MASAC vs MATD3: d=0.3 (small)

**Ganador(es)**: ['HAPPO', 'MAAC'] (primary=HAPPO, status=cowinners_cliff_tiebreak)
- Highest KW mean rank: HAPPO (Rmean=54.850).
- Dunn-Holm vs 2nd (MAAC, Rmean=40.500) not significant (p_holm=0.2012593299666483) -> co-winners.
- Tie-break Cliff's delta(HAPPO,MAAC)=0.44 (medium); oriented medians HAPPO=-823.7833, MAAC=-1132.6354.
- Cliff's delta prefers HAPPO (report as primary among co-winners).

### OE.3 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.789676308631897, p=0.0006085577770136297, normalidad_rechazada=True [ok]
- MAAC: W=0.634101390838623, p=6.783870503568323e-06, normalidad_rechazada=True [ok]
- MASAC: W=0.6930649876594543, p=3.2128220482263714e-05, normalidad_rechazada=True [ok]
- MATD3: W=0.8345080614089966, p=0.0029642092995345592, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=10.968289262608756, p=0.011898589168029721, heterocedasticidad=True.

**Kruskal-Wallis**: H=15.809115849709771, p=0.0012408782852464052, epsilon^2=0.20011539050265534, significativo=True.
Rangos medios: {'HAPPO': 57.95, 'MAAC': 34.25, 'MASAC': 31.85, 'MATD3': 37.95}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=3.232577042178554, p_raw=0.0012267905088062944, p_holm=0.006133952544031472, sig=True, Cliff d=0.62 (large)
- HAPPO vs MASAC: z=3.559926616070053, p_raw=0.0003709584417610716, p_holm=0.0022257506505664296, sig=True, Cliff d=0.62 (large)
- HAPPO vs MATD3: z=2.7279131157624925, p_raw=0.006373639321403983, p_holm=0.02549455728561593, sig=True, Cliff d=0.505 (large)
- MAAC vs MASAC: z=0.32734957389149894, p_raw=0.7434035013879343, p_holm=1.0, sig=False, Cliff d=0.1 (negligible)
- MAAC vs MATD3: z=-0.5046639264160615, p_raw=0.6137949019062272, p_holm=1.0, sig=False, Cliff d=-0.105 (negligible)
- MASAC vs MATD3: z=-0.8320135003075605, p_raw=0.405401324300674, p_holm=1.0, sig=False, Cliff d=-0.145 (negligible)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=0.62 (large)
- HAPPO vs MASAC: d=0.62 (large)
- HAPPO vs MATD3: d=0.505 (large)
- MAAC vs MASAC: d=0.1 (negligible)
- MAAC vs MATD3: d=-0.105 (negligible)
- MASAC vs MATD3: d=-0.145 (negligible)

**Ganador(es)**: ['HAPPO'] (primary=HAPPO, status=ok)
- Highest KW mean rank: HAPPO (Rmean=57.950).
- Dunn-Holm confirms HAPPO > MATD3 (p_holm=0.02549455728561593, alpha=0.05).

### OG — sintesis global (E1+E2+E3 como bloques)

**Friedman**: chi2=2.6000000000000014, p=0.45748954687818333, W=0.28888888888888903, significativo=False.
Rangos medios Friedman: {'HAPPO': 3.3333333333333335, 'MAAC': 2.6666666666666665, 'MASAC': 2.3333333333333335, 'MATD3': 1.6666666666666667}

**Nemenyi**: CD=2.707997260862172 (alpha=0.05)
- HAPPO vs MAAC: |dR|=0.666666666666667, sig=False
- HAPPO vs MASAC: |dR|=1.0, sig=False
- HAPPO vs MATD3: |dR|=1.6666666666666667, sig=False
- MAAC vs MASAC: |dR|=0.33333333333333304, sig=False
- MAAC vs MATD3: |dR|=0.9999999999999998, sig=False
- MASAC vs MATD3: |dR|=0.6666666666666667, sig=False

**TOPSIS (declaracion oficial de ganador)**
- #1 HAPPO: C*=0.9491414056780454
- #2 MATD3: C*=0.27537217635916017
- #3 MAAC: C*=0.19711358231799558
- #4 MASAC: C*=0.1896383276349491

**Validacion TOPSIS vs Friedman-Nemenyi**
- TOPSIS and Friedman agree on winner: HAPPO.