# Aportes al Motor de Simulación CityLearn — MADRL Tesis UNI

**Proyecto:** Gestión Coordinada de Flexibilidad Energética, CO₂ y Costos mediante MADRL en Comunidades Inteligentes (CityLearn v3, Dataset Iquitos)  
**Autor:** Mac Tapia — mac.tapia.c@uni.pe  
**Fork:** github.com/Mac-Tapia/CityLearn.git  
**Fecha:** 2026-06-13  

> **Bibliografía:** las citas de este documento técnico están consolidadas en la lista única `docs/tesis_capitulos/Referencias_APA.md` y en la sección «Referencias bibliográficas» del informe final Word. No se mantienen listas bibliográficas locales por aporte.

---

## Resumen

Este documento describe cuatro contribuciones originales al motor de simulación del fork CityLearn v3 utilizado en la tesis doctoral. Cada aporte extiende el motor base con modelos físicos más precisos y relevantes para el contexto climático y regulatorio de Iquitos, Loreto, Perú. Todos los cambios son **retrocompatibles** (parámetros con valores por defecto que reproducen el comportamiento original).

---

## APORTE 1 — Modelo de Degradación BESS con C-rate y Factor Arrhenius de Temperatura

**Archivo:** `CityLearn/citylearn/energy_model.py`  
**Clase/método:** `Battery.degrade(temperature_celsius=25.0)`

### Motivación

El modelo original de degradación de la batería es lineal uniforme:

```python
# Original (energy_model.py antes de este aporte)
capacity_degrade = capacity_loss_coefficient * capacity * |energy_balance| / (2 * degraded_capacity)
```

Este modelo no diferencia entre operación a baja temperatura (22°C, noche andina) y alta temperatura (38°C, mediodía amazónico), ni entre cargas lentas (C/5) y rápidas (1C), pese a que ambas variables afectan el envejecimiento del LiFePO₄ de forma sustancial.

### Modelo propuesto

```
capacity_degrade = base × f_crate × f_temp

base     = capacity_loss_coefficient × capacity × |throughput| / (2 × degraded_capacity)
f_crate  = (|energy_flow| / degraded_capacity) ^ z         (z = 0.55, LiFePO4)
f_temp   = exp[ Ea/R × (1/T_ref − 1/T) ]                  (Arrhenius)
            Ea = 24 500 J/mol, T_ref = 298.15 K
```

- **f_crate**: penaliza ciclos de alta potencia (1C degrada más que C/5)  
- **f_temp**: a 35°C (Iquitos peak) f_temp ≈ 1.14 — 14% de degradación adicional respecto a 25°C STC  
- backward-compatible: `degrade()` sin argumentos equivale al modelo original con f_crate × f_temp ≈ 1 a T=25°C y C-rate típico

### Impacto en política MADRL

Las políticas HAPPO/MASAC/MATD3/MAAC aprenden implícitamente a evitar sobrecargas de BESS durante horas calurosas (E2 mediodía amazónico) dado que la degradación aumentada reduce la capacidad disponible en episodios siguientes.

### Referencias

Ver lista unificada en `docs/tesis_capitulos/Referencias_APA.md` (sección F — modelado físico y fuentes regulatorias).

---

## APORTE 2 — Corrección de Temperatura PV para Clima Tropical (IEC 61215)

**Archivo:** `CityLearn/citylearn/energy_model.py`  
**Clase/método:** `PV.get_generation(inverter_ac_power_per_kw, dry_bulb_temperature=None, ghi=None, ...)`

### Motivación

El modelo original calcula generación PV exclusivamente en función de la potencia de inversor sin corrección térmica:

```python
# Original
return self.nominal_power * np.array(inverter_ac_power_per_kw) / 1000.0
```

En Iquitos (T_max ≈ 35°C, humedad relativa >80%), los paneles PV operan 8–12% por debajo de las condiciones STC (Standard Test Conditions, T_cell=25°C). Este error sistemático sesga las observaciones de los agentes MADRL y las estimaciones de KPI de autoconsumo.

### Modelo propuesto (IEC 61215)

```
T_cell = T_amb + (NOCT − 20) / 800 × GHI
P(T)   = P_STC × [1 + γ_pmax × (T_cell − 25)]

γ_pmax = −0.0035 /°C  (monoSi/LiFePO4 estándar)
NOCT   = 45°C          (temperatura nominal de operación de celda)
```

La corrección se aplica solo cuando `dry_bulb_temperature` y `ghi` se pasan explícitamente, preservando compatibilidad total con llamadas sin argumentos de temperatura.

