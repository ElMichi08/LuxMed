from __future__ import annotations

from typing import TypeVar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono, tamano_icono
from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA

LayoutCaja = TypeVar("LayoutCaja", bound=QBoxLayout)


def establecer_propiedad(widget: QWidget, nombre: str, valor: object) -> None:
    if widget.property(nombre) == valor:
        return
    widget.setProperty(nombre, valor)
    repolish(widget)


def etiqueta(texto: str = "", rol: str | None = None, objeto: str | None = None) -> QLabel:
    resultado = QLabel(texto)
    if rol is not None:
        resultado.setProperty("rol", rol)
    if objeto is not None:
        resultado.setObjectName(objeto)
    return resultado


def boton(
    texto: str,
    variante: str = "secundario",
    nombre_icono: str | None = None,
    alto: int = GEOMETRIA.boton,
) -> QPushButton:
    resultado = QPushButton(texto)
    resultado.setProperty("variante", variante)
    resultado.setFixedHeight(alto)
    resultado.setCursor(Qt.CursorShape.PointingHandCursor)
    if nombre_icono is not None:
        color = COLORES.blanco if variante == "primario" else COLORES.tinta_sec
        resultado.setIcon(icono(nombre_icono, color, 16))
        resultado.setIconSize(tamano_icono(16))
    return resultado


def marco(objeto: str, layout: QLayout | None = None) -> QFrame:
    resultado = QFrame()
    resultado.setObjectName(objeto)
    if layout is not None:
        resultado.setLayout(layout)
    return resultado


def fila(margenes: tuple[int, int, int, int] = (0, 0, 0, 0), espacio: int = 0) -> QHBoxLayout:
    return _configurar(QHBoxLayout(), margenes, espacio)


def columna(margenes: tuple[int, int, int, int] = (0, 0, 0, 0), espacio: int = 0) -> QVBoxLayout:
    return _configurar(QVBoxLayout(), margenes, espacio)


def separador_vertical(alto: int = 16) -> QFrame:
    resultado = QFrame()
    resultado.setObjectName("separador_vertical")
    resultado.setFixedSize(1, alto)
    return resultado


def _configurar(layout: LayoutCaja, margenes: tuple[int, int, int, int], espacio: int) -> LayoutCaja:
    layout.setContentsMargins(*margenes)
    layout.setSpacing(espacio)
    return layout
