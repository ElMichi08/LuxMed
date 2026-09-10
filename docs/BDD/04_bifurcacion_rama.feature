# Fuente: business-rules.md §3 "Regla de Bifurcación de Ruta (Rama A / Rama B)"
# Estado: reescrito en sesión SDD 2026-09-10 para alinear con business-rules.md v1.1.0 — reemplaza
# la versión anterior (menor de edad O seguro "IESS"/"Afiliado Seguro Campesino" = Rama A), que
# estaba solo parcialmente correcta.
#
# Regla real (confirmada por el propietario 2026-09-10): el Portal 1 devuelve un tipo de cobertura
# dentro de dos familias mutuamente excluyentes — nadie tiene cobertura vigente de ambas al mismo
# tiempo:
#   - Familia IESS: incluye TODAS sus variantes tal como las devuelve el Portal 1 (Afiliado Seguro
#     General, Afiliado Seguro Campesino, Dependiente hijo menor de 18 años de afiliado al Seguro
#     General, entre otras). Cualquier variante IESS → Rama A, siempre pasa por Portal 2, que aquí
#     actúa como VALIDADOR de si el paciente es titular o dependiente de otro titular (ya no se
#     "salta" el Portal 2 para ningún caso IESS).
#   - Entidad Previsional Especial (nombre genérico de documentación — ver ARCHITECTURE.md ADR 003):
#     agrupa los regímenes ajenos al IESS. Cualquier cobertura de esta familia → Rama B, omite
#     siempre el Portal 2.
# La minoría de edad NO es un factor de bifurcación independiente: un menor dependiente de un
# titular IESS cae en Rama A por el tipo de cobertura devuelto, no por su edad. Esto es distinto del
# invariante de invalidez por minoría sin cobertura (business-rules.md, no afectado por este cambio).

Feature: Bifurcación de rama según Portal 1

  Como sistema
  Quiero determinar la familia de cobertura del paciente
  Para decidir si consulto el Portal 2 como validador de titularidad

  Scenario: Rama A — cualquier variante de cobertura IESS
    Given el Portal 1 indica una cobertura de la familia IESS, en cualquiera de sus variantes
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama A"
    And el flujo continuará por el Portal 2, que actúa como validador de titularidad/dependencia

  Scenario: Rama B — cobertura de la Entidad Previsional Especial
    Given el Portal 1 indica una cobertura de la Entidad Previsional Especial
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama B"
    And se omite el Portal 2
    And el flujo continúa directamente al Portal 3 con la cédula del paciente

  Scenario: La minoría de edad no bifurca por sí sola
    Given un paciente menor de edad con cobertura vigente de la Entidad Previsional Especial
    When el sistema evalúa la rama
    Then el paciente se clasifica en "Rama B" igual que un paciente mayor de edad con esa misma cobertura
    # La edad no es un criterio de bifurcación; solo endurece el invariante de invalidez cuando NO hay cobertura alguna (business-rules.md).