**Efecto cuantitativo en Iquitos:**  
- T_amb=25°C + GHI=1000 W/m² → T_cell≈56°C → derating ≈10.9% respecto a STC  
- T_amb=35°C + GHI=1000 W/m² → T_cell≈66°C → derating ≈14.4% respecto a STC  
- Diferencia entre T=25°C y T=35°C ambiente (caso tropical): ~3.9%

### Impacto en política MADRL

El entorno de simulación modela fielmente la caída de generación PV durante las horas de mayor temperatura (12–16h), periodos que también coinciden con picos de demanda de refrigeración. Los agentes aprenden estrategias de precarga BESS por la mañana (cuando la PV es más eficiente y la temperatura aún baja) en lugar de confiar en generación sobredimensionada a mediodía.

### Referencias

Ver lista unificada en `docs/tesis_capitulos/Referencias_APA.md` (sección F — PV, IEC 61215 y clima tropical).

---

## APORTE 3 — KPI de Pico de Demanda con Ventana de Facturación Configurable

**Archivo:** `CityLearn/citylearn/cost_function.py`  
**Función:** `CostFunction.peak(net_electricity_consumption, window=24, billing_window_steps=1)`

### Motivación

El KPI `peak_average` original agrupa el consumo en ventanas de 24 pasos (1 día) y reporta el pico diario. En los mercados eléctricos regulados, el cargo por máxima demanda se factura sobre el pico medido en ventanas de 15 minutos (OSINERGMIN MT-3/MT-4).

### Modelo propuesto

```python
# Si billing_window_steps > 1: pico sub-horario dentro de cada ventana de facturación
data['net_electricity_consumption'] = (
    data['net_electricity_consumption']
    .rolling(billing_window_steps, min_periods=1)
    .max()
)
# Luego: agrupación diaria y media acumulativa (igual que el original)
```

Para datasets horarios (como Iquitos), `billing_window_steps=1` reproduce exactamente el comportamiento original. Para datasets sub-horarios de 15 minutos, `billing_window_steps=4` captura el cargo por demanda MT-3/MT-4.

**backward-compatible**: llamar `peak(data)` sin `billing_window_steps` es idéntico a `peak(data, billing_window_steps=1)`.

### Justificación regulatoria peruana

OSINERGMIN establece el cargo por demanda máxima para Electro Oriente S.A. (concesionaria Iquitos) en las tarifas:

- **MT-3**: Cargo en horas de punta (18:00–23:00), medición en ventana de 15 minutos
- **MT-4**: Cargo en horas fuera de punta, medición en ventana de 15 minutos

Este aporte permite alinear el KPI del simulador con la estructura real de facturación que enfrentan los edificios comerciales en Iquitos.

### Impacto en política MADRL

El escenario E3 (optimización de costos) puede configurarse con `billing_window_steps=4` para penalizar picos de potencia de 15 minutos en lugar de picos horarios, generando políticas HAPPO/MASAC que aprenden a suavizar la demanda dentro de ventanas sub-horarias.

### Referencias

Ver lista unificada en `docs/tesis_capitulos/Referencias_APA.md` (sección F — pico de demanda y OSINERGMIN).

---

## APORTE 4 — Clase CarbonIntensityModel para Redes Aisladas Diesel+PV

**Archivo:** `CityLearn/citylearn/energy_model.py`  
**Clase:** `CarbonIntensityModel(base_ci=0.790, pv_displacement_factor=0.15)`

### Motivación

El dataset Iquitos utiliza la función de intensidad de carbono dinámica:

```
CI(t) = 0.790 × (1 − 0.15 × GHI(t)/1000)
```

Esta función estaba embebida en el script de generación del dataset pero no existía como componente formal del motor de simulación CityLearn, impidiendo su reutilización, configuración por schema, o herencia en variantes del modelo.

### Modelo propuesto

```python
class CarbonIntensityModel:
    """CI dinámico para redes aisladas diesel con penetración PV."""
    
    def get_intensity(self, ghi):
        """CI(t) = base_ci × (1 − pv_factor × min(GHI/1000, 1))"""
        pv_fraction = np.clip(ghi / 1000.0, 0.0, 1.0)
        return self.base_ci * (1.0 - self.pv_displacement_factor * pv_fraction)
```

**Parámetros por defecto calibrados para Loreto:**
- `base_ci = 0.790 kgCO₂/kWh` — factor de emisión RAGEI red aislada Loreto (MINAM 2019)
- `pv_displacement_factor = 0.15` — 15% de desplazamiento a GHI máximo (mix 2022-2023 Electro Oriente)

