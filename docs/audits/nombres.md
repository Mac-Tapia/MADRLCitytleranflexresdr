# Implementación del renombramiento

Alcance: N1–N7 de `docs/plans/renombrar_rutas.md`. El estado verificable actual
está en `data/maintenance/names/acceptance.json`; el mapa exacto y sus hashes
están en `map.json`, el recibo nativo en `results.json` y la procedencia de rutas
en `aliases.json`, dentro de esa misma carpeta.
El entrenamiento nuevo T0–T13 es otro trabajo; esta migración no lo acredita.

## Registro de decisiones y coordinación

- Se trabaja en la raíz autorizada ya existente. El guard de contexto exige esa
  raíz; no se crea otro checkout ni se mezclan los cambios previos. Sin commit,
  stage, push, cambios de rama o edición de dependencias.
- El mandato actual autoriza ejecutar el plan. Sustituye la restricción de
  «solo planificación» de la entrega anterior.
- N1→N2: el inventario de bytes/consumidores alimenta un mapa de archivos exactos.
  N2→N3/N4: expandir movimientos padre/hijo una sola vez; consumidores se
  preparan contra el destino final. N5→N6: nombres de almacenamiento se
  desacoplan de fingerprints antes de cualquier congelación o entrenamiento.
- Los planes de fundación, jurado, objetivos, orquestación y agentes contienen
  contratos propios; se retienen por tema como referencia previa, subordinados
  al plan de entrenamiento actual. No se decide su eliminación por fecha/tamaño.
- Los tres Word contienen contenido diferente. `tesis.docx` e `informe.docx`
  siguen como los dos canónicos; `auditoria_tesis.docx` conserva el informe de
  auditoría previo, sin promoverlo a tercer canon ni alterar texto aprobado.
  Se inspeccionaron relaciones XML: no hay vínculos externos a archivos locales.
- Los informes JSON de auditoría conservan bytes, nombres originales y hashes
  que atestiguan. `aliases.json` resuelve la ubicación actual sin reescribir
  evidencia pasada. Los contratos activos (`workflow_manifest.json`, scripts,
  imports, notebooks, índices) sí se actualizan.
- `outputs/` es salida/estado de ejecución y entrega, no un árbol de fuentes.
  No se renombra su contenido activo o congelado. Los nombres cortos se aplican
  a los nuevos tratamientos mediante el layout; no se recrean históricos.

## Pruebas

RED observado: `test_names.py` falla al importar `audit_names`, todavía ausente.
Los resultados finales, mapa, integridad y vínculos se registran en
`data/maintenance/names/`; no se acredita cierre antes de verificarlos.

La revisión independiente detectó descubrimiento de runs limitado a un nivel,
rutas `Path / ...` que cambiaban de directorio, confianza en `treatments.json`,
rollback con handles abiertos, colisión no directorio en `try_01`, filtro de
secretos incompleto y aceptación sin mapa. Cada fallo importante tiene una
regresión que se observó fallar y se corrigió. La búsqueda dinámica `HISTORIA*`
se sustituyó por la ruta explícita de historia; las convenciones de herramientas
admiten kebab-case breve, pero conservan límites de longitud e identificadores.

No se elimina ninguno de los planes temáticos con requisitos propios ni se
fusionan Word por esta migración. Coste de esta decisión: quedan documentos de
referencia distintos, con roles explícitos, cuya eventual consolidación exige
una revisión de contenido separada. No se cambia la evidencia científica ni
se afirma haber ejecutado T0–T13.

## Sustento consultado en la web

PEP 8 respalda módulos cortos y legibles; 24/40 caracteres son preferencias del
propietario. Pineau et al. (2021), JMLR 22(164), respalda trazabilidad de código,
datos y procedimientos, no mejoras energéticas por cambiar nombres.

- PEP 8: https://peps.python.org/pep-0008/
- Pineau et al.: https://www.jmlr.org/papers/v22/20-303.html
- Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy
  Optimization: Taxonomy and Experimental Evaluation in CityLearn*. Tesis de
  maestría, Politecnico di Torino: https://webthesis.biblio.polito.it/40396/
- Charbonnier, F. V. J. (2023). *Multi-agent reinforcement learning for the
  coordination of residential energy flexibility*. Doctorado, Oxford:
  https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5/files/d5h73pw65d

Las fichas institucionales y el artículo sustentan reproducibilidad y alcance
experimental; no prescriben el árbol, los alias ni demuestran aprendizaje nuevo.
No se infiere indexación de una tesis. La verificación editorial de CityLearn
está documentada en el diseño de entrenamiento.

## Compatibilidad Windows y recuperación

El primer lote real se revirtió tras el rechazo de truncado de README por
un lector con memoria mapeada. Se verificaron todos los movimientos y
consumidores originales por SHA-256: sin pérdidas ni renombramientos parciales.
El ejecutor usa reemplazo atómico con staging temporal comprobado; conserva la
vista previa de un lector y publica los bytes nuevos al reabrir. Los escritores
activos siguen bloqueados. Se probó con un mapa de memoria nativo real y con
un fallo después de consolidar el duplicado. Los temporales propios se retiran
al terminar. Coste: un lector que retenga un snapshot verá el contenido anterior
hasta reabrirlo. No se cierran aplicaciones ni se alteran sus procesos.

También se impide sustituir globalmente un nombre genérico como specs: la
raíz de contratos specs/ conserva su función y solo cambia el slug de cada
SPEC. El cambio de inventario entre lecturas bloquea la planificación; el
ejecutor contrasta el hash del movimiento con el del consumidor preparado.
Las rutas antiguas en test_names.py son fixtures explícitos de regresión.

Referencia técnica primaria de la operación atómica y sus modos de apertura:
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew
