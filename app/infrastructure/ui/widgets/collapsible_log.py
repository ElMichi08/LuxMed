from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QPlainTextEdit, QToolButton, QWidget

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA
from app.infrastructure.ui.widgets.base import columna, etiqueta, fila

LINEAS_MAXIMAS = 500
ALTO_EXPANDIDO = 180


class CollapsibleLog(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._toggle = QToolButton()
        self._toggle.setObjectName("bitacora_toggle")
        self._toggle.setText("BITÁCORA")
        self._toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.clicked.connect(self._alternar)
        self._ultima = etiqueta("", "mono")
        cabecera = fila((8, 0, 12, 0), 8)
        cabecera.addWidget(self._toggle)
        cabecera.addWidget(etiqueta("|", "nota"))
        cabecera.addWidget(self._ultima, 1)
        barra = QFrame()
        barra.setObjectName("bitacora")
        barra.setFixedHeight(GEOMETRIA.barra_estado)
        barra.setLayout(cabecera)
        self._consola = QPlainTextEdit()
        self._consola.setReadOnly(True)
        self._consola.setMaximumBlockCount(LINEAS_MAXIMAS)
        self._consola.setFixedHeight(ALTO_EXPANDIDO)
        self._consola.hide()
        layout = columna()
        layout.addWidget(barra)
        layout.addWidget(self._consola)
        self.setLayout(layout)
        self._refrescar_icono()

    def agregar(self, texto_plano: str, resumen: str) -> None:
        self._consola.appendPlainText(texto_plano)
        self._ultima.setText(resumen)

    def limpiar(self) -> None:
        self._consola.clear()
        self._ultima.setText("")

    def _alternar(self) -> None:
        self._consola.setVisible(not self._consola.isVisible())
        self._refrescar_icono()

    def _refrescar_icono(self) -> None:
        nombre = "expand_more" if self._consola.isVisible() else "expand_less"
        self._toggle.setIcon(icono(nombre, COLORES.tinta, 14))