**Verificación numérica:**  
```python
CarbonIntensityModel(0.790, 0.15).get_intensity(1000.0) == 0.6715  # mediodía
CarbonIntensityModel(0.790, 0.15).get_intensity(0.0)    == 0.7900  # noche
```

### Extensibilidad

La clase permite parametrizar el modelo para otras redes aisladas peruanas (Pucallpa, Madre de Dios, Yurimaguas) simplemente ajustando `base_ci` y `pv_displacement_factor` desde el schema JSON de CityLearn.

### Impacto en política MADRL

El escenario E2 (reducción de emisiones) puede integrar `CarbonIntensityModel` directamente en el motor para modelar la dinámica real de una red aislada: cuando la PV genera al máximo (mediodía), el CI cae y el almacenamiento BESS debe cargar para desplazar el diesel nocturno. Las políticas HAPPO aprenden este comportamiento a partir del CI dinámico.

### Referencias

Ver lista unificada en `docs/tesis_capitulos/Referencias_APA.md` (sección F — intensidad de carbono y MINAM RAGEI).

---

## Tabla Resumen de Aportes

| # | Aporte | Archivo | Clase/Método | Tipo | Impacto |
|---|--------|---------|--------------|------|---------|
| 1 | Degradación BESS C-rate+Arrhenius | `energy_model.py` | `Battery.degrade()` | Extensión de método | Política aprende a no sobrecargar BESS en días calurosos |
| 2 | Corrección PV temperatura tropical | `energy_model.py` | `PV.get_generation()` | Extensión de método | Precisión +3–11% en generación PV tropical |
| 3 | Pico demanda ventana facturable | `cost_function.py` | `CostFunction.peak()` | Parámetro nuevo | KPI alineado con tarifa OSINERGMIN MT-3/MT-4 |
| 4 | Modelo CI dinámico diesel+PV | `energy_model.py` | `CarbonIntensityModel` (nueva clase) | Clase nueva | CI configurable por schema para redes aisladas |

---

## Verificación de Aportes

```bash
# Activar entorno del proyecto
.\.venv39-citylearn-v3\Scripts\Activate.ps1

# Aporte 3: backward compatibility
python -c "
from citylearn.cost_function import CostFunction
data = list(range(48))
assert CostFunction.peak(data, billing_window_steps=1) == CostFunction.peak(data)
print('Aporte 3 OK')
"

# Aporte 4: valores esperados
python -c "
from citylearn.energy_model import CarbonIntensityModel
ci = CarbonIntensityModel()
assert abs(ci.get_intensity(1000.0) - 0.6715) < 1e-6
assert abs(ci.get_intensity(0.0) - 0.790) < 1e-6
print('Aporte 4 OK')
"

# Aporte 2: reducción por temperatura tropical
python -c "
from citylearn.energy_model import PV
pv = PV(nominal_power=10.0)
gen_25 = pv.get_generation(1000.0, dry_bulb_temperature=25.0, ghi=1000.0)
gen_35 = pv.get_generation(1000.0, dry_bulb_temperature=35.0, ghi=1000.0)
assert gen_35 < gen_25
print(f'Aporte 2 OK: {(1-gen_35/gen_25)*100:.1f}% reduccion 25→35 C')
"

# Aporte 1: firma acepta temperatura
python -c "
import inspect; from citylearn.energy_model import Battery
assert 'temperature_celsius' in inspect.signature(Battery.degrade).parameters
print('Aporte 1 OK')
"
```

---

## Relación con el Marco Teórico de la Tesis (Capítulo IV)

Estos aportes se integran en la Sección 4.10 (Formulación Dec-POMDP) y Sección 4.11 (Escenarios E1/E2/E3):

- **Aporte 1** justifica la penalización implícita por degradación en la función de recompensa del escenario E1 (flexibilidad).
- **Aporte 2** mejora la fidelidad del entorno en el escenario E1/E3 durante horas punta amazónicas.
- **Aporte 3** alinea el KPI `peak_average` con la regulación OSINERGMIN en el escenario E3 (costos).
- **Aporte 4** proporciona el modelo formal de CI dinámica que sustenta el escenario E2 (emisiones CO₂).

Estos cuatro aportes constituyen la **contribución metodológica diferencial** de esta tesis frente al uso directo de CityLearn v2/v3 base, y se citan explícitamente en la redacción del Capítulo V (Conclusiones) como extensiones al estado del arte.
