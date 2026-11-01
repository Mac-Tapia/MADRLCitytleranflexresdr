# Tareas — SPEC-001

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-001.1:** Política y evaluador implementados — `governance/open_source_policy.yaml, uc3m/governance/open_source.py`
- [x] **FR-001.2:** Auditor de dependencias e inventario inicial — `tools/ops/audit_open_source_dependencies.py, data/audits/open_source_dependency_manifest.json`
- [x] **FR-001.2:** Rol de cada submódulo (`runtime`/`reference_only`) con evidencia; MicroGrids (EUPL-1.1), prosumpy (EUPL-1.1) y evcc quedan como referencia no importada, verificada por prueba contractual — `governance/dependency_roles.yaml, tests/contract/test_dependency_roles.py`
- [x] **FR-001.2:** Paquetes declarados verificados desde metadatos instalados: numpy 1.23.5, pandas 2.0.3 y scipy 1.10.1, todos BSD-3-Clause — `data/audits/open_source_dependency_manifest.json`
- [x] **FR-001.2:** HARL, MARL y MATD3implementation no tienen licencia en origen (API de GitHub `license=null`, sin LICENSE en el árbol fijado) y son backends de HAPPO, MASAC y MATD3. Decisión del propietario (2026-11-01): excepción acotada con vencimiento 2027-06-30 (opción C), que la puerta informa como `verified_with_exceptions`; una prueba impide incluir `external/` en imágenes publicadas — `governance/open_source_policy.yaml, tests/contract/test_dependency_roles.py`
- [ ] **FR-001.2:** Publicar los pedidos de licencia (opción A) tras aprobación explícita y retirar la excepción si llega una licencia; si vence sin respuesta, evaluar la sustitución del backend (opción B) después de la tesis — `docs/research/license_requests.md`
- [x] **FR-001.3:** SBOM CycloneDX 1.5 local: 247 componentes (paquetes del entorno y submódulos fijados), 15 sin licencia verificable marcados `unverified`; se regenera en la puerta — `tools/ops/generate_sbom.py, data/audits/sbom.cdx.json`
- [x] **FR-001.5:** Inventarios que declaran un conector desactivado ya no cuentan como uso en tiempo de ejecución: 0 hallazgos críticos — `tools/ops/audit_closed_services_and_secrets.py`
- [x] **FR-001.4:** Registro de repositorios — `docs/research/repository_registry.yaml`
- [x] **FR-001.5:** Auditor de secretos y servicios cerrados — `tools/ops/audit_closed_services_and_secrets.py`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_foundation_gates.ps1`
