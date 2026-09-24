# Handoff · Fase 4 cerrada, Fase 5 y 6 para Israel

> **Léelo así (agente de código):** primero `AGENTS.md` (raíz del repo, manda siempre), luego este documento, luego `docs/UI/spec-ui-contrato.md` para el detalle de contratos. Este archivo es el **plano de contexto** que exige `AGENTS.md` §1: solo autoriza los archivos y cambios listados en la sección 4. Cualquier cosa fuera de esa lista requiere una especificación nueva del desarrollador.
> **Fecha:** 2026-09-23. **Rama:** `UI`. **Estado:** Fases 0b a 4 completas y verificadas. Fases 5 y 6 sin empezar.
> **Documentos relacionados:** `AGENTS.md`, `docs/UI/plan-implementacion-ui.md` (fases y backend necesario), `docs/UI/spec-ui-contrato.md` (§5 puertos, §6 señales, §7 máquina de estados, §10 archivos por fase), `docs/UI/propuesta-cambios-spec-sin-pausa.md` (§7 prevalece sobre los PNG), `docs/UI/stitch/v2/` (mocks).
> **Skill de apoyo:** `.claude/skills/pyqt6-desktop-ui-hexagonal/` (local, fuera de git; sus scripts `check_ui_rules.py` y `contrast_check.py` están pendientes de moverse a `scripts/`, ver plan §5).

---

## 1. Reglas que no se negocian (resumen de `AGENTS.md`)

1. **Sin autonomía estructural.** No se crean archivos ni se toman decisiones de diseño fuera de la especificación. Si falta un dato (campo, puerto, transición), se pregunta.
2. **Cero comentarios y cero docstrings.** Claridad por tipado estricto y nombres explícitos.
3. **Arquitectura hexagonal.** PyQt6 solo se importa dentro de `app/infrastructure/ui/`. Los adaptadores nunca se importan entre sí; se comunican por puertos del dominio inyectados desde `main.py`. `tests/architecture` lo verifica.
4. **SOLID.** El orquestador no cambia al añadir un portal; `medical_flow` no importa Playwright ni SQLite; interfaces delgadas (ISP).
5. **Hilos.** La UI vive solo en el hilo principal. Todo lo pesado (Pandas, SQLite, Playwright) corre en una subclase de `QThread` y comunica hacia la UI únicamente con señales `pyqtSignal(object)` que llevan DTOs `frozen=True, slots=True`. Cierre con `requestInterruption()` y `wait()`; jamás `terminate()`.
6. **Sin PII** en logs, `batch_failed` (solo el nombre del tipo de error), tooltips ni títulos de ventana.
7. **Estilo.** Ningún hex fuera de `theme/tokens.py`. Ningún emoji ni carácter Unicode usado como icono (hay SVG en `assets/icons/`). Ningún `QTableWidget` en pantallas de lote. Qt 6.7.2: sin APIs de 6.8+.

Protocolo por tarea (`AGENTS.md` §2): el desarrollador entrega la firma o el plano; el agente valida que no viole reglas de dominio; luego escribe de forma quirúrgica, sin tocar líneas adyacentes ni añadir dependencias no autorizadas.

---

## 2. Estado entregado (Fases 0b a 4)

| Fase | Contenido | Dónde |
|---|---|---|
| 0b | DTOs y puertos | `app/application/dto.py`, `app/application/ui_ports.py` |
| 1 | Tema (tokens, paleta, QSS, fuentes, iconos) y `bootstrap.py` | `app/infrastructure/ui/theme/`, `assets/`, `bootstrap.py` |
| 2 | Shell: riel, barra superior, barra de estado, navegación, panel de bitácora | `app/infrastructure/ui/shell/` |
| 3 | Widgets base | `app/infrastructure/ui/widgets/` |
| 4 | 8 pantallas, 5 diálogos, 6 modelos/delegates, 9 presenters con `Protocol` por vista, fakes en memoria | `screens/`, `dialogs/`, `models/`, `presenters/`, `tests/ui/fakes/` |

**Verificación al cierre:** 100 tests en `tests/ui` y `tests/architecture` pasan (`QT_QPA_PLATFORM=offscreen`); `mypy` limpio en `app/infrastructure/ui` y `tests/ui`; `check_ui_rules.py` sin incumplimientos; auditoría de emojis en cero. Hallazgos de `ruff` aceptados a propósito: `BLE001` en `upload_presenter.py` (captura en frontera) y `DTZ001` en `tests/ui/fakes/dataset.py` (todo el proyecto usa fechas sin zona horaria).

