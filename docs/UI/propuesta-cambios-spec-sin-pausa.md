# Propuesta de cambios a la spec derivados de la UI v2 (sin pausa)

> **Estado:** borrador para consolidar en la rama `docs` mediante una ronda SDD. No se modificó ningún `.feature` ni `business-rules.md` / `ARCHITECTURE.md`. La ronda SDD del 2026-09-21 (rama `UI`) resolvió las preguntas de §4, salvo la 5; cada resolución está marcada como **Resuelta** y sus efectos se reflejan en §1, §2, §3.1, §3.5–§3.7, §6 y §7.
> **Origen:** revisión del mock de Stitch en `docs/UI/stitch/v2/` (13 pantallas) y decisiones del producto del 2026-09-21.

---

## 1. Decisiones de producto que originan la propuesta

1. **No hay funcionalidad de pausa ni de reanudación.** No existe botón Pausar/Reanudar ni pantalla de reanudación.
2. **El login manual del Portal 3 se hace una sola vez**, como requisito previo a la ejecución del pipeline (al pulsar "Iniciar campaña"), nunca durante el procesamiento de los pacientes.
3. **Si la sesión del Portal 3 expira a mitad del lote, el lote se detiene** con un aviso. Los pacientes ya procesados se conservan; para continuar hay que iniciar un lote nuevo con el listado.
4. **No hay vista de Historial por ahora.** El ítem queda en el riel lateral, deshabilitado y sin funcionalidad.
5. **Ajustes solo expone la carpeta de salida.** Espera entre consultas, reintentos y tiempo máximo por portal dejan de ser configurables por el usuario.
6. **Errores se mantiene** como pantalla propia: lista los pacientes en `ERROR_PORTAL_1/2/3` y permite reintentarlos sin volver a consultar los portales ya resueltos.
7. **Cerrar la ventana con un lote `EN_CURSO` detiene el lote, previa confirmación.** No hay botón "Detener lote" ni "Cancelar lote" en la barra superior. El lote queda `DETENIDO` conservando lo ya procesado (§3.1).
8. **Los errores y el checkpoint persisten entre sesiones.** Al abrir la aplicación, la pantalla Errores y su badge reflejan el último lote, aunque no haya lote activo (§3.6).

---

## 2. Impacto por documento

