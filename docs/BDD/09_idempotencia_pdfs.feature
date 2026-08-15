# Fuente: Requisitos.MD — Feature "Idempotencia de PDFs al reanudar"
# Estado: validado con el propietario (v1.0)
#
# Nota (sesión BDD 2026-08-12): 11_consolidacion_pdf_paciente.feature introduce que los PDFs
# individuales (#1/#2/#3) se descartan una vez armado el PDF combinado del paciente. Los 2
# escenarios de abajo asumen PDFs individuales todavía presentes — eso sigue siendo correcto
# MIENTRAS el paciente no haya llegado a la fase de combinación. Resuelto: el checkpoint registra
# qué fases/portales ya se completaron para cada paciente, independientemente de si el combinado ya
# se armó. El combinado es el último paso; si el proceso se corta antes, al reanudar el sistema usa
# ese registro de fases (no la presencia de los PDFs individuales, que pueden ya no existir) para
# saber qué le falta. Ver escenario nuevo en 11_consolidacion_pdf_paciente.feature.

Feature: Idempotencia de PDFs al reanudar

  Como sistema
  Quiero no re-descargar trabajo ya válido
  Para ahorrar consultas y respetar el throttling de los portales

  Scenario: PDF previo íntegro se conserva
    Given un paciente con un PDF descargado en una corrida anterior
    When el sistema reanuda y verifica ese PDF
    And el PDF está íntegro
    Then el sistema omite su descarga y continúa con las fases pendientes

  Scenario: PDF previo corrupto se vuelve a descargar
    Given un paciente con un PDF descargado en una corrida anterior
    When el sistema reanuda y verifica ese PDF
    And el PDF está corrupto o incompleto
    Then el sistema vuelve a descargar ese PDF