**Cómo verla funcionando hoy:** `python scripts/demo_ui.py`. Es una herramienta de desarrollo (fuera de `app/`, importa los fakes de `tests/ui/fakes/`) que arma el flujo completo sobre datos simulados: login (`admision.01` / `lux2026`) → shell real → Carga → Revisión → Procesando (+ detalle) → Resumen, más Errores, Ajustes y un menú de diálogos sueltos. **Es el plano de referencia del cableado de la sección 4.1.**

---

## 3. Pendientes antes del push y merge a `main`

Checklist para quien haga el PR de la rama `UI`:

- [ ] Llevar `main` a `UI` otra vez si avanzó (`git merge origin/main`), resolviendo `.gitignore` si choca.
- [ ] Confirmar que `tests/ui/_capturas/` sigue ignorado (lo está) y que no se cuela ningún PNG ni `debug_*` en la raíz.
- [ ] Revisar que las 4 eliminaciones ya preparadas (`login_view.py`, `main_window.py`, `processing_view.py`, `upload_view.py` del scaffold viejo en `app/infrastructure/ui/`) entran en el mismo PR que sus reemplazos en `screens/` y `shell/`.
- [ ] Correr en verde los 3 jobs del workflow (fronteras hexagonales, pytest en Windows; ruff y mypy son informativos).
- [ ] Decidir si `scripts/demo_ui.py` entra a `main` (recomendado: sí, es útil para Israel y para revisar la UI sin backend) o queda local.
- [ ] Decidir si se abre un PR único de la rama `UI` o se parte por fase (el plan §3 sugiere un PR pequeño por fase).
- [ ] Los `.md` de `docs/` (este handoff y la cabecera de `plan-implementacion-ui.md`) **no** se suben con la rama `UI`: se dejan locales y se llevan a la rama `docs` (ver sección 8).

---

## 4. Trabajo de la Fase 5 (integración) · a cargo de Israel

**Depende de** el backend de `plan-implementacion-ui.md` §4 (login manual del Portal 3, captcha con decisión del médico, estados granulares, lote y reproceso persistidos, progreso, PDF `NOMBRE_CEDULA.pdf`, WAL en SQLite). Sin eso la UI solo funciona con los fakes. Israel decide quién y en qué rama hace el backend.

### 4.1 Cablear el shell de producción (`shell/main_window.py` y `main.py`)

Hoy `MainWindow` registra tres páginas vacías (`_pagina_vacia`) y `bootstrap.ejecutar()` solo muestra esa ventana. Falta enchufar las pantallas reales siguiendo la máquina de estados de la spec §7. El patrón ya está probado en `scripts/demo_ui.py`:

- **Arranque:** mostrar `LoginView` **sin riel** (`SIN_SESION`). Al autenticar, llamar `TopBar.establecer_sesion(usuario, iniciales)` y pasar al shell.
- **Destino `LOTE`:** un `QStackedWidget` interno con Carga (02), Revisión (03), Procesando (05, con panel 08 embebido) y Resumen (09). La transición la manda la máquina de estados, no el usuario.
- **Destinos `ERRORES` y `AJUSTES`:** siempre disponibles desde `SIN_LOTE`. Historial sigue deshabilitado.
- **Riel:** `boton_errores.establecer_contador(n)` con `IErrorListQuery.errores_pendientes()` al arrancar y tras cada `batch_ended`.
- **Barra superior:** `establecer_sin_lote()` o `establecer_lote(texto, chip, tono)` con tonos válidos `proceso` (`EN_CURSO`), `alerta` (`DETENIDO`), `exito` (`FINALIZADO`), `neutro`.
- **Composición en `main.py`:** instanciar los adaptadores reales y **inyectarlos** en los presenters. La UI nunca importa Playwright, SQLite ni Pandas (DIP).

Conexiones señal → presenter que hoy nadie hace fuera del demo:

