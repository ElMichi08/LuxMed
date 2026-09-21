# Fuente: business-rules.md §7 "Consolidación y Entregables del Lote" (Entregable Dual de Excel).
# Estado: reescrito en sesión SDD 2026-09-10 — reemplaza la versión anterior (BORRADOR) que
# proponía un único Excel con una columna "ESTADO" en texto. El propietario confirmó que el
# entregable real es el ENTREGABLE DUAL ya descrito en ARCHITECTURE.md/business-rules.md v1.0:
# un Excel Limpio + un Excel Auditado ("Espejo") con celdas pintadas de rojo — no una columna de
# texto.
#
# Resuelto (color, confirmado por el propietario 2026-09-10): el color es ROJO UNIFORME para
# cualquier paciente cuyo estado final sea distinto de COMPLETADO, sin distinguir visualmente el
# motivo (CI inválida, sin cobertura, error técnico de portal, etc.). El color solo señala
# "requiere revisión" — el detalle del motivo vive en la base de datos/checkpoint interno, no en el
# color de la celda. Los 6 estados finales posibles (COMPLETADO, CEDULA_INVALIDA, NO_ENCONTRADO,
# ERROR_PORTAL_1, ERROR_PORTAL_2, ERROR_PORTAL_3) se siguen usando internamente y se exponen en el
# Resumen Numérico del Lote (ver 13_resumen_numerico_lote.feature), pero no como columna de texto en
# el Excel.
#
# CORREGIDO (sesión SDD 2026-09-10, segunda ronda): se eliminaron los estados
# SIN_COBERTURA_PORTAL_2 y PDF_CORRUPTO_PORTAL_2 — el Portal 2 no genera documentos (ver
# 05_consulta_portal2.feature), así que "sin cobertura" en realidad era el desenlace normal
# "seguro_derivado = False" (no un rechazo), y no existe ningún PDF de Portal 2 que pueda corromperse.

Feature: Exportación del entregable dual de Excel del lote

  Como departamento de origen del listado de pacientes
  Quiero recibir el Excel original limpio, y una copia auditada que resalte los registros que requieren revisión
  Para saber qué registros están correctos y cuáles requieren corrección en su fuente, sin perder el archivo original intacto

  Background:
    Given un lote que terminó de procesar todos sus pacientes

  Scenario: Generación del entregable dual al completar el lote
    When el sistema genera el entregable consolidado del lote
    Then produce un "Excel Limpio" idéntico al original, sin ninguna modificación visual
    And produce un "Excel Auditado" (Espejo) con las mismas columnas y filas del original

  Scenario: Fila sin pintar — paciente completado con éxito
    Given un paciente que terminó con estado interno "COMPLETADO"
    When se genera el Excel Auditado
    Then su fila conserva el color original, sin pintarse

  Scenario Outline: Fila pintada en rojo — cualquier estado distinto de COMPLETADO
    Given un paciente que terminó con estado interno "<estado_interno>"
    When se genera el Excel Auditado
    Then su fila se pinta de rojo (`PatternFill`) para señalar que requiere revisión
    # El color no distingue el motivo específico del fallo; ver 13_resumen_numerico_lote.feature para el desglose por estado.

    Examples:
      | estado_interno   |
      | CEDULA_INVALIDA  |
      | NO_ENCONTRADO    |
      | ERROR_PORTAL_1   |
      | ERROR_PORTAL_2   |
      | ERROR_PORTAL_3   |
