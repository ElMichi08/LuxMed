# Spec de contrato de la capa de UI (Fase 0)

> **Estado:** borrador para aprobación. No existe código de la UI todavía.
> **Rama:** `UI`. **Fecha:** 2026-09-21.
> **Fuentes:** `AGENTS.md`, `docs/ARCHITECTURE.md` (ADR 001–003), `docs/business-rules.md`, `docs/UI/propuesta-cambios-spec-sin-pausa.md` (decisiones de la ronda SDD) y las 12 pantallas de `docs/UI/stitch/v2/`.
> **Alcance:** define qué datos consume la UI, qué puertos usa, qué señales emite el hilo de procesamiento, cómo se navega entre pantallas y qué archivos se crean en cada fase. La aprobación de este documento autoriza la lista de archivos de la sección 10.

---

## 1. Reglas que gobiernan la UI

1. **La UI es un adaptador de infraestructura** (ADR 001). Vive en `app/infrastructure/ui/`. Solo ese paquete importa PyQt6. No importa Playwright, SQLite ni Pandas ni otro adaptador.
2. **`main.py`, en la raíz, es la raíz de composición.** Construye los adaptadores, los inyecta en los casos de uso y estos en los presenters.
3. **Hilos** (`AGENTS.md` §4). La UI corre solo en el hilo principal. Toda lectura con Pandas, escritura en SQLite o exportación de archivos se ejecuta en un hilo de trabajo. El bucle de procesamiento corre en una subclase de `QThread`.
4. **Señales.** Los eventos del hilo a la UI son DTOs inmutables definidos en `domain` y se emiten con `pyqtSignal(object)`. El camino UI → hilo usa el puerto `OperatorGate`.
5. **Código.** Tipado estático estricto, nombres descriptivos y cero comentarios (`AGENTS.md` §1).
6. **Estados y textos.** Solo los nombres de estado de `business-rules.md` §4 (con `PENDIENTE` en lugar de `HIGIENIZADO`) y los de lote de la propuesta §2. Sin nombres reales de entidades o portales (ADR 003): la UI dice "Portal 1", "Portal 2" y "Portal 3".
7. **Versión de Qt:** 6.7.2. No se usan APIs de 6.8 o posteriores.

---

## 2. Convención de nombres (a confirmar)

- Enums y DTOs de dominio en **español**, tomados del vocabulario de `business-rules.md` (`EstadoPaciente`, `seguro_derivado`, `es_auditoria_rojo`).
- Puertos y clases técnicas en **inglés**, por rol (`OperatorGate`, `ProgressReporter`).
- Los valores de los enums coinciden con los nombres del negocio (`COMPLETADO`, `ERROR_PORTAL_3`).

---

## 3. Vocabulario de dominio que consume la UI

```python
class EstadoPaciente(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CEDULA_INVALIDA = "CEDULA_INVALIDA"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    ERROR_PORTAL_1 = "ERROR_PORTAL_1"
    ERROR_PORTAL_2 = "ERROR_PORTAL_2"
    ERROR_PORTAL_3 = "ERROR_PORTAL_3"


class Rama(StrEnum):
    A = "A"
    B = "B"


class EstadoLote(StrEnum):
    SIN_INICIAR = "SIN_INICIAR"
    EN_CURSO = "EN_CURSO"
    FINALIZADO = "FINALIZADO"
    DETENIDO = "DETENIDO"


class Portal(IntEnum):
    P1 = 1
    P2 = 2
    P3 = 3


class EstadoPaso(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    RESUELTO = "RESUELTO"
    OMITIDO = "OMITIDO"
    FALLIDO = "FALLIDO"


class MotivoDetencion(StrEnum):
    SESION_EXPIRADA = "SESION_EXPIRADA"
    CIERRE_APLICACION = "CIERRE_APLICACION"


class AccionOperador(StrEnum):
    LOGIN_PORTAL_3 = "LOGIN_PORTAL_3"
    CAPTCHA_PORTAL_2 = "CAPTCHA_PORTAL_2"


class DecisionOperador(StrEnum):
    CANCELAR_LOGIN = "CANCELAR_LOGIN"
    REINTENTAR_CAPTCHA = "REINTENTAR_CAPTCHA"
    MARCAR_ERROR_PORTAL_2 = "MARCAR_ERROR_PORTAL_2"
```

