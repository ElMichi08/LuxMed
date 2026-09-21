# Fuente: Requisitos.MD — Feature "Consulta Portal 3 (siempre, salvo corte) — atención médica"
# Estado: los escenarios de consulta (Rama A con y sin titular, Rama B) están validados con el
# propietario (v1.0 y sesión SDD 2026-09-10, segunda ronda).
#
# CONFIRMADO (sesión SDD 2026-09-10, primera ronda): el modelo genérico de timeout/reintento (hasta
# 3 reintentos adicionales) y fallo persistente → `ERROR_PORTAL_3` quedó promovido a
# business-rules.md §5 como regla general aplicable a cualquier portal, Portal 3 incluido. El mapeo
# de `ERROR_PORTAL_3` en 12_exportacion_excel_resultado.feature (color rojo uniforme) y en
# 13_resumen_numerico_lote.feature también quedó resuelto.
#
# CONFIRMADO (sesión SDD 2026-09-10, segunda ronda — corrección del modelo de Portal 2): con
# `seguro_derivado` (ver 05_consulta_portal2.feature), la vieja pregunta "¿qué pasa si Rama A
# termina sin cédula del titular?" se resuelve así: cuando `seguro_derivado = False` (no hay
# titular), el paciente SÍ continúa al Portal 3, pero con su PROPIA cédula — no se omite el Portal 3
# en ese caso. El Portal 3 solo se omite cuando el paciente ya quedó en un estado terminal de error
# antes de llegar aquí (`ERROR_PORTAL_2` por ALTCHA, o `ERROR_PORTAL_1` al re-consultar por el
# titular cuando `seguro_derivado = True`) — consecuencia directa de la máquina de estados de
# business-rules.md §4, no una inferencia nueva.
#
# CONFIRMADO (sesión SDD 2026-09-10, tercera ronda): el criterio de 03_consulta_portal1.feature
# (fallo de integridad del PDF en la primera descarga se trata igual que un timeout, hasta 3
# reintentos y luego el ERROR_PORTAL correspondiente) aplica también al PDF de este portal — ver
# business-rules.md §5 "Fallo de Integridad en la Primera Descarga". Sin puntos pendientes en este
# archivo.

Feature: Consulta Portal 3 (siempre, salvo corte previo) — atención médica

  Como sistema
  Quiero descargar el PDF de atención médica
  Para completar el entregable del paciente

  Scenario: Rama A con seguro derivado — consulta con la cédula del titular
    Given un paciente de "Rama A" con "seguro_derivado" en verdadero y la cédula del titular obtenida
    And el médico tiene una sesión activa en el Portal 3
    When el sistema consulta la atención médica con la cédula del titular
    Then el sistema descarga el PDF de atención
    And el sistema verifica la integridad del PDF

  Scenario: Rama A sin seguro derivado — consulta con la cédula del propio paciente
    Given un paciente de "Rama A" con "seguro_derivado" en falso
    And el médico tiene una sesión activa en el Portal 3
    When el sistema consulta la atención médica con la cédula del propio paciente
    Then el sistema descarga el PDF de atención
    And el sistema verifica la integridad del PDF

  Scenario: Rama B — consulta con la cédula del paciente
    Given un paciente de "Rama B"
    And el médico tiene una sesión activa en el Portal 3
    When el sistema consulta la atención médica con la cédula del paciente
    Then el sistema descarga el PDF de atención
    And el sistema verifica la integridad del PDF

  Scenario Outline: El Portal 3 se omite si el paciente ya quedó en un estado terminal de error antes de llegar aquí
    Given un paciente de "Rama A" que ya terminó con estado interno "<estado_previo>"
    When el sistema evalúa si corresponde consultar el Portal 3
    Then el Portal 3 se omite para ese paciente
    And el sistema continúa con el siguiente paciente

    Examples:
      | estado_previo   |
      | ERROR_PORTAL_2  |
      | ERROR_PORTAL_1  |

  Scenario: Timeout dispara reintentos acotados
    Given un paciente con sesión activa en el Portal 3
    When el sistema consulta el Portal 3
    And la consulta produce timeout
    Then el sistema reintenta hasta 3 veces adicionales sobre el intento actual

  Scenario: Fallo persistente del Portal 3 tras reintentos
    Given el sistema agotó los 3 reintentos adicionales por timeout en el Portal 3
    When la consulta sigue fallando
    Then el sistema marca al paciente como "ERROR_PORTAL_3"
    And el sistema continúa con el siguiente paciente
