# GUI — Sistema de Validación Automatizada de Seguros Médicos

> **Estado:** diseño superficial, no cerrado al 100%. Sin wireframes todavía. Se retoma y ajusta cuando se instale la skill de la librería de web scraping (Playwright) en otra sesión.
> **Ver también:** `docs/arquitectura.md` para cómo esta capa se conecta con la orquestación.

## Por qué hay GUI

El Apéndice A de stack (ver `CLAUDE.md`) menciona CLI (typer) como interfaz de referencia, pero el propietario confirmó que necesita una interfaz gráfica desde el inicio: el médico debe poder cargar el Excel, ver el progreso del lote y pausar/reanudar sin usar una terminal, y al final descargar los resultados. El CLI queda como opción secundaria de soporte/debug (ver `docs/arquitectura.md`), no como interfaz principal.

## Pantallas (nivel superficial, descritas por el propietario)

1. **Carga de datos**
   - Importar el Excel de pacientes al programa.
   - Corresponde a la Feature "Normalización previa del Excel" (`docs/BDD/01_normalizacion_excel.feature`): cédulas inválidas se filtran antes de iniciar el lote, con reporte de descartados (`CEDULA_INVALIDA`).

2. **Progreso**
   - Barra de avance, ej. `40/500`.
   - Botón para pausar la automatización.
   - Debe reflejar también la **pausa forzada por expiración de sesión del Portal 3** (Feature "Pausa y reanudación del lote") — no solo la pausa manual del médico, sino avisar que se necesita re-autenticar para continuar.
   - Debe reflejar el login asistido inicial: el sistema abre el navegador visible en la página de login del Portal 3 y esta pantalla debe comunicar que está esperando esa autenticación manual antes de arrancar el lote.

3. **Resumen**
   - Resultado consolidado del flujo al terminar (o al pausar) el lote.
   - Botones para descargar los procesos/PDFs generados por paciente.
   - Debe distinguir estados finales por paciente: `COMPLETADO`, `NO_ENCONTRADO`, `ERROR_PORTAL_1`, `ERROR_PORTAL_2` — coherente con la Feature "Definición de éxito por paciente".
   - Al reanudar un lote pausado, esta misma información (resumen de procesados/pendientes) se muestra antes de que el médico confirme continuar (Feature "Pausa y reanudación del lote").

## Conexión con la capa de aplicación

- La GUI **no contiene lógica de negocio**. Es un consumidor de `application/process_batch.py`, igual que lo sería un CLI.
- El orquestador corre en un **worker/thread separado** del hilo principal de la GUI, para no bloquear la ventana mientras Playwright trabaja (procesamiento serial, sin ráfagas concurrentes).
- El orquestador emite **eventos de dominio neutros** (`application/events.py`: `PatientStateChanged`, `BatchPaused`, `SessionExpired`, `BatchCompleted`). Una capa delgada de **viewmodel**, fuera del dominio, traduce esos eventos a lo que el framework de GUI elegido necesite (ej. señales, callbacks, bindings). Así el dominio no depende del framework de GUI, y si este cambia en el futuro, solo se reescribe esa capa fina.
- El botón "pausar" no interrumpe una consulta a medias: setea una señal que el orquestador revisa **entre pacientes**, alineado con el checkpoint por paciente.

## Pendiente / no decidido todavía

- **Framework de GUI concreto.** Se conversó PySide6 (Qt) como candidato natural para Windows, por su soporte maduro de threading (worker thread + señales) para este patrón de "tarea larga en background + barra de progreso + pausar" — pero no está decidido en firme.
- Wireframes o mockups reales de las 3 pantallas.
- Cómo se muestra en pantalla la coexistencia entre la ventana de la GUI y la ventana visible del navegador Playwright (el médico interactúa con ambas: login/captcha en el navegador, control del lote en la GUI).
- Detalle de qué información exacta lleva cada botón de descarga en la pantalla de resumen. El formato del entregable ya no está abierto a nivel de contenido — `docs/BDD/11_consolidacion_pdf_paciente.feature` define un único PDF combinado por paciente (no PDFs sueltos) y `docs/BDD/12_exportacion_excel_resultado.feature` define el Excel de resultados con columna "ESTADO" — lo que falta decidir es la mecánica de descarga en pantalla: ¿un botón por paciente, un zip del lote completo, o ambos?
- Manejo en pantalla de los dos ciclos de intervención humana de Portal 2 (`docs/BDD/05_consulta_portal2.feature`, @borrador): fallo de ALTCHA (pide resolver el captcha en la ventana del navegador) y PDF del titular corrupto (pide revisar el documento y escribir la cédula a mano). Son mecánicamente distintos entre sí y del diálogo simple de "continuar vs. pausar" — ambos se apoyan en el puerto `human_intervention` de `docs/arquitectura.md`, pero la GUI necesita una pantalla/diálogo por cada tipo, no una genérica.
