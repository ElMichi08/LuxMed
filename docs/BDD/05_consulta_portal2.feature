# Fuente: Requisitos.MD — Feature "Consulta Portal 2 (solo Rama A) — titular del seguro"
# Estado: validado con el propietario. Los 2 primeros escenarios (espera ALTCHA, consulta
# exitosa) ya estaban validados en v1.0; el resto fue reescrito en sesión BDD 2026-08-12 a
# partir de un modelo más preciso del comportamiento real del Portal 2 — reemplaza al escenario
# original "No se puede extraer la cédula del titular" de Requisitos.MD v1.0 — y confirmado
# explícitamente por el propietario el 2026-08-15:
#
#   - El Portal 2 tiene 3 desenlaces posibles, no uno solo genérico de "extracción fallida":
#     1) Responde con un PDF válido del titular (caso normal).
#     2) Responde "SIN COBERTURA" directamente en el HTML, sin generar ningún PDF.
#     3) Responde con un PDF, pero el PDF está corrupto/no se puede leer — esto solo lo puede
#        juzgar el médico viendo el documento, no un chequeo automático.
#   - El fallo de ALTCHA (no pasar la prueba de trabajo) y el fallo de lectura del PDF son
#     problemas de naturaleza distinta (automatización de navegador vs. dato ilegible) y cada
#     uno tiene su propio ciclo de reintento + intervención humana.
#   - "Headless = false" (navegador visible) todo el tiempo es el modo normal de operación, no
#     algo exclusivo de la intervención humana — coherente con el Apéndice A de stack (ver
#     CLAUDE.md).
#
# Punto abierto (todavía sin confirmación explícita, fuera del alcance de este cierre): en
# todos los casos donde el paciente termina sin cédula del titular (ERROR_PORTAL_2,
# SIN_COBERTURA_PORTAL_2, PDF_CORRUPTO_PORTAL_2), se asume que el Portal 3 se omite para ese
# paciente — ver el escenario @pendiente correspondiente en 06_consulta_portal3.feature. Depende
# de que se confirme el comportamiento real de Portal 3, no se puede cerrar por conversación.

Feature: Consulta Portal 2 (solo Rama A) — titular del seguro

  Como sistema
  Quiero obtener la cédula del titular que extendió la cobertura
  Para poder consultar la atención en el Portal 3 con el identificador correcto

  Background:
    Given un paciente clasificado en "Rama A"

  Scenario: El sistema espera la verificación del captcha ALTCHA antes de enviar
    Given el formulario del Portal 2 está cargado con cédula del paciente, fecha de atención y motivo "Enfermedad"
    When el widget ALTCHA ejecuta su prueba de trabajo (proof-of-work)
    Then el sistema espera a que la verificación se complete antes de enviar el formulario
    # Sincronización con el widget legítimo del portal, no evasión del control.

  Scenario: Fallo de ALTCHA — reintentos automáticos y luego intervención humana
    Given el formulario del Portal 2 está cargado con cédula del paciente, fecha de atención y motivo "Enfermedad"
    When el widget ALTCHA no logra completar la verificación tras 3 intentos automáticos vía Playwright
    Then el sistema pausa el navegador visible y le pide al médico resolver el ALTCHA manualmente
    And al resolverse manualmente, el sistema retoma el envío del formulario de forma automática

  Scenario: Fallo persistente de ALTCHA tras intervención humana — decide el médico
    Given la intervención humana en el ALTCHA tampoco logró completar la verificación
    When el sistema consulta al médico cómo proceder
    Then si el médico elige reintentar, se repite el ciclo completo (3 intentos automáticos + 1 con intervención humana)
    And si el médico elige marcar como error, el paciente se marca "ERROR_PORTAL_2" y el sistema continúa con el siguiente paciente

  Scenario: Consulta exitosa entrega el PDF del titular
    Given el formulario del Portal 2 fue enviado con la verificación completada
    When el Portal 2 responde con cobertura vigente del titular
    Then el sistema descarga el PDF #2 del titular del seguro
    And el sistema verifica la integridad del PDF #2

  Scenario: El Portal 2 responde "SIN COBERTURA" — no hay PDF que descargar
    Given el formulario del Portal 2 fue enviado con la verificación completada
    When el Portal 2 responde "SIN COBERTURA" directamente en el HTML de la página, sin generar ningún PDF
    Then el sistema marca al paciente como "SIN_COBERTURA_PORTAL_2"
    And no se descarga ningún PDF #2
    # En el Excel de resultados este estado se traduce como "Desactualizado" — ver 12_exportacion_excel_resultado.feature.

  Scenario: Extracción exitosa de la cédula del titular
    Given el PDF #2 fue descargado y verificado
    When el sistema extrae localmente los datos del titular
    Then obtiene la cédula del titular para usarla en el Portal 3
    # Extracción local determinista (sin LLM). El Portal 2 solo genera este PDF cuando sí hay
    # cobertura, así que el formato es consistente y la extracción no debería fallar por datos
    # ausentes — el único fallo esperable en este punto es que el archivo esté corrupto (ver abajo).

  Scenario: El PDF del titular está corrupto — reintento y luego intervención humana
    Given el PDF #2 fue descargado pero no se puede leer o falla su verificación de integridad
    When el sistema reintenta la descarga hasta 3 veces
    And el PDF sigue sin poder leerse
    Then el sistema pausa y le pide al médico revisar el documento en el navegador y escribir manualmente la cédula del titular en un campo de texto
    # Solo un humano puede juzgar si el PDF realmente está corrupto o no.

  Scenario: El médico tampoco puede resolver el PDF corrupto del titular
    Given el médico revisó el PDF del titular y no puede proporcionar su cédula
    When el médico marca el paciente como fallo
    Then el paciente se marca "PDF_CORRUPTO_PORTAL_2"
    And el sistema continúa con el siguiente paciente