| Documento | Sección o escenario | Situación actual | Propuesta |
|---|---|---|---|
| `BDD/08_pausa_reanudacion_lote.feature` | Feature completa | Pausa manual, pausa forzada por expiración de sesión, reanudación con confirmación | **Reemplazar** por una feature de "Detención del lote por expiración de sesión del Portal 3" (ver §3.1). Retirar los escenarios de pausa manual y de reanudación |
| `business-rules.md` | §6, viñetas "Pausa Manual o Forzada" y "Reanudación con Confirmación" | Describen pausa y estado reanudable | **Eliminar** y sustituir por la regla de detención del lote (§3.1) |
| `business-rules.md` | §6, viñeta "Idempotencia de PDFs al Reanudar" | Idempotencia al reanudar un lote pausado | **Reformular** para el reproceso desde Errores (§3.3). El checkpoint por paciente sigue siendo necesario |
| `business-rules.md` | §7, "Resumen Numérico del Lote" | "…excluyendo el tiempo que el lote estuvo en pausa" | Quitar la exclusión: la duración es `hora de fin − hora de inicio` |
| `business-rules.md` | §4 (máquina de estados) | Solo estados de paciente | Documentar los estados de **lote**: `SIN_INICIAR`, `EN_CURSO`, `FINALIZADO`, `DETENIDO` (los usa la UI como chip de estado) |
| `business-rules.md` | §4, estado `HIGIENIZADO` y transición prohibida `INGESTADO → EN_PROCESO` | Usa `HIGIENIZADO` | **Renombrar** a `PENDIENTE`, nombre que ya usan `01_normalizacion_excel.feature`, `ARCHITECTURE.md` §5.2 y la UI (§4, pregunta 6) |
| `business-rules.md` | §2, alerta visual `es_auditoria_rojo` | Rojo para todo estado final distinto de `COMPLETADO` | Aclarar que en un lote `DETENIDO` los pacientes `PENDIENTE` también van en rojo (§3.1) |
| `business-rules.md` | §7, "Resumen Numérico del Lote", desglose por rama | Desglose por Rama A / Rama B | Aclarar que los estados sin rama muestran "—" en ambas columnas y que el total de la fila los incluye (§3.7) |
| `business-rules.md` | §5, viñeta ALTCHA | "el sistema pausa el navegador visible…" | Solo aclarar el verbo: aquí "pausa" es esperar al médico, no pausar el lote |
| `business-rules.md` | §8 (changelog) | v1.3.0 | Nueva entrada v1.4.0 con estos cambios |
| `BDD/02_arranque_autenticacion_portal3.feature` | Cabecera y escenario "Login manual único al inicio del lote" | Remite a 08 para la re-autenticación; "el sistema pausa y espera…" | Quitar la referencia a 08 y el verbo "pausa" (usar "espera"); añadir escenario de cancelación del login (§3.2) |
| `BDD/09_idempotencia_pdfs.feature` | Feature "…al reanudar" | Escenarios de PDF íntegro/corrupto "al reanudar" | Renombrar a "Idempotencia de PDFs al reprocesar" y cambiar "reanuda" por "reprocesa" (§3.3) |
| `BDD/11_consolidacion_pdf_paciente.feature` | Escenario "Reanudación antes de armar el combinado" y comentario de cabecera | Habla de lote pausado o cortado | Reformular para "lote detenido o reproceso desde Errores"; la lógica del checkpoint no cambia |
| `BDD/12_exportacion_excel_resultado.feature` | Generación de entregables | Solo tras el cierre del lote | Permitir generar los entregables de un lote `DETENIDO` y pintar en rojo a los `PENDIENTE` (§3.1, §3.5) |
| `BDD/13_resumen_numerico_lote.feature` | Comentario de cabecera y escenario "Duración del lote" | "duración de tiempo activo… excluyendo pausa" | Duración total sin exclusión; desglose por rama solo en columnas Rama A y Rama B (§3.7). Indicar "lote incompleto" en un lote `DETENIDO` (§3.5) |
| `BDD/14_reproceso_errores.feature` (nueva) | — | — | Feature nueva con §3.3 y el escenario de persistencia de errores entre sesiones (§3.6) |
| `ARCHITECTURE.md` | §7, párrafo del Portal 3 | Remite a `08_pausa_reanudacion_lote.feature` para la re-autenticación | Cambiar la referencia a la nueva feature de detención del lote |
| `ARCHITECTURE.md` / `AGENTS.md` | §3 y §4 (señales UI ↔ hilo) | `pyqtSignal(str)` como ejemplo de señal | Indicar que las señales transportan DTOs inmutables con `pyqtSignal(object)` y que el camino UI → hilo usa un puerto `OperatorGate` (§6) |
| `BDD/10`, `BDD/03`, `BDD/04`, `BDD/05`, `BDD/06`, `BDD/07`, `BDD/01` | — | — | Sin cambios de comportamiento. Solo revisar comentarios que mencionen 08 |

---

## 3. Escenarios propuestos

### 3.1 Reemplazo de `08`: detención del lote por sesión expirada

```gherkin
Feature: Detención del lote por expiración de sesión del Portal 3

  Como médico
  Quiero que el sistema se detenga con un aviso claro si mi sesión del Portal 3 expira
  Para no generar errores en cadena y saber exactamente qué quedó procesado

  Scenario: La sesión expira a mitad del lote
    Given un lote en curso con la sesión del Portal 3 establecida
    When la sesión del Portal 3 expira
    Then el sistema detiene el lote
    And el lote queda en estado "DETENIDO"
    And el sistema informa cuántos pacientes ya se procesaron y cuántos quedaron pendientes

  Scenario: Los pacientes ya procesados se conservan
    Given un lote "DETENIDO" por expiración de sesión
    Then los pacientes ya procesados conservan su estado final y sus PDFs consolidados
    And el sistema no reanuda el lote

  Scenario: Continuar exige un lote nuevo
    Given un lote "DETENIDO"
    When el médico desea procesar a los pacientes pendientes
    Then debe iniciar un lote nuevo con el listado

  Scenario: Los pacientes sin procesar quedan como Pendiente
    Given un lote "DETENIDO"
    Then los pacientes que no se procesaron, incluido el que estaba en proceso, permanecen en estado "PENDIENTE"
    And en el Excel Auditado sus filas se pintan en rojo

  Scenario: El médico cierra la aplicación con un lote en curso
    Given un lote en estado "EN_CURSO"
    When el médico cierra la ventana
    Then el sistema pide confirmar que cerrar detiene el lote
    And si el médico confirma, el lote queda en estado "DETENIDO" y conserva lo ya procesado
    And si el médico no confirma, el lote continúa sin interrupción
```

