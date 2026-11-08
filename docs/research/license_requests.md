# Pedidos de licencia a repositorios de origen

**Estado:** publicados el 2026-11-08 con la aprobación del propietario.
**Motivo:** SPEC-001. HARL, MARL y MATD3implementation no declaran licencia (la API de GitHub devuelve `license=null` y no hay `LICENSE` en el árbol fijado, revisado el 2026-10-31). Mientras tanto rige la excepción acotada de `governance/open_source_policy.yaml`.

Los textos van en inglés porque los repositorios son internacionales. Antes de publicar, comprobar que no exista ya un issue equivalente abierto.

## PKU-MARL/HARL

**Título:** Could you add a license to the repository?

> Hello, and thank you for releasing HARL. We use it as the HAPPO backend in a doctoral thesis on multi-agent reinforcement learning for building energy flexibility in CityLearn (Universidad Nacional de Ingeniería, Peru).
>
> The repository does not include a license file, so by default all rights remain with the authors and we cannot be sure how the code may be used, modified or cited in reproducible research. Would you consider adding an OSI-approved license (for example MIT or Apache-2.0)?
>
> We cite the HARL paper (Zhong et al., JMLR 2024) in our work. Thank you for your time.

## puyuan1996/MARL

**Título:** License for the MARL implementations

> Hello, and thank you for publishing these MARL implementations. We use the MASAC implementation as a backend in a doctoral thesis on multi-agent reinforcement learning for building energy flexibility in CityLearn (Universidad Nacional de Ingeniería, Peru).
>
> The repository has no license file, so the terms for using and modifying the code in reproducible research are unclear. Would you consider adding an OSI-approved license (for example MIT or Apache-2.0)?
>
> We credit the repository in our work. Thank you.

## JohannesAck/MATD3implementation

**Título:** Could you add a license to the repository?

> Hello, and thank you for sharing this MATD3 implementation. We use it as the MATD3 backend in a doctoral thesis on multi-agent reinforcement learning for building energy flexibility in CityLearn (Universidad Nacional de Ingeniería, Peru).
>
> The repository has no license file, so by default all rights remain with you and the terms for reuse in reproducible research are unclear. Would you consider adding an OSI-approved license (for example MIT or Apache-2.0)?
>
> We credit the repository and the MATD3 paper in our work. Thank you.

## Seguimiento

| Repositorio | Issue | Fecha | Respuesta |
|---|---|---|---|
| PKU-MARL/HARL | https://github.com/PKU-MARL/HARL/issues/77 | 2026-11-08 | pendiente |
| puyuan1996/MARL | https://github.com/puyuan1996/MARL/issues/3 | 2026-11-08 | pendiente |
| JohannesAck/MATD3implementation | https://github.com/JohannesAck/MATD3implementation/issues/5 | 2026-11-08 | pendiente |

Si se obtiene licencia: añadir el archivo `LICENSE` al fork, volver a ejecutar `scripts/quality/run_foundation_gates.ps1` y retirar la excepción. Si vence la excepción sin respuesta, evaluar la sustitución del backend (SPEC-001, opción B) en una versión posterior a la tesis.
