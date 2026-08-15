# Fuente: NO estaba en Requisitos.MD v1.0 (Apéndice C la mencionaba como "formato del entregable
# consolidado del lote", sin especificar) — especificada en sesión BDD 2026-08-12.
# Estado: validado con el propietario (confirmación explícita 2026-08-15), con una excepción —
# ver nota sobre ERROR_PORTAL_3 abajo.
#
# Mapeo de estados internos a la columna ESTADO (confirmado en sesión BDD 2026-08-12, ratificado
# explícitamente por el propietario el 2026-08-15):
#   COMPLETADO            -> "Correcto"
#   NO_ENCONTRADO          -> "Desactualizado"  (Portal 1 dice que no hay cobertura)
#   SIN_COBERTURA_PORTAL_2  -> "Desactualizado"  (Portal 2 dice que no hay cobertura del titular)
#   CEDULA_INVALIDA          -> "CI no válida"
#   ERROR_PORTAL_1            -> "Error Portal 1"  (técnico: timeout/fallo persistente del portal)
#   ERROR_PORTAL_2             -> "Error Portal 2"  (técnico: ALTCHA no resuelto ni con intervención humana)
#   PDF_CORRUPTO_PORTAL_2       -> "Error Portal 2"  (técnico: PDF del titular ilegible, sin poder resolverlo)
#   ERROR_PORTAL_3                -> "Error Portal 3"  (técnico: timeout/fallo persistente del portal)
#
# "Error Portal 2" agrupa ERROR_PORTAL_2 y PDF_CORRUPTO_PORTAL_2 porque ambos son fallos técnicos
# del Portal 2 que un humano no pudo resolver — a diferencia de SIN_COBERTURA_PORTAL_2, que es un
# resultado de negocio válido (no es un fallo, es información real del portal). Agrupamiento
# confirmado explícitamente por el propietario el 2026-08-15.
#
# Excepción — fila ERROR_PORTAL_3: el texto "Error Portal 3" queda confirmado *condicionalmente*
# a que el estado ERROR_PORTAL_3 llegue a existir. El propio estado sigue @pendiente en
# 06_consulta_portal3.feature (comportamiento de Portal 3 no explorado todavía) — no se puede
# cerrar por conversación, requiere revisar el portal real en otra sesión.
#
# Punto abierto: PAUSADO es un estado de LOTE, no de paciente — el Excel solo se genera cuando el
# lote ya terminó (sin pendientes), así que PAUSADO nunca debería aparecer en esta columna. Se deja
# fuera del mapeo a propósito.

Feature: Exportación de Excel de resultados del lote

  Como departamento de origen del listado de pacientes
  Quiero recibir el Excel original con el resultado de cada paciente
  Para saber qué registros están correctos y cuáles requieren corrección en su fuente

  Background:
    Given un lote que terminó de procesar todos sus pacientes

  Scenario: Generación del Excel de resultados al completar el lote
    When el sistema genera el entregable consolidado del lote
    Then produce un nuevo Excel con todas las columnas y filas del Excel original sin modificar
    And agrega una columna "ESTADO" al final de todas las columnas originales

  Scenario: Estado "Correcto"
    Given un paciente que terminó con estado interno "COMPLETADO"
    When se genera el Excel de resultados
    Then su columna ESTADO se llena con "Correcto"

  Scenario: Estado "Desactualizado" — Portal 1 no encuentra cobertura
    Given un paciente cuyo registro en el Excel original asumía cobertura de seguro vigente
    And el Portal 1 respondió "no encontrado" (estado interno "NO_ENCONTRADO")
    When se genera el Excel de resultados
    Then su columna ESTADO se llena con "Desactualizado"
    # Señala que el departamento de origen no actualizó su fuente de datos respecto al Portal 1.

  Scenario: Estado "Desactualizado" — Portal 2 no encuentra cobertura del titular
    Given un paciente de "Rama A" cuyo registro en el Excel original asumía cobertura de seguro vigente
    And el Portal 2 respondió "SIN COBERTURA" (estado interno "SIN_COBERTURA_PORTAL_2")
    When se genera el Excel de resultados
    Then su columna ESTADO se llena con "Desactualizado"

  Scenario: Estado "CI no válida"
    Given un registro descartado en la normalización previa con estado "CEDULA_INVALIDA"
    When se genera el Excel de resultados
    Then su columna ESTADO se llena con "CI no válida"

  Scenario Outline: Estados de error técnico por portal
    Given un paciente que terminó con estado interno "<estado_interno>"
    When se genera el Excel de resultados
    Then su columna ESTADO se llena con "<estado_excel>"
    # La fila ERROR_PORTAL_3 queda condicionada a que ese estado llegue a existir — sigue
    # @pendiente en 06_consulta_portal3.feature hasta explorar el portal real.

    Examples:
      | estado_interno         | estado_excel    |
      | ERROR_PORTAL_1         | Error Portal 1  |
      | ERROR_PORTAL_2         | Error Portal 2  |
      | PDF_CORRUPTO_PORTAL_2  | Error Portal 2  |
      | ERROR_PORTAL_3         | Error Portal 3  |
