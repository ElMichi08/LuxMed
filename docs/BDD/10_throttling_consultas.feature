# Fuente: Requisitos.MD — Feature "Ritmo de consultas y comportamiento respetuoso"
# Estado: validado con el propietario (v1.0)

Feature: Ritmo de consultas y comportamiento respetuoso

  Como operador responsable
  Quiero un ritmo de consultas moderado
  Para no parecer un ataque ni provocar el bloqueo de la cuenta

  Scenario: Throttling entre consultas
    Given el sistema procesa pacientes en serie
    When realiza consultas a cualquier portal
    Then espera un intervalo prudente entre consultas (con variación)
    And no envía ráfagas concurrentes contra un mismo portal