`INGESTADO` y `EXPORTADO_DUAL` (business-rules §4) son estados internos que la UI no muestra.

**Representación de la ruta P1·P2·P3** (columna "Ruta" del mock 05):

| `EstadoPaso` | Símbolo en el mock |
|---|---|
| `PENDIENTE` | círculo vacío |
| `EN_CURSO` | círculo con el número del portal |
| `RESUELTO` | punto lleno verde |
| `OMITIDO` | círculo punteado (P2 en Rama B) |
| `FALLIDO` | cruz roja |

---

## 4. DTOs inmutables (en `domain`)

Todos son `@dataclass(frozen=True, slots=True)`.

```python
@dataclass(frozen=True, slots=True)
class RutaPortales:
    p1: EstadoPaso
    p2: EstadoPaso
    p3: EstadoPaso


@dataclass(frozen=True, slots=True)
class PacienteRef:
    paciente_id: str
    nombre: str
    cedula: str


@dataclass(frozen=True, slots=True)
class FilaPaciente:
    paciente_id: str
    nombre: str
    cedula: str
    edad: int
    rama: Rama | None
    seguro_derivado: bool | None
    ruta: RutaPortales
    estado: EstadoPaciente
    hora: datetime | None


@dataclass(frozen=True, slots=True)
class ContadoresLote:
    total: int
    completados: int
    invalidos: int
    en_proceso: int
    pendientes: int
    con_error: int


@dataclass(frozen=True, slots=True)
class LineaBitacora:
    hora: datetime
    portal: Portal | None
    mensaje: str


@dataclass(frozen=True, slots=True)
class ProgresoLote:
    procesados: int
    total: int
    portal_actual: Portal | None
    contadores: ContadoresLote


@dataclass(frozen=True, slots=True)
class SolicitudOperador:
    accion: AccionOperador
    paciente: PacienteRef | None


@dataclass(frozen=True, slots=True)
class CabeceraLote:
    lote_id: str
    archivo: str
    total_filas: int
    estado: EstadoLote


@dataclass(frozen=True, slots=True)
class ConteoEstado:
    estado: EstadoPaciente
    total: int
    rama_a: int | None
    rama_b: int | None


@dataclass(frozen=True, slots=True)
class ResumenLote:
    cabecera: CabeceraLote
    procesados: int
    pendientes: int
    conteos: tuple[ConteoEstado, ...]
    hora_inicio: datetime | None
    hora_fin: datetime | None
    duracion: timedelta | None
    filas_en_rojo: int
    expedientes_consolidados: int
    incompleto: bool


@dataclass(frozen=True, slots=True)
class ResultadoEjecucion:
    estado_lote: EstadoLote
    motivo_detencion: MotivoDetencion | None
    resumen: ResumenLote


@dataclass(frozen=True, slots=True)
class FilaRevision:
    fila_excel: int
    nombre: str
    cedula: str
    fecha_nacimiento: date
    edad: int
    seguro: str
    establecimiento: str
    motivo_descarte: str | None


@dataclass(frozen=True, slots=True)
class PreviewLote:
    cabecera: CabeceraLote
    listos: tuple[FilaRevision, ...]
    descartados: tuple[FilaRevision, ...]
    menores_de_edad_listos: int


@dataclass(frozen=True, slots=True)
class PasoRuta:
    portal: Portal
    etiqueta: str
    hora: datetime
    tamano_kb: int | None
    nota: str | None


@dataclass(frozen=True, slots=True)
class ExpedienteConsolidado:
    nombre_archivo: str
    documentos: int
    tamano_kb: int
    ruta: Path


@dataclass(frozen=True, slots=True)
class DetallePaciente:
    fila: FilaPaciente
    cedula_titular: str | None
    cobertura: str | None
    pasos: tuple[PasoRuta, ...]
    expediente: ExpedienteConsolidado | None
    reprocesable: bool


@dataclass(frozen=True, slots=True)
class FilaError:
    paciente_id: str
    nombre: str
    cedula: str
    portal_fallido: Portal
    motivo: str
    intentos: int
    intentos_maximos: int
    ultimo_intento: datetime
    estado: EstadoPaciente


@dataclass(frozen=True, slots=True)
class SesionUsuario:
    usuario: str
    iniciales: str


@dataclass(frozen=True, slots=True)
class SeleccionEntregables:
    excel_limpio: bool
    excel_auditado: bool
    expedientes: bool
    carpeta_destino: Path


@dataclass(frozen=True, slots=True)
class ResultadoEntregables:
    carpeta: Path
    filas_excel: int
    filas_en_rojo: int
    expedientes_generados: int
```

