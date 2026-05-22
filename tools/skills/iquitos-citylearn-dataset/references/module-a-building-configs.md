# Module A — Building Configurations (17 Edificios Iquitos)

Inventario completo de los 17 edificios confirmados con datos web verificados,
clasificacion MADRL por equipo, constantes Python, y datos reales del estudio GD-Iquitos V3.

---

## Constante Principal: MADRL_BUILDING_CONSTANTS

```python
MADRL_BUILDING_CONSTANTS = {
    1:  {'name': 'Electro Oriente S.A.',         'non_shiftable_base': 17.7,  'cooling_peak': 126.86, 'shiftable': 14.8,  'bldg_type': 'industrial',    'area_techada_m2': 14000},
    2:  {'name': 'Complejo Champios',             'non_shiftable_base': 3.76,  'cooling_peak': 29.0,   'shiftable': 35.6,  'bldg_type': 'deportivo',     'area_techada_m2': 8000},
    3:  {'name': 'Aeropuerto IQT',                'non_shiftable_base': 55.3,  'cooling_peak': 67.0,   'shiftable': 95.0,  'bldg_type': 'transporte_24h','area_techada_m2': 6000},
    4:  {'name': 'Hiperbodega Precio UNO',        'non_shiftable_base': 14.8,  'cooling_peak': 29.5,   'shiftable': 22.2,  'bldg_type': 'mall',          'area_techada_m2': 2500},
    5:  {'name': 'Hotel El Dorado Plaza',         'non_shiftable_base': 5.4,   'cooling_peak': 150.5,  'shiftable': 99.0,  'bldg_type': 'hotelero_24h',  'area_techada_m2': 9000},
    6:  {'name': 'Mall Aventura Iquitos',         'non_shiftable_base': 78.5,  'cooling_peak': 850.0,  'shiftable': 176.0, 'bldg_type': 'mall',          'area_techada_m2': 20637},
    7:  {'name': 'UNAP Zungarococha',             'non_shiftable_base': 9.5,   'cooling_peak': 167.0,  'shiftable': 39.2,  'bldg_type': 'universitario', 'area_techada_m2': 8300},
    8:  {'name': 'Escuela Tecnica PNP',           'non_shiftable_base': 6.9,   'cooling_peak': 222.0,  'shiftable': 99.3,  'bldg_type': 'educacion',     'area_techada_m2': 21000},
    9:  {'name': 'Complejo CNI',                  'non_shiftable_base': 2.18,  'cooling_peak': 19.5,   'shiftable': 10.7,  'bldg_type': 'deportivo',     'area_techada_m2': 3500},
    10: {'name': 'Gobierno Regional Loreto',      'non_shiftable_base': 12.43, 'cooling_peak': 117.5,  'shiftable': 22.2,  'bldg_type': 'administrativo','area_techada_m2': 5000},
    11: {'name': 'Hospital Regional Loreto',      'non_shiftable_base': 195.0, 'cooling_peak': 366.6,  'shiftable': 73.0,  'bldg_type': 'salud_24h',     'area_techada_m2': 12000},
    12: {'name': 'EsSalud Hospital III',          'non_shiftable_base': 125.0, 'cooling_peak': 222.0,  'shiftable': 34.5,  'bldg_type': 'salud_24h',     'area_techada_m2': 6000},
    13: {'name': 'Facultad Economia UNAP',        'non_shiftable_base': 1.75,  'cooling_peak': 62.5,   'shiftable': 14.8,  'bldg_type': 'universitario', 'area_techada_m2': 3000},
    14: {'name': 'Terminal Portuario ENAPU',      'non_shiftable_base': 15.7,  'cooling_peak': 49.5,   'shiftable': 47.0,  'bldg_type': 'portuario_24h', 'area_techada_m2': 5000},
    15: {'name': 'Colegio Nacional CNI',          'non_shiftable_base': 2.76,  'cooling_peak': 48.0,   'shiftable': 22.2,  'bldg_type': 'educacion',     'area_techada_m2': 2500},
    16: {'name': 'I.E. San Juan',                 'non_shiftable_base': 4.55,  'cooling_peak': 100.0,  'shiftable': 51.54, 'bldg_type': 'educacion',     'area_techada_m2': 6500},
    17: {'name': 'IEST Pedro del Aguila Hidalgo', 'non_shiftable_base': 4.2,   'cooling_peak': 93.0,   'shiftable': 26.3,  'bldg_type': 'educacion',     'area_techada_m2': 5200},
}

# Cargas especiales
REFRIGERACION_COMERCIAL = {
    3:  (30.0,  0.70),
    4:  (12.0,  0.85),
    5:  (18.0,  0.90),
    6:  (515.0, 0.85),
    11: (180.0, 1.00),
    12: (90.0,  1.00),
}
SHORE_POWER_B14 = {'kw_per_vessel': 15.0, 'max_vessels': 4}
EVENT_LOAD_B9   = {'event_kw': 70.0, 'event_hours': [19, 20, 21, 22]}

# Datos reales de facturacion (GD-Iquitos V3)
REAL_CONSUMPTION_KWH_DAY = {
    1: 16091, 7: 436, 8: 297, 10: 3358,
    11: 9971, 12: 6407, 13: 412, 14: 973, 15: 472,
}
```

