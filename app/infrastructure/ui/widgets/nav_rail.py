from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QButtonGroup, QFrame, QToolButton

from app.infrastructure.ui.theme.fuentes import fuente_mono
from app.infrastructure.ui.theme.icons import icono_con_estados, tamano_icono
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA, TIPOGRAFIA
from app.infrastructure.ui.widgets.base import columna, etiqueta

ALTO_INSIGNIA = 14
ANCHO_MINIMO_INSIGNIA = 14


class RailItem(QToolButton):
    def __init__(self, clave: str, texto: str, nombre_icono: str) -> None:
        super().__init__()
        self.clave = clave
        self._insignia = 0
        self.setObjectName("item_riel")
        self.setText(texto)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIcon(
            icono_con_estados(nombre_icono, COLORES.tinta_sec, COLORES.indigo, COLORES.tinta_ter)
        )
        self.setIconSize(tamano_icono(20))
        self.setFixedSize(GEOMETRIA.riel_ancho - 1, GEOMETRIA.riel_item)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def establecer_insignia(self, cantidad: int) -> None:
        self._insignia = cantidad
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        super().paintEvent(event)
        if self._insignia <= 0:
            return
        texto = str(self._insignia) if self._insignia < 100 else "99+"
        painter = QPainter(self)
        painter.setFont(fuente_mono(TIPOGRAFIA.micro))
        ancho = max(ANCHO_MINIMO_INSIGNIA, painter.fontMetrics().horizontalAdvance(texto) + 6)
        area = QRectF(self.width() / 2 + 4, 6, ancho, ALTO_INSIGNIA)
        painter.fillRect(area, QColor(COLORES.rojo))
        painter.setPen(QColor(COLORES.blanco))
        painter.drawText(area, Qt.AlignmentFlag.AlignCenter, texto)
        painter.end()


class NavRail(QFrame):
    seleccionado = pyqtSignal(str)

    def __init__(self, version: str) -> None:
        super().__init__()
        self.setObjectName("riel")
        self.setFixedWidth(GEOMETRIA.riel_ancho)
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._items: dict[str, RailItem] = {}
        self._layout = columna()
        self._layout.addStretch(1)
        version_label = etiqueta(version, objeto="riel_version")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(version_label)
        self.setLayout(self._layout)

    def agregar(self, clave: str, texto: str, nombre_icono: str, habilitado: bool = True, ayuda: str = "") -> RailItem:
        item = RailItem(clave, texto, nombre_icono)
        item.setEnabled(habilitado)
        item.setToolTip(ayuda or texto)
        item.clicked.connect(lambda: self.seleccionado.emit(clave))
        self._grupo.addButton(item)
        self._items[clave] = item
        self._layout.insertWidget(len(self._items) - 1, item)
        return item

    def marcar(self, clave: str) -> None:
        self._items[clave].setChecked(True)

    def item(self, clave: str) -> RailItem:
        return self._items[clave]
