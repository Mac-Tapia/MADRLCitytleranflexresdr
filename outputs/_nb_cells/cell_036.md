## Sección 4: Entorno Dec-POMDP — 17 agentes

**Dec-POMDP:** cada edificio es un agente con observación parcial local.
**CTDE:** el crítico usa el estado global durante entrenamiento; la ejecución es completamente local.

```
Dataset: citylearn_iquitos_2023_2025 (17 edificios reales, Iquitos 2023-2025)

Observación local oᵢ(t): HETEROGÉNEA por edificio (varía según nº de chargers EV)
  ├── Building_1:  64 dimensiones (3 chargers EV Modo 3 AC)
  ├── Building_2:  78 dimensiones (5 chargers EV)
  ├── Building_3:  92 dimensiones (7 chargers EV)
  └── ... (rango: 57–330 dims según chargers EV del edificio)

  Componentes por agente:
  ├── Tiempo (mes, hora, day_type)
  ├── Física edificio (non_shiftable_load, dhw_demand, cooling_demand, solar_generation)
  ├── BESS (SOC, nominal_power, acciones previas)
  ├── EV por charger (SOC_k, departure_time_k, required_soc_k, estimated_arrival_k, state_k)
  └── Señales globales (carbon_intensity, electricity_pricing, outdoor_dry_bulb_temp,
                        diffuse_solar_irradiance, direct_solar_irradiance)

Acción local aᵢ(t): HETEROGÉNEA por edificio
  ├── Building_1: 6 acciones  (BESS_charge + 3 EV_charger_power + 2 adicionales)
  ├── Building_2: 8 acciones
  └── ... (rango: 5–44 acciones según nº de EV chargers)

Nota HAPPO: share_param=False — cada edificio tiene política INDEPENDIENTE.
            Permite aprender patrones locales distintos (edificio industrial vs residencial).
Nota histórica MAPPO: no es baseline oficial ni algoritmo principal de este flujo; se mantiene solo como antecedente metodológico de políticas compartidas.
```
