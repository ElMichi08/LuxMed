from __future__ import annotations

import pytest

from app.infrastructure.ui.theme.tokens import COLORES

TEXTO_MINIMO = 4.5
ATENUADO_MINIMO = 3.0

PARES: tuple[tuple[str, str, float], ...] = (
    ("tinta", "panel", TEXTO_MINIMO),
    ("tinta", "lienzo", TEXTO_MINIMO),
    ("tinta", "blanco", TEXTO_MINIMO),
    ("tinta_sec", "panel", TEXTO_MINIMO),
    ("tinta_sec", "lienzo", TEXTO_MINIMO),
    ("panel", "tinta", TEXTO_MINIMO),
    ("verde", "verde_fondo", TEXTO_MINIMO),
    ("rojo", "rojo_fondo", TEXTO_MINIMO),
    ("rojo", "panel", TEXTO_MINIMO),
    ("indigo", "indigo_suave", TEXTO_MINIMO),
    ("indigo", "panel", TEXTO_MINIMO),
    ("tinta_ter", "panel", ATENUADO_MINIMO),
)


def canal(valor: int) -> float:
    escalado = valor / 255
    return (
        escalado / 12.92 if escalado <= 0.03928 else ((escalado + 0.055) / 1.055) ** 2.4
    )


def luminancia(color: str) -> float:
    rojo, verde, azul = (int(color[indice : indice + 2], 16) for indice in (1, 3, 5))
    return 0.2126 * canal(rojo) + 0.7152 * canal(verde) + 0.0722 * canal(azul)


def contraste(frente: str, fondo: str) -> float:
    claro, oscuro = sorted((luminancia(frente), luminancia(fondo)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


@pytest.mark.parametrize("frente, fondo, minimo", PARES)
def test_contraste_cumple_wcag(frente: str, fondo: str, minimo: float) -> None:
    valor_frente = getattr(COLORES, frente)
    valor_fondo = getattr(COLORES, fondo)
    assert contraste(valor_frente, valor_fondo) >= minimo
