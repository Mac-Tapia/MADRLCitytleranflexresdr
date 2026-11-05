# Addendum del Revisor A al plan integrado — 2026-11-01

Para: la sesión del Revisor B que mantiene [`docs/plans/remediacion_integrada.md`](../../plans/remediacion_integrada.md) y su JSON.
De: sesión del Revisor A `865ad199-53fa-4aa9-acc3-c3dfb37f0edd`, en rol de auditor independiente de solo lectura.
Corte: HEAD `d55c6c62` más el árbol sucio en curso (ver `head.txt`). Este addendum no cambia código ni el plan.

**Propiedad.** Revisor A solo escribe en esta carpeta. No toca archivos de las tareas I00–I18 ni el plan integrado. La fusión en `remediacion_integrada.{md,json}` y en `coverage_validation.json` corresponde al Revisor B, que administra sus hashes.

## 1. Resolución de C69 (Bandit)

La contradicción tiene explicación. El dictamen inicial decía que Bandit no estaba instalado en `.venv39-citylearn-v3`, y eso era cierto. Después se ejecutó de forma aislada con `uvx`, sin instalar nada en el entorno. En este corte se repitió y se guardó la evidencia:

- Comando: `uvx bandit -r uc3m tools scripts deploy examples_madrl_v3 -x tools/skills -ll -f json -o bandit.json`
- Versión: `bandit 1.9.4` (`bandit.version.txt`). Salida 1, que en Bandit significa que hay hallazgos (`bandit.exit.txt`).
- `bandit.json`: 62.350 líneas analizadas; **1 aviso alto y 7 medios**, todos de confianza alta.

| Severidad | Regla | Ubicación | Tarea |
|---|---|---|---|
| Alta | B324 MD5 | `tools/eval/audit_drive_figure_integrity.py:23` (herramienta clasificada como obsoleta) | I10/I14 |
| Media | B614 `torch.load` | `uc3m/adapters/algorithms/evidence.py:45`; `uc3m/adapters/citylearn/policy_inference.py:462,654,655` | I10 (C58) |
| Media | B310 `urlopen` | `uc3m/data/adapters/remote_http.py:162`; `tools/figures/embed_mermaid_svgs.py:87` | I10 |
| Media | **B314 `xml.etree`** | **`uc3m/application/training/gate_report.py:39` — archivo nuevo de I01** | I01/I10, ver C70 |

Son señales estáticas, no vulnerabilidades demostradas. C05 queda respaldado por este log.

## 2. Reproducciones reutilizables (H20, C47–C51)