| Origen (señal) | Destino |
|---|---|
| `LoginView.intento_ingreso` | `LoginPresenter.intentar_ingresar` (su callback recibe `SesionUsuario`) |
| `UploadView.archivo_elegido(str)` | `UploadPresenter.archivo_elegido` |
| `ReviewView.lote_descartado` / `campana_iniciada` | `ReviewPresenter.descartar_lote` / `iniciar_campana` |
| `ProcessingView.paciente_seleccionado(str)` | `PatientDetailPresenter.mostrar` |
| `ProcessingView.entregables_solicitados` y `SummaryView.entregables_solicitados` | abrir `DeliverablesDialog(resumen, IOutputFolderSettings.obtener())` |
| `DeliverablesDialog.generar_solicitado(SeleccionEntregables)` | `DeliverablesPresenter.exportar` (en `TaskThread`); su resultado vuelve a `DeliverablesDialog.mostrar_resultado` y el error a `mostrar_error` |
| `CaptchaDialog.decision_tomada(DecisionOperador)` | `BatchRunnerThread.resolver_operador` |
| `Portal3LoginDialog.boton_cancelar` (reject) | `resolver_operador(DecisionOperador.CANCELAR_LOGIN)` |
| `BatchStoppedDialog` (aceptar) | `ocultar_lote_detenido` |
| `ErrorsView.reproceso_solicitado(tuple[str, ...])` | `IReprocessExecutionFactory.ejecucion_de_reproceso(ids)` → `ESPERANDO_LOGIN` |
| `PatientDetailPanel.reproceso_solicitado(str)` | igual que la anterior con un solo id, solo si `DetallePaciente.reprocesable` |
| `SettingsView.carpeta_elegida(Path)` | `SettingsPresenter.cambiar_carpeta` |
| `Rail.destino_elegido(str)` | `Navigation.mostrar(Destino(...))` (ya cableado en `MainWindow`) |

### 4.2 Hilos (`app/infrastructure/ui/workers/`, archivos nuevos según spec §10)

- `batch_runner_thread.py`: `BatchRunnerThread(QThread)` implementa `IProgressReporter` e `IOperatorGate`. Señales `patient_updated`, `log_line`, `batch_progress`, `operator_action_requested`, `operator_action_closed`, `batch_ended` (todas `pyqtSignal(object)`) y `batch_failed` (`pyqtSignal(str)`, solo el nombre del tipo de error). `resolver_operador(decision)` activa un `threading.Event`. `sync_playwright()` se crea **dentro de `run()`**; nunca se pasa una `Page` entre hilos. Detalle en spec §5 (contrato de `IOperatorGate`) y §6.
- `task_thread.py`: `TaskThread(QThread)` corre una tarea única y emite `succeeded(object)` o `failed(str)`. Se usa para `IBatchIntake.leer_listado` y `IDeliverablesExporter.exportar`. Hoy `UploadPresenter` llama a `leer_listado` en el hilo principal (válido solo con el fake): pasarlo a `TaskThread`.
- **Presenter de procesamiento:** `ProcessingPresenter` hoy solo carga estado fijo. Debe convertirse en el `QObject` (hilo principal) que recibe las señales del hilo, acumula `patient_updated` en un diccionario por `paciente_id` y lo vuelca a `BatchTableModel.apply_updates` con un `QTimer` de 150 ms (coalescencia), y llama a `actualizar_progreso`, `mostrar_solicitud_*`, `ocultar_solicitud_*` y `mostrar_lote_detenido` según las señales.
- **Cierre de ventana:** `MainWindow.closeEvent` en `EN_CURSO` abre `CloseConfirmationDialog` (ya construido, con `boton_cancelar` y `boton_confirmar`). Confirmar → `requestInterruption()` + `wait()` → `DETENIDO`; cancelar → `event.ignore()`. Hoy **no existe** ese `closeEvent`.

### 4.3 Adaptadores reales de los puertos de `ui_ports.py`

Implementarlos en `app/infrastructure/` **sin importarse entre sí** (AGENTS §1). Correspondencia con lo ya mergeado en plan §3 (tabla de la Fase 0b). Puertos sin fake en `tests/ui/fakes/ports.py` porque requieren hilos reales: `IBatchExecution`, `IBatchExecutionFactory`, `IReprocessExecutionFactory`, `IProgressReporter`, `ICurrentBatchQuery`. Israel puede añadir fakes en memoria para probar el hilo sin Playwright (recomendado).

### 4.4 Ajustes de contrato conocidos

- **Ya resuelto en la UI (2026-09-23).** `IProcessingView.mostrar_solicitud_login_portal3(es_reproceso: bool = False)` pasa el flag al `Portal3LoginDialog`; en reproceso omite "Solo lo harás una vez" y la nota de campaña automática. Para el modo en vivo, `IProcessingView` y `ProcessingView` exponen `aplicar_actualizaciones(filas)` (delega en `BatchTableModel.apply_updates`) y `agregar_linea_bitacora(LineaBitacora)` (formato `HH:MM:SS Portal N · mensaje`). El presenter de Isra solo tiene que llamarlas; `ErrorsView.mostrar_errores(())` ya muestra el estado vacío "No hay errores pendientes".
- **Confirmación tras exportar (spec §13.2, hecho en la UI).** `DeliverablesDialog` ya no se cierra al generar: pasa a "Generando…" y espera. Isra debe conectar el resultado de `DeliverablesPresenter` (callback `al_exportar`) a `dialogo.mostrar_resultado(ResultadoEntregables)` y el `failed(str)` de `TaskThread` a `dialogo.mostrar_error(str)`. "Abrir carpeta" usa `QDesktopServices` dentro del diálogo (acción de SO, sin puerto). Los contadores del Excel limpio y del auditado usan `cabecera.total_filas` (§13.3).
- **`ProcessingView.establecer_cabecera`** habilita "Generar entregables" solo en `DETENIDO` y `FINALIZADO`. El presenter debe volver a llamarlo con cada cambio de estado del lote.