---

## B1 — Electro Oriente S.A. (Utility / Administrativo) — 14 000 m2

**Datos confirmados**: Sede central Av. Augusto Freyre Monterroso 1168, Iquitos.
Sistemas WatchGuard UTM/NGFW, VPN, SCADA red electrica.
Suministra Loreto, San Martin, Amazonas y norte-centro Cajamarca.
**Consumo real**: 482 735 kWh/mes | 16 091 kWh/dia (GD-Iquitos V3)

**Inventario AC real (confirmado por usuario)**:
| Area | N AC | Tipo BTU | kW electrico |
|------|------|----------|-------------|
| Centro de control | 1 | 24 000 | 2.0 |
| Proyectos | 3 | 36 000 | 9.6 |
| Comercial | 6 | 36 000 | 19.2 |
| Gerencial General | 7 | 36 000 | 22.4 |
| Contabilidad | 2 | 36 000 | 6.4 |
| Finanzas | 5 | 36 000 | 16.0 |
| Logistica | 2 | 36 000 | 6.4 |
| Perdidas | 2 | 36 000 | 6.4 |
| Area tecnica | 6 | 36 000 | 19.2 |
| Distribucion | 2 | 36 000 | 6.4 |
| Operaciones | 4 | 36 000 | 12.8 |
| Ventilador techo | 1 | -- | 0.06 |
| **TOTAL** | **41** | | **126.86 kW** |

```python
NON_SHIFTABLE_BASE_B1_KW = 17.7   # SCADA + servidores + telco + seguridad exterior
COOLING_PEAK_B1_KW = 126.86       # 40 splits 36 000 BTU electrico
SHIFTABLE_B1_KW    = 14.8         # 2 cargadores EV x 7.4 kW
```

---

## B2 — Complejo Deportivo Champios — 8 000 m2

**Datos**: Complejo multidisciplinar Iquitos. Datos web limitados; estimacion por tipo.
**AC total estimado**: ~29 kW | **20 ventiladores HVLS/industriales**

```python
NON_SHIFTABLE_BASE_B2_KW = 3.76
COOLING_PEAK_B2_KW = 29.0
SHIFTABLE_B2_KW    = 35.6   # bomba piscina + 4 EV chargers
```

---

## B3 — Aeropuerto Internacional Francisco Secada Vignetta — 6 000 m2

**Datos confirmados** (Wikipedia IQT): terminal unica planta baja, 1M+ pasajeros/anio,
ISO 9001. Servicios: Martina Cafe, RUTTA restaurante, Caral VIP Lounge, tiendas, ATMs.
Operacion 24h. **AC total**: ~67 kW | **20 ventiladores techo**