**Reglas de derivación**
- `ContadoresLote.invalidos` = `CEDULA_INVALIDA` + `NO_ENCONTRADO` (ARCHITECTURE §5 llama "INVÁLIDO" al paciente sin cobertura).
- `ContadoresLote.con_error` = `ERROR_PORTAL_1` + `ERROR_PORTAL_2` + `ERROR_PORTAL_3`.
- `ResumenLote.filas_en_rojo` = todo paciente distinto de `COMPLETADO`, incluidos los `PENDIENTE` de un lote `DETENIDO`.
- `ResumenLote.incompleto` es `True` solo si `cabecera.estado` es `DETENIDO`.
- `ConteoEstado.rama_a` y `rama_b` son `None` en los estados que terminan sin rama. El total de la fila los incluye siempre.
- Los DTOs no cargan PII más allá de la que se muestra al operador en pantalla. `LineaBitacora.mensaje` y los mensajes de error nunca incluyen cédulas ni nombres.

---

## 5. Puertos que consume la UI (en `domain/ports.py`)

Puertos delgados, uno por responsabilidad (ISP).

```python
class LocalAuthenticator(Protocol):
    def autenticar(self, usuario: str, contrasena: str) -> SesionUsuario | None: ...


class BatchIntake(Protocol):
    def leer_listado(self, ruta: Path) -> PreviewLote: ...


class ProgressReporter(Protocol):
    def paciente_actualizado(self, fila: FilaPaciente) -> None: ...
    def linea_bitacora(self, linea: LineaBitacora) -> None: ...
    def progreso_lote(self, progreso: ProgresoLote) -> None: ...


class OperatorGate(Protocol):
    def solicitar(self, solicitud: SolicitudOperador) -> None: ...
    def esperar(
        self,
        accion: AccionOperador,
        resuelto: Callable[[], bool],
    ) -> DecisionOperador | None: ...
    def cerrar(self, accion: AccionOperador) -> None: ...


class BatchExecution(Protocol):
    def ejecutar(
        self,
        progreso: ProgressReporter,
        compuerta: OperatorGate,
    ) -> ResultadoEjecucion: ...


class BatchExecutionFactory(Protocol):
    def ejecucion_de_lote(self, lote_id: str) -> BatchExecution: ...


class ReprocessExecutionFactory(Protocol):
    def ejecucion_de_reproceso(
        self,
        paciente_ids: tuple[str, ...],
    ) -> BatchExecution: ...


class CurrentBatchQuery(Protocol):
    def cabecera_actual(self) -> CabeceraLote | None: ...


class BatchSummaryQuery(Protocol):
    def resumen_actual(self) -> ResumenLote: ...


class PatientDetailQuery(Protocol):
    def detalle(self, paciente_id: str) -> DetallePaciente: ...


class ErrorListQuery(Protocol):
    def errores_pendientes(self) -> tuple[FilaError, ...]: ...


class DeliverablesExporter(Protocol):
    def exportar(self, seleccion: SeleccionEntregables) -> ResultadoEntregables: ...


class OutputFolderSettings(Protocol):
    def obtener(self) -> Path: ...
    def guardar(self, carpeta: Path) -> None: ...
```