`reproductions.py` contiene las reproducciones que el plan registra como «declaradas por el Revisor A, no repetidas». Solo crea directorios temporales y no entrena. Se ejecuta así:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -X utf8 docs/audits/addendum_auditoria_20261101/reproductions.py .
```

Importa las APIs tal como estaban en `d55c6c62` (`treatment_trust_reasons`, `restore_finished_attempts(..., trust=)`, `pipeline.main`). Si I01, I08 o I09 cambian esas firmas, **hay que adaptar las llamadas, no las expectativas**.

| Caso | Resultado observado en `d55c6c62` | Resultado exigido tras la corrección |
|---|---|---|
| P1 H20: 0 actualizaciones, 0 pasos, intento ajeno, 1 de 2 tratamientos, informe de 2 campos | `scientifically_complete`, `scientific_acceptance=true` | Rechazo con motivos del contrato estricto y de cobertura incompleta |
| P2 C48: corte antes de escribir el manifiesto de Drive | Conflicto permanente, CLI con salida 0, nada restaurable | Adopción verificada o aislamiento explícito; conflicto con salida distinta de 0 |
| P3 C51: ruta `sub/../../outside.txt` en el manifiesto | Escribe fuera de `artifacts` | Rechazo antes de escribir |
| P4 C49: `evaluate` con tratamientos fallidos | Salida 0 | Salida distinta de 0, o un estado que el cuaderno trate como bloqueo |
| P5 C50: `.partial` residual | `analyze` queda bloqueado para siempre | Reintento posible sin sobrescribir un análisis completo |

Hash SHA-256 de `reproductions.py` en esta entrega: `fc452b59fbcd63e82da527345a5af418225dbf807fd320640f519e4ffad47ade`.

## 3. Observaciones nuevas propuestas (C70–C74)

| ID | Tarea | Observación | Criterio de cierre |
|---|---|---|---|
| C70 | I01, I10 | `gate_report.py:39` parsea el JUnit con `xml.etree` (B314). El riesgo es bajo si el JUnit siempre es local, pero el reporte de la puerta es justo la entrada que I01 deja de dar por confiable | Justificar el origen local con hash del JUnit **antes** de parsearlo, o usar un parser endurecido. Probar que un XML con expansión de entidades se rechaza |
| C71 | I10 | Evidencia positiva: `outputs/colab_delivery/colab_modular_overlay.zip` tiene 2.683 entradas y 0 rutas de navegador, credenciales o `.env`. El `Dockerfile` raíz solo copia `CityLearn/`, `uc3m/` y `tests/`, y las reglas `.gitignore` del perfil de navegador funcionan | Mantenerlo como prueba de regresión, regenerando el zip y comprobando la imagen, no solo este snapshot |
| C72 | I13 | `vulture` (confianza ≥80): `uc3m/env/wrappers.py:106`, `options` sin usar en `reset`. Encaja con H11, porque el wrapper ignora parámetros del reset | Resolverlo dentro del contrato de H11, no como limpieza aislada |
| C73 | I01 | La fixture `_campaign` de `tests/fresh_training/test_security_and_acceptance.py` codificaba el contrato débil: evidencia sin `env_steps`, `completed_episodes` ni hashes de parámetros. Tiene cambios en curso | La fixture base debe pasar `attempt_evidence_reasons` estricto, y las cuatro variantes de P1 deben estar como casos negativos |
| C74 | I12 | Afina C18: en una medición, `Select-String` sobre `tools/skills/` tardó 15 s con el perfil de navegador y unos 0 s sin él. Las llamadas Git de la guarda tardaron 124 ms. El resto de los 43 s no está explicado | Medir de forma repetida. Si se confirma, excluir de la búsqueda de referencias globales los directorios de datos que no son skills, sin dejar de rechazar referencias reales |

## 4. Plan del Revisor A: qué hago y cuándo

1. **Ahora (hecho):** evidencia de C69, reproducciones y C70–C74 en esta carpeta.
2. **Cuando Revisor B marque I01, I08 o I09 como listos para revisar:** ejecuto `reproductions.py` sobre ese corte, reviso el diff de forma adversarial con un brief propio y entrego mis hallazgos en esta carpeta (`audit_I01.md`, etc.). Las actas `data/maintenance/integracion/<cut_id>/` las escribe Revisor B. No apruebo nada por la sola existencia de pruebas verdes.
3. **I13, revisión semántica a fin de archivo (requiere autorización del usuario para usar varios agentes):** lotes calculados con el registro por archivo, 722 archivos propios versionados de código y documentación, sin `docs/audits/`:

| Lote | Archivos | Líneas |
|---|---:|---:|
| L1 `uc3m/` + `configs/` | 114 | 18.022 |
| L2 `scripts/` + `tools/` (53 de `tools/skills/`) | 219 | 62.182 |
| L3 `tests/` | 122 | 15.186 |
| L4 `docs/` + `specs/` | 107 | 15.561 |
| L5 `deploy/`, `governance/`, `examples_madrl_v3/`, `.github/`, `.claude/` y raíz | 160 | 21.883 |

   Cada archivo tendría rol, consumidores, hallazgos, pruebas y estado de revisión, que es el criterio de cierre de I13. La cifra de 773 incluía `docs/audits/`; si Revisor B quiere esos paquetes en I13, deberá añadirse como L6.

## 5. Peticiones al Revisor B

1. Fusionar C70–C74 en `remediacion_integrada.{md,json}` y regenerar `coverage_validation.json`.
2. Sustituir en C48–C51 «no repetida» por referencias a `reproductions.py`, y en C69 «sin log» por `bandit.json`.
3. Revisar C70 antes de cerrar I01: el archivo nuevo `gate_report.py` es justo el punto de entrada de la puerta.
4. Avisar cuando I01, I08 o I09 estén listos para la auditoría independiente, indicando el `cut_id`.
