# Fuente: Requisitos.MD — Feature "Bifurcación de rama según Portal 1"
# Estado: validado con el propietario (v1.0)

Feature: Bifurcación de rama según Portal 1

  Como sistema
  Quiero determinar si el titular del seguro es un tercero
  Para decidir si consulto el Portal 2

  Scenario: Rama A — menor de edad requiere Portal 2
    Given el Portal 1 indica que el paciente es menor de edad
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama A"
    And el flujo continuará por el Portal 2

  Scenario: Rama A — seguro IESS/Campesino requiere Portal 2
    Given el Portal 1 indica tipo de seguro "IESS" o "Afiliado Seguro Campesino"
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama A"
    And el flujo continuará por el Portal 2

  Scenario: Rama B — el titular es el propio paciente
    Given el paciente no es menor de edad
    And el tipo de seguro no es "IESS" ni "Afiliado Seguro Campesino"
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama B"
    And se omite el Portal 2
    And el flujo continúa directamente al Portal 3 con la cédula del paciente
