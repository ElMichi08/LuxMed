from __future__ import annotations

import math

from PyQt6.QtCore import QElapsedTimer, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from app.infrastructure.ui.theme.tokens import COLORES

INTERVALO_MS = 16
GRADOS_POR_SEGUNDO = 280
CICLO_ARCO_MS = 1400
ARCO_MINIMO = 30
ARCO_VARIABLE = 230


class Spinner(QWidget):
    def __init__(self, diametro: int = 32, grosor: int = 3, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._diametro = diametro
        self._grosor = grosor
        self._reloj = QElapsedTimer()
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(INTERVALO_MS)
        self._temporizador.setTimerType(Qt.TimerType.PreciseTimer)
        self._temporizador.timeout.connect(self.update)
        self.setFixedSize(diametro, diametro)

    def sizeHint(self) -> QSize:
        return QSize(self._diametro, self._diametro)

    def iniciar(self) -> None:
        if not self._temporizador.isActive():
            self._reloj.start()
            self._temporizador.start()
        self.show()

    def detener(self) -> None:
        self._temporizador.stop()
        self.hide()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        transcurrido = self._reloj.elapsed() if self._reloj.isValid() else 0
        angulo = (transcurrido * GRADOS_POR_SEGUNDO / 1000) % 360
        fase = (transcurrido % CICLO_ARCO_MS) / CICLO_ARCO_MS
        arco = ARCO_MINIMO + ARCO_VARIABLE * (0.5 - 0.5 * math.cos(2 * math.pi * fase))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margen = self._grosor / 2 + 1
        area = QRectF(margen, margen, self._diametro - 2 * margen, self._diametro - 2 * margen)
        painter.setPen(QPen(QColor(COLORES.filete_suave), self._grosor))
        painter.drawEllipse(area)
        pluma = QPen(QColor(COLORES.indigo), self._grosor)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pluma)
        painter.drawArc(area, round(-angulo * 16), round(-arco * 16))
        painter.end()
