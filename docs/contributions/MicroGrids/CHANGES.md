# Cambios propios — external/MicroGrids (aporte de investigación)

> Plantilla generada en la reorganización del proyecto (Fase 7). Completar
> cada vez que se modifique este submódulo como parte de la tesis MADRL.
> Workflow: forkear MicroGrids a una cuenta propia, apuntar `.gitmodules` al
> fork con una rama propia (p.ej. `madrl-iquitos-mods`), y documentar aquí
> cada cambio con su justificación bibliográfica (ver `bibliografia.bib`).

## Convenciones

- Cada entrada de cambio debe incluir: fecha, archivo(s) modificado(s),
  descripción del cambio, motivación (qué limitación de la versión original
  soluciona) y referencia(s) bibliográficas (clave BibTeX de
  `bibliografia.bib`).
- En el código modificado, agregar un comentario `# MADRL-IQUITOS-MOD:
  ver docs/contributions/MicroGrids/CHANGES.md#<entrada>` para trazabilidad
  bidireccional código <-> documentación.

## Registro de cambios

| Fecha | Archivo(s) | Descripción | Motivación | Referencia(s) |
|-------|-----------|-------------|------------|---------------|
| 2026-11-01 | MicroGrids/Model_Resolution.py | <a id="solver-configurable"></a>Solver elegido con la variable `MICROGRIDS_SOLVER` (p. ej. `appsi_highs`, `glpk`); por defecto se mantiene `cplex` como en el original. | El original exige CPLEX (comercial); el proyecto usa solo herramientas abiertas. Verificado: ejemplo LP original Optimal con HiGHS 1.7.2 en 5 s (HiGHS 1.11.0 se cae en Windows). | HiGHS (Huangfu y Hall, 2018) |
| 2026-11-01 | MicroGrids/Initialize.py | <a id="datos-configurables"></a>Carpeta de entrada elegida con `MICROGRIDS_DATA_DIR` (por defecto `Example`); las hojas se leen con `index_col=0`. | Con pandas >= 1 la primera columna (periodo 1..T) dejó de ser el índice y el modelo fallaba con `KeyError: 8760`; además permite pasar la demanda medida y la FV de pvlib de Iquitos en lugar de los ejemplos. | Balderrama et al. (MicroGrids) |
| 2026-11-01 | MicroGrids/Model_Creation.py, MicroGrids/Constraints.py, MicroGrids/Model_Resolution.py | <a id="exportacion-red"></a>Exportación a la red opcional en la formulación LP: parámetros `Export_Price` (por defecto 0) y `Allow_Curtailment` (por defecto 1), variables `Energy_Export[s,t]` y `Scenario_Export_Revenue[s]`; el balance resta `Energy_Export`, el VPN resta el ingreso descontado y `No_Curtailment` fija `Energy_Curtailment = 0` cuando `Allow_Curtailment = 0`. `Scenario_Net_Present_Cost` pasa a `Reals` porque con ingresos el VPN puede ser negativo. | Decisión del usuario (2026-11-01): todos los edificios están conectados a la red pública, nada se desperdicia; el excedente FV que no cabe en la BESS se inyecta y se acredita al precio de compra del edificio (facturación neta, inexistente hoy en Iquitos: decisión de escenario). El original solo podía recortar el excedente sin valor. Verificado: con los valores por defecto el ejemplo LP original da el mismo VPN (109530.9186 USD, FV 6.5655 u., BESS 189390.27 Wh) que la formulación sin cambios, ambos con HiGHS 1.7.2. | Balderrama et al. (MicroGrids); decisión del usuario |
| 2026-11-01 | MicroGrids/Model_Creation.py, MicroGrids/Constraints.py, MicroGrids/Model_Resolution.py | <a id="tarifa-horaria-demanda"></a>Precio horario de la red y cargo mensual por demanda máxima en punta en la formulación LP: parámetros `Grid_Energy_Price[s,t]`, `Export_Price_Hourly[s,t]`, `Months`, `Period_Month[t]`, `Peak_Period[t]` y `Demand_Charge[m]` (todos por defecto 0); variables `Peak_Demand[s,m]` (máxima importación de red en el bloque de punta del mes) y `Scenario_Grid_Cost[s]`; restricción `Peak_Demand_Bound` (`Peak_Demand[s,m] >= Generator_Energy[s,t]/Delta_Time` en cada hora de punta del mes) y `Scenario_Grid_Cost` (energía a precio horario + Σ cargo×pico, descontados cada año) sumado al VPN; el ingreso de exportación suma `Export_Price_Hourly`. | Decisión del usuario (2026-11-01): tarifa oficial por bloques + demanda (pliego Osinergmin, sector Iquitos). El original solo tenía un costo marginal constante y no podía valorar el recorte de punta de una BESS. Verificado: con los valores por defecto el ejemplo LP original da el mismo VPN (109530.9186 USD, FV 6.5655 u., BESS 189390.27 Wh) que la formulación sin cambios, con HiGHS 1.7.2. | Balderrama et al. (MicroGrids); pliego tarifario Osinergmin |
