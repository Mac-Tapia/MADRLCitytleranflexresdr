# Module E — Documentacion de Decisiones de Diseno

Registro completo de decisiones tecnicas, correcciones aplicadas, datos confirmados
vs estimados, y justificacion de cada eleccion de diseno para el dataset Iquitos.
Permite trazabilidad academica y reproducibilidad del dataset.

---

## Tabla Global de Decisiones de Diseno

| Decision | Justificacion | Alternativa descartada |
|---------|---------------|----------------------|
| PVGIS-ERA5 + NASA POWER | Gratuito, sin API key (PVGIS); cobertura lat/lon Iquitos | ERA5 (cdsapi requiere registro + quota) |
| Sandia SAPM | Base calibrada empiricamente, integrada en pvlib | PVWatts (simplificado, menos preciso) |
| DoD = 0.80 LFP | Balance seguridad/capacidad; 3000+ ciclos a 80% DoD | DoD = 0.90 NMC (menos ciclos, mayor riesgo) |
| COP 2.5/2.8/3.0 por tipo | ASHRAE 2022 + condiciones tropicales reales | COP uniforme (no refleja diferencias tecnologicas) |
| T_indoor con modelo RC | OE.1 pre-enfriamiento requiere senal termica real | Vacio (impide aprendizaje de estrategia termica) |
| Carbon intensity variable | Senal de despacho horaria para OE.2 | Constante 0.79 (no incentiva despacho solar) |
| Tarifa MT (no BT) | 17 edificios son grandes consumidores con acometida MT | BT (incorrecta para hospitales, mall, aeropuerto) |
| 50 charger files | Refleja parque vehicular real por edificio | 1 charger por edificio (no representa diversidad) |
| cooling_demand no-cero | OE.1 y OE.3 dependen de senal de carga termica real | Cero (no se puede optimizar pre-enfriamiento) |
| inactive_observations=[] | HAPPO/MASAC/MATD3/MAAC usan todas las observaciones | Desactivar cols. (reduce espacio de observacion) |

---

## Decisiones por Tipo de CSV

### Building_X.csv

| Decision | Justificacion |
|---------|---------------|
| Columnas 5/6/7 con valores reales (no vacias) | OE.1 requiere senal termica para aprender pre-enfriamiento; demo original las deja vacias |
| non_shiftable_load excluye AC | Separacion CityLearn v2: HVAC va a cooling_demand para que el agente lo controle |
| Ruido gaussiano ±2% en non_shiftable_load | Realismo estadistico; evita series exactamente periodicas que facilitan overfitting |
| Seed = bldg_id para RNG | Reproducibilidad entre ejecuciones sin fijar semilla global |
| dhw_demand = 0 excepto B5/B11/B12 | Solo edificios con ACS significativo (hotel, hospitales); resto no tiene demanda termica ACS |
| heating_demand = 0 siempre | Iquitos T_min = 24°C; no existe calefaccion en clima tropical amazónico |

### weather.csv

| Decision | Justificacion |
|---------|---------------|
| PVGIS 2023 + NASA POWER 2024-2025 | PVGIS-ERA5 cubre hasta ~2023; anios recientes requieren NASA POWER |
| Cache parquet en .cache/weather/ | Evita re-descargar 3 anios de datos en cada ejecucion |
| Predicciones por shift(-N).ffill() | Replica exacta del formato CityLearn; ultimas filas con ffill evitan NaN finales |

### carbon_intensity.csv

| Decision | Justificacion |
|---------|---------------|
| FE_diesel = 0.79 kg CO2/kWh | Fuente oficial MINAM RAGEI 2019 para sistemas aislados diesel Peru |
| Variacion horaria con GHI | Incentiva al agente a preferir horas solares (baja intensidad) = senal OE.2 efectiva |
| Archivo metadata JSON | Trazabilidad academica: DOI, URL, fecha de acceso, valores exactos usados |

### pricing.csv

| Decision | Justificacion |
|---------|---------------|
| Descarga OSINERGMIN MT mensual | Precios reales con variacion inflacionaria 2023-2025 |
| Fallback hardcoded si falla descarga | Garantiza que el script funciona offline con valores representativos |
| Punta 18:00-22:59, diferencia 46% | Patron TOU real OSINERGMIN MT Iquitos; diferencia maxima para entrenamiento MADRL |

### charger_X_Y.csv

| Decision | Justificacion |
|---------|---------------|
| seed = bldg_id*100 + charger_idx | Cada cargador tiene secuencia RNG independiente y reproducible |
| 90% probabilidad dia activo | Balance realismo (no todos los dias hay EV) vs cobertura de datos |
| Gaussian ±1h en hora llegada | Variabilidad real de llegada de vehiculos institucionales |
| SOC llegada uniforme [min, max] | Incertidumbre real del estado de carga al llegar |

---

