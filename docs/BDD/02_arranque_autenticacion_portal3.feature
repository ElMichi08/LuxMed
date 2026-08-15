# Fuente: Requisitos.MD — Feature "Arranque del lote y autenticación asistida (Portal 3)"
# Estado: validado con el propietario (v1.0)

Feature: Arranque del lote y autenticación asistida (Portal 3)

  Como médico
  Quiero autenticarme una sola vez al inicio
  Para que la máquina procese el lote reutilizando mi sesión

  Scenario: Login manual único al inicio del lote
    Given un lote normalizado listo para procesar
    When se inicia la corrida
    Then el sistema abre el navegador en modo visible en la página de login del Portal 3
    And el sistema pausa y espera a que el médico introduzca sus credenciales
    And el sistema no captura, almacena ni transmite esas credenciales

  Scenario: La sesión establecida se reutiliza para todo el lote
    Given el médico se autenticó correctamente en el Portal 3
    When el sistema procesa cada paciente que requiere Portal 3
    Then reutiliza la misma sesión de navegador sin volver a solicitar login
    And la sesión se mantiene solo en memoria (contexto no persistente)