---

## 5. Fase 6 · Verificación y empaquetado

- Comparar `widget.grab()` contra los PNG de `docs/UI/stitch/v2/` y probar a 100, 125, 150 y 175 % de DPI. El PNG `13_hoja_componentes` **nunca se generó** (propuesta §7); las etiquetas "QDialog" de Stitch en los mocks 04, 06, 07 y 10 no se implementan.
- `scripts/contrast_check.py` y `check_ui_rules.py` a `scripts/` y como pasos del CI (plan §5). Quitar el disparador temporal `ci/**` del workflow.
- Empaquetado con PyInstaller en modo `onedir`. Los binarios de Chromium de Playwright van aparte y se prueban en un equipo limpio.

---

## 6. Deuda conocida y decisiones abiertas

| Tema | Detalle |
|---|---|
| Fixture del lote incompleto | Cerrado el 2026-09-23 (spec §13.1): 308 de 428, con 120 pendientes. |
| `shell_lote.png` | Cerrado el 2026-09-24: el botón Lote del riel medía 44 px en vez de 64 por su política de tamaño horizontal `Fixed`. Corregido en la rama `UI` (commit `b7dd012`) con tests en `tests/ui/test_rail.py`. |
| Pulido visual | Las pantallas son fieles a los mocks pero sin acabado final. Aceptado para el MVP. |
| Cierre de la spec §12 | Abiertas y sin bloquear: banner de la pantalla 11 (omitido), definición del KPI "Inválidos" (`CEDULA_INVALIDA` + `NO_ENCONTRADO`), bitácora solo en memoria, `EXPORTADO_DUAL` no expuesto, sin roles. Cerradas el 2026-09-23 (spec §13): "Ver pacientes" se omite en el MVP y la confirmación de entregables es el paso 2 del diálogo 10. |
| Botón "Cambiar…" de Ajustes y de entregables | Abren el selector nativo de carpetas; no están cubiertos por tests (un diálogo nativo bloquea en modo offscreen). |
| Pipfile | Sigue pidiendo Python 3.14; el acordado es 3.12 (cambio aparte). |

---

## 7. Cómo verificar cada entrega (bucle de calidad)

```
python -m mypy --ignore-missing-imports app/infrastructure/ui tests/ui
python -m ruff check app/infrastructure/ui tests/ui
python .claude/skills/pyqt6-desktop-ui-hexagonal/scripts/check_ui_rules.py
set QT_QPA_PLATFORM=offscreen && python -m pytest tests/ui tests/architecture -q
python scripts/demo_ui.py
```

Las capturas de los tests se escriben en `tests/ui/_capturas/` (ignorado por git). Al revisarlas, **ampliar antes de dar algo por roto**: la vista previa pequeña pierde líneas finas y ha dado falsos positivos.

Trampas de Qt ya encontradas (no repetir):
1. `QHeaderView::section` con QSS necesita cerca de 1,8 veces el ancho que sugiere `QFontMetrics`: medir con un script aislado antes de fijar anchos de columna.
2. No consultar `geometry()` ni `sizeHint()` antes de que el layout corra; y no confiar en `isVisible()` de un widget hijo antes de mostrar toda la cadena de padres.
3. `QLabel` con `wordWrap` puede reservar una línea de menos si el ancho real es menor que el del hint: dar un ancho explícito o ampliar el contenedor.
4. El QSS no soporta `text-transform`: poner el texto en mayúsculas desde el código.

---

## 8. Flujo de ramas para este documento

Los documentos de `docs/` (features, arquitectura, planes, este handoff) viven en la rama `docs`, no en `UI`. Este archivo se creó con la rama `UI` activa pero **no se añadió a git**: queda local (sin trackear) hasta cambiar a `docs`, commitearlo allí y abrir su PR hacia `main`. Lo mismo aplica a cualquier edición de `docs/UI/*.md` hecha desde `UI` (por ejemplo, la cabecera de `plan-implementacion-ui.md`, que sigue diciendo "no existe código de la UI todavía").
