# Carga estocástica de VE: validación con la literatura (2026-11-07)

Pedido del propietario: validar el diseño estocástico de llegadas, SOC y cargadores con tesis, artículos recientes y proyectos. Revisión de solo lectura. Las citas no verificadas en el texto completo se marcan como tales.

## Diseño que se validó

- **Presencia diaria:** cada vehículo, cada día, con probabilidad igual al factor de ocupación del día del edificio (D-V6-39).
- **Hora de llegada:** al azar dentro de su ventana (D-V6-29).
- **Distancia diaria:** lognormal alrededor de la media de la clase. De ella sale el SOC al llegar, que se arrastra entre sesiones (D-V6-31, D-V6-40).
- **Tomas:** el mínimo que atiende todas las sesiones (D-V6-37), en equipos de dos tomas (D-V6-38).
- **Dirección:** solo las camionetas descargan, por V2L.

## Hallazgos

### Llegadas y permanencia

- **ACN-Data** (Lee, Li y Low, 2019, ACM e-Energy, <https://doi.org/10.1145/3307772.3328313>). Lugar de trabajo cerrado (JPL):
  - llegadas en un pico estrecho de 6 a 9 h, con cerca del 30 % de las sesiones en la hora de las 8;
  - salidas de 16 a 18 h, dispersas;
  - casi sin uso en fines de semana;
  - llegada, permanencia y energía modeladas con una mezcla gaussiana (GMM).
- **ElaadNL** (Lahariya, Benoit y Develder, 2020, *Energies* 13(16):4211). Carga pública abierta:
  - Poisson no homogéneo por mes, tipo de día y hora, validado con Kolmogórov-Smirnov;
  - permanencia y energía con GMM.
- **Poisson frente a Bernoulli:** no se encontró una Bernoulli por vehículo prescrita en la literatura. Para una flota finita y conocida, la binomial (Bernoulli por vehículo) es la forma coherente con una población cerrada; Poisson corresponde a una población abierta. Esto es inferencia de teoría de colas, no una cita.

### Distancia diaria y SOC

- **Lognormal, Weibull y gamma:** Plötz, Jakobsson y Sprei (2017), *Transportation Research Part B* 101:213–227, <https://doi.org/10.1016/j.trb.2017.04.008>. Con 190 000 días de autos, Weibull ajusta mejor a la mayoría; la lognormal es más conservadora.
- **Flota institucional:** He y Yamamoto (2020), *Sustainability* 12(2):690. La lognormal es la mejor de cinco distribuciones simples.
- **Motos del Sudeste Asiático:** Mitsukawa et al. (2019), *Honda R&D Technical Review* 31(1), informe industrial sin revisión por pares. Moda de 11–20 km/día y el 80 % o más por debajo de 50 km/día. **Los 40 km/día del modelo para las motos parecen altos.**
- **Mototaxis:** las cifras de India (50–70 km/día) son autodeclaradas o de mercado. No se encontraron datos medidos para Perú ni Latinoamérica.
- **SOC aleatorio derivado de la distancia:** Qian et al. (2011), *IEEE Trans. Power Systems* 26(2):802–810, <https://doi.org/10.1109/TPWRS.2010.2057456>.

### Dimensionado de cargadores

- **Simulación con nivel de servicio:** Graber et al. (2017) usan Monte Carlo con nivel de satisfacción (cita no verificada). Marchi et al. (2018) combinan teoría de colas con simulación de eventos discretos en un campus.
- **Tesis de maestría de la Universidad de Twente** (<https://purl.utwente.nl/essays/87721>): planificar al menos el 95 % de los puntos calculados.
- **Modelos de pérdida:** Erlang B (M/G/c/c) supone llegadas de Poisson. Para una flota finita corresponde Engset; esto es teoría estándar, sin cita aplicada.
- **Vehículos por cargador:** no se encontró una razón revisada por pares.

### V2G, V2B y V2L

- **Dos ruedas:** solo hay V2G con baterías intercambiables en estaciones (Chien y Hsieh, 2025, *Sustainable Cities and Society* 118:106004). **Ninguna fuente trata a motos o mototaxis enchufados como bidireccionales**: la decisión D-V6-33 es coherente con la literatura.
- **V2L hacia un edificio:** no se encontró un modelo revisado por pares. El tope de 6,6 kW se justifica con la ficha del vehículo (D-V6-32).

## Correcciones que propone la revisión

| # | Corrección | Fuente |
|---|---|---|
| 1 | Hora de llegada con pico, no uniforme: normal truncada o forma empírica con máximo cerca de 1 h tras la apertura | Lee et al. 2019 |
| 2 | Salida dispersa alrededor del cierre, no todas a la misma hora | Lee et al. 2019; Lahariya et al. 2020 |
| 3 | Los feriados y fines de semana anulan la presencia de todos a la vez; una Bernoulli independiente por vehículo no lo capta | inferencia |
| 4 | El SOC de llegada descuenta solo los km recorridos desde la última carga | inferencia |
| 5 | Lognormal truncada a la autonomía, citando que es conservadora frente a Weibull | Plötz et al. 2017; He y Yamamoto 2020 |
| 6 | Revisar las medias de km/día: motos de 11 a 20 km (moda); mototaxis probablemente más de 50 km si trabajan todo el día | Honda 2019; informes de India |
| 7 | Tomas con un nivel de servicio sobre varias semillas (por ejemplo, el 95 % de los días sin sesiones sin atender), en lugar del 100 % de un solo sorteo | tesis de Twente; Graber et al. |
| 8 | Solo las camionetas con V2L/V2B; motos y mototaxis solo cargan | coherente con la literatura |

## Lo que no se encontró

- Una Bernoulli por vehículo prescrita en la literatura.
- Kilómetros diarios medidos de mototaxis o de camionetas eléctricas en Perú o Latinoamérica.
- Un modelo de V2L hacia un edificio revisado por pares.
- Una razón de vehículos por cargador revisada por pares.
- Las cifras de las tesis del IIT Delhi (solo se leyó el índice) y de Nagoya (error 503).
