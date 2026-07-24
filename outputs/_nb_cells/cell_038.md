## Sección 5: Función de recompensa multiobjetivo

### Componentes (v4)

| Componente | Descripción |
|---|---|
| **Flexibilidad** | peak_penalty + ramping_penalty + load_factor + ev_service |
| **CO₂** | carbon_emissions × carbon_intensity |
| **Costo** | electricity_cost × price_signal |
| **EV urgency** | SOC_deficit × 1/horas_hasta_salida |
| **BESS degradación** | C-rate penalty Arrhenius LiFePO₄ (v4) |

### Pesos por escenario

| Escenario | flex | carbon | cost |
|:---:|:---:|:---:|:---:|
| **E1** | **0.70** | 0.15 | 0.15 |
| **E2** | 0.15 | **0.70** | 0.15 |
| **E3** | 0.25 | 0.15 | **0.60** |

### Recompensa mixta CTDE (team_ratio = 0.70)
```
r_i_mix = 0.30 × r_i_local  +  0.70 × mean(r₁,...,r₁₇)
```
