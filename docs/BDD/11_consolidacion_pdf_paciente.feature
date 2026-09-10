# Fuente: business-rules.md §7 "Consolidación y Entregables del Lote".
# Estado: CONFIRMADO con el propietario en sesión SDD 2026-09-10 y promovido a business-rules.md
# como fuente de verdad — reemplaza la versión anterior de este archivo (estado BORRADOR).
#
# Resuelto (convención de nombre, confirmada por el propietario 2026-09-10): el PDF combinado se
# nombra "{NOMBRE}_{CEDULA}.pdf", usando el nombre completo del paciente tal como se extrajo del
# Excel de origen. NO lleva fecha de atención en el nombre. No hay riesgo de colisión: el archivo se
# guarda en la carpeta del mes correspondiente a la fecha de atención del Excel procesado, y cada
# Excel de origen agrupa únicamente atenciones ya cerradas de un mes específico — si el mismo
# paciente vuelve a aparecer en un Excel de un mes distinto, su fecha de atención cae en ese otro
# mes y por tanto vive en una carpeta de mes distinta, sin sobrescribir el PDF anterior.
#
# Resuelto (idempotencia, ver 09_idempotencia_pdfs.feature): el checkpoint registra qué
# fases/portales ya se completaron para cada paciente, independientemente de si el combinado ya se
# armó. El combinado es el último paso del procesamiento de un paciente — si el lote se pausa o
# corta antes de armarlo, al reanudar el sistema se apoya en ese registro de fases (no en la
# presencia de los PDFs individuales, que para ese momento ya pueden no existir) para saber qué le
# falta, y arma el combinado recién cuando las fases requeridas por la rama ya están completas.
#
# CORREGIDO (sesión SDD 2026-09-10, segunda ronda): el "PDF #2" ya no sale del Portal 2 (que no
# genera documentos — ver 05_consulta_portal2.feature). Cuando la Rama A tiene "seguro_derivado en
# verdadero", el segundo documento sale de una re-consulta al PORTAL 1 con la cédula del titular.
# Cuando "seguro_derivado" es falso, no hay segundo documento en absoluto — el combinado de Rama A
# queda igual de 2 documentos que el de Rama B.

Feature: Consolidación de PDFs por paciente

  Como médico
  Quiero recibir un solo PDF por paciente en vez de 2 o 3 archivos sueltos
  Para tener un único documento de respaldo fácil de archivar y compartir

  Scenario: Unión de PDFs en Rama A con seguro derivado
    Given un paciente de "Rama A" con "seguro_derivado" en verdadero, con el PDF del paciente, el PDF del titular y el PDF de atención descargados y verificados
    When el sistema arma el entregable final del paciente
    Then los tres documentos se combinan en un único PDF en el orden: PDF del paciente (Portal 1), PDF del titular (Portal 1), PDF de atención (Portal 3)
    And el archivo combinado se nombra "{NOMBRE}_{CEDULA}.pdf" y se guarda en la carpeta del mes de la fecha de atención
    And los documentos individuales se descartan, conservando solo el PDF combinado

  Scenario: Unión de PDFs en Rama A sin seguro derivado
    Given un paciente de "Rama A" con "seguro_derivado" en falso, con el PDF del paciente y el PDF de atención descargados y verificados
    When el sistema arma el entregable final del paciente
    Then los dos documentos se combinan en un único PDF en el orden: PDF del paciente (Portal 1), PDF de atención (Portal 3)
    And el archivo combinado se nombra "{NOMBRE}_{CEDULA}.pdf" y se guarda en la carpeta del mes de la fecha de atención
    And los documentos individuales se descartan, conservando solo el PDF combinado

  Scenario: Unión de PDFs en Rama B
    Given un paciente de "Rama B" con el PDF del paciente y el PDF de atención descargados y verificados
    When el sistema arma el entregable final del paciente
    Then los dos documentos se combinan en un único PDF en el orden: PDF del paciente (Portal 1), PDF de atención (Portal 3)
    And el archivo combinado se nombra "{NOMBRE}_{CEDULA}.pdf" y se guarda en la carpeta del mes de la fecha de atención
    And los documentos individuales se descartan, conservando solo el PDF combinado

  Scenario: Reanudación antes de armar el combinado
    Given un paciente cuyas fases requeridas por su rama ya están completas (PDFs individuales descargados y verificados)
    And el lote se pausó o se cortó antes de armar el PDF combinado de ese paciente
    When el sistema reanuda el lote
    Then usa el registro de fases del checkpoint, no la presencia de los PDFs individuales, para saber que a ese paciente solo le falta el armado del combinado
    And arma el PDF combinado sin volver a consultar ningún portal

  Scenario: Mismo paciente en meses distintos no colisiona
    Given un paciente cuyo PDF combinado ya existe en la carpeta de un mes anterior
    And ese mismo paciente aparece en un nuevo Excel de origen con fecha de atención de otro mes
    When el sistema arma el entregable final del paciente
    Then el nuevo PDF combinado se guarda en la carpeta del nuevo mes
    And el PDF combinado del mes anterior no se modifica ni se sobrescribe
