# Fuente: Requisitos.MD — Feature "Definición de éxito por paciente"
# Estado: validado con el propietario (v1.0). Corregido en sesión SDD 2026-09-10 (segunda ronda):
# el criterio de éxito en Rama A ya NO depende solo de la rama, sino también de "seguro_derivado"
# (ver 05_consulta_portal2.feature) — el Portal 2 no genera documento propio, así que un paciente de
# Rama A sin titular (seguro_derivado = False) tiene el mismo número de documentos que uno de Rama B.

Feature: Definición de éxito por paciente

  Como operador
  Quiero un criterio claro de "procesado con éxito"
  Para separar los casos resueltos de los que requieren revisión

  Scenario: Éxito en Rama A con seguro derivado requiere 3 documentos
    Given un paciente de "Rama A" con "seguro_derivado" en verdadero
    When el sistema termina su procesamiento
    Then el paciente se marca "COMPLETADO" solo si tiene verificados el PDF del paciente (Portal 1), el PDF del titular (Portal 1) y el PDF de atención (Portal 3)

  Scenario: Éxito en Rama A sin seguro derivado requiere 2 documentos
    Given un paciente de "Rama A" con "seguro_derivado" en falso
    When el sistema termina su procesamiento
    Then el paciente se marca "COMPLETADO" solo si tiene verificados el PDF del paciente (Portal 1) y el PDF de atención (Portal 3)

  Scenario: Éxito en Rama B requiere 2 documentos
    Given un paciente de "Rama B"
    When el sistema termina su procesamiento
    Then el paciente se marca "COMPLETADO" solo si tiene verificados el PDF del paciente (Portal 1) y el PDF de atención (Portal 3)
