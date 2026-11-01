# Preparación del nuevo entrenamiento para Google Colab

## Entregables

- Notebook nuevo: `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb`.
- Paquete de cambios y dataset: `outputs/colab_delivery/colab_modular_overlay.zip`.
- Generador reproducible: `python -m tools.colab.build_modular_colab_notebook`.

El tutorial original de 77 celdas se conserva. El complemento reutiliza
literalmente su instalación Python 3.9 y llama al constructor original de
argumentos de `colab_a100_official_launcher`, evitando duplicar hiperparámetros.
El ZIP permite utilizar los cambios locales sin publicarlos ni hacer push.
No contiene entornos virtuales, salidas de entrenamiento o perfiles de navegador.

## Uso

1. Subir el notebook a Colab mediante Archivo → Subir notebook.
2. Seleccionar acelerador GPU disponible y ejecutar la primera celda; cuando
   lo solicite, subir `colab_modular_overlay.zip`.
3. Ejecutar la instalación original de Python 3.9 y dependencias.
4. Autorizar el montaje de tu Drive para checkpoints y resultados.
5. Revisar el plan generado: recursos, argumentos, semillas y 12 tratamientos.
6. Activar `RUN_TRAINING=True` únicamente para iniciar la campaña. La ejecución
   normal de todas las celdas prepara, pero no lanza entrenamiento.

La primera reconstrucción usa el commit del paquete. No se cambia de revisión
ni se borra un checkout preexistente incompatible; en ese caso usar un runtime
limpio. Cada corrida registra argumentos nativos, dataset y fuentes por hash.

## Recursos

50 episodios × 8760 pasos por defecto, cuatro algoritmos y E1–E3. Se mantiene
la agrupación original: HAPPO+MASAC y después MATD3+MAAC. El máximo de trabajos
simultáneos se calcula con CPU utilizable, RAM disponible y VRAM detectada,
hasta seis cuando cabe en el presupuesto. No se asume que haya A100/H100.

El presupuesto usa un máximo agregado de 85% de VRAM en los caps solicitados.
Estos caps no prueban ausencia de OOM: CUDA, buffers CPU y fragmentación deben
validarse en el runtime real. En RAM inferior a 32 GiB se reducen buffers y
se conserva esa decisión en los argumentos que forman la identidad. No mezclar
estadísticas de tratamientos con hiperparámetros efectivos distintos.

No exige compra de unidades ni Colab Pro. La disponibilidad, tipo de GPU y
tiempo de sesión no están garantizados por Colab:
https://research.google.com/colaboratory/faq.html .

## Fronteras y estado real

Colab/Drive se habilitan por la petición explícita del usuario como destino
opcional; no se reinstalan sus MCP ni se hacen obligatorios para las pruebas
locales. Son servicios externos, no componentes que se declaren software OSI.
La ejecución local sigue disponible sin cuenta ni suscripción.

En desarrollo rige exclusivamente D:/MADRLCitytleranflexresdr. En Colab se
autoriza exclusivamente /content/MADRLCitytleranflexresdr con el mismo origin;
la entrada Linux no intenta ejecutar PowerShell. No se usa otro proyecto.

Probado localmente: construcción de argumentos 4×3, presupuesto de recursos,
identidad, compilación de todas las celdas, preservación de fuentes y smokes
nativos de los cuatro algoritmos. NO ejecutado todavía en un runtime real de
Colab: instalación de wheels, GPU/CUDA, bloqueo sobre Drive y reanudación tras
desconexión real. La celda de preflight comprueba dataset y bloqueo antes de lanzar.

La preparación no demuestra paridad de optimizador/RNG/replay, validez de una
campaña multisemilla ni un mejor modelo final. El manifiesto mantiene esos
pendientes explícitos y no los cierra con un smoke.
