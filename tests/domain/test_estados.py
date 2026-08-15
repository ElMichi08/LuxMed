# Cubre docs/BDD/01, 03, 05, 07, 08 y 12 (validado con el propietario, EstadoPaciente sin
# ERROR_PORTAL_3 — ver domain/estados.py)
from domain.estados import EstadoLote, EstadoPaciente


def test_estado_paciente_no_incluye_error_portal_3_todavia():
    assert "ERROR_PORTAL_3" not in EstadoPaciente.__members__


def test_estado_paciente_incluye_los_7_valores_confirmados_mas_pendiente():
    assert set(EstadoPaciente.__members__) == {
        "PENDIENTE",
        "COMPLETADO",
        "NO_ENCONTRADO",
        "CEDULA_INVALIDA",
        "ERROR_PORTAL_1",
        "SIN_COBERTURA_PORTAL_2",
        "ERROR_PORTAL_2",
        "PDF_CORRUPTO_PORTAL_2",
    }


def test_estado_lote_tiene_los_4_valores_del_lote():
    assert set(EstadoLote.__members__) == {
        "PENDIENTE",
        "EN_PROCESO",
        "PAUSADO",
        "COMPLETADO",
    }
