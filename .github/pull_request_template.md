## Descripción del Cambio
<!-- Propósito del PR y problema que resuelve. Enlaza la spec (`docs/BDD/*.feature`, `docs/UI/*.md`) de la que parte. -->

## Tipo de Cambio
- [ ] Nueva funcionalidad (capa correspondiente)
- [ ] Corrección de bug
- [ ] Refactor / Mejora de código
- [ ] Documentación / BDD (`docs/` o `.feature`)
- [ ] Interfaz (`app/infrastructure/ui/`)
- [ ] Configuración transversal (CI, linters, git)

## Rama de origen y objetivo
- Rama de origen: `<nombre>` · Objetivo: `main`
- [ ] Rama actualizada con `git rebase origin/main` (flujo de integración acordado tras el merge de `backup`).
- [ ] Sin `push --force` sobre ramas compartidas sin avisar antes a su responsable.

## Checklist de Invariantes y Calidad
- [ ] **Regla de dependencia hexagonal**: `app/domain` no importa `app/application`, `app/infrastructure` ni librerías de I/O; `app/application` solo depende de `app/domain`; los adaptadores de `app/infrastructure/*` no se importan entre sí; PyQt6 solo en `app/infrastructure/ui/`. (Lo verifica `tests/architecture`.)
- [ ] **Privacidad y Retención Cero**: sin credenciales, tokens ni `.env`; sin archivos `.xlsx`, `.pdf` o `.db` con datos reales; sin cédulas ni nombres de pacientes en logs, mensajes de error, tooltips ni `print`.
- [ ] **Terminología (ADR 003)**: la documentación y los textos de la UI usan solo IESS, Entidad Previsional Especial y los portales por rol; los nombres reales viven únicamente en el código.
- [ ] **Determinismo (Sin LLM)**: ningún flujo incorpora llamadas a modelos de lenguaje ni componentes no deterministas.
- [ ] **AGENTS.md**: sin comentarios en código de producción, tipado estático estricto, cambios quirúrgicos y sin dependencias no autorizadas.
- [ ] **Pruebas**:
  - [ ] `pytest` pasa en el job de Windows.
  - [ ] La lógica nueva incluye tests unitarios.
  - [ ] Los tests de `tests/architecture` pasan.
- [ ] **Análisis estático** (informativo por ahora): no introduce errores nuevos de `ruff check` ni `mypy app` en los archivos tocados.