## Correcciones Aplicadas Durante el Diseno

### B5 Hotel El Dorado Plaza
- **Problema**: estimado inicial 90-100 habitaciones sin fuente verificada
- **Correccion**: 65 habitaciones confirmadas (Expedia 2026, Booking 2026)
- **Impacto**: AC 199 -> 150.5 kW; ACS 780 -> 614 kWh_th/dia
- **Fecha**: durante sesion de diseno del plan

### B15 Colegio Nacional CNI
- **Problema**: AC estimado sin considerar talleres vocacionales
- **Correccion**: AC 45 -> 48 kW tras confirmar taller arte + taller cocina (MINEDU Identicole)
- **Impacto**: cooling_peak actualizado; non_shiftable_load SHIFTABLE incluye horno ceramica y cocina
- **Fecha**: durante sesion de diseno del plan

### B8 Escuela Tecnica PNP
- **Problema**: datos de consumo real (297 kWh/dia) muy bajos para campus de 21 000 m2
- **Explicacion**: medidor especifico del estudio GD-Iquitos V3 corresponde a una subarea del campus
- **Decision**: usar NON_SHIFTABLE_BASE e inventario de equipos completo; consumo real como referencia de calibracion parcial
- **Pendiente**: confirmar si el medidor cubre todo el campus o solo pabellones educativos

---

## Datos Confirmados vs Estimados por Edificio

| # | Edificio | Datos confirmados (fuente web) | Datos estimados (metodo) |
|---|---------|-------------------------------|-------------------------|
| 1 | Electro Oriente | AC real (inventario usuario), SCADA/WatchGuard (xentic.com.pe), consumo real GD-V3 | area_techada (plano ciudad) |
| 2 | Champios | Tipo deportivo multidisciplinar Iquitos | TODO: inventario AC, area_techada |
| 3 | Aeropuerto IQT | Terminal planta baja, ISO 9001, servicios (Wikipedia), 24h | area_techada (foto satelital) |
| 4 | Precio UNO | Hiperbodega gran superficie, Av. Ejercito 1393 (Tiendeo) | AC total, area_techada |
| 5 | Hotel El Dorado | 65 hab. (Expedia 2026), amenidades completas (amazingperu.com) | area_techada (foto satelital) |
| 6 | Mall Aventura | 51 300 m2, 110 tiendas, 3 pisos, Aug 2023 (Wikipedia + mallaventura.pe) | AC total (densidad W/m2 Chow 2002) |
| 7 | UNAP Zungarococha | 5 facultades, CIEFOR, fibra optica (unapiquitos.edu.pe), consumo real GD-V3 | area_techada estimada |
| 8 | Escuela PNP | 750 alumnos, 97 180 m2 campus, 40M soles (MININTER) | AC total, area_techada techada |
| 9 | Complejo CNI | 24 576 espectadores, cesped artificial (Wikipedia + fichajes.com) | AC total, area_techada |
| 10 | Gobierno Regional | Horario L-V 07-15h, 5 gerencias (regionloreto.gob.pe), consumo real GD-V3 | area_techada |
| 11 | Hospital Regional | 176 camas, 35 especialidades, 6 pisos (hrloreto.gob.pe + Doctoralia), consumo real GD-V3 | area techada estimada |
| 12 | EsSalud Hospital III | 11 camas UCI, 12 ventiladores, 3 quirofanos, 600 consult/dia (essalud.gob.pe), consumo GD-V3 | area_techada |
| 13 | Facultad Economia UNAP | FACEN 5 escuelas, lab. computo (enlinea.unapiquitos.edu.pe), consumo real GD-V3 | area_techada |
| 14 | ENAPU | Muelles, almacenes, equipos portuarios (enapu.com.pe), consumo real GD-V3 | area_techada |
| 15 | Colegio CNI | 2 326 alumnos, instalaciones (MINEDU Identicole), consumo real GD-V3 | area_techada |
| 16 | I.E. San Juan | Piscina, coliseo, biblioteca tipo III (iesanjuan.edu.pe + MINEDU) | consumo real, area_techada |
| 17 | IEST Publico | 7 carreras, lab. mecatronica (logrosperu.com + deperu.com) | consumo real, area_techada |

---

## Pendientes de Confirmacion con el Usuario

| Edificio | Dato pendiente | Por que se necesita |
|---------|---------------|---------------------|
| B2 Champios | area_techada real y AC exacto | Mejora precision generacion FV y cooling_demand |
| B3 Aeropuerto | area_techada real techada | Mejora sizing FV (actualmente 6 000 m2 area total) |
| B5 Hotel | area_techada real (techo usable) | Mejora sizing FV |
| B9 Complejo CNI | area_techada real techada | Mejora sizing FV |
| B16 I.E. San Juan | consumo real kWh/mes (no en GD-V3) | Calibracion non_shiftable_load |
| B17 IEST Publico | consumo real kWh/mes | Calibracion non_shiftable_load |

