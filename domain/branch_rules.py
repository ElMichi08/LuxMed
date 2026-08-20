from __future__ import annotations

from domain.models import Rama

SEGUROS_RAMA_A = frozenset({"IESS", "Afiliado Seguro Campesino"})


def clasificar_rama(es_menor_edad: bool, tipo_seguro: str) -> Rama:
    if es_menor_edad or tipo_seguro in SEGUROS_RAMA_A:
        return Rama.RAMA_A
    return Rama.RAMA_B
