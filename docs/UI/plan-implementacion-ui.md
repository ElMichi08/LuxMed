# Plan de implementación de la UI (PyQt6)

> **Estado:** plan para aprobación. No existe código de la UI todavía.
> **Fecha:** 2026-09-21. **Rama de trabajo:** `UI`. **Base:** `main` @ `ae884df` (merge del PR #3, `backup` → `main`).
> **Documentos relacionados:** `spec-ui-contrato.md` (contratos, señales, estados y archivos por fase), `propuesta-cambios-spec-sin-pausa.md` (decisiones de producto y de arquitectura de la UI) y `stitch/v2/` (mocks).
> **Skill de apoyo:** `.claude/skills/pyqt6-desktop-ui-hexagonal/` (local, fuera de git).

---

## 1. Punto de partida

| Tema | Estado |
|---|---|
| Backend | `main` ya trae núcleo, tres portales, `excel_handler`, `pdf_merger` y SQLite. Está por detrás de `business-rules.md` v1.3.0 (ver sección 4) |
| CI | Workflow `tests.yml` en `main`: fronteras hexagonales y pytest en Windows bloquean; ruff y mypy son informativos. Corrió en verde sobre el merge |
| UI | Esqueleto vacío: `login_view.py`, `main_window.py`, `processing_view.py`, `upload_view.py` (0 bytes), `main.py` vacío |
| Specs | Contratos de UI redactados y pendientes de aprobación. Decisiones de producto y arquitectura cerradas en la ronda SDD del 2026-09-21 |
| Dependencias | `requirements.txt` con PyQt6 6.7.1 (Qt 6.7.2) y `requirements-dev.txt` con `pytest-qt`. El `Pipfile` sigue pidiendo Python 3.14 |

**Decisiones ya cerradas** (detalle en `propuesta-cambios-spec-sin-pausa.md` §4 y §6): UI en `app/infrastructure/ui/` con subcarpetas; DTOs congelados con `pyqtSignal(object)`; puerto `OperatorGate` con `threading.Event`; `QThread` como subclase; fuentes embebidas y SVG propios; `pytest-qt` solo en desarrollo; `PENDIENTE` como nombre canónico; errores persistidos entre sesiones; cerrar la ventana con lote en curso pide confirmación; tabla canónica del mock 05; entregables habilitados en `DETENIDO`; resumen solo con Rama A y Rama B.

---

## 2. Pendientes que condicionan el plan

La ronda SDD de la UI quedó en pausa. Estas preguntas se retoman antes de la Fase 0b (contratos), no antes de las Fases 1 a 3.

| # | Pendiente | Qué cambió tras revisar el código real |
|---|---|---|
| 1 | Versión de Python | El `Pipfile` pide 3.14 (`pandas==2.2.2` y `greenlet==3.0.3` no tienen rueda para 3.13 ni 3.14 en Windows). El CI usa 3.12. En el equipo hay 3.11.9 y 3.13. Propuesta: 3.11 o 3.12 |
| 2 | Ubicación de los contratos de UI | `app/domain/entities.py` y `ports.py` ya tienen otro modelo (`EstadoValidacion`, puertos `I*`). Propuesta: DTOs de vista y puertos de entrada en `app/application/`, y los enums de negocio nuevos en `domain` coordinados con Israel |
| 3 | Convención de nombres | El código usa clases abstractas con prefijo `I` (`IPacienteRepository`, `IExcelHandler`). El spec usa `Protocol` sin prefijo. Propuesta: `ABC` con prefijo `I` |
| 4 | Lecturas de SQLite en el hilo principal | `AGENTS.md` §4 prohíbe escribir, no leer. Requiere modo WAL en el adaptador |
| 5 | Preguntas 1, 2 y 5 a 9 de `spec-ui-contrato.md` §12 | Sin cambios; ver ese documento |

---

## 3. Fases

Cada fase se entrega en un PR pequeño a `main`, así el CI de Windows la valida. Los archivos de cada fase están listados en `spec-ui-contrato.md` §10.

### Fase 0b · Reconciliar el spec con el dominio real (sin código de UI)
- **Objetivo:** que los contratos del spec coincidan con lo que ya existe en `main`.
- **Trabajo:** actualizar `spec-ui-contrato.md` §4 y §5 con las decisiones de la sección 2 y con esta correspondencia:

| Puerto del spec | Lo que ya existe en el código |
|---|---|
| `BatchIntake` | `IExcelHandler.leer_pacientes` más `ValidatorService.higienizar_y_clasificar` |
| `OperatorGate` con `LOGIN_PORTAL_3` | `IScraperService.existe_autenticacion_portal_3` y `vincular_sesion_portal_3` (hoy sin interacción con la UI) |
| `OperatorGate` con `CAPTCHA_PORTAL_2` | `AltchaHandler`, que hoy solo espera 30 s |
| `DeliverablesExporter` | `IExcelHandler.exportar_excel_limpio` y `exportar_excel_auditoria`, más `IPdfConsolidator` |
| `BatchExecution` | `OrchestratorService.procesar_cola`, síncrono y sin progreso |
| Consultas de detalle, errores y resumen | `IPacienteRepository` (una sola tabla `pacientes`, sin lote) |

- **Hecho cuando:** el spec está aprobado y sus preguntas abiertas cerradas o aplazadas de forma explícita.

### Fase 1 · Tema
- **Entregables:** `bootstrap.py`, `theme/` (`tokens.py`, `palette.py`, `stylesheet.py`, `luxmed.qss.tpl`, `fonts.py`, `icons.py`), `assets/` (3 familias de fuentes y ~20 SVG) y `main.py` mínimo.
- **Tokens:** los 17 colores del spec §9. La escala tipográfica exacta se extrae de los HTML 05, 09 y 10.
- **Hecho cuando:** una ventana de prueba muestra los componentes base y `contrast_check.py` pasa.
- **Test:** `tests/ui/test_tokens_contrast.py`.

### Fase 2 · Shell y navegación
- **Entregables:** `shell/` con `main_window.py`, `navigation.py`, `rail.py`, `top_bar.py`, `status_bar.py` y `log_panel.py`.
- **Hecho cuando:** se navega entre páginas vacías del `QStackedWidget`, el riel usa botones `checkable` y Historial aparece deshabilitado.

### Fase 3 · Widgets base
- **Entregables:** `widgets/` con `card.py`, `status_chip.py`, `kpi_tile.py`, `dropzone.py`, `route_dots.py` y `empty_state.py`.
- **Hecho cuando:** cada widget se ve como en los mocks a 1280 px y tiene estados hover, foco, deshabilitado y vacío.

### Fase 4 · Pantallas sobre un simulador
- **Objetivo:** construir y verificar toda la UI sin Playwright ni SQLite.
- **Entregables:** `screens/`, `dialogs/`, `models/` y `presenters/`, más `tests/ui/fakes/` con implementaciones en memoria de todos los puertos, usando los datos del mock (428 filas: 94 `CEDULA_INVALIDA`, 311 `COMPLETADO`, 19 `NO_ENCONTRADO`, 4 `ERROR_PORTAL_3`).
- **Orden:** 01 login, 02 carga, 03 revisión previa, 05 lote en proceso (tabla en vivo) con los diálogos 04 y 06, 08 detalle, 07 lote detenido, 09 resumen, 10 entregables, 11 errores, 12 ajustes y el diálogo de cierre con lote en curso.
- **Hecho cuando:** un recorrido completo sobre el simulador reproduce las 12 pantallas, con pruebas de modelo, presenters y diálogos.

### Fase 5 · Integración con el backend real
- **Depende de** el trabajo de la sección 4. Sin él, la UI solo funciona con el simulador.
- **Entregables:** `workers/batch_runner_thread.py`, `workers/task_thread.py` y el cableado real en `main.py`.
- **Hecho cuando:** un lote de prueba de extremo a extremo (login manual, captcha, errores y entregables) corre desde la UI.

### Fase 6 · Verificación y empaquetado
- Comparación de `widget.grab()` contra los PNG de `stitch/v2/` y pruebas a 100, 125, 150 y 175 % de DPI.
- Empaquetado con PyInstaller en modo `onedir`. Los binarios de Chromium de Playwright van aparte y se prueban en un equipo limpio.

---

## 4. Trabajo de backend que necesita la Fase 5

No es alcance de la UI. Se coordina con Israel, que decide quién lo hace y en qué rama.

| Necesidad | Estado en `main` |
|---|---|
| Login del Portal 3 manual, una sola vez por lote, con sesión en memoria | `Portal3Adapter` inicia sesión en cada paciente con credenciales de `.env` |
| Captcha del Portal 2: 3 intentos automáticos y luego decisión del médico | `AltchaHandler` espera 30 s y devuelve `False` |
| Estados granulares (`COMPLETADO`, `ERROR_PORTAL_N`, `CEDULA_INVALIDA`, `NO_ENCONTRADO`) | Solo `PENDIENTE`, `VALIDO` e `INVALIDO` |
| Lote, checkpoint y reproceso, con persistencia | Sin lote; una tabla `pacientes` |
| Progreso hacia la UI y procesamiento en serie con throttling | `procesar_cola()` síncrono y sin progreso |
| Excel limpio idéntico al original y lectura por columnas B, C, E, G, H, M | Lee por nombre de columna y el limpio solo exporta `VALIDO` |
| PDF `NOMBRE_CEDULA.pdf` en la subcarpeta del mes, con verificación de integridad y carpeta de salida configurable | `CEDULA_NOMBRE_REPORT.pdf` plano en `data/pdf_exports`; los PDF corruptos se omiten |
| Sin cédulas ni nombres en logs | El orquestador y varios `print` los registran |
| Modo WAL y timeout en SQLite (lecturas desde la UI mientras el lote escribe) | Sin verificar |

---

## 5. Integración con el CI

- El test `tests/architecture` ya exige que PyQt6 solo se importe en `app/infrastructure/ui/` y que ningún adaptador importe a otro. La UI debe cumplirlo desde el primer archivo.
- Los tests de UI viven en `tests/ui/` y corren en el job de Windows con `QT_QPA_PLATFORM=offscreen` y `pytest-qt`, que ya están configurados en el workflow.
- Pendiente de aprobar: llevar `check_ui_rules.py` y `contrast_check.py` a `scripts/` (hoy están en `.claude/`, fuera de git) y añadirlos como pasos del CI.
- Cada PR de UI debe dejar en verde los 3 jobs del workflow y respetar la plantilla de PR.
- Limpieza pendiente del workflow: quitar el disparador temporal `ci/**`.

---

## 6. Flujo de ramas

1. Llevar `main` a la rama `UI` (merge o rebase, según el flujo que acuerde Israel). El `.gitignore` local tiene cambios sin commitear que chocarán con el de `main`; `main` ya ignora `.claude/`, `.env` y `.pytest_cache`. Faltan `.mypy_cache/`, `.ruff_cache/` y `.mcp.json`.
2. Un PR por fase hacia `main`. Nombres de rama sin mayúsculas que colisionen en Windows (`PlayWright` frente a `playwright`).
3. Los documentos de `docs/UI/` (untracked hoy) se commitean en su propio PR de documentación, separados del código.

---

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Backend por detrás de las decisiones de producto | Fases 1 a 4 sobre el simulador; la Fase 5 solo arranca cuando el backend ofrezca lote, progreso y login manual |
| Los contratos de UI chocan con `domain` de otras ramas | Definirlos en `application` y coordinar los enums nuevos con Israel antes de tocar `domain` |
| Playwright síncrono y `QThread` | Crear `sync_playwright()` dentro de `run()`; los adaptadores actuales ya son sin estado, lo que encaja |
| Versión de Python sin fijar | Decidir 3.11 o 3.12 antes de la Fase 1 y alinear `Pipfile` y CI |
| PII en la UI o en logs (LOPDP) | DTOs sin PII fuera de lo que se muestra; `batch_failed` solo con el nombre del tipo de error |
| Mocks con inconsistencias | Aplicar los cambios de `propuesta-cambios-spec-sin-pausa.md` §7; la propuesta prevalece sobre el PNG |

---

## 8. Siguiente paso

1. Retomar la ronda SDD con los pendientes de la sección 2 (en especial Python, ubicación de contratos y nombres).
2. Aprobar `spec-ui-contrato.md`, que autoriza la lista de archivos de la Fase 1 a la 6.
3. Con eso, arrancar la Fase 1. Las Fases 1 a 3 no dependen del backend.
