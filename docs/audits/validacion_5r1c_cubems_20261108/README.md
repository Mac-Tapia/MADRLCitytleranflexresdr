# Validación del método 5R1C con datos medidos tropicales (CU-BEMS), 2026-11-08

**Spec:** SPEC-016 D-V6-52 y D-V6-53 · **Herramienta:** `tools/validation/validate_5r1c_cubems.py` · **Resultado:** `data/validation/cubems/validation_5r1c.json`

## Por qué

No hay temperaturas interiores ni medidores del aire acondicionado en los edificios de Iquitos, y no existe un conjunto abierto de la Amazonía. El 5R1C de `iquitos_v6` quedó "calibrado a facturas, no validado". Esta prueba valida el **método**, no los parámetros de Iquitos, en un edificio tropical con mediciones reales.

## Datos

- **CU-BEMS** (Pipattanasomporn et al., 2020, *Scientific Data* 7:241; CC BY 4.0; figshare `10.6084/m9.figshare.11726517`, versión 6, MD5 verificado de los 14 CSV).
  - Edificio: oficinas de 7 plantas y 11 700 m² en Bangkok.
  - Por zona y minuto: potencia de cada aire acondicionado, luces y enchufes, y temperatura y humedad interior.
  - Periodo: julio de 2018 a diciembre de 2019.
- **Clima:** NASA POWER horario en el sitio (13,738 N; 100,532 E), la misma fuente que Iquitos.
- **Zonas:** las 20 con aire acondicionado y sensor, de las plantas 3 a 7.

## Método

El mismo código del entrenamiento (`citylearn.v3.thermal`, `thermal_calibration`).

- **Parámetros ajustados por zona (4):** conductancia de la envolvente, apertura solar, fracción de la planta que climatiza y COP del equipo.
- **Calibración:** julio de 2018 a junio de 2019. **Prueba fuera de muestra:** julio a diciembre de 2019.
- **Energía:** la carga que mantiene la temperatura medida en las horas con aire acondicionado ÷ COP, frente a la electricidad medida del aire acondicionado. Criterios de ASHRAE Guideline 14.
- **Dinámica:** la temperatura que da el modelo con la electricidad medida × COP, frente a la temperatura medida. G14 no fija criterio para la temperatura; se compara con la persistencia (la temperatura de la hora anterior).

### Supuestos declarados

- Área de cada planta = 11 700 / 7 m².
- Ocupación y ventilación de la fila de oficinas de EM.030.
- Hora ocupada = hora con el aire acondicionado por encima del 5 % de su máximo.
- Irradiancia = GHI horizontal.

## Resultados

### Primera versión: calibración solo con energía y temperatura en simulación libre

| Criterio | Resultado |
|---|---|
| Energía mensual, G14 | 7 de 20 |
| Energía horaria, G14 | 0 de 20 (CV(RMSE) mediano 51,6 %) |
| Temperatura en simulación libre | RMSE mediano 2,46 °C |

En esta versión, la comparación con la persistencia, que predice a 1 h, no era equivalente a una simulación de 6 meses.

### Segunda versión: identificación con error de salida (práctica de los modelos de caja gris)

Se ajustan a la vez la temperatura medida (con la electricidad medida del aire acondicionado) y la energía. Se añade la capacidad térmica como quinto parámetro (factor sobre la clase media de ISO 13790, tabla 12). La temperatura se evalúa a 1 h, a 24 h y en simulación libre, cada una con su referencia ingenua.

| Criterio (prueba fuera de muestra, 20 zonas) | Resultado |
|---|---|
| Temperatura a 24 h frente a la misma hora del día anterior | **20/20 zonas mejor**; RMSE mediano 1,03 °C frente a 1,95 °C |
| Temperatura a 1 h frente a la persistencia | 13/20 mejor; 1,25 °C frente a 1,19 °C (empate práctico) |
| Temperatura en simulación libre de 6 meses | RMSE mediano **1,68 °C**; 49 % de las horas dentro de ±1 °C |
| Energía mensual, G14 | 6/20 |
| Energía horaria, G14 | 0/20 (CV(RMSE) mediano 56,9 %) |
| Parámetros en el límite | 16/20 (COP en 11) |

### Parámetros identificados (percentiles 10/50/90)

| Parámetro | P10 | P50 | P90 |
|---|---|---|---|
| Envolvente (W/m²K) | 0,33 | 0,69 | 2,66 |
| Apertura solar (fracción del área, con GHI horizontal) | 0,000 | 0,003 | 0,011 |
| Fracción climatizada | 0,24 | 0,43 | 1,00 |
| Factor de capacidad térmica | 1,22 | **2,27** | 3,69 |

## Conclusión

