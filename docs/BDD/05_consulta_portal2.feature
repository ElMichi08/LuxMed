# Fuente: business-rules.md §1/§2/§5 (glosario "Seguro Derivado", regla de derivación, ALTCHA).
# Estado: CONFIRMADO con el propietario en sesión SDD 2026-09-10 (segunda ronda, a partir de una
# revisión de código del equipo) y promovido a business-rules.md v1.2.0 — reemplaza el modelo
# anterior de este archivo, que asumía que el Portal 2 generaba un PDF del titular.
#
# Modelo real confirmado: el Portal 2 **no genera ningún documento**. Solo devuelve un dato:
#   - Si identifica a un titular que le deriva la cobertura al paciente → `seguro_derivado = True`,
#     se guardan los datos de ese titular, y el sistema vuelve a consultar el PORTAL 1 (no el
#     Portal 2) con la cédula del titular para obtener su PDF de cobertura — ver
#     06_consulta_portal3.feature y business-rules.md §7 para el resto de esa ruta.
#   - Si no identifica ningún titular → `seguro_derivado = False`. Esto NO es un rechazo: el
#     paciente es su propio titular y continúa directo al Portal 3 sin ningún documento adicional
#     de esta fase (reemplaza a los antiguos escenarios "SIN_COBERTURA_PORTAL_2" y
#     "PDF_CORRUPTO_PORTAL_2", que trataban erróneamente este resultado — y la corrupción de un PDF
#     que en realidad no emite el Portal 2 — como estados de fallo/rechazo).
# El único motivo de error real en el Portal 2 es el fallo persistente del widget ALTCHA al enviar
# el formulario — no hay ningún PDF de Portal 2 que pueda "salir corrupto".

Feature: Consulta Portal 2 (solo Rama A) — determinación de seguro derivado

  Como sistema
  Quiero saber si existe un titular distinto que le derive la cobertura al paciente
  Para decidir si debo volver a consultar el Portal 1 por esa persona, o continuar directo al Portal 3

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
    # Este es el único motivo de error posible en el Portal 2: no genera documentos que puedan fallar de otra forma.

  Scenario: El Portal 2 identifica un titular — seguro derivado
    Given el formulario del Portal 2 fue enviado con la verificación completada
    When el Portal 2 responde identificando a un titular que le deriva la cobertura al paciente
    Then el sistema fija "paciente.seguro_derivado" en verdadero
    And guarda los datos del titular (incluyendo su cédula) para volver a consultar el Portal 1
    And no se descarga ningún documento en esta fase

  Scenario: El Portal 2 no identifica ningún titular — seguro propio
    Given el formulario del Portal 2 fue enviado con la verificación completada
    When el Portal 2 no identifica a ningún titular para el paciente
    Then el sistema fija "paciente.seguro_derivado" en falso
    And el paciente continúa directo al Portal 3 con su propia cédula
    And este resultado no se trata como un error ni como un rechazo del paciente
