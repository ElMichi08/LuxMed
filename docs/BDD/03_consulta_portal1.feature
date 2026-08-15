# Fuente: Requisitos.MD — Feature "Consulta Portal 1 (siempre) — cobertura del paciente"
# Estado: validado con el propietario (v1.0)
#
# Resuelto (sesión BDD 2026-08-12): si el PDF #1 falla la verificación de integridad en su primera
# descarga (no al reanudar), se trata igual que un timeout — reintenta hasta 3 veces (cubierto por
# los escenarios "Timeout dispara reintentos acotados" / "Fallo persistente..." de abajo) y luego
# ERROR_PORTAL_1. Este archivo (Portal 1) queda validado con este criterio; el mismo criterio se
# propuso por analogía para Portal 3, pero ahí sigue pendiente de revisión — ver 06_consulta_portal3.feature.

Feature: Consulta Portal 1 (siempre) — cobertura del paciente

  Como sistema
  Quiero obtener la cobertura y el tipo de seguro del paciente
  Para decidir la rama de procesamiento y obtener el PDF #1

  Background:
    Given un paciente con estado "PENDIENTE" en el lote
    And el paciente tiene cédula válida y fecha de atención

  Scenario: Consulta exitosa devuelve cobertura y tipo de seguro
    When el sistema consulta el Portal 1 con la cédula del paciente y la fecha de atención
    Then el sistema descarga el PDF #1 de cobertura interceptando la respuesta original
    And el sistema verifica la integridad del PDF #1
    And el sistema registra el tipo de seguro y si el paciente es menor de edad

  Scenario: Paciente no encontrado corta el flujo
    When el sistema consulta el Portal 1 con la cédula del paciente y la fecha de atención
    And el Portal 1 responde "no encontrado"
    Then el sistema marca al paciente como "NO_ENCONTRADO"
    And no se consulta el Portal 2 ni el Portal 3 para ese paciente
    And el sistema continúa con el siguiente paciente

  Scenario: Timeout dispara reintentos acotados
    When el sistema consulta el Portal 1
    And la consulta produce timeout
    Then el sistema reintenta hasta 3 veces adicionales sobre el intento actual

  Scenario: Fallo persistente del Portal 1 tras reintentos
    Given el sistema agotó los 3 reintentos adicionales por timeout
    When la consulta sigue fallando
    Then el sistema marca al paciente como "ERROR_PORTAL_1"
    And el sistema continúa con el siguiente paciente
    # Un fallo persistente puede deberse a mantenimiento/caída del Portal 1.