- **Dinámica de temperatura:** con la identificación correcta, la estructura 5R1C es **útil**. A 24 h supera a la referencia en todas las zonas, y en simulación libre queda cerca del ~1 °C que informa la literatura para modelos RC en simulación multipaso (ORNL: 0,89 °C; villa en clima cálido: 1,16 °C).
- **Energía horaria por zona:** **no cumple** G14. El COP en el límite apunta a equipos que ciclan dentro de la hora y a una sola zona térmica. La energía mensual cumple en un tercio de las zonas.
- **Para Iquitos:** el parámetro que fija la dinámica y que las facturas no identifican es la capacidad térmica. Se adopta la mediana medida en este edificio tropical análogo (2,27 veces la clase media) en lugar de la clase media supuesta (D-V6-56). La envolvente y la apertura siguen calibradas con las facturas.

El alcance sigue siendo el **método en un edificio análogo**: los parámetros de Iquitos no están validados con medición propia.

Los datos crudos se borraron el 2026-11-08 por decisión del propietario, para liberar espacio. Para repetir la validación, hay que descargar los 14 CSV de figshare (`10.6084/m9.figshare.11726517`) y el clima de NASA POWER (13,738 N; 100,532 E; 2018-06-30 a 2019-12-31) en `data/validation/cubems/raw/`.

## Diagnóstico de la energía horaria (tarjeta thermal-g14, 2026-11-08): trabajo incompleto

**Estado: diagnóstico parcial, sin mejora del modelo.** El propietario decidió que G14 sea solo informativo y el trabajo se cerró antes de ajustar variantes. **No se ajustó ni se seleccionó ninguna variante nueva del 5R1C, y no se puntuó nada nuevo en el periodo de prueba** (julio a diciembre de 2019). Los resultados de arriba siguen como estaban: energía horaria 0/20 y mensual 6/20. Esta sección no acredita cumplimiento de G14 ni lo descarta.

**Herramienta:** `tools/validation/diagnose_cubems_hourly.py` · **Resultado:** `data/validation/cubems/diagnosis_hourly_train_only.json` · **Descarga:** `tools/validation/fetch_cubems_raw.py`

La herramienta corta los datos en 2019-07-01 al cargarlos. Todas las cifras de esta sección son del periodo de entrenamiento: promedios de julio de 2018 a marzo de 2019, puntuados en abril a junio de 2019.

### Lo que se encontró

1. **El resultado anterior de energía usaba datos de la prueba como entrada.** En `validate_5r1c_cubems.py` (líneas 99 y 100) las horas con aire acondicionado salen de la potencia medida, también en la prueba. La consigna (línea 123) es la temperatura medida, también en la prueba. Por eso el 56,9 % no es una predicción: el modelo ya sabía qué horas y qué días funcionó el equipo. El error de una predicción sin esos datos no se midió. Las pruebas de temperatura son otro caso: dar la potencia medida para predecir la temperatura es correcto. En el ajuste de la capacidad térmica (D-V6-56) solo se usan horas de entrenamiento, salvo el umbral de encendido (línea 99), que se calcula con toda la serie; ese efecto no se cuantificó.
2. **No se confirmó que los equipos ciclen dentro de la hora, como sugería la conclusión anterior.** En las horas con al menos 50 minutos en marcha, la mediana es de 0,157 cambios de encendido o apagado por equipo y hora, uno cada 6 horas aproximadamente (de 0,049 a 0,305 según la zona). Lo que se vio, inspeccionando el minuto a minuto de una zona en un día, es un escalón de potencia (unos 25 kW y luego unos 13 kW), que esta medida no cuenta como ciclo.
3. **La operación parece programada de forma central.** Es una inferencia a partir del patrón; el artículo de CU-BEMS no lo dice en los pasajes leídos. En las plantas 3 a 7 el equipo arranca hacia las 07:55, para a mediodía y vuelve a las 13:00, y las horas 7, 11 y 16 son parciales. El modelo anterior da carga de hora completa a toda hora por encima del 5 %; que eso cause parte del error es una hipótesis sin medir. La planta 7 (zonas 1 y 2) tiene además uso por la tarde en algunos meses. Las plantas 1 y 2, fuera de las 20 zonas, no siguen este patrón.
4. **Hay días laborables en que se para casi todo el edificio.** De 260 días laborables con datos, en 243 funcionó más del 90 % de las zonas y en 17 funcionó menos del 30 %, sin ningún caso intermedio. Esos días concentran una mediana del 35 % del error cuadrático de la referencia por zona. Las fechas parecen feriados de Tailandia (por ejemplo, Songkran), pero **esto no está verificado con una fuente**: las páginas consultadas del Banco de Tailandia y de timeanddate no se pudieron abrir.

