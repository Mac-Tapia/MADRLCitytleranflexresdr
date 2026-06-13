# Cambios propios — CityLearn (fork `Mac-Tapia/CityLearn`, rama `citylearn-v3-madrl`) — aporte de investigación

CityLearn ya es un **fork propio** (`.gitmodules`: `https://github.com/Mac-Tapia/CityLearn.git`,
rama `citylearn-v3-madrl`), por lo que está plenamente habilitado para
modificarse como aporte de tesis. Este archivo documenta las
modificaciones acumuladas sobre el CityLearn v2/v3 original, con su
justificación bibliográfica (ver `bibliografia.bib`).

## Convenciones

- Cada entrada debe incluir: fecha, archivo(s) modificado(s), descripción,
  motivación (limitación del CityLearn original que se resuelve o extensión
  que habilita) y referencia(s) bibliográficas.
- En el código modificado, agregar un comentario `# MADRL-IQUITOS-MOD: ver
  docs/contributions/CityLearn/CHANGES.md#<entrada>` para trazabilidad.
- El dataset `data/datasets/citylearn_iquitos_2023_2025/` (17 edificios,
  185 cargadores EV, BESS, PV — ver `docs/workflow_manifest.json`) es en sí
  mismo un aporte de dataset; documentar aquí también las extensiones de
  esquema (`schema.json`) necesarias para soportarlo (p.ej.
  `electric_vehicles_def`, `community_market`) si no existían en el
  CityLearn original.

## Registro de cambios

| Fecha | Archivo(s) | Descripción | Motivación | Referencia(s) |
|-------|-----------|-------------|------------|---------------|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

> Nota: revisar el historial de commits del fork
> (`Mac-Tapia/CityLearn@citylearn-v3-madrl`) frente a `upstream/master`
> (CityLearn original) para poblar retroactivamente esta tabla con los
> cambios ya realizados (esquema EV, mercado comunitario, etc.).
