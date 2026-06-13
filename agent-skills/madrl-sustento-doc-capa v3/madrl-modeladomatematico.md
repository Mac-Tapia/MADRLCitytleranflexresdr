# CAPÍTULO IV
# DISEÑO E IMPLEMENTACIÓN DEL FRAMEWORK UNIVERSAL CITYLEARN v3 MODIFICADO

---

## Resumen del capítulo

Este capítulo desarrolla, formaliza y demuestra la contribución científica central de la tesis: un **framework universal** — denominado **Universal CityLearn v3 Modified (UC3M)** — construido sobre el motor físico de la plataforma CityLearn v3 (Nweye et al., 2024) e integrado nativamente con la librería **MARLlib** (Hu et al., 2023), capaz de (i) implementar y entrenar **cualquier** algoritmo de aprendizaje por refuerzo multi-agente profundo (Multi-Agent Deep Reinforcement Learning, MADRL) bajo el paradigma de Entrenamiento Centralizado con Ejecución Descentralizada (CTDE); (ii) integrar **edificios sin limitaciones tipológicas** —residenciales, comerciales, hospitalarios, industriales, agroindustriales— ubicados en **cualquier zona climática del planeta** —incluidas las regiones extremas del Perú (costa árida, sierra altoandina, selva amazónica) e internacionalmente bajo cualquier categoría Köppen-Geiger; (iii) optimizar simultáneamente **siete ejes operacionales acoplados** (emisiones de CO₂, costo económico, flexibilidad de red, confort térmico, degradación electroquímica, resiliencia ante fallos y eficiencia de agua caliente sanitaria) bajo un esquema de Procesos de Decisión de Markov Parcialmente Observables y Descentralizados (Dec-POMDP) cooperativos generalizados.

La contribución científica original se materializa en: (a) la definición axiomática de un **meta-Dec-POMDP universal** con cardinalidad arbitraria y propiedades topológicas y de medibilidad demostradas; (b) un **operador de recompensa holístico escalarizado** sobre los siete ejes con propiedades de continuidad, Lipschitz, acotamiento y consistencia dimensional probadas formalmente; (c) un **tensor de configuración del entorno** (Building-Asset-Climate Tensor, BACT) que codifica de manera universal cualquier edificio en cualquier sitio; (d) un **teorema de invariancia geográfica-climática** que garantiza la portabilidad del framework entre zonas Köppen-Geiger; (e) una **arquitectura de plugins algorítmicos** que demuestra la universalidad MADRL del marco; (f) un **índice de Pareto holístico 7-D normalizado** (Holistic Pareto Hypervolume Index, HPHI) como métrica original de evaluación multi-objetivo; (g) **teoremas originales** sobre existencia de la frontera de Pareto, equilibrios de Nash cooperativos y convergencia bajo no-estacionariedad multi-agente.

---

## Índice del capítulo

- 4.1. Introducción y posicionamiento epistémico
- 4.2. Formalización matemática universal del Meta-Dec-POMDP
- 4.3. Modelado físico-matemático profundo de los siete ejes operacionales
- 4.4. Arquitectura MARLlib-CTDE y universalidad algorítmica MADRL
- 4.5. Ecuaciones físicas detalladas de los activos distribuidos
- 4.6. Universalidad geográfica: integración Perú-internacional-mundial
- 4.7. Métricas originales: HPHI y consistencia multiobjetivo
- 4.8. Metodología experimental doctoral
- 4.9. Contextualización con el estado del arte
- 4.10. Síntesis, aportes científicos y discusión preliminar

---

## 4.1. Introducción y posicionamiento epistémico

### 4.1.1. Motivación científica y vacíos en la literatura

La transición energética hacia comunidades de edificios netamente positivos exige el diseño de sistemas de control que coordinen, en tiempo real y con observabilidad parcial, decenas a miles de activos heterogéneos distribuidos: sistemas fotovoltaicos, baterías estacionarias de ión-litio, baterías de fosfato de hierro y litio (LFP), de sodio-ión y de flujo, vehículos eléctricos con tecnología Vehicle-to-Grid (V2G), Vehicle-to-Home (V2H) y Vehicle-to-Building (V2B), bombas de calor aerotérmicas y geotérmicas, almacenamiento térmico de agua caliente sanitaria (ACS), almacenamiento de hielo y, prospectivamente, hidrógeno verde producido por electrolizadores PEM o alcalinos. La literatura ha identificado el aprendizaje por refuerzo profundo multi-agente (Multi-Agent Deep Reinforcement Learning, MADRL) como la familia de métodos más promisoria para esta tarea, gracias a su capacidad para operar sin un modelo explícito del entorno, escalar a alta dimensionalidad y descentralizar la ejecución preservando la privacidad de los usuarios (Vázquez-Canteli y Nagy, 2019, *Applied Energy* 235:1072–1089; Nweye et al., 2022, *Energy and AI* 10:100202).

Sin embargo, una revisión sistemática del estado del arte revela cuatro **vacíos críticos** que impiden la traducción de la investigación MARL en infraestructura desplegable:

1. **Vacío de universalidad algorítmica.** Los benchmarks existentes — CityLearn v1 (Vázquez-Canteli et al., 2019), CityLearn v2 (Nweye et al., 2024, *Journal of Building Performance Simulation* 18(1)), GridLearn (Pigott et al., 2022, *Electric Power Systems Research* 213:108521), PowerGridworld (Biagioni et al., 2022, *e-Energy'22*), COHORT (Jia et al., 2021, *BuildSys'21*) — proveen únicamente un conjunto restringido de algoritmos preimplementados (típicamente SAC, MADDPG o variantes de Q-learning). No definen una **interfaz matemática abstracta** que permita enchufar cualquier algoritmo MADRL futuro.
2. **Vacío de universalidad geográfica.** Los datasets oficiales se centran en climas templados de Norteamérica y Europa. Las particularidades de los climas extremos —el frío altoandino con escarcha y baja densidad del aire del altiplano peruano (3 800–4 200 msnm en Puno), el tropical húmedo con condensación masiva de la selva amazónica (Iquitos, 28 °C medios anuales, 85% de humedad relativa), el desértico árido de Lima con su característica humedad costera— quedan fuera del scope.
3. **Vacío en el modelado multiobjetivo.** Las funciones de recompensa de los benchmarks vigentes combinan típicamente entre uno y ocho objetivos sin formalizar las propiedades matemáticas de la escalarización ni las condiciones de existencia y unicidad de la frontera de Pareto. El presente trabajo formaliza **siete ejes operacionales** con derivación física rigurosa, KPIs cuantitativos y un teorema de invariancia geográfica.
4. **Vacío en garantías formales de convergencia.** Salvo trabajos puntuales (Kuba et al., 2022, ICLR, arXiv:2109.11251; Zhong et al., 2023, JMLR), no existe en la literatura aplicada a edificios un cuerpo de teoremas que garantice la convergencia MARL bajo no-estacionariedad inducida por la coevolución de políticas.

### 4.1.2. Posicionamiento de la contribución

El framework **UC3M** que se desarrolla en este capítulo cubre los cuatro vacíos mediante (i) la formalización axiomática de un **meta-Dec-POMDP universal** (§4.2); (ii) el modelado físico-matemático profundo de los siete ejes (§4.3); (iii) la **arquitectura de plugins MADRL** que demuestra universalidad algorítmica (§4.4); (iv) los modelos físicos de activos distribuidos (§4.5); (v) la formalización de la **universalidad geográfica** mediante un teorema de invariancia Köppen-Geiger y casos de uso Perú (§4.6); (vi) la métrica original **Holistic Pareto Hypervolume Index (HPHI)** (§4.7); y (vii) la metodología experimental con análisis estadístico riguroso (§4.8).

---

## 4.2. Formalización matemática universal del Meta-Dec-POMDP

### 4.2.1. La tupla universal generalizada

Sea $\mathbb{B}$ el conjunto universal de todas las edificaciones posibles (cualquier tipología, cualquier ubicación geográfica). Para un subconjunto finito arbitrario $\mathcal{C}\subset\mathbb{B}$ con $|\mathcal{C}|=N\in\mathbb{N}^+$ que constituye la **comunidad energética**, definimos el **Meta-Dec-POMDP universal** como la **tupla 11-aria**

$$
\boxed{\;\mathcal{M}_{\mathrm{UC3M}} = \langle \mathcal{I},\ \mathcal{S},\ \mathcal{A},\ \mathcal{O},\ \mathcal{T},\ \mathcal{R},\ \mathcal{Z},\ \gamma,\ H,\ b_0,\ \boldsymbol{\Lambda}\rangle\;}
$$

donde, siguiendo y extendiendo la formulación canónica de Oliehoek y Amato (2016, *A Concise Introduction to Decentralized POMDPs*, Springer):

- $\mathcal{I}=\{1,\ldots,N\}$ es el conjunto de **agentes** con cardinalidad arbitraria;
- $\mathcal{S}\subset\mathbb{R}^{d_s}$ es el **espacio de estados globales** (oculto en ejecución);
- $\mathcal{A}=\prod_{i\in\mathcal{I}}\mathcal{A}_i$ es el **espacio de acciones conjuntas**, con $\mathcal{A}_i\subset\mathbb{R}^{d_{a_i}}$ continuo y acotado;
- $\mathcal{O}=\prod_{i\in\mathcal{I}}\mathcal{O}_i$ es el **espacio de observaciones parciales**, con $\mathcal{O}_i\subset\mathbb{R}^{d_{o_i}}$;
- $\mathcal{T}:\mathcal{S}\times\mathcal{A}\to\Delta(\mathcal{S})$ es el **núcleo de transición estocástico**;
- $\mathcal{R}=(r^{(1)},\ldots,r^{(7)})$ es el **vector de funciones de recompensa por eje** (siete componentes);
- $\mathcal{Z}:\mathcal{S}\times\mathcal{A}\to\Delta(\mathcal{O})$ es la **función de emisión de observaciones**;
- $\gamma\in[0,1)$ es el **factor de descuento** (fijado en $\gamma=0{,}99$ para horizonte efectivo $\approx 100\,$h);
- $H\in\mathbb{N}^+$ es el **horizonte temporal** (típicamente $H=8\,760$ horas/año);
- $b_0\in\Delta(\mathcal{S})$ es la **distribución inicial de estados**;
- $\boldsymbol{\Lambda}=(\lambda_1,\ldots,\lambda_7)\in\Delta^{6}$ es el **simplex de ponderaciones de escalarización** de los siete ejes.

> **Observación 4.1.** La novedad respecto al Dec-POMDP estándar (Bernstein et al., 2002, *Mathematics of Operations Research*; Oliehoek y Amato, 2016) consiste en (a) reemplazar la recompensa escalar única $R$ por un vector $\mathcal{R}$ de siete componentes acopladas; (b) añadir explícitamente el simplex $\boldsymbol{\Lambda}$, transformando el problema en un **MOMDP cooperativo descentralizado y parcialmente observable** (MO-Dec-POMDP); (c) garantizar la independencia respecto a $N$ mediante el esquema de policy mapping de MARLlib.

### 4.2.2. Tensor de configuración del entorno (Building-Asset-Climate Tensor, BACT)

Para garantizar la universalidad tipológica y geográfica se introduce un objeto matemático nuevo:

**Definición 4.1 (BACT).** Para una comunidad $\mathcal{C}$ con $N$ edificios, el Building-Asset-Climate Tensor es

$$
\mathcal{B}\in\mathbb{R}^{N\times K_a\times K_c\times K_b},
$$

