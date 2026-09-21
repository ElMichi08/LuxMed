# Fuente: Requisitos.MD — Feature "Arranque del lote y autenticación asistida (Portal 3)"
# Estado: validado con el propietario (v1.0). Confirmado en sesión SDD 2026-09-10 (primera ronda):
# este login manual es independiente del login local de la app (RBAC, ver ARCHITECTURE.md §7) — son
# dos capas distintas, no un conflicto. Solo el Portal 3 requiere sesión; Portal 1 y 2 no la
# necesitan (Portal 2 confirmado como formulario público, sin autenticación, solo ALTCHA).
#
# RESUELTO (sesión SDD 2026-09-10, tercera ronda): la sesión/cookie del Portal 3 se mantiene
# únicamente en memoria (RAM) durante la corrida del lote — nunca se persiste a disco. Si la
# aplicación se cierra o falla a mitad de la corrida, la sesión se pierde junto con el resto del
# estado en memoria; aplica el mismo flujo de re-autenticación ya descrito para una expiración de
# sesión a mitad de lote (ver 08_pausa_reanudacion_lote.feature).

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
