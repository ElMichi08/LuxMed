# Fuente: NO estaba en Requisitos.MD v1.0 — feature nueva, levantada en sesión BDD 2026-08-12.
# Estado: validado con el propietario (confirmación explícita 2026-08-15).
#
# Resuelto (convención de nombre, decisión de ingeniería — no requiere validación del propietario):
# el PDF combinado se nombra "{cedula}_{fecha_atencion:%Y%m%d}.pdf". Se usa cédula + fecha de
# atención (no solo cédula) porque ese es el par que ya identifica de forma única cada fila del
# Excel de entrada (Feature "Consulta Portal 1" lo usa como clave de consulta) — un mismo paciente
# puede aparecer en más de un lote o más de una fecha de atención, y la cédula sola colisionaría.
#
# Resuelto (idempotencia, ver 09_idempotencia_pdfs.feature): el checkpoint registra qué
# fases/portales ya se completaron para cada paciente, independientemente de si el combinado ya se
# armó. El combinado es el último paso del procesamiento de un paciente — si el lote se pausa o
# corta antes de armarlo, al reanudar el sistema se apoya en ese registro de fases (no en la
# presencia de los PDFs individuales, que para ese momento ya pueden no existir) para saber qué le
# falta, y arma el combinado recién cuando las fases requeridas por la rama ya están completas.

Feature: Consolidación de PDFs por paciente

  Como médico
  Quiero recibir un solo PDF por paciente en vez de 2 o 3 archivos sueltos
  Para tener un único documento de respaldo fácil de archivar y compartir

  Scenario: Unión de PDFs en Rama A
    Given un paciente de "Rama A" con los PDFs #1, #2 y #3 descargados y verificados
    When el sistema arma el entregable final del paciente
    Then los tres PDFs se combinan en un único PDF en el orden Portal 1, Portal 2, Portal 3
    And los PDFs individuales se descartan, conservando solo el PDF combinado

  Scenario: Unión de PDFs en Rama B
    Given un paciente de "Rama B" con los PDFs #1 y #3 descargados y verificados
    When el sistema arma el entregable final del paciente
    Then los dos PDFs se combinan en un único PDF en el orden Portal 1, Portal 3
    And los PDFs individuales se descartan, conservando solo el PDF combinado

  Scenario: Reanudación antes de armar el combinado
    Given un paciente cuyas fases requeridas por su rama ya están completas (PDFs individuales descargados y verificados)
    And el lote se pausó o se cortó antes de armar el PDF combinado de ese paciente
    When el sistema reanuda el lote
    Then usa el registro de fases del checkpoint, no la presencia de los PDFs individuales, para saber que a ese paciente solo le falta el armado del combinado
    And arma el PDF combinado sin volver a consultar ningún portal
