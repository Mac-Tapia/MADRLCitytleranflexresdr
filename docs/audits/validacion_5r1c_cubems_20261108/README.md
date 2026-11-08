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

## Resultados (prueba fuera de muestra, 20 zonas)

| Criterio | Resultado |
|---|---|
| Energía mensual, G14 (NMBE ±5 %, CV(RMSE) ≤ 15 %) | **7 de 20** zonas cumplen; mediana de \|NMBE\| 7,7 % |
| Energía horaria, G14 (NMBE ±10 %, CV(RMSE) ≤ 30 %) | **0 de 20**; mediana del CV(RMSE) 51,6 % |
| Temperatura interior | RMSE mediano 2,46 °C; mediana del 28 % de las horas dentro de ±1 °C |
| Frente a la persistencia (RMSE mediano 1,19 °C) | **0 de 20** zonas la mejoran |
| Parámetros en el límite | 10 de 20 zonas (casi siempre el COP) |

## Conclusión

- **Energía agregada:** el método 5R1C reproduce de forma aceptable la energía mensual en un tercio de las zonas y con sesgo moderado en el resto.
- **Hora a hora:** no reproduce la energía horaria del aire acondicionado ni la dinámica de la temperatura interior de un edificio tropical real.
- **Validación:** el modelo **no queda validado** como modelo dinámico.

Esto confirma la declaración de D-V6-53 ("calibrado a facturas, no validado") y agrega una limitación medida:

> La respuesta horaria de la temperatura al aire acondicionado del entorno de entrenamiento es una aproximación física de primer orden. En un edificio tropical medido, su error mediano es de unos 2,5 °C, peor que repetir la temperatura de la hora anterior.

Los KPI de energía y costo agregados son más confiables que los de confort hora a hora. Los resultados de confort de la tesis deben leerse con esta limitación.

## Causas probables

- Una sola zona térmica (5R1C) para zonas abiertas con equipos que ciclan dentro de la hora.
- COP constante.
- Ocupación supuesta.
- Ganancias solares por GHI horizontal, sin orientación ni sombras.
- Área por zona desconocida.

Mejorar exige datos que este conjunto no da (planos con áreas, capacidad de los equipos) o un modelo de más orden. Ninguna de esas mejoras se hace sin decisión del propietario.
