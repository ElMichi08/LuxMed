# Fuente: Requisitos.MD — Feature "Definición de éxito por paciente"
# Estado: validado con el propietario (v1.0)

Feature: Definición de éxito por paciente

  Como operador
  Quiero un criterio claro de "procesado con éxito"
  Para separar los casos resueltos de los que requieren revisión

  Scenario: Éxito en Rama A requiere 3 PDFs
    Given un paciente de "Rama A"
    When el sistema termina su procesamiento
    Then el paciente se marca "COMPLETADO" solo si tiene los PDFs #1, #2 y #3 verificados

  Scenario: Éxito en Rama B requiere 2 PDFs
    Given un paciente de "Rama B"
    When el sistema termina su procesamiento
    Then el paciente se marca "COMPLETADO" solo si tiene los PDFs #1 y #3 verificados