### Referencia por día de la semana y hora (abril a junio de 2019, 20 zonas)

| Medida | Resultado |
|---|---|
| Referencia, CV(RMSE) horario mediano | 96,0 % |
| Referencia, zonas que cumplen G14 horario | 0/20 |
| Referencia, zonas que cumplen G14 mensual | 0/20 |
| Oráculo que conoce la energía real de cada día, CV(RMSE) horario mediano | 32,3 % (9/20 zonas en 30 % o menos) |

Reparto del error cuadrático de la referencia (medianas por zona): 54 % en las horas 8 a 11, 43 % en las horas 13 a 16 y 37 % en lunes. Son cortes que se solapan, así que no suman 100 %.

- **Estas cifras no son una cota de lo alcanzable.** El oráculo usa la energía medida de cada día, que un modelo no tiene, y mantiene fija la forma del perfil, de modo que un modelo con mejor forma podría superarlo. Solo indican que gran parte del error de la referencia está en el nivel de energía de cada día y no en la forma dentro del día.
- **No son comparables con el 56,9 %,** que es de otro periodo y usa los datos de la prueba. El tramo de abril a junio incluye el mes más exigente observado (abril) y varios días de parada, así que es difícil para un perfil aprendido antes.

### Alcance de G14

Según la edición 2002 (la única abierta; **no se consultó la edición 2014**), el enfoque de simulación calibrada se define para todo el edificio («whole building calibrated simulation», 5.1.3) y exige NMBE de 5 % y CV(RMSE) de 15 % mensuales o, con datos horarios, 10 % y 30 %. Su alcance habla de instalaciones o medidores individuales (2.2). En los pasajes leídos no hay un criterio por zona. Aplicarlo por zona es entonces una extensión nuestra, no el uso previsto, y debe describirse así. Lo apoya el artículo de SimBuild 2018 citado abajo, que indica que esos objetivos están pensados para datos horarios de todo el edificio.

### Fuentes abiertas (solo los pasajes pertinentes, no lectura completa)

- ASHRAE Guideline 14-2002, copia alojada por un tercero: https://www.eeperformance.org/uploads/8/6/5/0/8650231/ashrae_guideline_14-2002_measurement_of_energy_and_demand_saving.pdf
- Pipattanasomporn et al. (2020), *Scientific Data* 7:241: https://doi.org/10.1038/s41597-020-00582-3 (55 equipos; sensores retirados del 15 de septiembre de 2018 al 5 de marzo de 2019).
- *Advances in Calibration of Building Energy Models to Time Series Data*, SimBuild 2018: https://doi.org/10.26868/25746308.2018.c059
- *Is Monthly and Whole Building Level Calibration Enough?*, SimBuild 2014: https://doi.org/10.26868/25746308.2014.23
- Kim et al., *Development of an RC Model Including Set-point Temperature for Predicting Room Temperature and Cooling Energy*, Building Simulation 2025: https://doi.org/10.26868/25222708.2025.1793 (informa CV(RMSE) de 24,7 % en energía de refrigeración con un RC; no se revisaron sus condiciones ni si es fuera de muestra).
- CalTRACK, métodos (intervalos de hora de la semana): https://docs.caltrack.org/en/latest/methods.html

No se abrió ningún estudio que aplique G14 horario por zona con un RC en un edificio comparable, así que la búsqueda de literatura queda incompleta.

### Sin terminar

- Variantes de calendario, horario, COP, carga latente, consigna y ganancias: ninguna ajustada; **no hay tabla de variantes**.
- Prueba final y cuentas de G14 por zona, planta y edificio con un modelo nuevo: no hechas.
- La referencia en el periodo de prueba, la regresión de hora de la semana y temperatura, y una estimación formal de la cota: no hechas.
- Verificación de los feriados con una fuente oficial: no hecha.
- Si la conductancia, el COP y la fracción climatizada se confunden entre sí y por eso el COP queda en su límite: hipótesis sin probar.

### Qué se transfiere a Iquitos

**Nada de esto cambia el método ni el conjunto de datos: no hay motivo aquí para reconstruir `iquitos_v6_trial12`.** No se demostró ninguna mejora, y no se tocó `CityLearn/`, `tools/dataset/` ni `configs/`. Una futura mejora con horarios aprendidos de la potencia medida no se transferiría, porque Iquitos no tiene medidores de aire acondicionado, ni luces, enchufes u horarios medidos, ni temperatura interior. Un calendario de feriados sí sería un dato público disponible, pero no se comprobó si el constructor del conjunto ya los contempla ni si ayudaría allí.

Los datos crudos se descargaron de nuevo para este diagnóstico (MD5 de los 14 CSV verificados contra figshare, versión 6) y se borraron al terminar.
