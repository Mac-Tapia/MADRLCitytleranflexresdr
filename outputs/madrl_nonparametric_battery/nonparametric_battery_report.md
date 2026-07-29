# Bateria no parametrica MADRL (HAPPO, MAAC, MASAC, MATD3)

alpha=0.05, complementary=True
expected_n_seeds=12, sample_unit=seed
TOPSIS weights: {'OE.1': 0.3333333333333333, 'OE.2': 0.3333333333333333, 'OE.3': 0.3333333333333333}
TOPSIS criteria kinds: {'OE.1': 'benefit', 'OE.2': 'cost', 'OE.3': 'cost'}

### OE.1 — bateria no parametrica

Orientacion: mayor es mejor.
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 49, 'MAAC': 50, 'MASAC': 50, 'MATD3': 50} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.8942834734916687, p=0.00035935695632360876, normalidad_rechazada=True [ok]
- MAAC: W=0.7530270218849182, p=8.482652447128203e-08, normalidad_rechazada=True [ok]
- MASAC: W=0.7621653079986572, p=1.3063412040992262e-07, normalidad_rechazada=True [ok]
- MATD3: W=0.6874924898147583, p=4.9697614912247445e-09, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=8.958477138459248, p=0.029848080213775673, heterocedasticidad=True.

**Kruskal-Wallis**: H=52.86463058906723, p=1.959331223860867e-11, epsilon^2=0.26699308378316783, significativo=True.
Rangos medios: {'HAPPO': 65.36734693877551, 'MAAC': 145.12, 'MASAC': 105.2, 'MATD3': 83.62}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=-6.889149718622038, p_raw=5.612684466008719e-12, p_holm=3.3676106796052315e-11, sig=True, Cliff d=-0.6644897959183673 (large)
- HAPPO vs MASAC: z=-3.4408022817503334, p_raw=0.0005799921824784429, p_holm=0.0021138675361909824, sig=True, Cliff d=-0.48081632653061224 (large)
- HAPPO vs MATD3: z=-1.5766906162270027, p_raw=0.11486673061368713, p_holm=0.12197162503595116, sig=False, Cliff d=-0.24 (small)
- MAAC vs MASAC: z=3.4658963921249506, p_raw=0.0005284668840477456, p_holm=0.0021138675361909824, sig=True, Cliff d=0.5256 (large)
- MAAC vs MATD3: z=5.339494692276665, p_raw=9.320599835875012e-08, p_holm=4.660299917937506e-07, sig=True, Cliff d=0.628 (large)
- MASAC vs MATD3: z=1.873598300151714, p_raw=0.06098581251797558, p_holm=0.12197162503595116, sig=False, Cliff d=0.2624 (small)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=-0.6644897959183673 (large)
- HAPPO vs MASAC: d=-0.48081632653061224 (large)
- HAPPO vs MATD3: d=-0.24 (small)
- MAAC vs MASAC: d=0.5256 (large)
- MAAC vs MATD3: d=0.628 (large)
- MASAC vs MATD3: d=0.2624 (small)

**Ganador(es)**: ['MAAC'] (primary=MAAC, status=ok)
- Highest KW mean rank: MAAC (Rmean=145.120).
- Dunn-Holm confirms MAAC > MASAC (p_holm=0.0021138675361909824, alpha=0.05).

### OE.2 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 49, 'MAAC': 50, 'MASAC': 50, 'MATD3': 50} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.9332813620567322, p=0.008154917508363724, normalidad_rechazada=True [ok]
- MAAC: W=0.7056064605712891, p=1.0447892329068509e-08, normalidad_rechazada=True [ok]
- MASAC: W=0.7643879652023315, p=1.4532379566389864e-07, normalidad_rechazada=True [ok]
- MATD3: W=0.611748456954956, p=2.921810016154325e-10, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=33.50414943186012, p=2.5210538218983065e-07, heterocedasticidad=True.

**Kruskal-Wallis**: H=23.806380047521955, p=2.7416281510917326e-05, epsilon^2=0.1202342426642523, significativo=True.
Rangos medios: {'HAPPO': 131.6734693877551, 'MAAC': 100.45, 'MASAC': 91.13, 'MATD3': 77.38}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=2.7017734231531807, p_raw=0.006897074520365125, p_holm=0.0275882980814605, sig=True, Cliff d=0.3902040816326531 (medium)
- HAPPO vs MASAC: z=3.508234998293281, p_raw=0.000451090394279833, p_holm=0.002255451971399165, sig=True, Cliff d=0.4220408163265306 (medium)
- HAPPO vs MATD3: z=4.698025412260702, p_raw=2.6268875395750553e-06, p_holm=1.576132523745033e-05, sig=True, Cliff d=0.4546938775510204 (medium)
- MAAC vs MASAC: z=0.8105657317991041, p_raw=0.4176151028011883, p_holm=0.46351381722702123, sig=False, Cliff d=0.1028 (negligible)
- MAAC vs MATD3: z=2.006411097919026, p_raw=0.04481240523080026, p_holm=0.13443721569240077, sig=False, Cliff d=0.2976 (small)
- MASAC vs MATD3: z=1.195845366119922, p_raw=0.23175690861351061, p_holm=0.46351381722702123, sig=False, Cliff d=0.1616 (small)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=0.3902040816326531 (medium)
- HAPPO vs MASAC: d=0.4220408163265306 (medium)
- HAPPO vs MATD3: d=0.4546938775510204 (medium)
- MAAC vs MASAC: d=0.1028 (negligible)
- MAAC vs MATD3: d=0.2976 (small)
- MASAC vs MATD3: d=0.1616 (small)

