# Arquitectura — Sistema de Validación Automatizada de Seguros Médicos

> **Estado:** base de trabajo, no cerrada al 100%. Se retoma y ajusta cuando se instale la skill de la librería de web scraping (Playwright) en otra sesión.
> **Fuente:** decisiones conversadas originalmente a partir de `Requisitos.MD` v1.0 (eliminado del repositorio — su comportamiento quedó cubierto y superado por `docs/BDD/`, su Preámbulo/Apéndice A están duplicados en `CLAUDE.md`, su Apéndice B legal en `docs/legal.md`), **actualizadas** (sesión de arquitectura 2026-08-14) contra `docs/BDD/*.feature`, que es la fuente de verdad vigente del comportamiento (sesión BDD 2026-08-12: consolidación de PDFs, exportación a Excel, resumen numérico, y un modelo más preciso de fallos del Portal 2).
> Varios escenarios de `docs/BDD/` siguen etiquetados `@borrador` o `@pendiente` (sin confirmación explícita del propietario, o extrapolados por analogía — el caso más notorio es Portal 3, ver `docs/BDD/06_consulta_portal3.feature`). Este documento asume esas formas como plausibles para diseñar las capas, pero **no** las trata como cerradas; no construir el adapter de Portal 3 ni fijar `ERROR_PORTAL_3` en el dominio hasta que se confirmen con el propietario.

## Decisión

**Monolito de despliegue + arquitectura interna hexagonal (puertos y adaptadores).**

