# Fuente: Requisitos.MD — Feature "Pausa y reanudación del lote"
# Estado: validado con el propietario (v1.0)

Feature: Pausa y reanudación del lote

  Como médico
  Quiero poder pausar el lote y retomarlo en otra sesión
  Para atender otros asuntos, almorzar o terminar mi jornada sin perder el progreso

  Scenario: Pausa manual por decisión del médico
    Given un lote en proceso
    When el médico solicita pausar el lote
    Then el sistema guarda el progreso por paciente (checkpoint)
    And el lote queda en estado reanudable

  Scenario: Pausa forzada por expiración de sesión del Portal 3
    Given un lote en proceso
    When la sesión del Portal 3 expira a mitad del lote
    Then el sistema pausa el lote de forma reanudable
    And el sistema informa que será necesario re-autenticarse para continuar

  Scenario: Reanudación con confirmación del médico
    Given un lote pausado con progreso guardado
    When el médico relanza el lote y se re-autentica en el Portal 3
    Then el sistema muestra un resumen de pacientes procesados y pendientes
    And el sistema espera la confirmación del médico para continuar
    And al confirmar, retoma desde el primer paciente pendiente