donde $K_a$ es el número de tipos de activos disponibles (PV, BESS, EV, HP, EH, ACS, eólica, H₂, etc.), $K_c$ es la dimensión del descriptor climático del sitio (latitud, longitud, altitud, zona Köppen, TMY-EPW índices), y $K_b$ es la dimensión del descriptor constructivo (transmitancias térmicas $U$ de muros/cubiertas/ventanas, capacidades térmicas $C$, factores solares $g$, infiltración, tipología vernácula/moderna).

La componente $\mathcal{B}_{i,a,c,b}$ codifica el atributo $b$ del activo $a$ del edificio $i$ bajo el clima $c$. El BACT es el **descriptor universal** que permite al framework integrar cualquier edificio en cualquier lugar.

### 4.2.3. Vector de observaciones parciales locales

En cada paso de tiempo $t\in\{0,1,\ldots,H\}$ el agente $i$ recibe

$$
o_{i,t} = \big(o_{i,t}^{\text{ld}},\ o_{i,t}^{\text{th}},\ o_{i,t}^{\text{gen}},\ o_{i,t}^{\text{stor}},\ o_{i,t}^{\text{mov}},\ o_{i,t}^{\text{tar}},\ o_{i,t}^{\text{emi}},\ o_{i,t}^{\text{met}}\big),
$$

con:
- $o_{i,t}^{\text{ld}} = P_i^{\text{load,fix}}(t)$ — potencia de carga eléctrica básica no gestionable [kW];
- $o_{i,t}^{\text{th}} = (Q_i^{\text{clim}}(t),\,Q_i^{\text{ACS}}(t),\,T_i^{\text{int}}(t))$ — demandas térmicas (climatización y ACS) y temperatura interior;
- $o_{i,t}^{\text{gen}} = P_i^{\text{PV}}(t)$ — generación fotovoltaica instantánea [kW];
- $o_{i,t}^{\text{stor}} = (\mathrm{SoC}_i^{\text{BESS}}(t),\,\mathrm{SoC}_i^{\text{EV}}(t),\,T_i^{\text{tank}}(t))$ — estados de carga del BESS estacionario, del EV y nivel térmico del tanque ACS;
- $o_{i,t}^{\text{mov}} = \mathbb{1}_{\text{plug},i}(t)\in\{0,1\}$ — indicador binario estocástico de acoplamiento físico del vehículo al cargador;
- $o_{i,t}^{\text{tar}} = p_t^{\text{imp/exp}}$ — tarifa eléctrica comercial dinámica de importación/exportación [€/kWh];
- $o_{i,t}^{\text{emi}} = \xi_t^{\text{CO}_2}$ — intensidad de carbono dinámica de la red [kgCO₂eq/kWh];
- $o_{i,t}^{\text{met}} = (T_t^{\text{out}},\,\varphi_t,\,G_t,\,v_t^{\text{w}})$ — subvector meteorológico: temperatura de bulbo seco, humedad relativa, radiación global horizontal y velocidad del viento.

### 4.2.4. Vector de acciones continuas multidimensionales

Cada agente opera sobre variables de control continuas acotadas:

$$
a_{i,t}=\big(a_i^{\text{BESS}}(t),\ a_i^{\text{EV}}(t),\ a_i^{\text{ACS}}(t),\ a_i^{\text{HP}}(t),\ a_i^{\text{EH}}(t)\big)\in[-1,1]^{d_{a_i}},
$$

con normalización estándar:
- $a_i^{\text{BESS}}(t)\in[-1,1]$ gobierna el flujo del BESS (positivo: carga; negativo: descarga);
- $a_i^{\text{EV}}(t)\in[-1,1]$ controla la inyección bidireccional V2G, sujeto a $\mathbb{1}_{\text{plug},i}(t)=1$;
- $a_i^{\text{ACS}}(t)\in[-1,1]$ regula el almacenamiento térmico de ACS;
- $a_i^{\text{HP}}(t)\in[0,1]$ modula la bomba de calor;
- $a_i^{\text{EH}}(t)\in[0,1]$ modula el calentador eléctrico.

> **Observación 4.2.** La dimensión $d_{a_i}$ es **variable por agente** —un edificio sin EV no instancia $a_i^{\text{EV}}$—; la arquitectura MARLlib (§4.4) gestiona esta heterogeneidad mediante *policy mapping* personalizado, dando soporte natural a comunidades con dotaciones de activos asimétricas.

### 4.2.5. Propiedades topológicas y de medibilidad

**Proposición 4.1 (Compacidad del espacio global).** *El espacio de estados $\mathcal{S}$ es un subconjunto compacto de $\mathbb{R}^{d_s}$ bajo la topología euclídea estándar.*

*Demostración.* Cada componente de $\mathcal{S}$ es físicamente acotada por restricciones operacionales o termodinámicas:
- Temperaturas climáticas en $[-30,+50]\,$°C (rango planetario);
- Radiaciones solares en $[0,1\,500]\,$W/m² (constante solar TOA aproximada);
- Humedades relativas en $[0,100]\,\%$;
- Estados de carga normalizados en $[0,1]$;
- Temperaturas interiores en $[10,35]\,$°C (rango habitabilidad);
- Temperaturas del tanque ACS en $[10,90]\,$°C;
- Precios marginales en $[p_{\min},p_{\max}]$ con $p_{\max}<\infty$;
- Factores de emisión en $[0,\xi_{\max}]$ con $\xi_{\max}\leq 1{,}1\,$kgCO₂eq/kWh.

El producto cartesiano de conjuntos compactos en $\mathbb{R}$ es compacto en $\mathbb{R}^{d_s}$ por el teorema de Tijonov en su versión finita (Munkres, 2000, *Topology*, Prentice Hall). $\blacksquare$

**Lema 4.2 (Medibilidad y acotación de la recompensa).** *Si cada $r^{(k)}:\mathcal{S}\times\mathcal{A}\to\mathbb{R}$ es continua para $k=1,\ldots,7$, entonces la recompensa escalarizada $R(s,\mathbf{a})=-\sum_{k=1}^7\lambda_k\,r^{(k)}(s,\mathbf{a})$ es Borel-medible y acotada $|R|\leq M<\infty$.*

*Demostración.* Toda función continua sobre un espacio métrico es Borel-medible. La suma finita de funciones Borel-medibles es Borel-medible. Como $\mathcal{S}\times\mathcal{A}$ es compacto (Prop. 4.1), $R$ alcanza máximo y mínimo, por tanto $|R|\leq M$. La integrabilidad respecto a cualquier medida $\mu\in\Delta(\mathcal{S}\times\mathcal{A})$ se sigue de $|\int R\,d\mu|\leq M$. $\blacksquare$

### 4.2.6. Núcleo de transición factorizado con justificación física

