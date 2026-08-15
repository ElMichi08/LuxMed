# Cubre docs/BDD/04_bifurcacion_rama.feature (validado con el propietario, v1.0)
from domain.branch_rules import clasificar_rama
from domain.models import Rama


def test_menor_de_edad_es_rama_a():
    assert clasificar_rama(es_menor_edad=True, tipo_seguro="Privado") == Rama.RAMA_A


def test_seguro_iess_es_rama_a():
    assert clasificar_rama(es_menor_edad=False, tipo_seguro="IESS") == Rama.RAMA_A


def test_seguro_afiliado_campesino_es_rama_a():
    assert (
        clasificar_rama(es_menor_edad=False, tipo_seguro="Afiliado Seguro Campesino")
        == Rama.RAMA_A
    )


def test_titular_propio_paciente_es_rama_b():
    assert clasificar_rama(es_menor_edad=False, tipo_seguro="Privado") == Rama.RAMA_B
