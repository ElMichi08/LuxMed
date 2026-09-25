from __future__ import annotations

import ctypes
import sys

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from app.infrastructure.ui.theme.tokens import COLORES, TIPOGRAFIA

LETRA = "L"
PROPORCION_LETRA = 0.5
PROPORCION_LETRA_PEQUENA = 0.7
LADO_PEQUENO = 20
TAMANOS_ICONO = (16, 20, 24, 32, 40, 48, 64, 128, 256)
ID_APLICACION_WINDOWS = "LuxMed.Escritorio"


def pixmap_logo(lado: int, relacion_pixeles: float = 1.0) -> QPixmap:
    fisico = round(lado * relacion_pixeles)
    pixmap = QPixmap(fisico, fisico)
    pixmap.fill(QColor(COLORES.tinta))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    fuente = QFont(TIPOGRAFIA.sans)
    proporcion = PROPORCION_LETRA_PEQUENA if lado <= LADO_PEQUENO else PROPORCION_LETRA
    fuente.setPixelSize(max(1, round(fisico * proporcion)))
    fuente.setWeight(QFont.Weight.Bold)
    painter.setFont(fuente)
    painter.setPen(QColor(COLORES.panel))
    painter.drawText(QRectF(0, 0, fisico, fisico), Qt.AlignmentFlag.AlignCenter, LETRA)
    painter.end()
    pixmap.setDevicePixelRatio(relacion_pixeles)
    return pixmap


def icono_app() -> QIcon:
    icono = QIcon()
    for lado in TAMANOS_ICONO:
        icono.addPixmap(pixmap_logo(lado))
    return icono


def registrar_id_barra_de_tareas() -> None:
    if sys.platform != "win32":
        return
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ID_APLICACION_WINDOWS)
