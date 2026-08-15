# Fuente: Requisitos.MD — Feature "Consulta Portal 3 (siempre, salvo corte) — atención médica"
# Estado: los 2 escenarios de consulta (Rama A / Rama B) están validados con el propietario (v1.0).
#
# PENDIENTE (sesión BDD 2026-08-12, sin cerrar): el resto de este archivo (timeout/reintento/fallo
# persistente, el corte por falta de cédula del titular) se agregó por analogía con Portal 1 y 2,
# pero el propietario todavía no revisó el comportamiento real del Portal 3 en detalle — y la
# experiencia con Portal 2 (05_consulta_portal2.feature) mostró que ese tipo de analogía puede
# quedar corta o directamente equivocada una vez que se explora el portal real (ej. Portal 2 resultó
# tener 3 desenlaces distintos, no uno). Tratar TODO este archivo, salvo los 2 primeros escenarios,
# como no confiable hasta que se revise el flujo de Portal 3 específicamente en otra sesión. Esto
# también deja pendiente, indirectamente, el mapeo de "Error Portal 3" en
# 12_exportacion_excel_resultado.feature y 13_resumen_numerico_lote.feature.

Feature: Consulta Portal 3 (siempre, salvo corte) — atención médica

  Como sistema
  Quiero descargar el PDF de atención médica
  Para completar el entregable del paciente

  Scenario: Rama A — consulta con la cédula del titular
    Given un paciente de "Rama A" con la cédula del titular obtenida del Portal 2
    And el médico tiene una sesión activa en el Portal 3
    When el sistema consulta la atención médica con la cédula del titular
    Then el sistema descarga el PDF #3 de atención
    And el sistema verifica la integridad del PDF #3

  Scenario: Rama B — consulta con la cédula del paciente
    Given un paciente de "Rama B"
    And el médico tiene una sesión activa en el Portal 3
    When el sistema consulta la atención médica con la cédula del paciente
    Then el sistema descarga el PDF #3 de atención
    And el sistema verifica la integridad del PDF #3

  @pendiente
  Scenario: Rama A sin cédula del titular — se omite el Portal 3
    Given un paciente de "Rama A" que terminó el Portal 2 sin obtener la cédula del titular
    When el sistema evalúa si corresponde consultar el Portal 3
    Then el Portal 3 se omite para ese paciente
    And el sistema continúa con el siguiente paciente

  @pendiente
  Scenario: Timeout dispara reintentos acotados
    Given un paciente con sesión activa en el Portal 3
    When el sistema consulta el Portal 3
    And la consulta produce timeout
    Then el sistema reintenta hasta 3 veces adicionales sobre el intento actual

  @pendiente
  Scenario: Fallo persistente del Portal 3 tras reintentos
    Given el sistema agotó los 3 reintentos adicionales por timeout en el Portal 3
    When la consulta sigue fallando
    Then el sistema marca al paciente como "ERROR_PORTAL_3"
    And el sistema continúa con el siguiente paciente
