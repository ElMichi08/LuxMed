from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from app.application.dto import EstadoPaso, RutaPortales
from app.infrastructure.ui.theme.tokens import COLORES

RADIO_PUNTO = 4
ANCHO = 56
ALTO = 14

ETIQUETA_PASO = {
    EstadoPaso.PENDIENTE: "Pendiente",
    EstadoPaso.EN_CURSO: "En curso",
    EstadoPaso.RESUELTO: "Hecho",
    EstadoPaso.OMITIDO: "Omitido",
    EstadoPaso.FALLIDO: "Fallido",
}


def texto_tooltip_ruta(ruta: RutaPortales) -> str:
    pasos = (ruta.p1, ruta.p2, ruta.p3)
    return " · ".join(
        f"P{indice + 1}: {ETIQUETA_PASO[paso]}" for indice, paso in enumerate(pasos)
    )


def pintar_ruta(painter: QPainter, rect: QRectF, ruta: RutaPortales) -> None:
    pasos = (ruta.p1, ruta.p2, ruta.p3)
    centro_y = rect.center().y()
    ancho_util = rect.width() - RADIO_PUNTO * 2
    centros_x = [
        rect.left() + RADIO_PUNTO + indice * (ancho_util / 2) for indice in range(3)
    ]

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    for indice in range(2):
        omitido = EstadoPaso.OMITIDO in (pasos[indice], pasos[indice + 1])
        pluma_linea = QPen(QColor(COLORES.filete), 1)
        if omitido:
            pluma_linea.setDashPattern([1, 1])
        painter.setPen(pluma_linea)
        painter.drawLine(
            int(centros_x[indice] + RADIO_PUNTO),
            int(centro_y),
            int(centros_x[indice + 1] - RADIO_PUNTO),
            int(centro_y),
        )

    for indice, paso in enumerate(pasos):
        _dibujar_paso(painter, centros_x[indice], centro_y, paso)

    painter.restore()


def _dibujar_paso(
    painter: QPainter, centro_x: float, centro_y: float, paso: EstadoPaso
) -> None:
    rectangulo = QRectF(
        centro_x - RADIO_PUNTO, centro_y - RADIO_PUNTO, RADIO_PUNTO * 2, RADIO_PUNTO * 2
    )
    if paso is EstadoPaso.RESUELTO:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORES.verde))
        painter.drawEllipse(rectangulo)
    elif paso is EstadoPaso.EN_CURSO:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORES.indigo))
        painter.drawEllipse(rectangulo)
    elif paso is EstadoPaso.OMITIDO:
        pluma = QPen(QColor(COLORES.tinta_ter), 1)
        pluma.setDashPattern([1, 1])
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(pluma)
        painter.drawEllipse(rectangulo)
    elif paso is EstadoPaso.FALLIDO:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORES.rojo))
        painter.drawEllipse(rectangulo)
        margen = RADIO_PUNTO * 0.45
        painter.setPen(QPen(QColor(COLORES.blanco), 1))
        painter.drawLine(
            QPointF(centro_x - margen, centro_y - margen),
            QPointF(centro_x + margen, centro_y + margen),
        )
        painter.drawLine(
            QPointF(centro_x - margen, centro_y + margen),
            QPointF(centro_x + margen, centro_y - margen),
        )
    else:
        painter.setBrush(QColor(COLORES.blanco))
        painter.setPen(QPen(QColor(COLORES.filete), 1))
        painter.drawEllipse(rectangulo)


class RouteDots(QWidget):
    def __init__(
        self, ruta: RutaPortales | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._ruta = ruta
        self.setFixedSize(ANCHO, ALTO)
        if ruta is not None:
            self.setToolTip(texto_tooltip_ruta(ruta))

    def establecer_ruta(self, ruta: RutaPortales) -> None:
        self._ruta = ruta
        self.setToolTip(texto_tooltip_ruta(ruta))
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(ANCHO, ALTO)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        if self._ruta is None:
            return
        painter = QPainter(self)
        pintar_ruta(painter, QRectF(0, 0, self.width(), self.height()), self._ruta)
        painter.end()