```python
NON_SHIFTABLE_BASE_B3_KW = 55.3   # torre + seguridad + FIDS + check-in + catering + ilum.
COOLING_PEAK_B3_KW = 67.0
SHIFTABLE_B3_KW    = 95.0         # carros bagaje + 4 EV DC fast 22 kW
REFRIGERACION_B3   = (30.0, 0.70) # catering refrigerado 24h
```

---

## B4 — Hiperbodega Precio UNO — 2 500 m2

**Datos confirmados** (Tiendeo): hiperbodega gran superficie, Av. del Ejercito 1393.
NO es mall -- formato bodega comercial con secciones frescos, ropa, hogar, electrodomesticos.
**AC total**: ~29.5 kW | **Refrigeracion comercial**: 12 kW

```python
NON_SHIFTABLE_BASE_B4_KW = 14.8   # refrigeracion perecederos 24h
COOLING_PEAK_B4_KW = 29.5
SHIFTABLE_B4_KW    = 22.2         # 3 EV chargers
REFRIGERACION_B4   = (12.0, 0.85) # frescos + bebidas
```

---

## B5 — Hotel El Dorado Plaza (5 estrellas, 24h) — 9 000 m2

**Datos confirmados** (Expedia 2026): Jr. Napo 258, Plaza de Armas.
**65 habitaciones confirmadas** todas con AC, minibar y flat-screen TV.
Piscina exterior, fitness center, business center, sala conferencias, restaurant, lavanderia.
**AC total (65 hab.)**: ~150.5 kW | **6 ventiladores restaurante**
**ACS**: 614 kWh_termico/dia (65 hab. x 50 L/dia x DeltaT=35 C / COP_ACS=0.85)

```python
NON_SHIFTABLE_BASE_B5_KW = 5.4    # refrigeracion + recepcion 24h PMS/CCTV
COOLING_PEAK_B5_KW = 150.5
SHIFTABLE_B5_KW    = 99.0         # cocina + lavanderia + piscina + steam + 3 EV 11 kW
DHW_DAILY_B5_KWH_THERMAL = 614.0  # ACS 65 hab.
REFRIGERACION_B5   = (18.0, 0.90) # camara frigorifica + bar + minibar
```

Correccion documentada: 65 habitaciones confirmadas (vs estimado 90-100 inicial).
AC actualizado 199 -> 150.5 kW. ACS recalculado 780 -> 614 kWh_th/dia.

---

## B6 — Mall Aventura Iquitos — 20 637 m2 GLA

**Datos confirmados** (Wikipedia + mallaventura.pe): Inaugurado 31 agosto 2023.
51 300 m2 totales, 3 pisos, ~110 tiendas. Parking: 400 autos + 340 motos.
Anclas: Falabella (pisos 1-2), Ripley (pisos 1-2), Sodimac, Tottus.
Cine: Movie Time 6 salas. Gym: Smart Fit 1 300 m2. Food court: 10 operadores.
**AC total estimado**: ~850 kW | **73 ventiladores HVLS**

```python
NON_SHIFTABLE_BASE_B6_KW = 78.5   # Tottus refrig. + CCTV/BMS + seguridad exterior
COOLING_PEAK_B6_KW = 850.0
SHIFTABLE_B6_KW    = 176.0        # 8 EV DC fast 22 kW
REFRIGERACION_B6   = (515.0, 0.85)# Tottus + food court + heladerias (20 637 m2 x 25 W/m2)
```

---

## B7 — UNAP Zungarococha (Universitario / Forestal) — 8 300 m2

**Datos confirmados** (unapiquitos.edu.pe): Campus 18 km de Iquitos, 2 000 ha totales.
5 facultades: Biologicas, Farmacia, Forestales, Agronomia, Industrias Alimentarias. CIEFOR.
**Consumo real**: 13 089 kWh/mes | 436 kWh/dia | Demanda max 139 kW (GD-Iquitos V3)
**AC total**: ~167 kW