**Contrato de `OperatorGate`**
- `solicitar` no bloquea: hace que la UI muestre el diálogo correspondiente.
- `esperar` bloquea el hilo de procesamiento hasta que ocurra una de tres cosas: la UI entrega una decisión, `resuelto()` devuelve `True` (el scraper detectó el login o el captcha resuelto) o se pidió la interrupción del hilo. En los dos últimos casos devuelve `None`.
- `cerrar` hace que la UI cierre el diálogo de esa acción.
- La implementación vive en `workers/batch_runner_thread.py` y usa un `threading.Event`. Nunca abre un modal desde el hilo.

**Acciones que no pasan por un puerto** (integración con el sistema operativo, solo en la UI): abrir un PDF, abrir la carpeta contenedora, copiar la cédula al portapapeles y elegir carpetas o archivos con diálogos nativos.

---

## 6. Señales del hilo de procesamiento

`BatchRunnerThread` (subclase de `QThread`) implementa `ProgressReporter` y `OperatorGate`. Todas las señales viajan del hilo secundario al hilo principal y llegan a un presenter (`QObject` creado en el hilo principal).

| Señal | Carga | Cuándo se emite |
|---|---|---|
| `patient_updated` | `FilaPaciente` | Cada cambio de estado o de paso de un paciente |
| `log_line` | `LineaBitacora` | Cada evento relevante (consulta iniciada o completada, reintento) |
| `batch_progress` | `ProgresoLote` | Tras cada paciente y en cada cambio de portal activo |
| `operator_action_requested` | `SolicitudOperador` | Al necesitar login del Portal 3 o captcha del Portal 2 |
| `operator_action_closed` | `AccionOperador` | Cuando el scraper resolvió la acción sin decisión de la UI |
| `batch_ended` | `ResultadoEjecucion` | Fin de la ejecución: `FINALIZADO`, `DETENIDO` o `SIN_INICIAR` (login cancelado) |
| `batch_failed` | `str` | Excepción no controlada: solo el nombre del tipo de error, sin mensaje ni PII |

Todas se declaran como `pyqtSignal(object)`, salvo `batch_failed`, que es `pyqtSignal(str)`.

**Camino inverso (UI → hilo)**
- `resolver_operador(decision: DecisionOperador)`: método público de `BatchRunnerThread` que activa el `Event`. Es lo único que la UI invoca sobre el hilo, además de `requestInterruption()`.
- Cerrar la ventana con un lote en curso: `requestInterruption()` y `wait()`. Nunca `terminate()`.

**Coalescencia.** El presenter acumula `patient_updated` en un diccionario por `paciente_id` y lo vuelca al modelo con un `QTimer` de 150 ms, para evitar repintados por cada evento.

**Hilos auxiliares.** `TaskThread` ejecuta una tarea única fuera del hilo principal y emite `succeeded(object)` o `failed(str)`. Se usa para `BatchIntake.leer_listado` y `DeliverablesExporter.exportar`.

---

## 7. Máquina de estados de la UI

| Estado de la UI | Pantalla | Entra por | Sale por |
|---|---|---|---|
| `SIN_SESION` | 01 Login | Arranque; no hay sesión de usuario | `LocalAuthenticator.autenticar` devuelve una sesión → `SIN_LOTE` |
| `SIN_LOTE` | 02 Carga | Sesión iniciada; "Descartar lote" | Soltar o elegir `.xlsx` → `LEYENDO` |
| `LEYENDO` | 02 Carga con estado de lectura | `BatchIntake.leer_listado` en un `TaskThread` | `succeeded` → `REVISION`; `failed` → `SIN_LOTE` con aviso |
| `REVISION` | 03 Revisión previa (`SIN_INICIAR`) | Vista previa lista | "Descartar lote" → `SIN_LOTE`; "Iniciar campaña" → `ESPERANDO_LOGIN` |
| `ESPERANDO_LOGIN` | 03 con diálogo 04 | `operator_action_requested` con `LOGIN_PORTAL_3` | "Cancelar" (decisión `CANCELAR_LOGIN`) → `REVISION`; `operator_action_closed` → `EN_CURSO` |
| `EN_CURSO` | 05 Lote en proceso (+ panel 08) | Login resuelto | `batch_ended` |
| `EN_CURSO` con captcha | 05 con diálogo 06 | `operator_action_requested` con `CAPTCHA_PORTAL_2` | "Reintentar" o "Marcar como error y continuar"; `operator_action_closed` |
| `DETENIDO` | 05 con chip "Detenido" y diálogo 07 | `batch_ended` con `DETENIDO` | "Entendido" cierra el diálogo. "Generar entregables" queda habilitado |
| `FINALIZADO` | 09 Resumen | `batch_ended` con `FINALIZADO` | "Generar entregables" abre el diálogo 10 |
| Cierre con lote | Diálogo de confirmación | `closeEvent` en `EN_CURSO` | Confirmar → `requestInterruption()` + `wait()` → `DETENIDO`; rechazar ignora el cierre |

