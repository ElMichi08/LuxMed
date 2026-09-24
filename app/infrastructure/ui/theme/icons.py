from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

ICONOS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

_cache: dict[tuple[str, str, int, float], QIcon] = {}


def icon_from_svg(
    path: Path, color: str, size: int, device_pixel_ratio: float = 1.0
) -> QIcon:
    render_size = max(1, round(size * device_pixel_ratio))
    renderer = QSvgRenderer(str(path))
    pixmap = QPixmap(render_size, render_size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return QIcon(pixmap)


def icono(nombre: str, color: str, tamano: int, relacion_pixeles: float = 1.0) -> QIcon:
    clave = (nombre, color, tamano, relacion_pixeles)
    if clave not in _cache:
        ruta = ICONOS_DIR / f"{nombre}.svg"
        _cache[clave] = icon_from_svg(ruta, color, tamano, relacion_pixeles)
    return _cache[clave]