```python
NON_SHIFTABLE_BASE_B7_KW = 9.5    # refrig. muestras bio + ilum. exterior campus
COOLING_PEAK_B7_KW = 167.0
SHIFTABLE_B7_KW    = 39.2         # autoclave + procesam. alimentos + 3 EV 7.4 kW
```

---

## B8 — Escuela Tecnica Superior PNP — 21 000 m2

**Datos confirmados** (MININTER): 750 estudiantes, campus 97 180 m2, inversion 40M soles.
3 pabellones educativos, 2 pabellones dormitorios, piscina semi-olimpica, gimnasio 40 pers.,
comedor 400 comensales, lab. criminalistica, auditorio, lavanderia industrial.
**Consumo real**: 8 925 kWh/mes | 297 kWh/dia | Demanda max 37 kW (medidor especifico)
**AC total**: ~222 kW | **16 ventiladores techo**

```python
NON_SHIFTABLE_BASE_B8_KW = 6.9    # topico + seguridad perimetral 24h
COOLING_PEAK_B8_KW = 222.0
SHIFTABLE_B8_KW    = 99.3         # cocina + piscina + lavanderia + polideportivo + 2 EV
```

Nota: medidor especifico B8 registra consumo pequenio; campus completo tendria mayor consumo.

---

## B9 — Complejo CNI (Deportivo / Institucional) — 3 500 m2

**Datos confirmados** (Wikipedia + fichajes.com): Estadio CNI capacidad 24 576 espectadores.
Campo futbol cesped artificial + pista atletica. Club fundado 30 julio 1996.
**AC total**: ~19.5 kW | **18 ventiladores HVLS/industriales**

```python
NON_SHIFTABLE_BASE_B9_KW = 2.18   # seguridad exterior 24h (sin evento)
COOLING_PEAK_B9_KW = 19.5
EVENT_LOAD_B9_KW   = 70.0         # iluminacion estadio durante partidos nocturnos
SHIFTABLE_B9_KW    = 10.7         # riego + 2 EV ligeros
```

---

## B10 — Gobierno Regional Loreto — 5 000 m2

**Datos confirmados** (regionloreto.gob.pe): Sede Av. Jose Abelardo Quiniones Km. 1.4 (Belen).
Horario: L-V 07:00-15:00. Gerencias: General Regional, Planeamiento/Presupuesto,
Infraestructura, Seguridad Ciudadana, Desarrollo Economico.
**Consumo real**: 100 751 kWh/mes | 3 358 kWh/dia | Demanda max 597 kW (GD-Iquitos V3)
**AC total**: ~117.5 kW | **2 ventiladores cafeteria**

```python
NON_SHIFTABLE_BASE_B10_KW = 12.43  # servidores gov + CCTV + ilum. exterior/bandera
COOLING_PEAK_B10_KW = 117.5
SHIFTABLE_B10_KW    = 22.2         # 3 EV chargers (solo dias laborales)
```

---

## B11 — Hospital Regional Loreto "Felipe Santiago Arriola Iglesias" — 12 000 m2

**Datos confirmados** (hrloreto.gob.pe + Doctoralia + gob.pe):
6 pisos, 176 camas adultos + 9 cunas neonatologia, hospital referencial tercer nivel.
Av. 28 de Julio S/N, Punchana. 35 especialidades medicas. 20 oficinas administrativas.
**Consumo real**: 299 141 kWh/mes (T1+T2) | 9 971 kWh/dia | Demanda max 809 kW
**AC critico**: 120 kW | **AC no critico**: 120 kW | **Total AC**: 240 kW (base) + VRF UCI/quir.

Clasificacion critica MADRL:
- CRITICO (no controlable): ~195 kW -- UCI + UCIN + quirofanos + emergencia + refrig. vital
- PARCIAL (modulable): ~165 kW -- consultorios + admin + AC no critico + ilum. dimeable
- DESPLAZABLE: ~73 kW -- esterilizacion + lavanderia + cocina (ventanas nocturnas)

