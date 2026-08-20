## Descripción del Cambio
<!-- Explica brevemente el propósito de este PR y qué problema resuelve. -->

## Tipo de Cambio
- [ ] Nueva funcionalidad (capa correspondiente)
- [ ] Corrección de bug
- [ ] Refactor / Mejora de código
- [ ] Documentación / BDD (`docs/` o `.feature`)
- [ ] Configuración transversal (CI, linters, git)

## Checklist de Invariantes y Calidad
- [ ] **Regla de Dependencia Hexagonal**: `domain` no importa `application`, `infrastructure`, `interface` ni librerías de I/O externas; `application` solo depende de `domain` y sus propios `ports`.
- [ ] **Privacidad y Retención Cero**: No se incluyen credenciales, tokens ni archivos locales con datos reales de pacientes (`.xlsx`, `.pdf`, `.db`).
- [ ] **Determinismo (Sin LLM)**: Ningún flujo incorpora llamadas a modelos de lenguaje o componentes no deterministas.
- [ ] **Pruebas Automatizadas**:
  - [ ] Los tests existentes pasan (`pytest`).
  - [ ] Se incluyeron tests unitarios para la nueva lógica.
  - [ ] Los tests de frontera arquitectónica pasan sin errores.
- [ ] **Análisis Estático**: `ruff check .` y `mypy domain application tests` pasan sin advertencias.
- [ ] **Estrategia de Merges**: Se respetó la convención de ramas (`merge`, no `rebase`).
