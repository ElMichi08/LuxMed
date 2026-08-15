from __future__ import annotations

from domain.estados import EstadoPaciente

# CEDULA_INVALIDA no aparece como destino de ninguna transición: se asigna durante la
# normalización previa (docs/BDD/01_normalizacion_excel.feature), antes de que el registro
# entre al lote como "PENDIENTE" y sin consultar ningún portal — no es un desenlace del
# procesamiento en curso, es un filtro previo a él.
TRANSICIONES_VALIDAS: dict[EstadoPaciente, frozenset[EstadoPaciente]] = {
    EstadoPaciente.PENDIENTE: frozenset(
        {
            EstadoPaciente.COMPLETADO,
            EstadoPaciente.NO_ENCONTRADO,
            EstadoPaciente.ERROR_PORTAL_1,
            EstadoPaciente.SIN_COBERTURA_PORTAL_2,
            EstadoPaciente.ERROR_PORTAL_2,
            EstadoPaciente.PDF_CORRUPTO_PORTAL_2,
        }
    ),
    EstadoPaciente.COMPLETADO: frozenset(),
    EstadoPaciente.NO_ENCONTRADO: frozenset(),
    EstadoPaciente.CEDULA_INVALIDA: frozenset(),
    EstadoPaciente.ERROR_PORTAL_1: frozenset(),
    EstadoPaciente.SIN_COBERTURA_PORTAL_2: frozenset(),
    EstadoPaciente.ERROR_PORTAL_2: frozenset(),
    EstadoPaciente.PDF_CORRUPTO_PORTAL_2: frozenset(),
}


def es_transicion_valida(origen: EstadoPaciente, destino: EstadoPaciente) -> bool:
    return destino in TRANSICIONES_VALIDAS[origen]