```python
NON_SHIFTABLE_BASE_B11_KW = 195.0
COOLING_PEAK_B11_KW = 366.6
SHIFTABLE_B11_KW    = 73.0
DHW_DAILY_B11_KWH_THERMAL = 1200.0  # ~200 camas + cocina + esterilizacion
REFRIGERACION_B11   = (180.0, 1.00) # banco sangre + morgue + farmacia + cocina (CRITICO)
```

---

## B12 — EsSalud Hospital III Iquitos — 6 000 m2

**Datos confirmados** (essalud.gob.pe + noticias): Av. La Marina Km 1.5, Punchana.
Hospital referencial principal EsSalud Loreto. 600 consultas/dia. 11 camas UCI.
12 ventiladores mecanicos, 7 medicos intensivistas, 16 enfermeras. 3 quirofanos.
Neurocirugia compleja confirmada. Telemedicina CENATE (cardiologia, endocrinologia, nutricion).
**Consumo real**: 192 207 kWh/mes | 6 407 kWh/dia | Demanda max 540 kW (GD-Iquitos V3)

```python
NON_SHIFTABLE_BASE_B12_KW = 125.0
COOLING_PEAK_B12_KW = 222.0
SHIFTABLE_B12_KW    = 34.5
DHW_DAILY_B12_KWH_THERMAL = 780.0   # ~120 camas + cocina
REFRIGERACION_B12   = (90.0, 1.00)  # banco sangre + farmacia + cocina (CRITICO)
```

---

## B13 — Facultad Economia y Negocios UNAP (FACEN) — 3 000 m2

**Datos confirmados** (enlinea.unapiquitos.edu.pe): FACEN 51 aniversario 2025.
Escuelas: Administracion, Contabilidad, Economia, Negocios Internacionales, Turismo.
Laboratorio de computo FACEN confirmado. Campus principal Iquitos.
**Consumo real**: 12 367 kWh/mes | 412 kWh/dia | Demanda max 78 kW (GD-Iquitos V3)
**AC total**: ~62.5 kW

```python
NON_SHIFTABLE_BASE_B13_KW = 1.75
COOLING_PEAK_B13_KW = 62.5
SHIFTABLE_B13_KW    = 14.8   # 2 EV chargers (solo laboral)
```

---

## B14 — Terminal Portuario ENAPU — 5 000 m2

**Datos confirmados** (enapu.com.pe): Muelles flotantes 114m y 72m.
Zonas 7A (9 450 m2) y 1 (8 500 m2). Almacenes 4, 6 y 7 (dep. aduanero).
Terminal pasajeros: sala espera, food court, anfiteatro, migraciones, aduana, PNP, Senasa.
**Equipos confirmados**: Grua 22t, Montacargas 3.5t+2.5t, Tractores TCM 30t x4, Vagones 15t x53,
Balanza 60t+100t, Electrogenerador 380 kW. Inversion US$4.3M.
**Consumo real**: 29 203 kWh/mes | 973 kWh/dia | Demanda max 96 kW (GD-Iquitos V3)
**AC total**: ~49.5 kW | **18 ventiladores HVLS/industriales**

```python
NON_SHIFTABLE_BASE_B14_KW = 15.7   # ilum. muelle + CCTV almacenes + balizas seguridad
COOLING_PEAK_B14_KW = 49.5
SHIFTABLE_B14_KW    = 47.0         # montacargas + tractores carga + 2 EV 11 kW
SHORE_POWER_B14     = {'kw_per_vessel': 15.0, 'max_vessels': 4}
```

---

## B15 — Colegio Nacional de Iquitos CNI — 2 500 m2

**Datos confirmados** (MINEDU Identicole + guiadecolegios.info):
2 326 alumnos, 70 secciones secundaria, turnos maniana-tarde.
Av. Abelardo Quiniones Km 1.5, San Juan Bautista.
Instalaciones: auditorio, sala de musica, lab. ciencia y tecnologia, taller arte/ceramica,
lab. idiomas, taller cocina, coliseo polideportivo, losa multiuso 20x40 m.
**Consumo real**: 14 171 kWh/mes | 472 kWh/dia | Demanda max 92 kW (GD-Iquitos V3)
**AC total**: ~48 kW (actualizado con talleres)