**Ganador(es)**: ['HAPPO'] (primary=HAPPO, status=ok)
- Highest KW mean rank: HAPPO (Rmean=131.673).
- Dunn-Holm confirms HAPPO > MAAC (p_holm=0.0275882980814605, alpha=0.05).

### OE.3 — bateria no parametrica

Orientacion: menor es mejor (coste/emision).
Unidad de analisis: seed | n_esperado=12 | n_por_algoritmo={'HAPPO': 49, 'MAAC': 50, 'MASAC': 50, 'MATD3': 50} | cobertura_completa=True.

**Shapiro-Wilk (por algoritmo)**
- HAPPO: W=0.8576273918151855, p=2.9542197808041237e-05, normalidad_rechazada=True [ok]
- MAAC: W=0.6491007804870605, p=1.1234708718887987e-09, normalidad_rechazada=True [ok]
- MASAC: W=0.689295768737793, p=5.34453548084457e-09, normalidad_rechazada=True [ok]
- MATD3: W=0.792750895023346, p=5.992915248498321e-07, normalidad_rechazada=True [ok]

**Fligner-Killeen**: estadistico=24.352454674776503, p=2.1085753579708033e-05, heterocedasticidad=True.

**Kruskal-Wallis**: H=48.52985296268235, p=1.6425113687237728e-10, epsilon^2=0.2451002674882947, significativo=True.
Rangos medios: {'HAPPO': 148.79591836734693, 'MAAC': 90.22, 'MASAC': 75.88, 'MATD3': 86.08}

**Dunn post-hoc (Holm)**
- HAPPO vs MAAC: z=5.071266618070802, p_raw=3.951766754623681e-07, p_holm=1.5807067018494724e-06, sig=True, Cliff d=0.6677551020408163 (large)
- HAPPO vs MASAC: z=6.312765946294294, p_raw=2.7409187623179886e-10, p_holm=1.644551257390793e-09, sig=True, Cliff d=0.6718367346938775 (large)
- HAPPO vs MATD3: z=5.429691110319426, p_raw=5.645167290329435e-08, p_holm=2.8225836451647176e-07, sig=True, Cliff d=0.6122448979591837 (large)
- MAAC vs MASAC: z=1.2478174317663575, p_raw=0.2120979234574102, p_holm=0.6362937703722306, sig=False, Cliff d=0.1984 (small)
- MAAC vs MATD3: z=0.36024854724635424, p_raw=0.7186612729784835, p_holm=0.7495453943637778, sig=False, Cliff d=0.0648 (negligible)
- MASAC vs MATD3: z=-0.8875688845200033, p_raw=0.3747726971818889, p_holm=0.7495453943637778, sig=False, Cliff d=-0.108 (negligible)

**Cliff's delta (todos los pares, metrica orientada)**
- HAPPO vs MAAC: d=0.6677551020408163 (large)
- HAPPO vs MASAC: d=0.6718367346938775 (large)
- HAPPO vs MATD3: d=0.6122448979591837 (large)
- MAAC vs MASAC: d=0.1984 (small)
- MAAC vs MATD3: d=0.0648 (negligible)
- MASAC vs MATD3: d=-0.108 (negligible)

**Ganador(es)**: ['HAPPO'] (primary=HAPPO, status=ok)
- Highest KW mean rank: HAPPO (Rmean=148.796).
- Dunn-Holm confirms HAPPO > MAAC (p_holm=1.5807067018494724e-06, alpha=0.05).

### OG — sintesis global (E1+E2+E3 como bloques)

**Friedman**: chi2=3.4000000000000057, p=0.33396524909015995, W=0.37777777777777843, significativo=False.
Rangos medios Friedman: {'HAPPO': 3.3333333333333335, 'MAAC': 3.0, 'MASAC': 2.0, 'MATD3': 1.6666666666666667}

**Nemenyi**: CD=2.707997260862172 (alpha=0.05)
- HAPPO vs MAAC: |dR|=0.3333333333333335, sig=False
- HAPPO vs MASAC: |dR|=1.3333333333333335, sig=False
- HAPPO vs MATD3: |dR|=1.6666666666666667, sig=False
- MAAC vs MASAC: |dR|=1.0, sig=False
- MAAC vs MATD3: |dR|=1.3333333333333333, sig=False
- MASAC vs MATD3: |dR|=0.33333333333333326, sig=False

**TOPSIS (declaracion oficial de ganador)**
- #1 HAPPO: C*=0.9448972536659926
- #2 MAAC: C*=0.12030984787647217
- #3 MATD3: C*=0.10694539923062162
- #4 MASAC: C*=0.08215097939316716

**Validacion TOPSIS vs Friedman-Nemenyi**
- TOPSIS and Friedman agree on winner: HAPPO.