### 3.2 Añadido a `02`: cancelación del login previo

```gherkin
  Scenario: El médico cancela el login previo al lote
    Given el sistema espera que el médico inicie sesión en el Portal 3
    When el médico cancela
    Then no se inicia el procesamiento de ningún paciente
    And el lote permanece en estado "SIN_INICIAR" en la revisión previa
```

### 3.3 Reproceso desde Errores (nueva feature, p. ej. `14_reproceso_errores.feature`)

```gherkin
Feature: Reproceso de pacientes con error

  Como médico
  Quiero reintentar solo a los pacientes que terminaron en error de portal
  Para completar el lote sin repetir consultas ya resueltas

  Scenario: Reintentar pacientes seleccionados
    Given pacientes en estado "ERROR_PORTAL_1", "ERROR_PORTAL_2" o "ERROR_PORTAL_3"
    When el médico selecciona pacientes en la pantalla de Errores y pulsa "Reintentar seleccionados"
    Then el sistema pide iniciar sesión en el Portal 3 una vez, antes de comenzar
    And procesa solo a los seleccionados, en serie y con el throttling habitual
    And no vuelve a consultar los portales ya resueltos según el registro de fases del checkpoint

  Scenario: PDF previo íntegro se conserva al reprocesar
    Given un paciente con un PDF descargado en una corrida anterior
    When el sistema reprocesa al paciente y verifica ese PDF
    And el PDF está íntegro
    Then omite su descarga y continúa con las fases pendientes

  Scenario: PDF previo corrupto se vuelve a descargar al reprocesar
    Given un paciente con un PDF descargado en una corrida anterior
    When el sistema reprocesa al paciente y verifica ese PDF
    And el PDF está corrupto o incompleto
    Then vuelve a descargar ese PDF
```

### 3.4 Carpeta de salida (nueva o dentro de `11`/`12`)

```gherkin
  Scenario: Los entregables se guardan en la carpeta de salida configurada
    Given una carpeta de salida definida en Ajustes
    When el sistema genera los entregables del lote
    Then el Excel Limpio, el Excel Auditado y los PDFs consolidados se guardan bajo esa carpeta
    And los PDFs se guardan en la subcarpeta del mes de la fecha de atención
```

### 3.5 Entregables de un lote detenido (`12`, `13`)

```gherkin
  Scenario: Generar entregables de un lote detenido
    Given un lote en estado "DETENIDO"
    When el médico pulsa "Generar entregables"
    Then el sistema genera el Excel Limpio, el Excel Auditado y los PDFs consolidados de los pacientes completados
    And el resumen indica que el lote quedó incompleto con el número de pacientes procesados sobre el total
```

### 3.6 Persistencia de errores entre sesiones (`14`)

```gherkin
  Scenario: Los errores sobreviven al cierre de la aplicación
    Given un lote con pacientes en "ERROR_PORTAL_1", "ERROR_PORTAL_2" o "ERROR_PORTAL_3"
    When el médico cierra la aplicación y la vuelve a abrir
    Then la pantalla de Errores lista a esos pacientes
    And el médico puede reintentarlos sin volver a cargar el listado
```

### 3.7 Desglose por rama en el resumen (`13`)

```gherkin
  Scenario: Estados sin rama en el desglose
    Given un lote finalizado
    When el sistema muestra el resumen numérico
    Then cada estado muestra su total y su desglose en Rama A y Rama B
    And los estados que terminan antes de conocer la rama muestran "—" en ambas columnas
    And el total de cada fila incluye a todos los pacientes en ese estado
```

---

## 4. Preguntas de la ronda SDD y su resolución

