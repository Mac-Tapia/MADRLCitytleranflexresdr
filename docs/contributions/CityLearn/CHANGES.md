# Contribuciones locales a CityLearn

## Persistencia, reanudación y catálogo explícito — continuación

Las fachadas write_json/write_csv y append estable delegan en
uc3m.application.training.persistence. JSON/CSV completos se reemplazan
atómicamente; append rechaza columnas inesperadas y encabezados distintos.

Se corrigió un defecto observado por pruebas existentes: preload conservaba
el contador de filas escritas pero vaciaba el búfer, omitiendo nuevos episodios.
Ahora ambos conservan el mismo prefijo. Coste explícito: memoria histórica
proporcional a las filas. No se proclama una optimización de streaming.

ScenarioManager aplica el catálogo solo mediante UC3M_SCENARIO_CATALOG;
los lanzadores históricos no cambian su tarifa por defecto. Los tratamientos
no soportados de recompensa/restricción se rechazan. Se conserva el criterio
de no aceptar corridas sin KPI ni con etiqueta de escenario incompatible.

Pruebas antiguas que exigían omitir corridas sin KPI se actualizaron al criterio
estricto del SPEC aprobado; no se debilitó producción para satisfacerlas.
El fixture canónico HAPPO actual contiene 50 episodios y KPI auditados, por lo
que su expectativa se actualizó. La prueba de etiquetas erróneas ahora crea
su propio archivo determinista, en vez de omitir la prueba cuando no hay errores.

## 2026-10-31 — Extracción modular de rutas de entrenamiento

Autorización: el usuario pidió realizar los pendientes en su proyecto y aclaró
expresamente que incluye los proyectos derivados open source. Esta autorización
levanta la restricción previa de modificación local de CityLearn y external;
no sustituye las licencias de autores de terceros ni autoriza publicación remota.

Cambio: `CityLearn/scripts/citylearn_v3_training_common.py` reexporta las cinco
funciones de layout desde `uc3m/application/training/layout.py`. Se conserva
`HAPPO/E1` para semilla cero y `HAPPO/E1_s7` para semilla siete, las carpetas de
artefactos y las funciones legacy de descubrimiento/reanudación. No se movieron
datasets, checkpoints ni resultados. Se preservaron los demás cambios locales.

Pruebas: `tests/unit/application/training/test_layout.py` pasó de tres fallos
por módulo inexistente a tres aprobadas. La prueba existente
`CityLearn/tests/test_internal_refactor_parity.py` aprobó sus dos casos.

La extracción hace que los scripts CityLearn requieran la carpeta padre UC3M
para estas funciones; el lanzador agrega PROJECT_ROOT antes de importarlas.
El repositorio derivado debe distribuirse junto al superproyecto o con UC3M
instalado; ya no es autónomo para estos lanzadores.

## Sustento científico (APA)

Charbonnier, F. (2023). *Multi-agent reinforcement learning for the coordination
of residential energy flexibility* [Tesis doctoral, University of Oxford].
https://doi.org/10.5287/ora-ovzyxredj

Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy
Optimization: Taxonomy and Experimental Evaluation in CityLearn* [Tesis de
maestría, Politecnico di Torino]. https://webthesis.biblio.polito.it/40396/

Charbonnier, F., Morstyn, T., & McCulloch, M. (2022). Scalable multi-agent
reinforcement learning for distributed control of residential energy flexibility.
*Applied Energy*. Registro institucional y manuscrito:
https://ora.ox.ac.uk/objects/uuid:e5bfd168-d8ca-4462-a0a3-6ccd1f97376c

Estos trabajos sustentan comparación experimental y evaluación de coordinación
energética. La extracción de módulos es una decisión de ingeniería para mantener
esa reproducibilidad; no se atribuye a estas fuentes una arquitectura Python
específica ni validación del código local.

## Hallazgo de procedencia

HARL declara MIT en su `setup.py` local y en
https://github.com/PKU-MARL/HARL/blob/main/setup.py . La auditoría conservadora
anterior solo inspecciona LICENSE/LICENCE/COPYING de raíz. La declaración es
evidencia adicional, no un texto de licencia recuperado ni una resolución de
las otras dependencias. No se ha añadido una licencia ajena por conjetura.
