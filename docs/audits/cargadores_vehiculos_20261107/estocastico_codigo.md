# Carga de VE: revisión de código frente a CityLearn y proyectos de referencia (2026-11-07)

Revisión de solo lectura de `uc3m/application/dataset/ev_queue.py`, `tools/dataset/write_ev_v6.py` y `configs/dataset/ev_v6.yaml`. Se comparó con el código de CityLearn (fork, `a5b2252f`), `external/evcc` (`fed9678`) y los proyectos EV2Gym, ACN-Sim, SimBEV, RAMP-mobility, V2G-Sim y emobpy.

## Cómo trata CityLearn los VE

- **Lectura:** `citylearn/internal/loading.py:384-410` y `citylearn/data.py:853-941`. El SOC del CSV va en % y se divide entre 100. Los valores centinela son -1 en tiempos y -0,1 en SOC; coinciden con los nuestros.
- **SOC al conectarse:** `citylearn/internal/runtime.py:251-312`. CityLearn **fuerza** el SOC con `estimated_soc_arrival` en cada conexión nueva.
- **Fuera del cargador:** `runtime.py:314-385`. El SOC deriva con un factor aleatorio N(1; 0,2·√h), recortado a [0,6; 1,4]. No representa la energía del recorrido.
- **Cargador:** `citylearn/electric_vehicle_charger.py:326-380`.
  - Una acción positiva se eleva a `min_charging_power`.
  - La descarga usa `max_discharging_power` con la eficiencia del cargador.
- **Batería:** `citylearn/energy_model.py:1067-1093`. Sin `capacity_power_curve` ni `power_efficiency_curve`, las curvas **se sortean**. Con SOC 1,0 la potencia baja al 20-30 % de la nominal.
- **Exportación:** solo se limita con `electrical_service.limits.total.export_kw` (`citylearn/building.py:856-1000`). No hay un tope de descarga de VE igual a la demanda del edificio.
- **KPI de SOC de salida:** `citylearn/internal/kpi.py:236-250`. Detecta la salida solo cuando el estado pasa de 1 a otro valor.
- **evcc:** la potencia mínima es V × 6 A × fases (`core/loadpoint_effective.go:223-252`). La estimación del tiempo de carga usa una eficiencia de 0,85 y una reducción de potencia al acercarse al 100 % (`core/soc/estimator.go`). No modela V2G de vehículos.

## Errores y huecos de nuestra implementación

| # | Hallazgo | Dónde | Efecto |
|---|---|---|---|
| 1 | El SOC arrastrado entre sesiones queda fijo en el CSV y CityLearn lo sobrescribe en cada conexión | `ev_queue.py` (cola), `runtime.py:296-303` | Si el agente carga menos, o la camioneta descarga por V2L, la llegada siguiente no cambia. Descargar no tiene costo en el tiempo |
| 2 | El tiempo de conexión ignora las eficiencias y la reducción de potencia; las curvas de batería no se fijan | `ev_queue.py` (`charging_hours`), `write_ev_v6.py` (`ev_entry`) | El SOC pedido a la salida es inalcanzable y el KPI de salida falla por construcción. Las curvas dependen de la semilla del entorno |
| 3 | Falta el límite sin exportación; el FC solo se informa | `write_ev_v6.py`, `ev_queue.py` | La V2L de 6,6 kW puede exportar a la red, contra D-V6-28 |
| 4 | La camioneta se desconecta al llenarse | `ev_queue.py` (`fifo_queue`) | Pierde la V2B mientras sigue estacionada y sufre la deriva aleatoria del SOC |
| 5 | Dos vehículos seguidos en la misma toma, sin un paso libre entre ellos | `ev_queue.py` (`charger_tables`) | El KPI no detecta la salida del primero y no se escribe el aviso de llegada del segundo |
| 6 | Menores: aviso de llegada con 1 en lugar de 0, id `'NONE'` en lugar de vacío, tomas por equipo fijas en el código, un solo recorrido determinista por clase | `ev_queue.py`, `write_ev_v6.py` | Diferencias con el dataset de referencia de CityLearn |
| 7 | El mínimo de tomas se calcula sobre un solo sorteo | `ev_queue.py` (`required_chargers`) | Con aleatoriedad depende de la semilla; hace falta un nivel de servicio sobre varias semillas |

## Cómo lo hacen los proyectos de referencia

- **EV2Gym** (<https://github.com/StavrosOrf/EV2Gym>):
  - Llegadas Bernoulli por puerto y paso, con tasas de ElaadNL por cuarto de hora (`ev2gym/utilities/utils.py`, `EV_spawner`).
  - Estancia N(μ; 0,2μ). La energía pedida es N(μ; 0,5μ), y la energía de llegada es la capacidad menos la pedida.
  - Mínimo de emergencia y reducción de potencia en `ev2gym/models/ev.py`.
  - Exige el puerto libre en t-1 y t-2.
- **ACN-Sim** (<https://github.com/zach401/acnportal>):
  - Mezcla gaussiana de llegada, duración y energía (`acnsim/events/stochastic_events.py`).
  - `force_feasible` limita la energía a lo que se puede entregar.
  - Batería en dos tramos con reducción de potencia (`acnsim/models/battery.py`).
- **SimBEV** (<https://github.com/rl-institut/SimBEV>): tablas empíricas por región y decisión de carga según el SOC (`simbev/trip.py`).
- **RAMP-mobility** (<https://github.com/RAMP-project/RAMP-mobility>): ventanas con variación uniforme y distancia uniforme en ±r; carga forzada bajo un SOC de 0,25 (`core_model/`).
- **V2G-Sim** (<https://github.com/LBNL-ETA/V2G-Sim>): itinerarios NHTS; V2G entre un SOC de 0,1 y 0,95.
- **emobpy:** tablas empíricas de viajes con muestreo por inversa de la CDF. No se verificó en el código.

Ninguno usa la lognormal de forma explícita. La lognormal de los km diarios se apoya en Plötz et al. (2017). Para autos privados, la desviación del logaritmo ronda 0,6-0,9; para motos y mototaxis no hay fuente peruana.

## Correcciones recomendadas

1. **SOC de llegada endógeno en la capa v3:** el último SOC real menos la energía del recorrido, en lugar del valor fijo del CSV. Requiere cambiar `runtime.py` del fork.
2. **Duración con eficiencias:** (SOC objetivo − SOC) × capacidad ÷ (P × η del cargador × η de la batería), con las curvas de la batería fijadas en el esquema. El SOC pedido debe ser alcanzable.
3. **Límite de exportación:** escribir `electrical_service` o, mejor, un límite en el fork que acote la descarga de VE a la demanda del edificio (D-V6-28).
4. **V2B de la camioneta:** que siga conectada mientras esté estacionada, o un puerto V2L aparte.
5. **Un paso libre** entre sesiones de la misma toma.
6. **Nivel de servicio:** dimensionar las tomas con un percentil sobre N semillas.
