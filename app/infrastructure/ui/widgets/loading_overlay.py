from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget

from app.infrastructure.ui.theme.tokens import COLORES
from app.infrastructure.ui.widgets.base import columna, etiqueta, marco
from app.infrastructure.ui.widgets.spinner import Spinner

ANCHO_TARJETA = 360


class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._spinner = Spinner(36, 3)
        self._titulo = etiqueta("", "titulo_seccion")
        self._detalle = etiqueta("", "ayuda")
        self._detalle.setWordWrap(True)
        for texto in (self._titulo, self._detalle):
            texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contenido = columna((24, 24, 24, 24), 10)
        contenido.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignHCenter)
        contenido.addWidget(self._titulo)
        contenido.addWidget(self._detalle)
        tarjeta = marco("tarjeta_carga", contenido)
        tarjeta.setFixedWidth(ANCHO_TARJETA)
        layout = columna()
        layout.addStretch(1)
        layout.addWidget(tarjeta, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        self.setLayout(layout)
        parent.installEventFilter(self)
        self.hide()

    @property
    def activo(self) -> bool:
        return not self.isHidden()

    def mostrar(self, titulo: str, detalle: str = "") -> None:
        self._titulo.setText(titulo)
        self._detalle.setText(detalle)
        self._detalle.setVisible(bool(detalle))
        self._ajustar()
        self.raise_()
        self.show()
        self._spinner.iniciar()
        self.setFocus()

    def ocultar(self) -> None:
        self._spinner.detener()
        self.hide()

    def eventFilter(self, objeto: QObject | None, evento: QEvent | None) -> bool:
        if evento is not None and evento.type() == QEvent.Type.Resize:
            self._ajustar()
        return False

    def _ajustar(self) -> None:
        padre = self.parentWidget()
        if padre is not None:
            self.resize(padre.size())

    def paintEvent(self, event: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(COLORES.velo))
        painter.end()