---

## Fuentes Bibliograficas de Referencia del Dataset

### Consumo por tipo de edificio

| Fuente | Dato clave |
|--------|-----------|
| Chow et al. (2002) ScienceDirect Hong Kong malls subtropical | Mall: 391-454 kWh/m2/anio; AC+iluminacion = 85% consumo |
| Chang et al. (2024) ScienceDirect hospitales China clima calido | Hospital: 113-297 kWh/m2/anio (promedio ~200) |
| ASHRAE Handbook HVAC Applications 2022 | COP splits tropicales; dehumidificacion 35% humedad absoluta |
| MINEM Peru guia eficiencia energetica 2022 | Edificios Peru: 66% consumo en electricidad; AC = carga dominante |
| ASHRAE Handbook Refrigeration 2022 | Supermercado tropical: 150-250 W/m2 refrigeracion |

### Modelos fisicos

| Fuente | Metodo adoptado |
|--------|----------------|
| Hesse et al. (2017), DOI:10.3390/en10122107 | Sizing BESS: cumulative SOC balance; Li-ion LFP parametros |
| Nottrott et al. (2013), DOI:10.1016/j.renene.2013.05.030 | Referencia adicional sizing BESS: peak shaving |
| Oudalov et al. (2007), DOI:10.1109/TSTE.2012.2228541 | Sizing potencia BESS: percentil 99 pico descarga/carga |
| pvlib ModelChain SAPM | Generacion solar; modulo e inversor Sandia; temperatura open_rack_glass_glass |

### Emisiones CO2

| Fuente | Dato clave |
|--------|-----------|
| MINAM INFOCARBONO (infocarbono.minam.gob.pe) | Factor emision sistemas aislados diesel Peru |
| RAGEI 2019 Energia MINAM | FE = 0.79 tCO2/MWh generacion diesel aislada |
| IPCC Guidelines 2006 | Diesel estacionario: 0.79 kg CO2/kWh (coincide con RAGEI) |

### Tarifas electricas

| Fuente | Dato clave |
|--------|-----------|
| OSINERGMIN Pliegos Tarifarios (osinergmin.gob.pe) | MT3/MT4 ELECTRO ORIENTE -- tarifa real mensual |
| datosabiertos.gob.pe pliego tarifario | Dataset abierto mensual por empresa distribuidora |

---

## Log de Generacion del Dataset (a completar al ejecutar el script)

El script genera automaticamente `dataset_generation_log.json` con:

```json
{
  "fecha_generacion": "2026-XX-XX HH:MM:SS",
  "anios": [2023, 2024, 2025],
  "total_horas": 26304,
  "edificios_generados": 17,
  "archivos_generados": 72,
  "fuentes_meteorologicas": {
    "2023": "PVGIS-ERA5",
    "2024": "NASA POWER",
    "2025": "NASA POWER"
  },
  "modulo_sandia": "nombre_del_modulo_seleccionado",
  "inversor_sandia_ejemplo_B1": "nombre_del_inversor",
  "estadisticas_por_edificio": {
    "1": {
      "non_shiftable_load_mean_kWh": "...",
      "cooling_demand_mean_kWh": "...",
      "solar_generation_total_kWh": "...",
      "bess_capacity_kWh": "...",
      "bess_nominal_power_kW": "..."
    }
  },
  "validacion_citylearn": "exitosa",
  "carbon_intensity_range": "0.672-0.790 kg CO2/kWh",
  "pricing_range": "0.26-0.38 USD/kWh"
}
```

---

## Comparacion con Dataset Demo Original

| Aspecto | citylearn_three_phase_electrical_service_demo | citylearn_iquitos_2023_2025 |
|---------|----------------------------------------------|---------------------------|
| Edificios | 9 | 17 |
| Periodo | 1 anio (8 760 h) | 3 anios (26 304 h) |
| indoor_dry_bulb_temperature | vacia (NaN) | modelo RC primer orden real |
| indoor_relative_humidity | vacia (NaN) | dehumidificacion AC tropical real |
| average_unmet_cooling | vacia (NaN) | senal de discomfort real |
| cooling_demand | 0.0 (no usado) | kWh_termicos reales por edificio |
| dhw_demand | 0.0 | 0.0 para 14 edificios; real para B5/B11/B12 |
| solar_generation | datos USA | ModelChain SAPM lat=-3.75 Iquitos |
| carbon_intensity | cte EE.UU. | 0.672-0.790 Scope 2 diesel Peru |
| pricing | tarifa USA | OSINERGMIN MT TOU Peru |
| charger files | 8 (3 edificios) | 50 (17 edificios) |
| Area geografica | California, USA | Iquitos, Loreto, Peru |
| Sistema electrico | Red nacional USA | Sistema aislado diesel Loreto |