```python
NON_SHIFTABLE_BASE_B15_KW = 2.76
COOLING_PEAK_B15_KW = 48.0  # actualizado: taller arte + cocina MINEDU confirmados
SHIFTABLE_B15_KW    = 22.0  # talleres + 2 EV ligeros
```

Correccion documentada: AC 45 -> 48 kW (talleres confirmados por MINEDU Identicole).

---

## B16 — I.E. San Juan (Educacion secundaria) — 6 500 m2

**Datos confirmados** (iesanjuan.edu.pe + MINEDU Identicole): Escuela emblematica Iquitos.
Programa Escuelas Bicentenario. Instalaciones confirmadas: SUM (Sala de Usos Multiples),
auditorium, Biblioteca tipo III (120 m2+) primaria y secundaria, aula de innovacion pedagogica,
lab. ciencia y tecnologia, gimnasio, coliseo deportivo, piscina semi-olimpica bajo techo,
losa multiuso tipo II. Nueva infraestructura modular bioclimatica planificada 2026.
**AC total**: ~100 kW | **6 ventiladores comedor**

```python
NON_SHIFTABLE_BASE_B16_KW = 4.55
COOLING_PEAK_B16_KW = 100.0
SHIFTABLE_B16_KW    = 51.54  # piscina + coliseo + comedor + calentador + 1 EV
```

---

## B17 — IEST Publico "Pedro A. del Aguila Hidalgo" — 5 200 m2

**Datos confirmados** (logrosperu.com + deperu.com):
Av. Mariscal Caceres 1459, Iquitos. Instituto publico superior tecnologico.
7 carreras confirmadas: Produccion Agropecuaria, Contabilidad, Construccion Civil,
Electrotecnia Industrial, Mecanica Automotriz, Mecanica de Produccion, Secretariado Ejecutivo.
Lab. computo, lab. fabricacion digital (mecatronica), talleres por carrera.
**AC total**: ~93 kW | **4 ventiladores industriales talleres**

```python
NON_SHIFTABLE_BASE_B17_KW = 4.2
COOLING_PEAK_B17_KW = 93.0
SHIFTABLE_B17_KW    = 26.3   # autoclave + secador agropecuaria + 2 EV medianos
```

---

## Sizing FV por Edificio (Sandia SAPM, factor area 0.63)

| # | Edificio | Area techada m2 | n_modulos (est) | kWp (est) |
|---|---------|----------------|----------------|----------|
| 1 | Electro Oriente | 14 000 | ~4 410 | ~2 117 |
| 2 | Complejo Champios | 8 000 | ~2 520 | ~1 210 |
| 3 | Aeropuerto IQT | 6 000 | ~1 890 | ~907 |
| 4 | Hiperbodega Precio UNO | 2 500 | ~787 | ~378 |
| 5 | Hotel El Dorado Plaza | 9 000 | ~2 835 | ~1 361 |
| 6 | Mall Aventura Iquitos | 20 637 | ~6 500 | ~3 120 |
| 7 | UNAP Zungarococha | 8 300 | ~2 614 | ~1 255 |
| 8 | Escuela Tecnica PNP | 21 000 | ~6 615 | ~3 175 |
| 9 | Complejo CNI | 3 500 | ~1 102 | ~529 |
| 10 | Gobierno Regional | 5 000 | ~1 575 | ~756 |
| 11 | Hospital Regional | 12 000 | ~3 780 | ~1 814 |
| 12 | EsSalud Hospital III | 6 000 | ~1 890 | ~907 |
| 13 | Facultad Economia UNAP | 3 000 | ~945 | ~453 |
| 14 | Terminal Portuario ENAPU | 5 000 | ~1 575 | ~756 |
| 15 | Colegio Nacional CNI | 2 500 | ~787 | ~378 |
| 16 | I.E. San Juan | 6 500 | ~2 047 | ~982 |
| 17 | IEST Publico | 5 200 | ~1 638 | ~786 |

