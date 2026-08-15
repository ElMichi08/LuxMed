# Cubre docs/BDD/07_definicion_exito_paciente.feature (validado con el propietario, v1.0)
from domain.models import Rama
from domain.success_criteria import es_completado


def test_rama_a_requiere_los_3_pdfs():
    assert es_completado(Rama.RAMA_A, {1, 2}) is False
    assert es_completado(Rama.RAMA_A, {1, 2, 3}) is True


def test_rama_b_requiere_pdf_1_y_3():
    assert es_completado(Rama.RAMA_B, {1}) is False
    assert es_completado(Rama.RAMA_B, {1, 3}) is True


def test_rama_b_ignora_pdf_2_de_mas():
    assert es_completado(Rama.RAMA_B, {1, 2, 3}) is True
