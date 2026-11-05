# Autorización concedida: dos archivos adicionales de dependencias

El usuario autorizó expresamente ambos parches el 2026-11-02. Están aplicados solo a los archivos siguientes; [recibos de aplicación](dependency_application.json) fijan hashes anterior/posterior y respaldos de bytes. Los preflight conservan su estado histórico anterior a la aplicación.

| Archivo protegido | Parche preparado | Reproducción y comprobación del candidato |
|---|---|---|
| `external/HARL/harl/common/valuenorm.py` | [Registro de tres parámetros en su dispositivo](proposed_harl_valuenorm.patch) | [Diagnóstico](HARL_NORMALIZER.md); PyTorch real CPU/dtype/CUDA: el original pierde claves y el candidato conserva las tres y su roundtrip. `I15/harl_valuenorm_probe.json`. |
| `CityLearn/citylearn/internal/kpi.py` | [Límite terminal de liquidación](proposed_citylearn_kpi_terminal.patch) | MASAC nativo termina 24 acciones y el evaluador original intenta `pricing[24]` de longitud24. Probe analítico 24/48: costo completo7.2/14.4, cálculo intermedio idéntico, precios incompletos rechazados. [Preflight](citylearn_kpi_patch_preflight.json). |

Ambos candidatos compilan y fueron revisados independientemente sin hallazgos nuevos. Las cinco regresiones primero fallaron y después pasaron (`I15/dependency_red.xml`, `I15/dependency_green.xml`); incluyen evaluación nativa al terminar 24/48 acciones. El probe CPU/dtype/CUDA del normalizador aplicado pasa los tres casos (`I15/harl_valuenorm_applied_probe.json`). El perfil estricto se repite con una microcampaña nueva. El permiso no autoriza otros archivos externos, campaña anual, infraestructura pagada ni publicación.

La frontera de [AGENTS.md](../../../AGENTS.md) exige: «Do not edit submodules or dependencies unless the user explicitly asks in the same turn». La autorización adicional fue recibida antes de editar. Se conserva el rechazo de los checkpoints vacíos anteriores; no se rellenan retrospectivamente los estados perdidos.
