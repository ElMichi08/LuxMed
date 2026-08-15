import pytest

from domain.estados import EstadoPaciente
from domain.reporte import estado_a_texto_excel


@pytest.mark.parametrize(
    ("estado", "texto_esperado"),
    [
        (EstadoPaciente.COMPLETADO, "Correcto"),
        (EstadoPaciente.NO_ENCONTRADO, "Desactualizado"),
        (EstadoPaciente.SIN_COBERTURA_PORTAL_2, "Desactualizado"),
        (EstadoPaciente.CEDULA_INVALIDA, "CI no válida"),
        (EstadoPaciente.ERROR_PORTAL_1, "Error Portal 1"),
        (EstadoPaciente.ERROR_PORTAL_2, "Error Portal 2"),
        (EstadoPaciente.PDF_CORRUPTO_PORTAL_2, "Error Portal 2"),
    ],
)
def test_mapeo_estado_a_texto_excel(estado, texto_esperado):
    assert estado_a_texto_excel(estado) == texto_esperado


def test_pendiente_no_tiene_texto_de_reporte():
    # El Excel solo se genera cuando el lote ya terminó (docs/BDD/12_..., Background) — no
    # debería quedar ningún paciente en PENDIENTE llegado ese punto.
    with pytest.raises(KeyError):
        estado_a_texto_excel(EstadoPaciente.PENDIENTE)