**Elementos siempre disponibles (desde `SIN_LOTE`)**
- **Errores:** se puede abrir en cualquier momento. Su badge refleja `ErrorListQuery.errores_pendientes()` al arrancar y tras cada `batch_ended`.
- **Ajustes:** carpeta de salida (`OutputFolderSettings`).
- **Historial:** deshabilitado, sin acción.

**Reproceso** (pantalla 11): "Reintentar seleccionados" → `ESPERANDO_LOGIN` (diálogo 04 con texto adaptado) → `EN_CURSO` con la ejecución de `ReprocessExecutionFactory`. Al terminar vuelve a mostrar Errores actualizado.

**Habilitación de controles**
- "Iniciar campaña": solo en `REVISION`.
- "Generar entregables": solo en `DETENIDO` y `FINALIZADO`.
- "Reprocesar paciente" (panel 08): solo si `DetallePaciente.reprocesable`.
- Filtros y buscador de la tabla: siempre activos, sobre el proxy del modelo.

---

## 8. Datos por pantalla

| Pantalla | Datos que muestra | Fuente |
|---|---|---|
| 01 Login | Usuario, contraseña, error, versión | `LocalAuthenticator` |
| Cabecera (todas) | Archivo, lote, filas, chip de estado, usuario | `CurrentBatchQuery`, `SesionUsuario` |
| 02 Carga | Dropzone y texto de columnas leídas | Estático |
| 03 Revisión previa | Totales, aviso de menores, pestañas Listos y Descartados | `PreviewLote` |
| 04 Login Portal 3 | Estado de espera | `operator_action_requested` |
| 05 Lote en proceso | 6 KPI, tabla, bitácora, barra de estado | `patient_updated`, `batch_progress`, `log_line` |
| 06 Captcha Portal 2 | Paciente y mensaje | `SolicitudOperador` |
| 07 Lote detenido | Procesados conservados y pendientes | `ResultadoEjecucion.resumen` |
| 08 Detalle | Rama, seguro derivado, titular, cobertura, ruta ejecutada, expediente | `PatientDetailQuery` |
| 09 Resumen | Hora de inicio, hora de fin, duración, conteos por estado y rama, filas en rojo | `BatchSummaryQuery` |
| 10 Entregables | 3 opciones con conteos, carpeta de destino | `ResumenLote`, `OutputFolderSettings`, `DeliverablesExporter` |
| 11 Errores | Lista, motivo, intentos, selección | `ErrorListQuery` |
| 12 Ajustes | Carpeta de salida | `OutputFolderSettings` |

**Columnas de la tabla de lote (05, canónica):** Paciente, Cédula, Edad, Rama, Seguro derivado, Ruta (P1·P2·P3), Estado, Hora. Los pendientes muestran "—" en Hora.

**Color por estado de paciente**

| Estado | Chip |
|---|---|
| `COMPLETADO` | verde |
| `EN_PROCESO` | índigo |
| `PENDIENTE` | gris |
| `CEDULA_INVALIDA`, `NO_ENCONTRADO`, `ERROR_PORTAL_N` | rojo |

En el resumen 09, las filas con total 0 se atenúan en gris.

---

