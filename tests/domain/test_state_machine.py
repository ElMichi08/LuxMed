import pytest

from domain.estados import EstadoPaciente
from domain.state_machine import es_transicion_valida


@pytest.mark.parametrize(
    "destino",
    [
        EstadoPaciente.COMPLETADO,
        EstadoPaciente.NO_ENCONTRADO,
        EstadoPaciente.ERROR_PORTAL_1,
        EstadoPaciente.SIN_COBERTURA_PORTAL_2,
        EstadoPaciente.ERROR_PORTAL_2,
        EstadoPaciente.PDF_CORRUPTO_PORTAL_2,
    ],
)
def test_pendiente_puede_transicionar_a_cada_desenlace_confirmado(destino):
    assert es_transicion_valida(EstadoPaciente.PENDIENTE, destino) is True


def test_pendiente_no_puede_transicionar_a_cedula_invalida():
    # CEDULA_INVALIDA se asigna en la normalización previa (01_normalizacion_excel.feature),
    # nunca como transición desde un paciente ya en el lote.
    assert (
        es_transicion_valida(EstadoPaciente.PENDIENTE, EstadoPaciente.CEDULA_INVALIDA)
        is False
    )


def test_los_estados_terminales_no_tienen_transiciones_salientes():
    assert (
        es_transicion_valida(EstadoPaciente.COMPLETADO, EstadoPaciente.ERROR_PORTAL_1)
        is False
    )
    assert (
        es_transicion_valida(EstadoPaciente.ERROR_PORTAL_1, EstadoPaciente.COMPLETADO)
        is False
    )
