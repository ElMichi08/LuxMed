# Fuente: NO estaba en Requisitos.MD v1.0 — feature nueva, levantada en sesión BDD 2026-08-12,
# como parte del "entregable consolidado del lote" mencionado en el Apéndice C.
# Estado: validado con el propietario (confirmación explícita 2026-08-15).
#
# Usa el mismo mapeo de estados que 12_exportacion_excel_resultado.feature: Correcto,
# Desactualizado, CI no válida, Error Portal 1, Error Portal 2 (agrupa ERROR_PORTAL_2 y
# PDF_CORRUPTO_PORTAL_2), Error Portal 3 — mapeo confirmado explícitamente por el propietario,
# ver ese archivo (con la misma excepción condicional de "Error Portal 3": el texto queda
# confirmado, pero el estado ERROR_PORTAL_3 en sí sigue @pendiente hasta explorar el Portal 3
# real). PAUSADO es un estado de lote, no de paciente, y no aplica aquí porque el resumen solo se
# genera cuando el lote ya terminó.
#
# "Duración total": resuelto — mide solo tiempo activo de procesamiento, excluyendo el tiempo en
# pausa (confirmado en sesión BDD 2026-08-12).

Feature: Resumen numérico del lote (GUI)

  Como médico
  Quiero ver un resumen numérico al terminar el lote
  Para conocer de un vistazo cuántos pacientes quedaron en cada estado y cuánto tardó el proceso

  Background:
    Given un lote que terminó de procesar todos sus pacientes

  Scenario: Resumen unificado de las dos ramas
    When el sistema muestra el resumen del lote en la GUI
    Then presenta el total de pacientes procesados
    And presenta cuántos quedaron en cada estado (Correcto, Desactualizado, CI no válida, Error Portal 1, Error Portal 2, Error Portal 3), sumando Rama A y Rama B

  Scenario: Resumen desglosado por rama
    When el sistema muestra el resumen del lote en la GUI
    Then presenta los mismos conteos por estado separados para Rama A y para Rama B

  Scenario: Duración del lote
    When el sistema muestra el resumen del lote en la GUI
    Then presenta la hora de inicio y la hora de fin del lote
    And presenta la duración total de tiempo activo de procesamiento, excluyendo el tiempo que el lote estuvo en pausa
