from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from app.infrastructure.ui.theme.tokens import COLORES

PASO_GRADOS = 30
INTERVALO_MS = 60
ARCO_GRADOS = 270


class Spinner(QWidget):
    def __init__(self, diametro: int = 32, grosor: int = 3, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._diametro = diametro
        self._grosor = grosor
        self._angulo = 0
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(INTERVALO_MS)
        self._temporizador.timeout.connect(self._avanzar)
        self.setFixedSize(diametro, diametro)

    def sizeHint(self) -> QSize:
        return QSize(self._diametro, self._diametro)

    def iniciar(self) -> None:
        self._temporizador.start()
        self.show()

    def detener(self) -> None:
        self._temporizador.stop()
        self.hide()

    def _avanzar(self) -> None:
        self._angulo = (self._angulo + PASO_GRADOS) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margen = self._grosor / 2 + 1
        area = QRectF(margen, margen, self._diametro - 2 * margen, self._diametro - 2 * margen)
        painter.setPen(QPen(QColor(COLORES.filete_suave), self._grosor))
        painter.drawEllipse(area)
        pluma = QPen(QColor(COLORES.indigo), self._grosor)
        pluma.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pluma)
        painter.drawArc(area, -self._angulo * 16, ARCO_GRADOS // 3 * 16)
        painter.end()
