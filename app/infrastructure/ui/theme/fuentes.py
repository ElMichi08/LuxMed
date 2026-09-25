from __future__ import annotations

from PyQt6.QtGui import QFont

from app.infrastructure.ui.theme.tokens import TIPOGRAFIA


def fuente(
    familia: str = TIPOGRAFIA.sans,
    tamano: int = TIPOGRAFIA.base,
    peso: QFont.Weight = QFont.Weight.Normal,
) -> QFont:
    resultado = QFont(familia)
    resultado.setPixelSize(tamano)
    resultado.setWeight(peso)
    return resultado


def fuente_mono(tamano: int = TIPOGRAFIA.base, peso: QFont.Weight = QFont.Weight.Normal) -> QFont:
    return fuente(TIPOGRAFIA.mono, tamano, peso)