## 9. Tokens de diseño (entrada de la Fase 1)

Extraídos de `05_lote_en_proceso.html`. Todos viven en `theme/tokens.py`; ningún otro archivo contiene un hex.

| Token | Valor | Uso |
|---|---|---|
| `lienzo` | `#E6E6E2` | Fondo de la aplicación |
| `panel` | `#FAFAF8` | Tarjetas y paneles |
| `blanco` | `#FFFFFF` | Campos de entrada |
| `filete` | `#C9C9C3` | Bordes |
| `filete_suave` | `#DCDCD7` | Separadores y cabeceras de tabla |
| `tinta` | `#1A1A18` | Texto principal y botones primarios |
| `tinta_sec` | `#555550` | Texto secundario |
| `tinta_ter` | `#8E8E88` | Texto atenuado y elementos deshabilitados |
| `indigo` | `#4B3F72` | Selección, estado activo y `EN_PROCESO` |
| `indigo_suave` | `#EDEAF3` | Fondo de selección |
| `indigo_borde` | `#D5D0E3` | Borde de selección |
| `verde` | `#1F6B4A` | `COMPLETADO` |
| `verde_fondo` | `#E8F5E9` | Fondo del chip verde |
| `verde_borde` | `#C8E6C9` | Borde del chip verde |
| `rojo` | `#A3231D` | Errores e inválidos |
| `rojo_fondo` | `#FDEDEC` | Fondo del chip rojo |
| `rojo_borde` | `#F5C2C0` | Borde del chip rojo |

**Tipografía:** Archivo (cuerpo), Archivo Narrow (cabeceras de tabla y títulos compactos) e IBM Plex Mono (cédulas, horas, chips y cifras). Tamaños observados en el mock: 9, 10, 11, 12, 14, 16, 20 y 24 px; pesos 400, 500, 600 y 700; etiquetas en mayúsculas con tracking amplio. La escala tipográfica exacta se fija en la Fase 1 leyendo los HTML 05, 09 y 10.

**Geometría observada** (referencia de 1280 px de ancho): riel lateral de 64 px, filas de tabla de 40 px, bordes de 1 px, sin sombras y radios pequeños (a confirmar en la Fase 1). Grilla de 4 px.

**Contraste:** todo par texto y fondo se valida en la Fase 1 contra 4,5:1. El estado nunca se comunica solo por color: siempre hay texto (el chip) o símbolo (la ruta).

Medido con la paleta anterior (2026-09-21): todos los pares de texto superan 4,5:1 (mínimo 5,73:1, `verde` sobre `verde_fondo`), salvo `tinta_ter`, que da 3,15:1 sobre `panel` y 2,63:1 sobre `lienzo`. Por eso `tinta_ter` se reserva para elementos deshabilitados (Historial en el riel) y nunca para texto informativo sobre `lienzo`. Los subtítulos y notas atenuados usan `tinta_sec`.

---

## 10. Archivos por fase (a aprobar)

Todos bajo `app/infrastructure/ui/` salvo indicación. Los 4 archivos vacíos del scaffold se reubican: `login_view.py`, `upload_view.py` y `processing_view.py` pasan a `screens/`, y `main_window.py` a `shell/`.

**Fase 0b · Contratos** (`app/domain/`): completar `entities.py` (enums y DTOs de las secciones 3 y 4) y `ports.py` (Protocols de la sección 5), que hoy están vacíos. Ver pregunta 4.

**Fase 1 · Tema**
- `main.py` (raíz, composición mínima)
- `bootstrap.py`
- `theme/__init__.py`, `tokens.py`, `palette.py`, `stylesheet.py`, `luxmed.qss.tpl`, `fonts.py`, `icons.py`
- `assets/fonts/` (Archivo, Archivo Narrow, IBM Plex Mono) y `assets/icons/` (~20 SVG de Material Symbols)
- `tests/ui/test_tokens_contrast.py`

**Fase 2 · Shell**
- `shell/__init__.py`, `main_window.py`, `navigation.py`, `rail.py`, `top_bar.py`, `status_bar.py`, `log_panel.py`