La unidad de despliegue no está en discusión: un solo `.exe` en la máquina del médico, sin servidor central (invariante #1, ver `CLAUDE.md`) — no hay motivo para microservicios. La organización interna del código dentro de ese proceso sí es una decisión de diseño independiente; el porqué de hexagonal está a continuación, y una revisión posterior de esa justificación contra `docs/BDD/` está al final de este documento.

## Por qué hexagonal, y no "porque el flujo no cambia"

El argumento a favor de capas **no es** que el flujo de negocio vaya a cambiar (no va a cambiar: Portal 1 → Portal 2 condicional → Portal 3 es estable y así se documentó). El argumento real es otro:

> Los *adapters* de scraping sí van a cambiar, porque son páginas web de terceros (Portal 1, 2, 3) que pueden modificar su HTML/JS, su captcha, o su flujo sin aviso.

Si la lógica de negocio (clasificación Rama A/B, máquina de estados del paciente, criterio de éxito, reintentos) está mezclada con el código Playwright de cada portal, cualquier cambio de un portal obliga a tocar y re-testear reglas de negocio que no cambiaron. Aislar "cómo hablo con el Portal 2" detrás de una interfaz estable evita ese arrastre. Eso es bajo acoplamiento / alta cohesión aplicado al problema concreto, no ceremonia arquitectónica gratuita.

Esto se reforzó al confirmar que habrá **GUI desde el día uno** y que el mantenimiento será de un **equipo pequeño con posible traspaso**: la GUI es un tercer consumidor de la lógica de orquestación (además de tests, y opcionalmente un CLI de soporte), y un desarrollador que se incorpore necesita poder entender los límites del sistema sin leer todo el código de una sentada.

## Capas propuestas

```
domain/            Reglas de negocio puras. Sin Playwright, sin pandas, sin GUI.
  models.py          Patient, Batch, PdfArtifact, Rama
  estados.py           EstadoPaciente (enum) y EstadoLote (enum) — DOS enums separados, no uno.
                          EstadoPaciente: lista autoritativa = la tabla de mapeo de
                          docs/BDD/12_exportacion_excel_resultado.feature — COMPLETADO,
                          NO_ENCONTRADO, SIN_COBERTURA_PORTAL_2, CEDULA_INVALIDA, ERROR_PORTAL_1,
                          ERROR_PORTAL_2, PDF_CORRUPTO_PORTAL_2, ERROR_PORTAL_3 (este último aún
                          @pendiente, ver docs/BDD/06_consulta_portal3.feature).
                          EstadoLote: PENDIENTE, EN_PROCESO, PAUSADO, COMPLETADO — estado del lote,
                          no del paciente (docs/BDD/12_... aclara que PAUSADO nunca aplica a un
                          paciente individual).
  state_machine.py    Transiciones válidas de EstadoPaciente
  branch_rules.py      Clasificación Rama A / Rama B
  success_criteria.py   "COMPLETADO" según Rama (2 vs 3 PDFs) — también decide cuándo las fases
                          requeridas por la rama ya están completas para armar el PDF combinado
                          (ver docs/BDD/11_consolidacion_pdf_paciente.feature)
  reporte.py             estado_a_texto_excel(EstadoPaciente) -> str — mapeo puro y determinista
                          hacia la columna "ESTADO" del Excel de resultados (docs/BDD/12_...).
                          Vive en domain, no en el writer de infraestructura, para poder testearse
                          sin openpyxl. El agrupamiento "Error Portal 2" (que junta ERROR_PORTAL_2
                          y PDF_CORRUPTO_PORTAL_2) es una decisión de reporte, no de dominio: el
                          state_machine sigue distinguiendo ambos estados internamente.

application/         Casos de uso / orquestación. Depende de domain + ports, no de infra concreta.
  process_batch.py     Orquestador del lote: recorre pacientes, throttling, checkpoints, pausa/reanuda,
                          registra intervalos de pausa (para "tiempo activo" del resumen numérico)
  process_patient.py    Orquestación por paciente: Portal1 → decide rama → Portal2? → Portal3 →
                          combinar PDFs si las fases requeridas están completas
  generar_resumen_lote.py  Arma el Excel de resultados (docs/BDD/12_...) y el resumen numérico de
                              GUI (docs/BDD/13_...) a partir del checkpoint, una vez el lote termina
  events.py              Eventos de dominio: PatientStateChanged, BatchPaused, SessionExpired,
                            BatchCompleted, HumanInterventionRequested, HumanInterventionResolved
  ports/                  Interfaces (Protocol/ABC) — el contrato que infra debe cumplir
    portal_gateway.py       Portal1Gateway, Portal2Gateway, Portal3Gateway
    pdf_verifier.py
    pdf_merger.py             Combina PDFs verificados en el PDF único por paciente
    checkpoint_repository.py   Ver contrato detallado abajo — registra fases completadas, no
                                  presencia de archivos
    excel_source.py            Lectura del Excel original (normalización pre-flujo)
    excel_report_writer.py      Escritura del Excel de resultados (columna ESTADO) — puerto
                                    simétrico a excel_source, en sentido inverso
    human_intervention.py       Ver contrato detallado abajo — pausa el worker y pide una
                                    decisión/dato al médico vía GUI o CLI

infrastructure/       Adapters concretos — detalle técnico reemplazable
  playwright/
    portal1_adapter.py    Intercepción de respuesta + descarga PDF #1
    portal2_adapter.py     Espera ALTCHA, envío de formulario, descarga PDF #2. Reintentos
                              automáticos de ALTCHA (3) y de descarga/lectura del PDF (3) viven
                              aquí; agotados esos reintentos, delega en ports/human_intervention.py
                              en vez de decidir por su cuenta.
    portal3_adapter.py      Login asistido, sesión en memoria no persistente, PDF #3 — NO
                              implementar en firme hasta explorar el portal real (ver nota de
                              cabecera de este documento)
    browser_session.py       Wrapper de contexto de navegador (visible, no persistente)
  pdf/
    pikepdf_verifier.py       Verificación de integridad + extracción determinista
    pikepdf_merger.py          Combina PDF #1/#2/#3 verificados en un único PDF, orden Portal
                                  1→2→3; borra los individuales tras combinar con éxito
  excel/
    pandas_excel_source.py     Normalización y filtrado de cédulas (lectura)
    openpyxl_report_writer.py    Excel original + columna "ESTADO" (escritura, docs/BDD/12_...)
  persistence/
    sqlite_checkpoint_repository.py  Fases completadas por paciente + intervalos de pausa del lote
                                        (ver contrato abajo)
  throttling/
    rate_limiter.py               Intervalo con jitter, sin ráfagas concurrentes — mecanismo
                                      distinto del backoff de reintentos de cada adapter (ver
                                      "Decisiones ya tomadas")

interface/
  gui/                  Ver docs/gui.md — implementa human_intervention.py con un diálogo modal
  cli/                    Opcional — CLI delgado de soporte/debug (typer); implementa
                            human_intervention.py con un prompt de terminal

main.py                 Composition root: instancia adapters concretos e inyecta en el orquestador
```

### Contrato de `checkpoint_repository.py` (revisado)

Antes: "verificar si el PDF ya existe en disco y es válido" era suficiente para decidir qué re-descargar. Ya no lo es — `docs/BDD/11_consolidacion_pdf_paciente.feature` combina los PDFs individuales en uno solo y **borra los originales**, así que su ausencia en disco ya no significa "falta descargarlo". El contrato correcto:

- Por paciente, el repositorio guarda **qué fases se completaron** (`portal1_ok`, `portal2_ok`, `portal3_ok`, `combinado_ok`), no la presencia de archivos.
- Al reanudar, `process_patient.py` consulta las fases, no el filesystem, para saber qué falta. Si una fase está marcada pero el archivo individual ya no existe porque se combinó, eso es el comportamiento esperado, no una inconsistencia.
- El PDF combinado solo se arma cuando las fases requeridas por la Rama del paciente (via `success_criteria.py`) ya están todas en `_ok`.
- A nivel de lote, el repositorio también guarda los intervalos de pausa/reanudación (timestamps), necesarios para calcular "tiempo activo" en el resumen numérico (docs/BDD/13_...) sin contar el tiempo pausado.
- Convención de nombre del PDF combinado: `{cedula}_{fecha_atencion:%Y%m%d}.pdf` — resuelto como decisión de ingeniería (ver `docs/BDD/11_...`); cédula + fecha de atención es el mismo par que ya identifica de forma única cada fila del Excel de entrada, evita colisión si un paciente aparece en más de un lote o fecha.

### Contrato de `human_intervention.py` (nuevo)

`docs/BDD/05_consulta_portal2.feature` muestra que "agotar reintentos automáticos → bloquear el worker → pedir algo al médico → reanudar" no es un caso especial de Portal 2, es un patrón que ya se repite dos veces ahí mismo (fallo de ALTCHA tras 3 intentos automáticos; PDF del titular ilegible tras 3 reintentos) con formas de intervención distintas (resolver un captcha en el navegador vs. escribir una cédula a mano). Portal 3, cuando se explore, probablemente necesite lo mismo. Por eso es un puerto genérico de `application`, no lógica ad-hoc dentro de `process_patient.py`:

- El adapter de infraestructura (ej. `portal2_adapter.py`) agota sus reintentos internos y, si sigue fallando, invoca el puerto con un objeto que describe qué se necesita (tipo de intervención, contexto del paciente, opciones de decisión válidas).
- El puerto bloquea el worker thread hasta recibir una respuesta — implica una señal thread-safe (ej. `threading.Event` + cola de respuesta) entre el worker y el hilo de la GUI, disparada por un evento de dominio (`HumanInterventionRequested` / `HumanInterventionResolved`).
- La GUI implementa este puerto con un diálogo modal; el CLI de soporte, con un prompt de terminal. Ninguno de los dos mete lógica de negocio — solo recogen la decisión y se la devuelven al puerto.
- Este mecanismo de bloqueo cross-thread es una pieza de diseño que falta detallar en `docs/gui.md` — está señalado ahí como pendiente pero no resuelto.

**Regla de dependencia:** las flechas de import solo apuntan hacia adentro. `domain` no importa nada de `infrastructure` ni `interface`. `application` conoce `domain` y los `ports` (interfaces), nunca una clase concreta de Playwright/GUI. `infrastructure` e `interface` son los únicos lugares que conocen librerías externas concretas.

## Decisiones ya tomadas (sujetas a revisar con la skill de Playwright)

1. **Un gateway por portal, no un `PortalClient` genérico.** Cada portal tiene semántica distinta (Portal 1: interceptación de respuesta; Portal 2: sincronización con ALTCHA; Portal 3: sesión persistente en memoria reutilizada). Forzarlos a una interfaz común solo generaría parámetros opcionales e ifs internos.
2. **Máquina de estados explícita en `domain/state_machine.py`, con `EstadoPaciente` y `EstadoLote` como enums separados.** La lista de `EstadoPaciente` vigente es la de `domain/estados.py` arriba (anclada en la tabla de mapeo de `docs/BDD/12_...`), no la lista original de este documento — quedó corta frente a los desenlaces reales de Portal 2 (`SIN_COBERTURA_PORTAL_2`, `PDF_CORRUPTO_PORTAL_2`) y al `ERROR_PORTAL_3` (aún @pendiente). `PAUSADO` se saca de `EstadoPaciente`: es un valor de `EstadoLote`, nunca de un paciente individual.
3. **Orquestador desacoplado de la interfaz.** `process_batch` no sabe si lo llama la GUI o un CLI de soporte.
4. **Comunicación orquestador → interfaz vía eventos de dominio**, no acoplados a un framework de GUI específico. La traducción evento→UI vive en una capa delgada fuera del dominio (ver `docs/gui.md`).
5. **Playwright en modo síncrono**, no asíncrono, ejecutado dentro de un worker/thread dedicado. El requisito de "sin ráfagas concurrentes" y procesamiento serial hace innecesaria la complejidad de asyncio conviviendo con el loop de la GUI.
6. **Pausa entre pacientes, no a mitad de una consulta.** Coherente con "guarda el progreso por paciente (checkpoint)" — evita estados intermedios corruptos.
7. **SQLite vía capa fina (Repository pattern), sin ORM pesado.** El esquema ya no es tan simple como se pensó — ver el contrato revisado de `checkpoint_repository.py` arriba (fases por paciente + intervalos de pausa del lote) — pero sigue sin justificar un ORM para este volumen y equipo.
8. **Throttling centralizado en el orquestador**, no repetido en cada adapter de portal — la regla de ritmo aplica al lote en general, no portal por portal. Es un mecanismo **distinto** del backoff de reintentos dentro de cada adapter (los 3 reintentos de timeout de Portal 1, los 3 intentos de ALTCHA de Portal 2, etc.): el rate limiter espacía consultas entre pacientes; el backoff de reintentos evita ráfagas *dentro* del ciclo de fallo de una sola consulta. No deben compartir el mismo objeto ni la misma configuración sin pensarlo.
9. **La intervención humana es un puerto genérico (`human_intervention.py`), no un caso especial de Portal 2.** Ver contrato detallado arriba — motivado por que el patrón ya se repite dos veces solo en Portal 2 (ALTCHA, PDF corrupto) y es candidato a repetirse en Portal 3.
10. **El mapeo estado interno → texto de reporte vive en `domain/reporte.py`, no en el adapter de Excel.** Es una regla determinista y testeable sin I/O; el agrupamiento "Error Portal 2" es una decisión de presentación, no colapsa los estados internos distintos que sí importan para la máquina de estados.

## Estrategia de pruebas (relevante por el posible traspaso)

- **Unit tests de `domain` y `application`** usando *fakes* de los `ports` (sin browser real) — rápidos, cubren máquina de estados, clasificación de rama, criterio de éxito, reintentos.
- **Tests de contrato/integración de adapters** contra los portales reales — separados, más lentos, se corren manualmente, respetando el throttling (no golpear portales reales en cada commit).
- Documentar los `ports/*.py` como el contrato de referencia para quien se incorpore — es la superficie que un desarrollador nuevo necesita entender primero.

## Revisión de la justificación (2026-08-15)

Sesión aparte, con este documento y `docs/BDD/` ya estables: se revisó si "hexagonal" seguía justificado frente al comportamiento real documentado, o si era ceremonia de más para un ejecutable on-premise de un solo médico.

**Veredicto: sí se justifica**, por dos motivos reales — no por "el flujo no va a cambiar" (ya descartado como argumento arriba):

1. **Heterogeneidad genuina entre los 3 portales.** Portal 1 usa interceptación de respuesta; Portal 2 tiene ALTCHA con proof-of-work y **3 desenlaces de negocio distintos** (cobertura vigente, `SIN_COBERTURA_PORTAL_2`, PDF corrupto) más **2 ciclos de reintento + intervención humana independientes**; Portal 3 reutiliza una sesión persistente en memoria. "Un gateway por portal" evita forzar esto a un `PortalClient` genérico con parámetros opcionales e ifs internos.
2. **Lógica de negocio no trivial e independiente del scraping**, que vale la pena testear con fakes: clasificación Rama A/B, máquina de estados de 8 valores, criterio de éxito por rama, checkpoint por fase completada (no por archivo en disco, por la consolidación que borra los PDFs individuales — `docs/BDD/09_idempotencia_pdfs.feature` + `11_consolidacion_pdf_paciente.feature`), e intervalos de pausa para "tiempo activo". A esto se suma que el patrón "agotar reintentos → bloquear worker → pedir decisión al médico → reanudar" ya se repite dos veces solo dentro de Portal 2 (ALTCHA, PDF corrupto) antes de tocar Portal 3 — con el spec mostrando la repetición dos veces, `human_intervention.py` como puerto genérico no es abstracción prematura.

**Matices — no todo el diseño pesa igual:**

- Sólidos: `portal_gateway.py`, `human_intervention.py`, `checkpoint_repository.py` — volatilidad externa real o repetición de patrón confirmada por el spec.
- Justificados por testabilidad, no por volatilidad: `pdf_verifier.py`, `pdf_merger.py` — pikepdf no cambia como un portal de terceros, pero aislarlo permite testear la orquestación de consolidación sin I/O real.
- El más discutible: `excel_source.py` / `excel_report_writer.py` — una sola implementación esperada, sin volatilidad tipo "portal que cambia sin aviso". Se sostiene solo por testabilidad de `process_batch`, no por aislar cambio externo impredecible. Si algún día la capa de puertos pesa más de lo que aporta, es el primer candidato a recortar — no `portal_gateway.py`.

Esto no cambia ninguna decisión de las listadas arriba; confirma que se sostienen frente al comportamiento real documentado en `docs/BDD/`, y señala dónde el argumento es más débil si en el futuro se quisiera simplificar.

## Pendiente / no decidido todavía

- Framework de GUI concreto y su integración con el worker de orquestación — ver `docs/gui.md`.
- **Mecanismo concreto de bloqueo cross-thread para `human_intervention.py`** (worker esperando una respuesta que solo puede dar el hilo de la GUI, sin congelar la ventana) — la necesidad ya está confirmada por el spec, falta el diseño técnico.
- Empaquetado final para distribución on-premise en Windows. Riesgo concreto a resolver, no solo "candidato no confirmado": PyInstaller no empaqueta de forma transparente los binarios de Chromium de Playwright dentro del `.exe` — probablemente se necesite distribuir la carpeta de navegadores aparte (o `playwright install` post-instalación) y fijar `PLAYWRIGHT_BROWSERS_PATH`. Si el propietario espera literalmente un único archivo `.exe` sin nada al lado, hay que alinear esa expectativa antes de llegar al empaquetado.
- **Portal 3: todo su comportamiento de fallo (timeout, reintentos, `ERROR_PORTAL_3`, el corte cuando Rama A no obtuvo cédula del titular) es una extrapolación por analogía sin confirmar** — `docs/BDD/06_consulta_portal3.feature` lo marca explícitamente como no confiable, y la experiencia con Portal 2 mostró que esa analogía ya falló una vez (Portal 2 resultó tener 3 desenlaces, no 1). No implementar `portal3_adapter.py` en firme ni cerrar `ERROR_PORTAL_3` en `domain/estados.py` hasta explorar el portal real.
- Detalle exacto de cada `portal*_adapter.py` (selectores, timing de ALTCHA, manejo de sesión) — depende de explorar los portales reales con Playwright.
- Estrategia exacta de tests de integración contra portales reales (entorno de staging vs. producción, cuándo correrlos).
- **Confirmación explícita del propietario sobre el mapeo estado→texto de Excel**, en particular que "Error Portal 2" agrupe `ERROR_PORTAL_2` y `PDF_CORRUPTO_PORTAL_2` — propuesto por inferencia en `docs/BDD/12_exportacion_excel_resultado.feature`, no confirmado. Es una decisión de negocio/reporte, no de arquitectura: cualquiera de las dos respuestas cabe sin cambios en `domain/reporte.py`.
- **Confirmación explícita del propietario sobre el ciclo completo de Portal 2** (`05_consulta_portal2.feature`, 5 escenarios `@borrador`): forma exacta del ciclo ALTCHA (3 intentos automáticos + intervención humana + decisión del médico de reintentar o marcar error) y del ciclo de PDF corrupto del titular. No estructural — el puerto `human_intervention` ya está diseñado para absorber cualquier variante razonable de este ciclo — pero si el comportamiento real del portal resulta distinto en su *forma* (como pasó al pasar de "un solo fallo genérico" a "3 desenlaces"), sí puede obligar a revisar el contrato del puerto.
- **Confirmación de que Rama A sin cédula del titular omite Portal 3** — asunción documentada en `docs/BDD/06_...` y ya reflejada en la orquestación (`process_patient.py`), pero sin validar explícitamente por el propietario tras introducir los 3 estados nuevos de Portal 2.
