# Fuente: business-rules.md §7 "Consolidación y Entregables del Lote" (Resumen Numérico del Lote).
# Estado: CONFIRMADO con el propietario en sesión SDD 2026-09-10 y promovido a business-rules.md
# como fuente de verdad.
#
# Estados por paciente mostrados en el resumen (ya no se mapean a texto en el Excel — ver
# 12_exportacion_excel_resultado.feature, que ahora usa color uniforme, no columna de texto):
# COMPLETADO, CEDULA_INVALIDA, NO_ENCONTRADO, ERROR_PORTAL_1, ERROR_PORTAL_2, ERROR_PORTAL_3 — los 6
# estados finales de business-rules.md §4 (v1.2.0 — se eliminaron SIN_COBERTURA_PORTAL_2 y
# PDF_CORRUPTO_PORTAL_2, ver 05_consulta_portal2.feature). PAUSADO es un estado de lote, no de
# paciente, y no aplica aquí porque el resumen solo se genera cuando el lote ya terminó.
#
# "Duración total": mide solo tiempo activo de procesamiento, excluyendo el tiempo en pausa
# (confirmado en sesión BDD 2026-08-12).

Feature: Resumen numérico del lote (GUI)

  Como médico
  Quiero ver un resumen numérico al terminar el lote
  Para conocer de un vistazo cuántos pacientes quedaron en cada estado y cuánto tardó el proceso

  Background:
    Given un lote que terminó de procesar todos sus pacientes

  Scenario: Resumen unificado de las dos ramas
    When el sistema muestra el resumen del lote en la GUI
    Then presenta el total de pacientes procesados
    And presenta cuántos quedaron en cada estado (COMPLETADO, CEDULA_INVALIDA, NO_ENCONTRADO, ERROR_PORTAL_1, ERROR_PORTAL_2, ERROR_PORTAL_3), sumando Rama A y Rama B

  Scenario: Resumen desglosado por rama
    When el sistema muestra el resumen del lote en la GUI
    Then presenta los mismos conteos por estado separados para Rama A y para Rama B

  Scenario: Duración del lote
    When el sistema muestra el resumen del lote en la GUI
    Then presenta la hora de inicio y la hora de fin del lote
    And presenta la duración total de tiempo activo de procesamiento, excluyendo el tiempo que el lote estuvo en pausa
