from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

ICONOS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
RELACION_PIXELES = 2.0

_pixmaps: dict[tuple[str, str, int], QPixmap] = {}


def pixmap_svg(nombre: str, color: str, tamano: int) -> QPixmap:
    clave = (nombre, color, tamano)
    if clave not in _pixmaps:
        lado = round(tamano * RELACION_PIXELES)
        pixmap = QPixmap(lado, lado)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        QSvgRenderer(str(ICONOS_DIR / f"{nombre}.svg")).render(painter)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()
        pixmap.setDevicePixelRatio(RELACION_PIXELES)
        _pixmaps[clave] = pixmap
    return _pixmaps[clave]


def icono(nombre: str, color: str, tamano: int = 16) -> QIcon:
    return QIcon(pixmap_svg(nombre, color, tamano))


def icono_con_estados(
    nombre: str, normal: str, activo: str, deshabilitado: str, tamano: int = 20
) -> QIcon:
    resultado = QIcon()
    resultado.addPixmap(pixmap_svg(nombre, normal, tamano), QIcon.Mode.Normal, QIcon.State.Off)
    resultado.addPixmap(pixmap_svg(nombre, activo, tamano), QIcon.Mode.Normal, QIcon.State.On)
    resultado.addPixmap(pixmap_svg(nombre, deshabilitado, tamano), QIcon.Mode.Disabled, QIcon.State.Off)
    return resultado


def tamano_icono(tamano: int) -> QSize:
    return QSize(tamano, tamano)
