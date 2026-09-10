# Fuente: Requisitos.MD — Feature "Normalización previa del Excel (pre-flujo)"
# Estado: validado con el propietario (v1.0). Re-confirmado en sesión SDD 2026-09-10: la validación
# de cédula es solo longitud de 10 dígitos, sin algoritmo de dígito verificador — business-rules.md
# §2 se corrigió para dejar de exigirlo.

Feature: Normalización previa del Excel (pre-flujo)

  Como operador del sistema
  Quiero filtrar registros inválidos antes de iniciar el lote
  Para no gastar consultas contra los portales en datos defectuosos

  Background:
    Given un archivo Excel con el listado de pacientes a procesar

  Scenario: Registro con cédula válida entra al lote
    Given una fila cuyo campo cédula tiene exactamente 10 dígitos numéricos
    When se ejecuta la normalización
    Then el registro se acepta y entra al lote con estado "PENDIENTE"

  Scenario: Registro con cédula inválida se descarta antes del lote
    Given una fila cuyo campo cédula no tiene exactamente 10 dígitos numéricos
    When se ejecuta la normalización
    Then el registro se descarta y se reporta como "CEDULA_INVALIDA"
    And no se realiza ninguna consulta a los portales para ese registro

  Scenario: El motivo de consulta del Portal 2 es un valor fijo
    Given cualquier registro aceptado en el lote
    When el sistema prepara los datos de consulta
    Then el motivo de consulta para el Portal 2 se fija en "Enfermedad" para todos los pacientes
