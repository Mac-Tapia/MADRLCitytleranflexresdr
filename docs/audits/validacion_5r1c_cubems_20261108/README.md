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
