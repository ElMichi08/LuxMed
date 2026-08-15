# Fuente: NO estaba en Requisitos.MD v1.0 — feature nueva, levantada en sesión BDD 2026-08-12,
# como parte del "entregable consolidado del lote" mencionado en el Apéndice C.
# Estado: BORRADOR. Falta trasladar esta decisión a Requisitos.MD.
#
# Usa el mismo mapeo de estados que 12_exportacion_excel_resultado.feature: Correcto,
# Desactualizado, CI no válida, Error Portal 1, Error Portal 2 (agrupa ERROR_PORTAL_2 y
# PDF_CORRUPTO_PORTAL_2), Error Portal 3 — mapeo PENDIENTE de confirmación explícita del
# propietario, ver ese archivo. PAUSADO es un estado de lote, no de paciente, y no aplica aquí
# porque el resumen solo se genera cuando el lote ya terminó.
#
# "Duración total": resuelto — mide solo tiempo activo de procesamiento, excluyendo el tiempo en
# pausa (confirmado en sesión BDD 2026-08-12).

Feature: Resumen numérico del lote (GUI)

  Como médico
  Quiero ver un resumen numérico al terminar el lote
  Para conocer de un vistazo cuántos pacientes quedaron en cada estado y cuánto tardó el proceso

  Background:
    Given un lote que terminó de procesar todos sus pacientes

  @borrador
  Scenario: Resumen unificado de las dos ramas
    When el sistema muestra el resumen del lote en la GUI
    Then presenta el total de pacientes procesados
    And presenta cuántos quedaron en cada estado (Correcto, Desactualizado, CI no válida, Error Portal 1, Error Portal 2, Error Portal 3), sumando Rama A y Rama B

  @borrador
  Scenario: Resumen desglosado por rama
    When el sistema muestra el resumen del lote en la GUI
    Then presenta los mismos conteos por estado separados para Rama A y para Rama B

  @borrador
  Scenario: Duración del lote
    When el sistema muestra el resumen del lote en la GUI
    Then presenta la hora de inicio y la hora de fin del lote
    And presenta la duración total de tiempo activo de procesamiento, excluyendo el tiempo que el lote estuvo en pausa