1. **Estado de los pacientes pendientes en un lote `DETENIDO`.** No tienen estado final. ¿Se muestran como "Pendiente" en el resumen? ¿Se pintan de rojo en el Excel Auditado (hoy solo se pinta lo distinto de `COMPLETADO`)? Propuesta: sí, se consideran "no completados".
   **Resuelta (2026-09-21):** se muestran como "Pendiente" y van en rojo en el Excel Auditado. Incluye al paciente que estaba `EN_PROCESO` al detenerse el lote (§3.1).
2. **¿Se pueden generar entregables de un lote `DETENIDO`?** La UI v2 deshabilita "Generar entregables" hasta el cierre. Propuesta: permitirlo, con el resumen indicando que el lote quedó incompleto.
   **Resuelta (2026-09-21):** sí se permite; el resumen indica "lote incompleto" con los procesados sobre el total (§3.5). Cambia los mocks 07 y 10 (§7).
3. **Desglose por rama en el resumen (`13`).** Los estados que terminan antes de conocer la cobertura (`CEDULA_INVALIDA`, `NO_ENCONTRADO`, y `ERROR_PORTAL_1` en la primera consulta) no tienen rama. La UI v2 añade una columna "Sin rama". Confirmar que esa es la interpretación correcta del requisito "desglosado por Rama A / Rama B".
   **Resuelta (2026-09-21), distinta de la propuesta:** solo columnas Rama A y Rama B, sin "Sin rama". Los estados sin rama muestran "—" y el total de la fila los incluye, por lo que A + B no suma el total (§3.7). Cambia el mock 09 (§7).
4. **Reproceso y login.** La UI v2 asume que reintentar desde Errores exige iniciar sesión otra vez en el Portal 3 antes de empezar. Confirmar.
   **Resuelta (2026-09-21):** sí, siempre, antes de empezar. Se reutiliza el diálogo del mock 04 con el texto adaptado (§3.3, §7).
5. **Parámetros ya no configurables** (espera entre consultas con variación, 3 reintentos, tiempo máximo por portal): ¿quedan como constantes del sistema documentadas en `business-rules.md` §5/§6? Propuesta: sí, con los valores actuales.
   **Abierta.** No afecta a la UI; se resuelve en la ronda de la rama `docs`.
6. **Estado `PENDIENTE` vs `HIGIENIZADO`.** `01_normalizacion_excel.feature` usa `PENDIENTE` y `business-rules.md` §4 usa `HIGIENIZADO` para el mismo momento del ciclo de vida; la UI muestra "Pendiente". Unificar el nombre.
   **Resuelta (2026-09-21):** `PENDIENTE` en todo el sistema. Se renombra `HIGIENIZADO` en `business-rules.md` §4 y en la transición prohibida `INGESTADO → EN_PROCESO` (§2).
7. **Historial.** Sin vista por ahora. Confirmar si el lote se sigue persistiendo en SQLite (necesario para Errores y para futuras versiones) y si algún requisito lo cubre.
   **Resuelta (2026-09-21):** sí. El checkpoint y los pacientes en `ERROR_PORTAL_N` se guardan en `luxmed.db` y se restauran al abrir la aplicación; el badge de Errores es visible sin lote activo, como en los mocks 02 y 12 (§3.6).
8. **Cierre de la ventana con un lote `EN_CURSO`.** Sin pausa ni cancelar, ¿qué ocurre? Opciones evaluadas: confirmar y detener el lote, botón "Detener lote", o bloquear el cierre.
   **Resuelta (2026-09-21):** se pide confirmación y, si se acepta, el lote queda `DETENIDO` conservando lo procesado. No se añade ningún botón (§3.1, §7).
9. **Tabla canónica del lote.** Los mocks 05, 06 y 07 tienen columnas distintas.
   **Resuelta (2026-09-21):** la del mock 05, sin checkbox: Paciente, Cédula, Edad, Rama, Seguro derivado, Ruta (P1·P2·P3), Estado y Hora. Aplica a todos los estados del lote (§7).

---

## 5. Notas de trazabilidad

- El mock v2 usa los nombres **IESS**, **Entidad Previsional Especial** y los portales por rol, conforme al ADR 003.
- La cédula se valida solo por longitud de 10 dígitos numéricos, sin dígito verificador.
- Cifras de ejemplo del mock: 428 filas = 94 `CEDULA_INVALIDA` + 334 consultados (311 `COMPLETADO`, 19 `NO_ENCONTRADO`, 4 `ERROR_PORTAL_3`); 117 filas en rojo; duración 08:32–11:47 = 3 h 15 min.

