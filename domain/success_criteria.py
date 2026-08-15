from __future__ import annotations

from typing import AbstractSet

from domain.models import Rama

PORTALES_REQUERIDOS: dict[Rama, frozenset[int]] = {
    Rama.RAMA_A: frozenset({1, 2, 3}),
    Rama.RAMA_B: frozenset({1, 3}),
}


def es_completado(rama: Rama, portales_verificados: AbstractSet[int]) -> bool:
    return PORTALES_REQUERIDOS[rama] <= portales_verificados
