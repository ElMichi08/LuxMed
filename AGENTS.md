# AGENTS.md

Guía para cualquier agente de código (Claude Code, Cursor, Copilot, Codex u otro) que trabaje en este repositorio. Es el equivalente agnóstico de herramienta a `CLAUDE.md` — si tu agente lee `CLAUDE.md` de forma nativa, ese archivo tiene el detalle completo de arquitectura y flujo de negocio; este archivo se enfoca en **qué necesitas instalado/configurado antes de poder trabajar aquí**.

## Estado del repositorio

Fase de diseño con una primera capa de código: `domain/` ya tiene implementación (`models`, `branch_rules`, `success_criteria`, `estados`, `state_machine`, `reporte`) con tests en `tests/domain/`. Las demás capas (`application/`, `infrastructure/*`, `interface/`) siguen vacías. Antes de proponer o escribir código, lee en este orden:

1. `docs/BDD/*.feature` — especificación de comportamiento vigente (fuente de verdad del *qué*).
2. `docs/arquitectura.md` — decisiones de arquitectura interna (el *cómo* a nivel de capas).
3. `docs/gui.md` — diseño superficial de la GUI.
4. `docs/legal.md` — contexto legal (no comportamiento de software).
5. `CLAUDE.md` — invariantes de diseño, convención de ramas/commits y resumen de todo lo anterior.

No hay `package.json` ni `pyproject.toml` todavía. Sí hay tests: `python -m pytest` desde la raíz corre `tests/domain/` (requiere `pytest` instalado en el entorno; no hay `requirements.txt` todavía, instálalo manualmente si tu entorno no lo trae). La estructura de carpetas (`domain/`, `application/`, `infrastructure/`, `interface/`) ya está decidida — respétala en vez de improvisar una nueva.

## Ramas y commits

Una rama de git por capa, mismo nombre que la carpeta (`domain`, `application`, `infrastructure/excel`, `infrastructure/pdf`, `infrastructure/persistence`, `infrastructure/playwright`, `infrastructure/throttling`, `interface`). `main` es el tronco: ahí van `docs/BDD/*.feature`, el resto de `docs/`, `CLAUDE.md`, `AGENTS.md` y config transversal (`.gitignore`, futuro `pyproject.toml`, CI) — **nunca** directo en una rama de capa. El código de cada capa va solo en su propia rama. Si necesitás un cambio compartido mientras trabajás en una rama de capa, comitealo en `main` y traelo con `git merge main` (no rebase). Detalle completo y ejemplo real en `CLAUDE.md` → "Convención de ramas y commits". No pushees a `origin` sin que se te pida explícitamente.

## Skills requeridas

Este proyecto usa **Playwright** para automatizar 3 portales web de terceros (scraping/RPA). El repo declara sus skills en `skills-lock.json`:

```json
{
  "skills": {
    "playwright-dev": {
      "source": "microsoft/playwright",
      "sourceType": "github"
    }
  }
}
```

- `playwright-dev` documenta cómo desarrollar contra la librería Playwright: API, herramientas de MCP, comandos de CLI, dependencias de vendor. Es referencia para escribir los adapters de `infrastructure/playwright/` (ver `docs/arquitectura.md`).
- **El contenido instalado de la skill no está en el repo** (`.agents/` y `.claude/` están en `.gitignore` a propósito — son artefactos de instalación local, no código del proyecto). Si tu agente soporta el mecanismo de skills de Claude Code, instala `playwright-dev` desde `skills-lock.json` antes de tocar cualquier `*_adapter.py`. Si tu herramienta no soporta ese mecanismo, consulta la documentación pública de Playwright directamente (playwright.dev) como equivalente.
- No agregues código de scraping sin haber leído primero la skill (o la documentación equivalente) — los adapters de portal son la pieza más volátil del sistema (ver "Por qué hexagonal" en `docs/arquitectura.md`) y es fácil violar la regla de dependencia (`domain`/`application` nunca deben importar tipos de Playwright) si se escribe a ciegas.

### `gherkin-spec` — para tocar `docs/BDD/*.feature`

Fuente: [`ElMichi08/gherkin-spec`](https://github.com/ElMichi08/gherkin-spec.git). Todavía no está instalada en este proyecto (no aparece en `skills-lock.json` — instálala apuntando tu skill marketplace a ese repo antes de tocar cualquier `.feature`; su primera instalación debería agregar la entrada correspondiente al lockfile, con su propio `computedHash`).

- Mantiene el formato narrativo usado en este proyecto para `docs/BDD/`: Preámbulo de invariantes, Terminología, Features/Scenarios en español, Apéndices que separan stack técnico y contexto legal del comportamiento verificable — el mismo formato que tenía `Requisitos.MD` y que heredaron los `.feature` actuales.
- **Úsala siempre que modifiques o agregues un escenario** en `docs/BDD/` — `06_consulta_portal3.feature` sigue con escenarios `@pendiente` (ver `docs/arquitectura.md`, sección de pendientes) hasta explorar el Portal 3 real; el resto de features ya fue confirmado por el propietario (2026-08-15). Escribir un escenario a mano sin la skill es la forma más fácil de romper la consistencia narrativa entre los 13 archivos.
- No sustituye la validación del propietario (el médico) — la skill asegura que el *formato* quede correcto, no que el *contenido* esté confirmado como comportamiento real.

## Reglas no negociables al escribir código

Ver `CLAUDE.md` → "Invariantes de diseño" para el detalle completo. Resumen:

- On-premise, un solo ejecutable, sin servidor central.
- Cero retención de datos de paciente fuera de la máquina del médico.
- Automatización **asistida**: el sistema nunca vence controles de acceso automáticamente.
- Sin LLM en ninguna etapa — procesamiento 100% determinista.
- El sistema nunca recibe ni almacena credenciales del Portal 3.
- Regla de dependencia hexagonal: `domain` no importa nada de `infrastructure` ni `interface`; `application` conoce `domain` y `ports`, nunca una clase concreta de Playwright/GUI.

## Antes de implementar Portal 3

`docs/BDD/06_consulta_portal3.feature` marca su comportamiento de fallo como no confiable (extrapolado por analogía, sin validar contra el portal real). No implementes `portal3_adapter.py` en firme sin antes explorarlo con Playwright — ver la nota de cabecera de `docs/arquitectura.md`.