*Estimado con modulo tipo ~480 W, Area ~2.0 m2 -- valores exactos se calculan con Sandia SAPM*

Factor sizing: area_techada x 0.70 (area util excl. HVAC) x 0.90 (pasillos mantenimiento) = 0.63

---

## Datos Reales GD-Iquitos V3 (Facturacion ELECTRO ORIENTE 2023-2025)

| # | Edificio | kWh/mes real | kWh/dia real | Dem. max kW | PV modulos estudio | PV kWp |
|---|---------|-------------|-------------|------------|-------------------|--------|
| 1 | Electro Oriente | 482 735 | 16 091 | n/d | 5 900 | 500 |
| 7 | UNAP Zungarococha | 13 089 | 436 | 139 | 179 | 105 |
| 8 | Escuela PNP | 8 925 | 297 | 37 | 135 | 79 |
| 10 | Gobierno Regional | 100 751 | 3 358 | 597 | 1 156 | 400 |
| 11 | Hospital Regional | 299 141 | 9 971 | 809 | 2 650+2 070 | 500 |
| 12 | EsSalud Hospital III | 192 207 | 6 407 | 540 | 2 332 | 400 |
| 13 | Facultad Economia | 12 367 | 412 | 78 | -- | 90 |
| 14 | ENAPU | 29 203 | 973 | 96 | 324 | 190 |
| 15 | Colegio CNI | 14 171 | 472 | 92 | 169 | 99 |

Fuente: Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx

---

## Asignacion de Cargadores EV por Edificio (50 archivos charger)

| # | Edificio | N cargadores | kW/cargador | Tipo EV | Archivos |
|---|---------|-------------|------------|---------|---------|
| 1 | Electro Oriente | 2 | 7.4 AC | EV mediano | charger_1_1, charger_1_2 |
| 2 | Complejo Champios | 4 | 7.4 AC | EV mediano/ligero | charger_2_1..4 |
| 3 | Aeropuerto IQT | 4 | 22.0 DC fast | EV pesado + GSE | charger_3_1..4 |
| 4 | Hiperbodega Precio UNO | 3 | 7.4 AC | EV mediano | charger_4_1..3 |
| 5 | Hotel El Dorado Plaza | 3 | 11.0 AC | EV mediano | charger_5_1..3 |
| 6 | Mall Aventura | 8 | 22.0 DC fast | EV mediano/pesado | charger_6_1..8 |
| 7 | UNAP Zungarococha | 3 | 7.4 AC | EV mediano | charger_7_1..3 |
| 8 | Escuela PNP | 2 | 7.4 AC | EV mediano | charger_8_1, charger_8_2 |
| 9 | Complejo CNI | 2 | 3.3 AC | EV ligero | charger_9_1, charger_9_2 |
| 10 | Gobierno Regional | 3 | 7.4 AC | EV mediano | charger_10_1..3 |
| 11 | Hospital Regional | 4 | 11.0 AC + 1x22 kW | EV mediano + ambulancia | charger_11_1..4 |
| 12 | EsSalud | 3 | 7.4 AC | EV mediano | charger_12_1..3 |
| 13 | Facultad Economia | 2 | 7.4 AC | EV mediano | charger_13_1, charger_13_2 |
| 14 | ENAPU | 2 | 11.0 AC | EV mediano + carga | charger_14_1, charger_14_2 |
| 15 | Colegio CNI | 2 | 3.3 AC | EV ligero | charger_15_1, charger_15_2 |
| 16 | I.E. San Juan | 1 | 3.3 AC | EV ligero | charger_16_1 |
| 17 | IEST Publico | 2 | 7.4 AC | EV ligero/mediano | charger_17_1, charger_17_2 |