Definimos el núcleo $\mathcal{T}(s'\mid s,\mathbf{a})$ con factorización exógena-endógena:

$$
\mathcal{T}(s'\mid s,\mathbf{a})=\underbrace{P_{\text{ex}}\big(s'_{\text{clim}},s'_{\text{grid}}\mid s_{\text{clim}},s_{\text{grid}}\big)}_{\text{componente exógena}}\;\prod_{i=1}^N\underbrace{P_i^{\text{loc}}\big(s'^{\text{loc}}_i\mid s^{\text{loc}}_i,a_i,s'_{\text{clim}}\big)}_{\text{componente endógena}}.
$$

**Justificación física.** La factorización refleja: (a) los activos $i\neq j$ no se acoplan directamente en su dinámica interna, sino únicamente a través de la red mediante las leyes de Kirchhoff (§4.5.1); (b) la termodinámica exterior (clima) es común a todos los edificios del sitio; (c) la dinámica climática es markoviana de orden 1 a paso horario, en línea con la aproximación TMY ampliamente validada en simulación energética (Crawley et al., 2001, *Energy and Buildings* 33(4):319–331).

### 4.2.7. Operador de recompensa holístico escalarizado

**Definición 4.2 (Operador holístico).** Para cada agente $i$:

$$
\boxed{\;R_i(s,\mathbf{a})\;=\;-\sum_{k=1}^{7}\lambda_k\,\tilde r_i^{(k)}(s,\mathbf{a}),\quad \lambda_k\geq 0,\quad \sum_{k=1}^7\lambda_k=1\;}
$$

con normalización a la base RBC: $\tilde r_i^{(k)}=r_i^{(k)}/r_i^{(k),\text{base}}$.

**Teorema 4.3 (Consistencia escalarizada del operador holístico).** *Sea $r^{(k)}_i$ acotada y Borel-medible para todo $k\in\{1,\ldots,7\}$. Entonces, para toda política estacionaria $\pi$ que induzca medida de ocupación $\rho_\pi$ sobre $\mathcal{S}\times\mathcal{A}$, el valor descontado*

$$
V_\pi(s_0)=\mathbb{E}_{\rho_\pi}\!\left[\sum_{t=0}^{H}\gamma^t R(s_t,\mathbf{a}_t)\,\Big|\,s_0\right]
$$

*existe, es finito, y $|V_\pi(s_0)|\leq M/(1-\gamma)$.*

*Demostración.* Por Lema 4.2, $R$ es medible y acotada por $M$. La serie geométrica $\sum_{t=0}^\infty\gamma^t M$ converge a $M/(1-\gamma)$ para $\gamma<1$. Por el teorema de convergencia dominada de Lebesgue (Royden, 1988, *Real Analysis*, Macmillan, Cap. 4), $V_\pi$ está bien definido. $\blacksquare$

**Proposición 4.4 (Propiedades de Lipschitz).** *Si cada $r^{(k)}$ es $L_k$-Lipschitz respecto a $(s,\mathbf{a})$ en la métrica euclídea, entonces $R$ es $L$-Lipschitz con $L=\sum_{k=1}^7\lambda_k L_k$.*

*Demostración.* $|R(s,\mathbf{a})-R(s',\mathbf{a}')|\leq\sum_k\lambda_k|r^{(k)}(s,\mathbf{a})-r^{(k)}(s',\mathbf{a}')|\leq\sum_k\lambda_k L_k\|(s,\mathbf{a})-(s',\mathbf{a}')\|$. $\blacksquare$

### 4.2.8. Frontera de Pareto 7-dimensional

El problema multi-objetivo subyacente es

$$
\min_{\pi\in\Pi}\mathbf{J}(\pi)=\big(J_1(\pi),\ldots,J_7(\pi)\big),\quad J_k(\pi)=\mathbb{E}_{\rho_\pi}\!\left[\sum_t\gamma^t r^{(k)}\right].
$$

**Definición 4.3 (Pareto-dominancia).** $\pi^\star\preceq_P\pi'$ si y solo si $J_k(\pi^\star)\leq J_k(\pi')\,\forall k$ con al menos una desigualdad estricta. El conjunto Pareto óptimo es $\mathcal{P}=\{\pi\in\Pi:\nexists\pi'\in\Pi,\;\pi'\preceq_P\pi\}$.

**Teorema 4.5 (Existencia de la frontera de Pareto).** *Si $\Pi$ es compacto en una topología que hace continuas a las $J_k$ —por ejemplo, el espacio de políticas neuronales con pesos en una bola compacta y activaciones Lipschitz— entonces $\mathbf{J}(\Pi)\subset\mathbb{R}^7$ es compacto y $\mathbf{J}(\mathcal{P})\neq\emptyset$.*

*Esbozo de demostración.* La imagen continua de un compacto es compacta. Un compacto en $\mathbb{R}^7$ con orden parcial componente-a-componente admite mínimos (lema de Zorn aplicado al orden de Pareto invertido). $\blacksquare$

> **Nota epistémica.** El Teorema 4.5 es lo más fuerte que cabe demostrar en este nivel: garantiza existencia de la frontera, no unicidad ni cardinalidad. La escalarización lineal solo barre la **envolvente convexa** de $\mathbf{J}(\Pi)$ al variar $\boldsymbol\lambda\in\Delta^6$ (Roijers et al., 2013, *Journal of Artificial Intelligence Research* 48:67–113). Para regiones no convexas el UC3M ofrece escalarizaciones alternativas (Tchebycheff, $\varepsilon$-restricción, hipervolumen — Vamplew et al., 2011, *Machine Learning* 84(1-2):51–80).

### 4.2.9. Equilibrios de Nash cooperativos

En el régimen cooperativo ($R_i\equiv R$) el Dec-POMDP es un juego markoviano de equipo. Una política conjunta $\boldsymbol\pi^\star=(\pi_1^\star,\ldots,\pi_N^\star)$ es **equilibrio de Nash** si

$$
V_i(\boldsymbol\pi^\star)\geq V_i(\pi_i,\boldsymbol\pi_{-i}^\star),\quad\forall\pi_i\in\Pi_i,\;\forall i\in\mathcal{I}.
$$

**Teorema 4.6 (Convergencia monótona en HAPPO/HAML).** *Bajo las hipótesis de Zhong et al. (2023, JMLR, arXiv:2304.09870): (H1) $\mathcal{S}$ compacto, (H2) recompensa acotada y Lipschitz, (H3) políticas parametrizadas en clase $\mathcal{C}^1$, (H4) $\gamma<1$, los algoritmos HATRPO/HAPPO inducidos por el operador HAML garantizan mejora monótona del valor conjunto y convergen a un equilibrio de Nash de orden superior.*

La demostración descansa en el **Multi-Agent Advantage Decomposition Lemma** (Kuba et al., 2022, ICLR, arXiv:2109.11251), reproducido aquí:

$$
A^{\boldsymbol\pi}_{i_{1:N}}(s,\mathbf{a})=\sum_{m=1}^N A^{\boldsymbol\pi}_{i_m}(s,a_{i_{1:m-1}},a_{i_m}),
$$

que descompone la ventaja conjunta como suma de ventajas marginales secuenciales y permite la actualización por permutación aleatoria que caracteriza a HAPPO.

### 4.2.10. No-estacionariedad y condiciones de convergencia genéricas

Desde la perspectiva del agente $i$, el entorno cambia a medida que los demás actualizan sus políticas:

$$
P^{(i)}(o_i'\mid o_i,a_i;\boldsymbol\pi_{-i}^{(\tau)})\neq P^{(i)}(o_i'\mid o_i,a_i;\boldsymbol\pi_{-i}^{(\tau+1)}),
$$

violando la hipótesis markoviana del RL estándar.

**Proposición 4.7 (Mitigación CTDE).** *Bajo CTDE, donde el crítico se condiciona sobre $(s,\mathbf{a})$, la no-estacionariedad desde la perspectiva del optimizador se elimina: el objetivo de aprendizaje del crítico es estacionario respecto a las políticas conjuntas instantáneas.*

**Condiciones suficientes de convergencia genéricas** (síntesis del UC3M):

1. Tasas de Robbins–Monro: $\sum_\tau\alpha_\tau=\infty,\ \sum_\tau\alpha_\tau^2<\infty$;
2. Muestreo i.i.d. del replay buffer (off-policy) o ventanas suficientemente largas (on-policy);
3. Regularización entrópica (MASAC) o objetivo de margen de confianza (HATRPO/HAPPO);
4. Suavizado de política objetivo (MATD3, target smoothing);
5. Actualización secuencial con factor de corrección $M$ (HAPPO);
6. Sincronía polyak de redes objetivo con $\tau\in[10^{-3},10^{-2}]$.

---

## 4.3. Modelado físico-matemático profundo de los siete ejes operacionales

### 4.3.1. Eje 1 — Emisiones netas de CO₂ (con descarbonización del transporte)

**Derivación física.** El balance instantáneo de emisiones de la comunidad combina las emisiones indirectas debidas a la importación de electricidad de la red, las emisiones evitadas por exportación de excedentes renovables y la **descarbonización del transporte urbano** lograda por el vehículo eléctrico (combustible fósil que el EV evitó quemar mediante su uso):

$$
\boxed{\;\dot E_{\mathrm{CO}_2}^{(i)}(t)=\xi_t^{\text{marg}}\,\max\!\big(0,\,P_i^{\text{net}}(t)\big)-\xi_t^{\text{disp}}\,\max\!\big(0,\,-P_i^{\text{net}}(t)\big)-\xi^{\text{ff}}\,E_i^{\text{ev,disp}}(t)\;}
$$

con:
- $\xi_t^{\text{marg}}$ [kgCO₂eq/kWh]: factor de emisión **marginal** horario del mix eléctrico (Electricity Maps API, ENTSO-E, REE para España, COES Perú);
- $\xi_t^{\text{disp}}$: factor de emisión desplazada por exportación;
- $\xi^{\text{ff}}\approx 2{,}31\,$kgCO₂/L: factor de emisión del combustible fósil sustituido (gasolina, IPCC AR6 WG III, 2022, Cap. 6);
- $E_i^{\text{ev,disp}}(t)$ [L]: combustible fósil equivalente que el EV evitó quemar.

La energía neta extraída se obtiene del balance Kirchhoff (§4.5.1):

$$
P_i^{\text{net}}(t)=P_i^{\text{load,fix}}(t)+P_i^{\text{HP}}(t)+P_i^{\text{EH}}(t)+P_i^{\text{BESS}}(t)+P_i^{\text{EV}}(t)-P_i^{\text{PV}}(t).
$$

**Definición original (Lema 4.1).** *La intensidad neta de carbono de la comunidad (Net Community Carbon Intensity, NCCI) se define como*

$$
\mathrm{NCCI}=\frac{\sum_{i=1}^N\int_0^H\dot E_{\mathrm{CO}_2}^{(i)}(t)\,dt}{\sum_{i=1}^N\int_0^H P_i^{\text{cons}}(t)\,dt},\quad [\mathrm{kgCO_2eq/MWh}].
$$

*Esta métrica permite comparar comunidades de cualquier tamaño y ubicación bajo una base común.*

**Análisis de sensibilidad.** Variación $\pm 10\%$ en $\xi^{\text{marg}}$ propaga linealmente $\pm 10\%$ a las emisiones anuales (linealidad de la integral). El uso de factor marginal vs. promedio puede introducir sesgo de $\pm 30\%$ (Hawkes, 2010, *Energy Policy* 38(10):5977–5987).

**Condiciones de contorno.** $\xi^{\text{marg}}\geq 0$; en límite renovable $\xi\to 0$.

**KPIs cuantitativos del Eje 1.**

| Símbolo | Definición | Unidad | Rango típico |
|---------|------------|--------|--------------|
| NCCI | Net Community Carbon Intensity | kgCO₂eq/MWh | 50–800 |
| $\xi^{\text{marg}}$ | Factor de emisión marginal | kgCO₂eq/MWh | 100–900 |
| $\Delta E_{\mathrm{CO}_2}^{\text{ev}}$ | Emisiones evitadas vs. baseline | tCO₂eq/año | 1–50 |
| $G$ | KPI normalizado CityLearn | — | objetivo $<1$ |
| $\eta_{\text{disp}}^{\text{ev}}$ | Eficiencia de desplazamiento EV | kgCO₂/km | 0,05–0,12 |

---

### 4.3.2. Eje 2 — Costo económico operacional distribuido

**Derivación.** Bajo estructura tarifaria parametrizable en el tiempo (Real Decreto 244/2019 España; OSINERGMIN Perú):

$$
\boxed{\;\dot C^{(i)}(t)=p_t^{\text{imp}}\,\max(0,P_i^{\text{net}}(t))-p_t^{\text{exp}}\,\max(0,-P_i^{\text{net}}(t))+p^{\text{pot}}\,\max_t P_i^{\text{net}}\;}
$$

donde el tercer término modela la **componente fija por potencia contratada** característica de las tarifas industriales y comerciales (€/kW·mes).

**Costo Nivelado de Almacenamiento (LCOS, Levelized Cost of Storage):**

$$
\mathrm{LCOS}=\frac{\mathrm{CAPEX}+\sum_{t=1}^{T}\mathrm{OPEX}_t/(1+r)^t}{\sum_{t=1}^T E_t/(1+r)^t},\quad [\mathrm{€/MWh}],
$$

con tasa de descuento $r\in[5\%,7\%]$ (IRENA, 2023). El **payback** $T_{\mathrm{PB}}$ y el **valor presente neto** NPV son métricas estándar de evaluación económica.

**KPIs cuantitativos del Eje 2.**

| Símbolo | Definición | Unidad |
|---------|------------|--------|
| $C^{\text{anual}}$ | Costo neto anual | €/año |
| LCOS | Costo nivelado de almacenamiento | €/MWh |
| $\rho_{C/S}$ | Ratio costo/ahorro vs. baseline | — |
| $T_{\mathrm{PB}}$ | Payback period | años |
| NPV | Valor presente neto | € |
| $\varepsilon_p$ | Elasticidad-precio implícita del controlador | — |

---

### 4.3.3. Eje 3 — Flexibilidad y estabilidad de la infraestructura de red

Sea $P^{\text{com}}(t)=\sum_{i=1}^N P_i^{\text{net}}(t)$ el perfil agregado. El operador holístico de flexibilidad es

$$
\boxed{\;r^{(3)}(t)=\beta_1\big(P^{\text{com}}(t)-P^{\text{com}}(t-1)\big)^2+\beta_2\max\!\big(0,P^{\text{com}}(t)-P^{\text{lim}}_{\text{DSO}}\big)^2\;}
$$

con el primer término penalizando el **ramping** y el segundo penalizando los picos respecto al umbral $P^{\text{lim}}_{\text{DSO}}$ fijado por la empresa distribuidora.

**Métricas estándar.**

$$
\mathrm{PAR}=\frac{\max_t P^{\text{com}}(t)}{\langle P^{\text{com}}\rangle_t},\quad \mathrm{LF}=1/\mathrm{PAR},
$$

$$
\mathrm{Ramp}=\frac{1}{H}\sum_{t=1}^H|P^{\text{com}}(t)-P^{\text{com}}(t-1)|,\quad \mathrm{DPR}=1-\frac{\langle\max_{h\in d}P^{\text{com}}(h)\rangle_d}{\langle\max_{h\in d}P^{\text{com,base}}(h)\rangle_d}.
$$

**Conexión normativa.** IEEE 1547-2018, Reglamento (UE) 2016/1388 (*Network Code on Demand Connection*); Norma Técnica de Calidad de los Servicios Eléctricos (NTCSE) Perú; Código Nacional de Electricidad (NEC) Perú; OSINERGMIN.

**KPIs cuantitativos del Eje 3.**

| Símbolo | Unidad | Rango típico |
|---------|--------|--------------|
| PAR | — | 1,4–3,5 |
| LF | — | 0,28–0,70 |
| Ramp | kW/h | 5–80 |
| DPR | — | 0,1–0,4 |

---

### 4.3.4. Eje 4 — Confort térmico de los usuarios (con tropicalización)

**Formulación clásica.** PMV-PPD de Fanger (1970, *Thermal Comfort*) codificado en ASHRAE 55-2020 e ISO 7730:2005:

$$
\mathrm{PMV}=[0{,}303\,e^{-0{,}036M}+0{,}028]\cdot L(M,T_a,T_r,v_a,\varphi,I_{\text{cl}}),
$$

$$
\mathrm{PPD}=100-95\exp\!\big(-0{,}03353\,\mathrm{PMV}^4-0{,}2179\,\mathrm{PMV}^2\big).
$$

**Penalización cuadrática del UC3M:**

$$
\boxed{\;r^{(4),i}(t)=\big[\max(0,T_i^{\text{int}}(t)-T^{\text{up}}_{\text{adapt}})\big]^2+\big[\max(0,T^{\text{low}}_{\text{adapt}}-T_i^{\text{int}}(t))\big]^2\;}
$$

**Innovación: bandas adaptativas de De Dear-Brager (1998, *ASHRAE Transactions* 104(1):145–167; Brager y de Dear, 2001) para climas tropicales y vernáculos:**

$$
T^{\text{neutral}}_{\text{adapt}}(t)=0{,}31\,T^{\text{pma}}_t+17{,}8\quad [\mathrm{°C}],
$$

donde $T^{\text{pma}}_t$ es la media mensual ponderada de temperatura exterior. Las bandas son $T^{\text{up/low}}_{\text{adapt}}=T^{\text{neutral}}_{\text{adapt}}\pm 2{,}5\,$°C (80% aceptabilidad) o $\pm 3{,}5\,$°C (90%).

> **Aporte original al Eje 4.** El UC3M es el primer framework MARL que incorpora el modelo adaptativo De Dear-Brager para zonas tropicales (Iquitos, Tarapoto) y climas extremos altoandinos (Puno, Cusco), reconociendo que ASHRAE 55 estática introduce sesgo sistemático en estos contextos.

**KPIs cuantitativos del Eje 4.**

| Símbolo | Definición | Unidad |
|---------|------------|--------|
| PMV | Voto medio predicho | — |
| PPD | Porcentaje insatisfechos | % |
| DH | Grados-hora de disconfort | °C·h |
| $U$ | Unmet hours CityLearn | — |
| $\Delta T^{\text{adapt}}$ | Desviación respecto banda adaptativa | °C |

---

### 4.3.5. Eje 5 — Degradación macroscópica de activos electroquímicos

**Derivación electroquímica con cinética de Arrhenius.** La degradación de baterías Li-ion combina (a) componente calendárica (crecimiento difusivo de la capa SEI en el ánodo de grafito), (b) componente cíclica (fatiga del electrodo), y (c) efecto térmico acelerado.

**Crecimiento de la capa SEI** (modelo Tafel-Arrhenius; Bloom et al., 2001, *J. Power Sources* 101(2):238–247):

$$
Q_{\text{loss}}^{\text{cal}}(t)=A_0\exp\!\left(-\frac{E_a}{R\,T_{\text{cell}}}\right)t^{\,0{,}5},
$$

con $E_a\in[24,80]\,$kJ/mol (energía de activación de la SEI), $R=8{,}314\,$J/(mol·K) y $T_{\text{cell}}$ temperatura absoluta de la celda. La dependencia $t^{1/2}$ es la signature del crecimiento difusivo.

**Degradación por ciclado** (ley de Peukert + fatiga; Wang et al., 2011, *J. Power Sources* 196(8):3942–3948):

$$
Q_{\text{loss}}^{\text{cyc}}(N_{\text{eq}})=B_0\,N_{\text{eq}}^{\alpha}\,f(\mathrm{DoD}),
$$

con $\alpha\approx 0{,}55$, $f(\mathrm{DoD})\propto\mathrm{DoD}^2$, y los ciclos equivalentes por throughput

$$
N_{\text{eq}}=\frac{1}{2Q_{\text{nom}}}\int_0^t |I(\tau)|\,d\tau.
$$

**Formulación del UC3M (Eje 5):**

$$
\boxed{\;r^{(5),i}(t)=\frac{C^{\text{rep},i}}{N^{\text{nom},i}_{\text{cyc}}}\exp\!\left[\beta_T\!\left(\frac{1}{T^{\text{opt}}}-\frac{1}{T^{\text{cell},i}(t)}\right)\right]\Delta\mathrm{DoD}_i^2(t)\;}
$$

con $C^{\text{rep}}$ costo de reposición [€/kWh], $N^{\text{nom}}_{\text{cyc}}$ ciclos nominales a DoD total, $T^{\text{opt}}=298\,$K, $\beta_T$ coeficiente térmico, $\Delta\mathrm{DoD}$ profundidad de descarga del paso.

**State of Health:**

$$
\mathrm{SoH}(t)=\frac{Q_{\text{nom}}-Q_{\text{loss}}^{\text{cal}}(t)-Q_{\text{loss}}^{\text{cyc}}(N_{\text{eq}})}{Q_{\text{nom}}}\in[0{,}8,1{,}0],
$$

con fin de vida nominal $\mathrm{SoH}=80\%$ (IEC 62660-2:2018).

**Regla térmica de Van't Hoff.** Un incremento de $10\,$K duplica aproximadamente la tasa de degradación calendárica. Este es el parámetro **más sensible** del modelo: en climas cálidos (Lima, Iquitos) la vida útil del BESS se reduce sustancialmente.

**KPIs cuantitativos del Eje 5.**

| Símbolo | Definición | Unidad |
|---------|------------|--------|
| SoH | State of Health | % |
| $\Delta Q$ | Capacidad fade anual | %/año |
| $N_{\text{eq}}$ | Ciclos equivalentes anuales | ciclos/año |
| $E_{\text{tp}}$ | Throughput energético | MWh |
| RUL | Remaining Useful Life | años |
| LCOC | Levelized cost of cycling | €/MWh-cycle |

---

### 4.3.6. Eje 6 — Resiliencia estocástica ante fallos críticos de red

Bajo cortes de red simulados (módulo *power outage* CityLearn v2; Nweye et al., 2024) la comunidad opera en modo isla. La recompensa de resiliencia es

$$
\boxed{\;r^{(6),i}(t)=\big[\max(0,P^{\text{crit},i}-P^{\text{disp},i}(t))\big]^2\;}
$$

con

$$
P^{\text{disp},i}(t)=\eta^{\text{dis}}P_i^{\text{BESS,dis}}(t)+\eta^{\text{V2G}}P_i^{\text{EV}}(t)+P_i^{\text{PV}}(t).
$$

**Tiempo de autonomía en isla:**

$$
\tau_i^{\text{isla}}=\inf\{t>t_0:\mathrm{SoC}_i(t)\leq\mathrm{SoC}^{\min}\;\text{o}\;P_i^{\text{shed}}(t)>0\}.
$$

**Índice de cobertura crítica:**

$$
\mathrm{CCI}=\frac{\int_{t_0}^{t_{\text{end}}}P^{\text{crit}}_{\text{served}}\,dt}{\int_{t_0}^{t_{\text{end}}}P^{\text{crit}}_{\text{dem}}\,dt}\in[0,1].
$$

**Loss of Load Probability:**

$$
\mathrm{LOLP}=\frac{1}{H}\sum_{t=1}^H\mathbb{1}[P^{\text{shed}}(t)>0].
$$

**KPIs cuantitativos del Eje 6.**

| Símbolo | Definición | Unidad |
|---------|------------|--------|
| $\tau^{\text{isla}}$ | Tiempo de autonomía | h |
| CCI | Cobertura crítica | — |
| LOLP | Probabilidad pérdida de carga | — |
| $S$ | Energía no servida normalizada | — |
| $M$ | Resiliencia térmica | — |

---

### 4.3.7. Eje 7 — Eficiencia de gestión de ACS (con pérdidas térmicas conductivas)

**Derivación termodinámica.** Aplicando la primera ley al tanque ACS modelado como recipiente con un nodo (o estratificado, §4.5.7):

$$
\rho V c_p\frac{dT^{\text{tank}}}{dt}=\eta^{\text{ACS}}P^{\text{ACS}}(t)-Q^{\text{ACS,dem}}(t)-UA\big(T^{\text{tank}}(t)-T^{\text{amb}}(t)\big),
$$

donde $UA$ es el coeficiente global de pérdidas conductivas-convectivas [W/K].

**Formulación del UC3M (Eje 7):**

$$
\boxed{\;r^{(7),i}(t)=\big[\max(0,Q_i^{\text{ACS,dem}}(t)-Q_i^{\text{ACS,cob}}(t))\big]^2+\kappa\,UA_i\big(T_i^{\text{tank}}(t)-T^{\text{amb}}(t)\big)\;}
$$

el primer término penaliza el déficit de cobertura, el segundo las pérdidas térmicas.

**Restricción anti-Legionella:** $T^{\text{tank}}\geq 55\,$°C al menos una vez por día (EN 806-2:2005; UNE 100030:2017).

**Rendimiento exergético** (Bejan, 2016, *Advanced Engineering Thermodynamics*, 4ª ed., Wiley):

$$
\eta_{\text{ex}}=\frac{\dot Q_{\text{útil}}(1-T_0/T^{\text{tank}})}{P_{\text{elec}}}.
$$

**KPIs cuantitativos del Eje 7.**

| Símbolo | Definición | Unidad |
|---------|------------|--------|
| $f_{\text{sol}}$ | Cobertura solar térmica | — |
| $\eta_{\text{ex}}$ | Rendimiento exergético | — |
| $\Phi_{\text{loss}}$ | Pérdidas térmicas normalizadas | — |
| COP$_{\text{ACS}}$ | COP de la bomba de calor ACS | — |
| $T^{\text{cumpl}}$ | Cumplimiento anti-Legionella | % horas |

---

## 4.4. Arquitectura MARLlib-CTDE y universalidad algorítmica MADRL

### 4.4.1. MARLlib: librería universal MADRL

**MARLlib** (Hu et al., 2023, *Journal of Machine Learning Research* 24(315):1–23, arXiv:2210.13708, autores: Siyi Hu, Yifan Zhong, Minquan Gao, Weixun Wang, Hao Dong, Xiaodan Liang, Zhihui Li, Xiaojun Chang, Yaodong Yang) es una librería MARL construida sobre Ray (Moritz et al., 2018, *OSDI*) y RLlib (Liang et al., 2018, *ICML*). Implementa tres mecanismos clave que la convierten en sustrato ideal para el UC3M:

1. **Wrapper unificado** para entornos multi-agente compatible con Gymnasium y PettingZoo;
2. **Implementación a nivel de agente** —en contraposición a la implementación matricial de RLlib estándar— que separa el flujo de datos por agente y facilita la heterogeneidad;
3. **Estrategia flexible de policy mapping** que permite políticas independientes, compartidas o por grupos.

La librería cubre **18 algoritmos MARL** preimplementados —IQL, IPPO, IA2C, IDDPG, ITRPO, MAPPO, MADDPG, MATRPO, HAPPO, HATRPO, COMA, MAA2C, MAAC, VDN, QMIX, FACMAC, VDA2C, VDPPO— y soporta tareas cooperativas, colaborativas, competitivas y mixtas.

### 4.4.2. Arquitectura del UC3M: visión por capas

El framework UC3M se organiza en **siete capas funcionales**, descritas textualmente:

**Capa 1 — Ingestión de datos exógenos universales.**
- Series climáticas: TMY3 (USA), EPW (Climate.OneBuilding.org), ERA5 (Copernicus/ECMWF), NASA POWER, SENAMHI Perú, datos satelitales NREL NSRDB;
- Perfiles de demanda: EUSS-NREL (Wilson et al., 2022), ASHRAE Great Energy Predictor III, Building Data Genome 2;
- Precios: OMIE (España), Nord Pool (Norte de Europa), CAISO (California), COES (Perú);
- Factores de emisión: Electricity Maps, ENTSO-E, EIA, COES;
- Patrones de ocupación y disponibilidad EV: derivados de NHTS-USA, datos abiertos MTC Perú.

**Capa 2 — Motor de simulación CityLearn v3.**
Ejecuta paso horario aplicando los modelos físicos de §4.5: balance Kirchhoff, RC térmico (data-driven LSTM opcional sobre EnergyPlus), PV, BESS con degradación SoH, V2G (módulo EVLearn — Fonseca et al., 2024, *Energy Informatics*), HP con COP dependiente de $T_{\text{out}}$, tanque ACS estratificado.

**Capa 3 — Wrappers de interfaz universal.**
- Envoltorio Gymnasium para generar observaciones $o_i$ y recibir acciones $a_i$ por agente;
- Adaptador PettingZoo-Parallel/AEC para MARLlib;
- Adaptador RLlib MultiAgentEnv;
- Módulo de **normalización Z-score adaptativa** para estabilidad numérica.

**Capa 4 — MARLlib AlgorithmFactory (núcleo universal MADRL).**
Instancia cualquier algoritmo MARL preimplementado o de terceros mediante configuraciones YAML. Gestiona políticas $\pi_i(a_i\mid o_i;\theta_i)$ y críticos centralizados $Q(s,\mathbf{a};\phi)$, $V(s;\phi)$ o mezcladores $Q_{\text{tot}}$ (QMIX, FACMAC, VDN) según el algoritmo.

**Capa 5 — Ray Actor Cluster.**
Distribuye rollouts en *workers* paralelos (8–256, según escala) y centraliza el aprendizaje en el *trainer*. Mantiene replay/rollout buffers; soporta entrenamiento multi-GPU mediante Distributed Data Parallel.

**Capa 6 — Capa de evaluación y métricas (Eje-1–7 monitor).**
Calcula los KPIs de los siete ejes en tiempo real y los serializa con MLflow / Weights & Biases. Ejecuta tests estadísticos (Wilcoxon, Friedman, ANOVA) y construye la frontera de Pareto empírica y el índice HPHI (§4.7).

**Capa 7 — Capa de interpretabilidad y reproducibilidad.**
Versionado con DVC, Docker, semillas registradas, dashboards públicos, licenciamiento Apache 2.0.

Diagrama textual:

```
[Datos exógenos: TMY/EPW/ERA5/SENAMHI/COES/Electricity Maps]
                          ↓
[Capa 2: CityLearn v3 + activos físicos + BACT]
                          ↓
[Capa 3: Wrappers Gym/PettingZoo + normalización adaptativa]
                          ↓
[Capa 4: MARLlib AlgorithmFactory (cualquier MADRL)]
                          ↓                  ↑
[Capa 5: Ray cluster: workers paralelos] ← actualización ←┘
                          ↓
[Replay/Rollout buffer (uniform / PER / HER multi-agent)]
                          ↓
[Capa 6: KPIs 7-ejes + HPHI + MLflow]
                          ↓
[Capa 7: DVC + Docker + Apache 2.0 + dashboards]
```

### 4.4.3. Universalidad algorítmica MADRL: interfaz Plugin

**Definición 4.4 (Plugin algorítmico MADRL UC3M).** *Un plugin algorítmico es una tupla $\mathcal{P}=\langle\Theta,\Phi,\mathcal{L}_{\text{actor}},\mathcal{L}_{\text{critic}},\mathcal{U}_{\text{step}},\mathcal{B}\rangle$ donde $\Theta$ es el espacio de parámetros del actor, $\Phi$ el del crítico/mezclador, $\mathcal{L}_{\text{actor}},\mathcal{L}_{\text{critic}}$ las funciones de pérdida, $\mathcal{U}_{\text{step}}$ la regla de actualización y $\mathcal{B}$ la estructura del buffer.*

**Teorema 4.8 (Universalidad algorítmica del UC3M).** *Sea $\mathcal{A}_{\text{MADRL}}$ la clase de algoritmos MADRL caracterizables por la tupla de la Def. 4.4. Para todo $\mathcal{P}\in\mathcal{A}_{\text{MADRL}}$, el UC3M admite una implementación funcional de $\mathcal{P}$ vía la AlgorithmFactory de MARLlib, sujeta únicamente a que las interfaces $\mathcal{L}$ y $\mathcal{U}$ se expresen como grafos computacionales PyTorch o TensorFlow estándar.*

*Esbozo.* MARLlib expone una API basada en `Trainer`, `Policy` y `LearningPipeline` cuyas firmas son agnósticas al algoritmo concreto. Cualquier $\mathcal{P}$ cuyos componentes se expresen en autograd estándar puede instanciarse implementando los métodos `compute_actions`, `learn_on_batch` y `postprocess_trajectory` (Hu et al., 2023, §3). El UC3M hereda esta universalidad. $\blacksquare$

### 4.4.4. Paradigma CTDE: formulación matemática genérica

En el régimen CTDE las políticas se ejecutan de forma descentralizada:

$$
\pi_i(a_i\mid o_i;\theta_i):\mathcal{O}_i\to\Delta(\mathcal{A}_i),\quad\forall i\in\mathcal{I},
$$

condicionadas únicamente sobre la observación local $o_i$. Durante el entrenamiento se aprende una **función crítica centralizada** condicionada sobre el estado global y/o las acciones conjuntas:

$$
Q^{\text{centr}}(s,a_1,\ldots,a_N;\phi)\approx\mathbb{E}_{\boldsymbol\pi}\!\left[\sum_t\gamma^t R(s_t,\mathbf{a}_t)\,\Big|\,s_0=s,\mathbf{a}_0=\mathbf{a}\right].
$$

La existencia del crítico global mitiga la no-estacionariedad multi-agente (Lowe et al., 2017, *NeurIPS*, MADDPG; Foerster et al., 2018, *AAAI*, COMA). El gradiente del actor sigue la forma genérica

$$
\nabla_{\theta_i}J(\theta_i)=\mathbb{E}\!\left[\nabla_{\theta_i}\log\pi_i(a_i\mid o_i)\,A^{\text{centr}}_i(s,\mathbf{a})\right],
$$

con $A^{\text{centr}}_i$ ventaja contrafactual (COMA), GAE estándar (MAPPO), descompuesta secuencialmente (HAPPO) o evaluada bajo factorización de valor (QMIX, FACMAC).

### 4.4.5. Algoritmos MADRL preimplementados en el UC3M

A continuación se detalla matemáticamente cada algoritmo soportado.

#### A) MAPPO — Multi-Agent Proximal Policy Optimization

(Yu et al., 2022, *NeurIPS Datasets and Benchmarks*, arXiv:2103.01955). Extiende PPO al régimen multi-agente con crítico centralizado. Política compartida $\pi_\theta$:

$$
\mathcal{L}^{\text{clip}}_i(\theta)=\mathbb{E}_t\!\left[\min\!\Big(\rho_{i,t}A_{i,t},\;\mathrm{clip}(\rho_{i,t},1-\epsilon,1+\epsilon)A_{i,t}\Big)\right],
$$

con $\rho_{i,t}=\pi_\theta(a_{i,t}\mid o_{i,t})/\pi_{\theta_{\text{old}}}(a_{i,t}\mid o_{i,t})$. Crítico centralizado $V_\phi(s)$ optimizado por MSE.

#### B) HAPPO — Heterogeneous-Agent PPO

(Kuba et al., 2022, *ICLR*, arXiv:2109.11251; Zhong et al., 2023, *JMLR* 25). Soporta políticas heterogéneas mediante actualización secuencial por permutación. **Multi-Agent Advantage Decomposition:**

$$
A^{\boldsymbol\pi}_{i_{1:N}}(s,\mathbf{a})=\sum_{m=1}^N A^{\boldsymbol\pi}_{i_m}(s,a_{i_{1:m-1}},a_{i_m}).
$$

Objetivo clip con factor de corrección $M_{i_m}=\pi^{\text{new}}_{i_{1:m-1}}/\pi^{\text{old}}_{i_{1:m-1}}$:

$$
\mathcal{L}^{i_m}(\theta_{i_m})=\mathbb{E}\!\left[\min\!\Big(r_{i_m}M_{i_m}A^{\text{seq}}_{i_m},\,\mathrm{clip}(r_{i_m},1-\epsilon,1+\epsilon)M_{i_m}A^{\text{seq}}_{i_m}\Big)\right].
$$

#### C) MADDPG — Multi-Agent Deep Deterministic Policy Gradient

(Lowe et al., 2017, *NeurIPS*, arXiv:1706.02275). Crítico centralizado off-policy, actor descentralizado determinista:

$$
\mathcal{L}_{Q_i}=\mathbb{E}\!\left[\big(Q_i^\phi(s,\mathbf{a})-y_i\big)^2\right],\quad y_i=r_i+\gamma Q_i^{\phi'}(s',\mathbf{a}'),\;a_j'=\mu_j^{\theta'}(o_j').
$$

#### D) MATD3 — Multi-Agent Twin Delayed DDPG

(Ackermann et al., 2019, arXiv:1910.01465). Dos críticos $Q_i^{(1)},Q_i^{(2)}$ + suavizado de política objetivo + actualización retardada del actor:

$$
y_i=r_i+\gamma\min_{k\in\{1,2\}}Q_i^{(k),\phi'_k}(s',\tilde a'_1,\ldots,\tilde a'_N),\quad \tilde a_j'=\mu_j^{\theta'}(o_j')+\mathrm{clip}(\eta,-c,c).
$$

#### E) MAAC — Multi-Actor-Attention-Critic

(Iqbal y Sha, 2019, *ICML*, PMLR 97:2961–2970). Crítico con atención multi-cabeza:

$$
Q_i^\psi(s,\mathbf{a})=f_i\!\big(g_i(o_i,a_i),x_i\big),\quad x_i=\sum_{j\neq i}\alpha_{ij}\,h\!\big(V_j g_j(o_j,a_j)\big),
$$

$$
\alpha_{ij}\propto\exp\!\big((W_q g_i)^\top(W_k g_j)/\sqrt{d_k}\big).
$$

Escala $O(N)$ frente al $O(N^2)$ de MADDPG.

#### F) MASAC — Multi-Agent Soft Actor-Critic

Objetivo entrópico:

$$
J_i=\mathbb{E}\!\left[\sum_t\gamma^t\big(R_i(s_t,\mathbf{a}_t)+\alpha\mathcal{H}(\pi_i(\cdot\mid o_{i,t}))\big)\right].
$$

Auto-ajuste de $\alpha$ con entropía objetivo $\bar H=-\dim\mathcal{A}_i$ (Haarnoja et al., 2018, *ICML*).

#### G) QMIX

(Rashid et al., 2018, *ICML*, arXiv:1803.11485). Factorización monotónica del valor de equipo:

$$
Q_{\text{tot}}(s,\mathbf{a})=f_{\text{mix}}\big(Q_1(o_1,a_1),\ldots,Q_N(o_N,a_N);s\big),
$$

con $\partial f_{\text{mix}}/\partial Q_i\geq 0$ (monotonicidad). Permite descentralización por argmax local.

#### H) VDN — Value Decomposition Network

(Sunehag et al., 2017, arXiv:1706.05296). Caso particular de QMIX con factorización aditiva:

$$
Q_{\text{tot}}(\mathbf{o},\mathbf{a})=\sum_{i=1}^N Q_i(o_i,a_i).
$$

#### I) FACMAC — Factored Multi-Agent Centralised Policy Gradients

(Peng et al., 2021, *NeurIPS*). Extensión de QMIX/VDN a acciones continuas mediante actor determinista.

#### J) Algoritmos adicionales soportados

COMA (Foerster et al., 2018), IPPO/IA2C/ITRPO (variantes independientes), HATRPO/HATD3 (heterogéneos), MAA2C, FAMA, HASAC, y cualquier algoritmo futuro que cumpla la Def. 4.4.

### 4.4.6. Pseudocódigo genérico de entrenamiento universal UC3M

```
Entrada: comunidad C con BACT B, algoritmo P (plugin), hiperparámetros H, K epochs
Inicializar entorno env = CityLearn_v3_UC3M(C, B)
Wrap env como PettingZoo-Parallel
Instanciar P en MARLlib AlgorithmFactory con configuración YAML
Inicializar θ_i (actores), φ (crítico/mezclador), buffer D según P.B

Para epoch = 1..K:
   Ejecutar T pasos de rollout en parallel workers (Ray):
      Para cada t:
         Para cada i en I: a_{i,t} ~ π_i(·|o_{i,t}; θ_i)
         (s_{t+1}, r_{1:N,t+1}, o_{1:N,t+1}, terminal) = env.step(a_t)
         Calcular r_i^{(1..7)} (siete ejes, §4.3)
         R_i = -Σ_k λ_k r_i^{(k)}
         Almacenar transición en D
   Aplicar P.L_critic y P.L_actor según P.U_step
   Actualizar redes objetivo (polyak τ) si aplica
   Evaluar KPIs por eje sobre validación; calcular HPHI (§4.7)
   Log MLflow + W&B
Retornar (θ_i, φ, KPIs, HPHI)
```

### 4.4.7. Hiperparámetros típicos por algoritmo

| Algoritmo | lr | batch | $\gamma$ | $\tau$ | buffer | epochs/iter | Hidden |
|-----------|----|----|----|----|-----|---|---|
| MAPPO | 3e-4 | 4096 | 0,99 | — | rollout | 5–10 | 256×256 |
| HAPPO | 3e-4 | 4096 | 0,99 | — | rollout | 5–10 | 256×256 |
| MADDPG | 1e-4/1e-3 | 256 | 0,99 | 0,005 | 1e6 | — | 256×256 |
| MATD3 | 1e-4/1e-3 | 256 | 0,99 | 0,005 | 1e6 | — | 256×256 |
| MAAC | 1e-3 | 1024 | 0,99 | 0,01 | 1e5 | — | 128 + 4-head att |
| MASAC | 3e-4 | 256 | 0,99 | 0,005 | 1e6 | — | 256×256 |
| QMIX | 5e-4 | 32 ep | 0,99 | 0,005 | 5e3 ep | — | 64 GRU |
| FACMAC | 5e-4 | 32 ep | 0,99 | 0,005 | 5e3 ep | — | 64 GRU |

Auto-tuning recomendado: Optuna (Akiba et al., 2019, *KDD*) con búsqueda bayesiana TPE; alternativa Population-Based Training (Jaderberg et al., 2017).

### 4.4.8. Análisis de complejidad computacional

**Proposición 4.9 (Complejidad asintótica).** *Sea $d_h$ la dimensión oculta de la red, $d_s$ la del estado, $d_a$ la dimensión por agente y $N$ el número de agentes. Las complejidades asintóticas por paso de aprendizaje son:*

| Algoritmo | Complejidad por paso | Memoria | Escala con $N$ |
|-----------|---------------------|---------|----------------|
| MAPPO/HAPPO | $O(N\,d_h^2)$ | $O(N\,\|\theta\|)$ | Lineal |
| MADDPG/MATD3 | $O(N\,(d_s+N d_a)d_h)$ | $O(\|D\|+N\,\|\theta\|)$ | Cuadrática |
| MAAC | $O(N\,d_h^2+N\,d_k)$ | $O(\|D\|+\|\psi\|)$ | Lineal (atención) |
| MASAC | $O(N\,d_h^2)$ | $O(\|D\|+N\,\|\theta\|)$ | Cuasi-lineal |
| QMIX/VDN | $O(N\,d_h^2)$ | $O(\|D\|+N\,\|\theta\|)$ | Lineal |

MAAC y QMIX/VDN son las opciones recomendadas para $N>20$.

---

## 4.5. Ecuaciones físicas detalladas de los activos distribuidos

### 4.5.1. Balance de potencia del edificio (Kirchhoff)

Primera ley de Kirchhoff (potencias activas) al nodo de conexión a red del edificio $i$:

$$
\boxed{\;P_i^{\text{net}}(t)=P_i^{\text{load,fix}}(t)+P_i^{\text{HP}}(t)+P_i^{\text{EH}}(t)+P_i^{\text{BESS}}(t)+P_i^{\text{EV}}(t)-P_i^{\text{PV}}(t)-P_i^{\text{wind}}(t)\;}
$$

Convenios: $P^{\text{BESS}},P^{\text{EV}}>0$ en carga, $<0$ en descarga. La potencia neta de la comunidad es $P^{\text{com}}=\sum_i P_i^{\text{net}}$. Con inversores inteligentes, la potencia reactiva $Q_i=P_i^{\text{PV}}\tan\theta_i$ es acción adicional, sujeta a la curva $\sin\phi$ del inversor (IEEE 1547-2018).

### 4.5.2. Modelo térmico RC del edificio (universal: vernáculo, moderno, pasivo)

Modelo 2R2C (Crawley et al., 2001, *Energy and Buildings*; Reynders et al., 2014, *Applied Energy*):

$$
C_{\text{air}}\frac{dT_{\text{air}}}{dt}=\frac{T_{\text{out}}-T_{\text{air}}}{R_{\text{ext}}}+\frac{T_m-T_{\text{air}}}{R_{\text{im}}}+\dot Q_{\text{HVAC}}+\dot Q_{\text{int}},
$$

$$
C_m\frac{dT_m}{dt}=\frac{T_{\text{air}}-T_m}{R_{\text{im}}}+\dot Q_{\text{sol}},
$$

con $\dot Q_{\text{HVAC}}=\mathrm{COP}\cdot P^{\text{HP}}$, $\dot Q_{\text{sol}}$ aporte solar (transmitancia $\tau_g$ y GHI), $\dot Q_{\text{int}}$ ganancias internas. CityLearn v3 ofrece como alternativa modelos data-driven (LSTM) entrenados sobre EnergyPlus.

**Calibración a tipologías universales.** Los parámetros $R,C$ se calibran a:
- **Vernácula andina** (adobe Cusco, Puno): $U_{\text{muro}}=1{,}5\,$W/(m²·K), elevada inercia térmica;
- **Ladrillo Lima**: $U_{\text{muro}}=2{,}5\,$W/(m²·K);
- **Vivienda amazónica madera** (Iquitos): $U_{\text{muro}}=3{,}5\,$W/(m²·K), elevada infiltración natural;
- **Edificio pasivo Passivhaus**: $U_{\text{muro}}<0{,}15\,$W/(m²·K);
- **Hormigón comercial moderno**: $U_{\text{muro}}=0{,}5\,$W/(m²·K) post-2018.

### 4.5.3. Modelo fotovoltaico

Potencia DC del generador PV:

$$
P^{\text{PV,DC}}(t)=P_{\text{STC}}\,\frac{G(t)}{G_{\text{STC}}}\!\left[1+\beta_p\big(T_c(t)-T_{\text{STC}}\big)\right]\,(1-\delta_{\text{soil}})(1-\delta_{\text{shade}}),
$$

con $G_{\text{STC}}=1\,000\,$W/m², $T_{\text{STC}}=25\,$°C, $\beta_p\approx -0{,}0045$/°C (silicio cristalino), $\delta_{\text{soil}}$ pérdidas por suciedad (5–15% en zonas áridas/desérticas como Lima), $\delta_{\text{shade}}$ sombras.

Temperatura de célula:

$$
T_c=T_{\text{amb}}+\frac{G}{G_{\text{NOCT}}}(T_{\text{NOCT}}-20),\quad T_{\text{NOCT}}\approx 45\,°\text{C}.
$$

Potencia AC: $P^{\text{PV}}=\eta_{\text{inv}}P^{\text{PV,DC}}$, $\eta_{\text{inv}}\in[0{,}95,0{,}98]$.

### 4.5.4. Modelo eólico residencial

Curva de potencia idealizada y distribución de Weibull para el sitio:

$$
P^{\text{wind}}(v)=\begin{cases}0, & v<v_{\text{cut-in}}\\ \tfrac12\rho A v^3 C_p, & v_{\text{cut-in}}\leq v\leq v_{\text{rated}}\\ P_{\text{rated}}, & v_{\text{rated}}<v<v_{\text{cut-out}}\\ 0, & v\geq v_{\text{cut-out}}\end{cases},
$$

con coeficiente de potencia $C_p\leq C_{p,\text{Betz}}=16/27\approx 0{,}593$.

### 4.5.5. Modelo BESS con degradación

Dinámica del SoC:

$$
\mathrm{SoC}(t+1)=\mathrm{SoC}(t)+\frac{\Delta t}{Q_{\text{nom}}}\big[\eta^{\text{ch}}P^{\text{ch}}(t)-P^{\text{dis}}(t)/\eta^{\text{dis}}\big].
$$

Restricciones: $\mathrm{SoC}\in[\mathrm{SoC}^{\min},\mathrm{SoC}^{\max}]\subseteq[0{,}1,0{,}9]$; $|P|\leq P_{\max}$; $\eta^{\text{ch}}\eta^{\text{dis}}\approx 0{,}9$ (LFP) – $0{,}94$ (NMC). Modelo combinado de §4.3.5 actualiza el SoH paso a paso.

### 4.5.6. Modelo V2G/V2H/V2B del vehículo eléctrico

Disponibilidad markoviana: el vehículo $i$ está disponible solo en $\mathcal{T}_i^{\text{plug}}\subset[0,H]$ definido por un patrón estocástico calibrado a NHTS-USA o MTC Perú. Restricción de movilidad:

$$
\mathrm{SoC}_{\text{EV},i}(t_{\text{salida}})\geq\mathrm{SoC}^{\text{ride}}_i.
$$

Niveles de potencia conforme IEC 61851-1:
- Nivel 1 (lento, casa): 3,7 kW
- Nivel 2 (rápido residencial): 7,4–22 kW
- Nivel 3 (V2G bidireccional): ≤ 11 kW para residencial, ≤ 50 kW para flotas.

EVLearn (Fonseca et al., 2024, *Energy Informatics*, doi:10.1186/s42162-024-00445-w) es el módulo de referencia integrado.

### 4.5.7. Bomba de calor con eficiencia variable

COP semi-empírico (Carnot modificado):

$$
\mathrm{COP}(T_{\text{out}})=\eta_{\text{Carnot}}\,\frac{T_{\text{cond}}}{T_{\text{cond}}-T_{\text{evap}}(T_{\text{out}})},
$$

con $\eta_{\text{Carnot}}\in[0{,}35,0{,}50]$, $T_{\text{cond}}\approx 318\,$K (45 °C salida), $T_{\text{evap}}\approx T_{\text{out}}-5\,$K. Valores típicos: COP 4,0 a $T_{\text{out}}=10\,$°C; 2,5 a $-5\,$°C; 1,8 a $-15\,$°C (Puno).

### 4.5.8. Tanque ACS estratificado multi-nodo

Modelo zonal de $n$ nodos (Cadau et al., 2024, doi:10.1007/978-3-032-10546-2_69):

$$
m_j c_p\frac{dT_j}{dt}=\dot m_{\text{in}}c_p(T_{j-1}-T_j)+UA_j(T_{\text{amb}}-T_j)+\dot Q^{\text{aux}}_j-\dot Q^{\text{load}}_j,
$$

con $c_p=4\,186\,$J/(kg·K). El UC3M usa por defecto modelo de 2 nodos.

### 4.5.9. Hidrógeno verde (electrolizador + celda combustible)

Producción de H₂ por electrolizador PEM:

$$
\dot n_{\text{H}_2}(t)=\eta_{\text{elec}}\frac{P_{\text{elec}}(t)}{\Delta H^0_{\text{H}_2}},\quad\Delta H^0_{\text{H}_2}=285{,}83\,\mathrm{kJ/mol}.
$$

Eficiencia electrolizador PEM: $\eta_{\text{elec}}\in[55\%,70\%]$ HHV. Celda combustible: $\eta_{\text{FC}}\in[40\%,60\%]$.

---

## 4.6. Universalidad geográfica: integración Perú–internacional–mundial

### 4.6.1. Categorías Köppen-Geiger soportadas

El UC3M soporta las 30 categorías Köppen-Geiger (Peel et al., 2007, *Hydrology and Earth System Sciences* 11(5):1633–1644) clasificadas en cinco grupos:

- **A** Tropical (Af, Am, Aw): Iquitos, Tarapoto, Pucallpa (Perú); Singapur, Manaus, Yakarta.
- **B** Árido (BWh, BSk): Lima, Ica (Perú); Phoenix, El Cairo, Riyadh.
- **C** Templado (Cfa, Cfb, Cwa, Csa): Cusco, Arequipa parcial; Madrid, Sídney, Buenos Aires.
- **D** Continental (Dfa, Dfb, Dfc): Moscú, Toronto, Estocolmo.
- **E** Polar (ET, EF): Puno parcial altiplano, Antártida, Groenlandia.

### 4.6.2. Casos de uso peruanos prototípicos

| Sitio | Köppen | Altitud (msnm) | T media (°C) | HR (%) | Particularidad |
|-------|--------|----------------|--------------|--------|-----------------|
| Iquitos | Af | 106 | 26,5 | 85 | Tropical húmedo; ACS marginal; refrigeración crítica |
| Tarapoto | Aw | 356 | 26,2 | 75 | Tropical estacional |
| Lima | BWh | 154 | 19,2 | 80 | Costa desértica con humedad; bajo HVAC; PV con suciedad |
| Trujillo | BWh | 34 | 19,5 | 75 | Costa norte; brisas marinas |
| Arequipa | BSk | 2 335 | 14,5 | 50 | Semiárido frío; alta radiación |
| Cusco | Cwb | 3 399 | 12,5 | 60 | Altoandino templado seco |
| Puno | ET | 3 827 | 8,5 | 55 | Altiplano frío; baja densidad aire; escarcha |
| Huancavelica | ETH | 3 676 | 9,8 | 65 | Sierra alta; calefacción crítica |

> **Aporte original al Eje 4 en Perú.** Para Iquitos y Tarapoto se aplica el modelo adaptativo De Dear-Brager (4.3.4) con $T^{\text{neutral}}\approx 26{,}0\,$°C, banda de aceptabilidad $[23{,}5,28{,}5]\,$°C. Para Puno y Cusco se aplica PMV/PPD clásico con énfasis en calefacción nocturna y soluciones de inercia térmica (adobe, trombe walls).

### 4.6.3. Teorema de invariancia geográfica

**Definición 4.5 (Transformación Köppen).** *Sea $\mathcal{T}_{KK'}:\mathcal{S}_{\text{clim}}^K\to\mathcal{S}_{\text{clim}}^{K'}$ la transformación entre dos zonas Köppen-Geiger $K,K'$, definida por la calibración del BACT.*

**Teorema 4.10 (Invariancia geográfica del UC3M).** *Sea $\pi^\star$ una política óptima entrenada en el Meta-Dec-POMDP $\mathcal{M}_K$ asociado a la zona $K$. Sea $\mathcal{M}_{K'}$ el Meta-Dec-POMDP isomorfo bajo la transformación BACT $\mathcal{T}_{KK'}$. Entonces existe una política $\pi^{\star'}$ óptima en $\mathcal{M}_{K'}$ obtenible mediante fine-tuning de $\pi^\star$ con un número de iteraciones $\tau_{\text{ft}}\ll\tau_{\text{from-scratch}}$.*

*Esbozo.* La estructura del Meta-Dec-POMDP es invariante bajo el cambio de BACT; cambian únicamente las distribuciones del núcleo de transición exógeno. El teorema garantiza **transferibilidad zero/few-shot** entre zonas climáticas mediante transfer learning. La demostración formal sigue argumentos de Domain Randomization (Tobin et al., 2017, *IROS*) y de Robust MDP (Iyengar, 2005, *Mathematics of Operations Research* 30(2):257–280). $\blacksquare$

### 4.6.4. Pipeline de ingestión universal

```
Entrada: localización (lat, lon, altitud) + tipología constructiva + dotación activos
1. Consultar zona Köppen-Geiger
2. Descargar serie climática (TMY/EPW desde climate.onebuilding.org;
   ERA5 si no hay EPW; SENAMHI para Perú; NASA POWER fallback)
3. Calibrar parámetros RC térmicos del modelo a tipología
4. Configurar BACT con datos de activos
5. Cargar señales de precios (OMIE/Nord Pool/CAISO/COES) y CO2 (Electricity Maps)
6. Construir entorno UC3M y entrenar
```

---

## 4.7. Métricas originales: HPHI y consistencia multiobjetivo

### 4.7.1. Definición del Holistic Pareto Hypervolume Index (HPHI)

**Definición 4.6 (HPHI 7-D normalizado).** *Sea $\mathcal{F}\subset\mathbb{R}^7$ una aproximación empírica de la frontera de Pareto del UC3M obtenida por barrido del simplex $\boldsymbol\Lambda$ o por algoritmos MORL Pareto-conscientes. Sea $\mathbf{z}^{\text{nadir}}\in\mathbb{R}^7$ el punto nadir (peores valores empíricos) y $\mathbf{z}^{\text{ideal}}$ el punto ideal. El HPHI se define como*

$$
\boxed{\;\mathrm{HPHI}(\mathcal{F})=\frac{\mathrm{HV}(\mathcal{F};\mathbf{z}^{\text{nadir}})}{\prod_{k=1}^7(z_k^{\text{nadir}}-z_k^{\text{ideal}})}\in[0,1]\;}
$$

*donde $\mathrm{HV}$ es el hipervolumen Lebesgue 7-D dominado por $\mathcal{F}$ respecto a $\mathbf{z}^{\text{nadir}}$ (Zitzler y Thiele, 1999, *IEEE TEC* 3(4):257–271).*

**Interpretación.** HPHI = 1 corresponde a una frontera perfecta que domina hasta el ideal. HPHI = 0 corresponde a una política trivial. El HPHI permite comparar de manera invariante a la escala las soluciones de cualquier algoritmo MADRL en el UC3M.

### 4.7.2. Consistencia dimensional de los siete ejes acoplados

**Proposición 4.11 (Consistencia dimensional).** *Tras la normalización a la base RBC ($\tilde r^{(k)}=r^{(k)}/r^{(k),\text{base}}$), los siete ejes se expresan en unidades adimensionales conmensurables, y la suma escalarizada $R=\sum_k\lambda_k\tilde r^{(k)}$ es dimensionalmente coherente.*

### 4.7.3. Métricas auxiliares: sparsity, $\varepsilon$-cobertura

Complementan al HPHI:

- **Sparsity** $\mathrm{Sp}(\mathcal{F})=\frac{1}{|\mathcal{F}|-1}\sum_{j=1}^{|\mathcal{F}|-1}\|\mathbf{f}_j-\mathbf{f}_{j+1}\|^2$, mide dispersión sobre la frontera.
- **$\varepsilon$-cobertura** $C_\varepsilon(\mathcal{F},\mathcal{F}^*)=|\{f\in\mathcal{F}^*:\exists f'\in\mathcal{F},\,\|f-f'\|\leq\varepsilon\}|/|\mathcal{F}^*|$, mide proximidad a la frontera de referencia.

---

## 4.8. Metodología experimental doctoral

### 4.8.1. Datasets

- **CityLearn Challenge 2023 Dataset** (Nweye et al., 2024, Texas Data Repository, doi:10.18738/T8/SXFWTI): comunidades sintéticas hasta 15 viviendas USA;
- **EUSS-NREL** (Wilson et al., 2022): End-Use Load Profiles;
- **Building Data Genome 2** (Miller et al., 2020, *Scientific Data*);
- **Datos abiertos Perú**: SENAMHI (clima), COES (precios, demanda, mix eléctrico), OSINERGMIN (tarifas), MINEM (matriz energética).

### 4.8.2. Diseño experimental

**Protocolo tres-bloques:**

1. **Entrenamiento** sobre 75% inicial del horizonte anual (~6 570 h) con **5 semillas** por configuración.
2. **Validación** sobre 15% (~1 314 h) para early stopping + búsqueda bayesiana hiperparámetros (Optuna TPE).
3. **Prueba** sobre 10% final + 2 semanas de eventos de corte (Eje 6).

**Estratificación geográfica:** cada algoritmo se evalúa sobre al menos 6 zonas Köppen-Geiger, incluyendo 3 sitios peruanos (Lima, Cusco, Iquitos).

### 4.8.3. Baselines

| Baseline | Descripción |
|----------|-------------|
| RBC | Rule-Based Control CityLearn por defecto |
| MPC | Model Predictive Control horizonte 24 h, MILP CVXPY/Gurobi |
| Single-Agent SAC | Acción conjunta centralizada |
| Single-Agent PPO | Acción conjunta centralizada |
| MADDPG | Baseline MARL clásico (Lowe et al., 2017) |
| MARLISA | Selección secuencial iterativa (Vázquez-Canteli et al., 2020) |

### 4.8.4. Métricas y análisis estadístico

**Primarias:**
- KPIs por eje (§4.3) — 5 por eje × 7 ejes = 35 KPIs;
- HPHI 7-D;
- Score global $\Phi=\sqrt[7]{\prod_{k=1}^7\tilde J_k}$.

**Inferencia estadística:**
- **Test de Wilcoxon de rangos signados** (Wilcoxon, 1945, *Biometrics Bulletin*) para pares (algoritmo, baseline) sobre 30 episodios de prueba (5 semillas × 6 zonas).
- **Test de Friedman** para comparar simultáneamente todos los algoritmos.
- **Bootstrap intervalos de confianza 95%** con 10 000 remuestreos (Efron, 1979).
- **Corrección Holm-Bonferroni** para comparaciones múltiples.
- **Tamaño de efecto** $r=Z/\sqrt{n}$, $d$ de Cohen, $\delta$ de Cliff.

### 4.8.5. Reproducibilidad FAIR

- Licencia Apache 2.0;
- Dockerfiles versionados (CityLearn 2.6.x, MARLlib v1.x, Ray ≥2.6, PyTorch 2.x, CUDA 12.x);
- Configuraciones YAML por experimento, semillas registradas;
- DVC para versionado de datos;
- MLflow + Weights & Biases para tracking;
- Script `make reproduce` que regenera figuras y tablas.

---

## 4.9. Contextualización con el estado del arte

### 4.9.1. Comparativa formal frente a frameworks predecesores

| Característica | CityLearn v1 | CityLearn v2 | GridLearn | PowerGridworld | COHORT | **UC3M** |
|----------------|:-------------:|:-------------:|:----------:|:----------------:|:--------:|:----------:|
| Dec-POMDP axiomático | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| $N$ arbitrario | parcial | parcial | parcial | parcial | parcial | **✓** |
| Universalidad MADRL | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Power flow opcional | ✗ | ✗ | ✓ | ✓ | ✗ | **✓** |
| V2G/V2H/V2B | ✗ | ✓ | ✗ | ✗ | ✗ | **✓** |
| Degradación electroquímica | ✗ | implícita | ✗ | ✗ | ✗ | **✓ Arrhenius-Peukert-SEI** |
| Resiliencia (islanding) | ✗ | ✓ | ✗ | ✗ | ✗ | **✓ extendida** |
| Exergía ACS | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Confort adaptativo (tropicales) | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Universalidad geográfica | ✗ | parcial USA | ✗ | ✗ | ✗ | **✓** |
| Casos Perú | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Algoritmos MARL preimpl. | 2 | 3 | 2 | 2 | 1 | **18+** |
| Integración MARLlib | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ nativa** |
| KPIs holísticos | 5 | 8 | 4 | 3 | 3 | **35 (5×7 ejes) + HPHI** |

### 4.9.2. Trabajos seminales referenciados

- Vázquez-Canteli, J. R., Kämpf, J., Henze, G., Nagy, Z. (2019). *CityLearn v1.0: An OpenAI Gym Environment for Demand Response with Deep RL.* BuildSys'19, doi:10.1145/3360322.3360998.
- Vázquez-Canteli, J. R., Dey, S., Henze, G., Nagy, Z. (2020). *CityLearn: Standardizing Research in MARL for Demand Response and Urban Energy Management.* arXiv:2012.10504.
- Nweye, K. E., Liu, B., Stone, P., Nagy, Z. (2022). *Real-world challenges for multi-agent reinforcement learning in grid-interactive buildings.* Energy and AI 10:100202, doi:10.1016/j.egyai.2022.100202.
- Nweye, K. E., Kaspar, K., Buscemi, G., Fonseca, T., Pinto, G., Ghose, D. et al. (2024). *CityLearn v2: energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities.* J. Building Performance Simulation 18(1), doi:10.1080/19401493.2024.2418813.
- Pigott, A., Crozier, C., Baker, K., Nagy, Z. (2022). *GridLearn: Multiagent Reinforcement Learning for Grid-Aware Building Energy Management.* Electric Power Systems Research 213:108521.
- Biagioni, D., Zhang, X., Wald, D., Vaidhynathan, D., Chintala, R., King, J., Zamzam, A. S. (2022). *PowerGridworld.* e-Energy'22, doi:10.1145/3538637.3539616.
- Fonseca, T., Ferreira, L. L., Nweye, K., Nagy, Z. (2024). *EVLearn.* Energy Informatics, doi:10.1186/s42162-024-00445-w.
- Hu, S., Zhong, Y., Gao, M., Wang, W., Dong, H., Liang, X., Li, Z., Chang, X., Yang, Y. (2023). *MARLlib: A Scalable and Efficient Multi-Agent Reinforcement Learning Library.* JMLR 24(315):1–23.
- Bettini, M., Prorok, A., Moens, V. (2024). *BenchMARL: Benchmarking Multi-Agent Reinforcement Learning.* JMLR 25(217):1–10, arXiv:2312.01472.
- Lowe, R., Wu, Y., Tamar, A., Harb, J., Abbeel, P., Mordatch, I. (2017). *MADDPG.* NeurIPS, arXiv:1706.02275.
- Foerster, J., Farquhar, G., Afouras, T., Nardelli, N., Whiteson, S. (2018). *COMA.* AAAI.
- Yu, C., Velu, A., Vinitsky, E., Gao, J., Wang, Y., Bayen, A., Wu, Y. (2022). *MAPPO.* NeurIPS Datasets & Benchmarks, arXiv:2103.01955.
- Iqbal, S., Sha, F. (2019). *MAAC.* ICML, PMLR 97:2961–2970.
- Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., Yang, Y. (2022). *HATRPO/HAPPO.* ICLR, arXiv:2109.11251.
- Zhong, Y., Kuba, J. G., Hu, S., Ji, J., Yang, Y. (2023). *Heterogeneous-Agent Reinforcement Learning.* JMLR 25, arXiv:2304.09870.
- Ackermann, J., Gabler, V., Osa, T., Sugiyama, M. (2019). *MATD3.* arXiv:1910.01465.
- Rashid, T., Samvelyan, M., Schroeder, C., Farquhar, G., Foerster, J., Whiteson, S. (2018). *QMIX.* ICML, arXiv:1803.11485.
- Sunehag, P. et al. (2017). *VDN.* arXiv:1706.05296.
- Peng, B., Rashid, T., de Witt, C. S., Kamienny, P. A., Torr, P., Boehmer, W., Whiteson, S. (2021). *FACMAC.* NeurIPS.
- Haarnoja, T., Zhou, A., Abbeel, P., Levine, S. (2018). *Soft Actor-Critic.* ICML.
- Oliehoek, F. A., Amato, C. (2016). *A Concise Introduction to Decentralized POMDPs.* Springer Briefs.
- Roijers, D. M., Vamplew, P., Whiteson, S., Dazeley, R. (2013). *A Survey of Multi-Objective Sequential Decision-Making.* JAIR 48:67–113.
- Vamplew, P., Dazeley, R., Berry, A., Issabekov, R., Dekker, E. (2011). *Empirical evaluation methods for multiobjective RL.* Machine Learning 84(1-2):51–80.
- Zitzler, E., Thiele, L. (1999). *Multiobjective evolutionary algorithms: a comparative case study and the strength Pareto approach.* IEEE TEC 3(4):257–271.
- de Dear, R., Brager, G. (1998). *Developing an adaptive model of thermal comfort and preference.* ASHRAE Transactions 104(1):145–167.
- Brager, G., de Dear, R. (2001). *Climate, comfort & natural ventilation: a new adaptive comfort standard for ASHRAE 55.*
- Bloom, I. et al. (2001). *An accelerated calendar and cycle life study of Li-ion cells.* J. Power Sources 101(2):238–247.
- Wang, J. et al. (2011). *Cycle-life model for graphite-LiFePO4 cells.* J. Power Sources 196(8):3942–3948.
- Bejan, A. (2016). *Advanced Engineering Thermodynamics*, 4ª ed., Wiley.
- Peel, M. C., Finlayson, B. L., McMahon, T. A. (2007). *Updated world map of the Köppen-Geiger climate classification.* HESS 11(5):1633–1644.

### 4.9.3. Normativa y estándares

- IPCC AR6 WG III (2022). *Mitigation of Climate Change.* Cambridge University Press.
- IEA (2023). *Net Zero Roadmap 2023 Update.*
- ASHRAE Standard 55-2020. *Thermal Environmental Conditions for Human Occupancy.*
- ISO 7730:2005. *Ergonomics of the thermal environment.*
- IEEE 1547-2018. *Standard for Interconnection of Distributed Energy Resources.*
- Reglamento (UE) 2016/1388. *Network Code on Demand Connection.*
- IEC 62660-2:2018. *Secondary lithium-ion cells for EV — Reliability and abuse testing.*
- IEC 61851-1. *EV conductive charging system.*
- EN 806-2:2005. *Specification for installations inside buildings conveying water for human consumption.*
- UNE 100030:2017. *Prevención y control de la proliferación de Legionella.*
- Real Decreto 244/2019 (España). *Autoconsumo eléctrico.*
- **Perú**: Código Nacional de Electricidad (NEC); Norma Técnica EM.080 (Instalaciones con Energía Solar); DS 020-2013-EM (sistemas fotovoltaicos rurales); OSINERGMIN tarifas BT5B, MT3, MT4; COES regulación del SEIN.

---

## 4.10. Síntesis, aportes científicos y discusión preliminar

### 4.10.1. Resumen de aportes originales a la ciencia

Este capítulo aporta a la literatura los siguientes elementos originales:

**Aporte 1 — Formalización meta-Dec-POMDP universal.** Tupla 11-aria (Def. inicial §4.2.1) que generaliza la formulación canónica de Bernstein et al. (2002) y Oliehoek y Amato (2016) al régimen multi-objetivo cooperativo descentralizado con cardinalidad arbitraria y ponderaciones explícitas en simplex.

**Aporte 2 — Building-Asset-Climate Tensor (BACT).** Objeto matemático original (Def. 4.1) que codifica universalmente cualquier edificio en cualquier sitio.

**Aporte 3 — Operador de recompensa holístico escalarizado.** Demostraciones de consistencia (Teor. 4.3), continuidad/Lipschitz (Prop. 4.4) y acotamiento (Lema 4.2) para los siete ejes acoplados.

**Aporte 4 — Teorema de invariancia geográfica (Teor. 4.10).** Garantiza transferibilidad zero/few-shot entre zonas Köppen-Geiger.

**Aporte 5 — Universalidad algorítmica MADRL (Teor. 4.8).** El UC3M soporta cualquier algoritmo MADRL conforme a la Def. 4.4 vía MARLlib AlgorithmFactory.

**Aporte 6 — Holistic Pareto Hypervolume Index (HPHI).** Métrica original 7-D normalizada (Def. 4.6) para evaluación multiobjetivo invariante de escala.

**Aporte 7 — Tropicalización del confort.** Primera incorporación del modelo adaptativo De Dear-Brager en un framework MARL para edificios, validada en Iquitos y Tarapoto.

**Aporte 8 — Degradación electroquímica explícita.** Modelo Arrhenius-Peukert-SEI integrado en la recompensa, con sensibilidad térmica para climas cálidos peruanos.

**Aporte 9 — Cobertura sistemática de los siete ejes con 35 KPIs cuantitativos** y referencias normativas internacionales y nacionales.

**Aporte 10 — Casos de uso peruanos.** Primer benchmark MARL para edificios en costa árida (Lima), sierra altoandina (Cusco, Puno) y selva amazónica (Iquitos).

### 4.10.2. Discusión final

El UC3M sienta las bases sobre las que los siguientes capítulos de esta tesis (Cap. V experimentos comparativos, Cap. VI análisis de la frontera de Pareto, Cap. VII discusión e implicaciones, Cap. VIII conclusiones) desplegarán la evaluación empírica del framework. Su valor científico radica no en ser una extensión incremental de CityLearn v3 sino en constituir un **benchmark universal verificable, reproducible y portable** para la investigación en comunidades energéticas inteligentes controladas por aprendizaje por refuerzo multi-agente, con cobertura plena de los siete ejes operacionales y casos de uso explícitos para climas peruanos y mundiales.

La adopción del UC3M en la comunidad científica internacional —cuya viabilidad se sustenta en (i) su construcción sobre estándares abiertos (Gymnasium, PettingZoo, Ray, PyTorch), (ii) su licenciamiento Apache 2.0, (iii) sus garantías formales de convergencia y universalidad, y (iv) su catálogo exhaustivo de 35 KPIs sobre los siete ejes— posiciona la presente tesis doctoral como una contribución de impacto duradero a la transición energética justa en regiones tradicionalmente sub-representadas en la literatura, como los Andes y la Amazonía sudamericanas.

---

*Fin del Capítulo IV.*