---

## 6. Decisiones de arquitectura de la UI (rama `UI`, ronda SDD 2026-09-21)

No cambian ningún `.feature`. Afectan a `ARCHITECTURE.md`, `AGENTS.md` y a la implementación de la capa visual.

1. **Ubicación.** La UI vive en `app/infrastructure/ui/` con subcarpetas (`theme/`, `shell/`, `screens/`, `dialogs/`, `widgets/`, `models/`, `presenters/`, `workers/`). Se conservan `login_view.py`, `upload_view.py`, `processing_view.py` y `main_window.py`. `main.py` queda en la raíz como raíz de composición.
2. **Contrato de señales.** Los eventos del hilo del scraper a la UI son DTOs inmutables (`dataclass(frozen=True, slots=True)`) definidos en `domain`, sin dependencia de Qt, y se emiten con `pyqtSignal(object)`. `AGENTS.md` §4 cita `pyqtSignal(str)` como ejemplo; se interpreta así y se anotará en ese documento. Tipos de evento previstos: actualización de paciente, línea de bitácora y progreso del lote.
3. **Camino UI → hilo.** Un puerto `OperatorGate` en `domain` más un `threading.Event`. El hilo emite una señal de acción del operador y espera; la UI abre el diálogo y responde con la decisión. Cubre: cancelar el login del Portal 3 y reintentar o marcar como error el captcha del Portal 2. El "Entendido" del lote detenido solo cierra el diálogo, porque el hilo ya terminó. Nunca se abre un modal desde el hilo.
4. **Hilo.** Subclase de `QThread` con `run()`, como pide `AGENTS.md`. Playwright se crea dentro del hilo mediante una fábrica de sesión inyectada. El cierre usa `requestInterruption()` y `wait()`, nunca `terminate()`.
5. **Dependencias autorizadas.**
   - Fuentes embebidas: Archivo, Archivo Narrow e IBM Plex Mono (licencia OFL).
   - Iconos SVG propios tomados de Material Symbols. `qtawesome` no se adopta.
   - `pytest-qt` solo como dependencia de desarrollo.
   - Se permite añadir iconos y fuentes siempre que no afecten a los módulos productivos.
6. **Versión de Qt.** El `Pipfile` fija `pyqt6-qt6==6.7.2`; no se usan APIs de Qt 6.8 o posteriores.
7. **Skill de apoyo.** Un skill local del proyecto, `pyqt6-desktop-ui-hexagonal`, en `.claude/skills/` (fuera de git). No modifica el repositorio `pyqt6-ui-designer`.

---

## 7. Cambios pendientes en los mocks de Stitch v2

Los mocks se implementan como widgets nativos de PyQt6; estos ajustes son la referencia visual corregida, aunque no se regeneren en Stitch.

| Mock | Cambio |
|---|---|
| `07_lote_detenido` | Habilitar "Generar entregables". Usar la tabla canónica del mock 05 (sin checkbox ni "Seguro en Excel"). Cambiar el chip "Inválido" por `CEDULA_INVALIDA`. |
| `06_captcha_portal2` | Usar la tabla canónica del mock 05 como fondo. |
| `09_resumen_lote` | Quitar la columna "Sin rama". Mostrar "—" en Rama A y Rama B para los estados sin rama y añadir una nota de que el total incluye a todos los pacientes. |
| `10_generar_entregables` | Cambiar "Duración activa" por "Duración". En un lote `DETENIDO`, indicar "lote incompleto" con los procesados sobre el total. |
| `04_login_portal3` | Adaptar el texto para el reproceso: quitar "Solo lo harás una vez" y "La campaña comenzará automáticamente". |
| Nuevo | Diálogo de confirmación al cerrar la ventana con un lote `EN_CURSO`. |
| `01_login` y riel | Unificar la versión: el login muestra `1.0.0` y el riel `v2.4`. |
| `13_hoja_componentes` | Falta generarla. Las etiquetas "QDialog" de Stitch en los diálogos 04, 06, 07 y 10 no se implementan. |