**Fase 3 · Widgets**
- `widgets/__init__.py`, `card.py`, `status_chip.py`, `kpi_tile.py`, `dropzone.py`, `route_dots.py`, `empty_state.py`

**Fase 4 · Pantallas sobre un simulador**
- `screens/`: `login_view.py`, `upload_view.py`, `review_view.py`, `processing_view.py`, `patient_detail_panel.py`, `summary_view.py`, `errors_view.py`, `settings_view.py`
- `dialogs/`: `portal3_login_dialog.py`, `captcha_dialog.py`, `batch_stopped_dialog.py`, `deliverables_dialog.py`, `close_confirmation_dialog.py`
- `models/`: `batch_table_model.py`, `batch_filter_proxy.py`, `review_table_model.py`, `errors_table_model.py`, `status_chip_delegate.py`, `route_dots_delegate.py`
- `presenters/`: uno por pantalla, más `contracts.py` con el `Protocol` de cada vista
- `tests/ui/fakes/`: implementaciones en memoria de todos los puertos, con datos del mock (428 filas)

**Fase 5 · Integración**
- `workers/batch_runner_thread.py`, `workers/task_thread.py`
- Cableado real en `main.py`

**Fase 6 · Verificación**
- `tests/ui/` (modelos, presenters, hilo) y comparación de capturas contra los PNG de `docs/UI/stitch/v2/`
- Empaquetado con PyInstaller (`onedir`)

---

## 11. Criterios de aceptación de la Fase 0

1. Los tipos de las secciones 3 y 4 cubren todos los campos visibles en las 12 pantallas.
2. Ningún puerto de la sección 5 expone un tipo de Qt.
3. Ningún módulo fuera de `app/infrastructure/ui/` importa PyQt6.
4. Todo evento que cruza de hilo es un DTO congelado.
5. Cada transición de la sección 7 tiene un origen (señal, botón o cierre de ventana) y un destino definidos.

---

## 12. Preguntas abiertas

1. **Banner de la pantalla 11.** El mock muestra "El Portal 3 presentó intermitencia entre las 14:18 y las 14:31" y un chip "HTTP 504 Gateway Timeout". No hay dato de origen para eso. Propuesta: omitir el banner y mostrar solo el motivo por fila.
2. **KPI "Inválidos".** Propuesta: `CEDULA_INVALIDA` + `NO_ENCONTRADO` (sección 4). Las cifras del mock 05 no cuadran con esa regla y son ilustrativas.
3. **Lecturas desde el hilo principal.** `AGENTS.md` §4 prohíbe escribir en SQLite y leer con Pandas en el hilo principal, pero no menciona las lecturas de SQLite. Propuesta: permitir consultas de lectura acotadas (detalle, errores, cabecera) y ejecutar en `TaskThread` todo lo demás.
4. **Ubicación de los contratos.** Los enums, DTOs y puertos se definen en `app/domain/`, que también es territorio de la rama `domain`. Hay que coordinar para no chocar en el merge.
5. **Tabla tras `FINALIZADO`.** La pantalla 09 no permite volver a ver la tabla de pacientes. Propuesta: añadir un acceso "Ver pacientes" que abra la tabla en modo lectura.
6. **Estado de lectura del Excel.** El mock 02 no muestra qué ocurre mientras se lee el archivo. Propuesta: la dropzone muestra "Leyendo archivo…" y se deshabilita.
7. **Bitácora.** Propuesta: vive solo en memoria durante el lote y no se persiste.
8. **`EXPORTADO_DUAL`.** Propuesta: la UI no lo expone; tras generar entregables solo muestra confirmación.
9. **Roles (RBAC).** `ARCHITECTURE.md` §7 nombra RBAC básico sin definir roles. Propuesta: la UI no diferencia permisos; `SesionUsuario` solo lleva usuario e iniciales.
10. **Versión de Python.** `ARCHITECTURE.md` dice 3.11+, el `Pipfile` 3.14 y los `.pyc` son de 3.13. Falta fijar la versión objetivo.
11. **Convención de nombres** de la sección 2.
