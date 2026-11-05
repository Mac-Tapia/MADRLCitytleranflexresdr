# Corrección autorizada y aplicada: persistencia de ValueNorm en GPU

La microcampaña explícita `native_3e44c183b05947caba82c0b749db8d83` produjo 336 interacciones HAPPO, dos episodios y diez actualizaciones en cada uno de sus 18 propietarios. El proceso nativo terminó con código 0. El lector rechazó el intento: `value_normalizer.pt` contiene un `OrderedDict` sin tensores, aunque existen los 17 actores y el crítico. Esa evidencia no se aprueba ni se modifica retrospectivamente.

`external/HARL/harl/common/valuenorm.py` crea `nn.Parameter(...).to(device)`. Cuando la transferencia cambia de dispositivo devuelve un tensor y deja de registrarse como parámetro del módulo. En CPU la transferencia puede devolver el mismo objeto, ocultando el defecto. Las tres variables se usan y actualizan durante aprendizaje; perderlas rompe la persistencia, aunque los actores se hayan entrenado.

[Parche exacto](proposed_harl_valuenorm.patch): crear los tensores directamente en el dispositivo/dtype y después envolverlos en `nn.Parameter(requires_grad=False)`. Conserva los tres nombres, formas, actualización, normalización y dinámica; corrige su registro y serialización. No se aceptarán checkpoints vacíos previos ni se regenerarán valores ausentes.

El [probe reproducible](probar_parche_harl.py) se ejecutó con PyTorch 2.8.0+cu126 y NVIDIA GeForce RTX 4060 Laptop GPU, sin modificar HARL. En CPU/float32 el original pasa; en CPU con dtype inicial float64 y en CUDA/float32 pierde las tres claves. La propuesta en memoria pasa los tres casos: claves registradas, update finito, roundtrip real de `state_dict` y denormalización conservada. Evidencia: `data/maintenance/integracion/c20261101i01/I15/harl_valuenorm_probe.json`. La [preparación del parche](preparar_parche_harl.py) compila el candidato y fija hashes anterior/posterior en `harl_patch_preflight.json`.

Tras la autorización expresa se aplicó solo ese archivo de HARL. Su regresión CPU/dtype pasó tras el RED y el probe aplicado CPU/dtype/CUDA pasó los tres casos (`I15/harl_valuenorm_applied_probe.json`). La microcampaña debe regenerarse bajo el nuevo hash de código. La validación del lector sigue rechazando diccionarios vacíos. La revisión independiente confirmó por lectura que el parche conserva las ecuaciones y corrige el registro.

La frontera vigente de [AGENTS.md](../../../AGENTS.md) dice: «Do not edit submodules or dependencies unless the user explicitly asks in the same turn». El usuario concedió autorización adicional para HARL y el límite de KPI CityLearn; véase [el registro consolidado](PARCHES_DEPENDENCIAS.md).

La corrección responde al defecto reproducido y al criterio de custodia/reproducción de [Pineau et al. (2021)](https://www.jmlr.org/papers/v22/20-303.html); no es una mejora de recompensa ni evidencia de rendimiento científico.
