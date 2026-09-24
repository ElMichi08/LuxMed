from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QResizeEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA, TIPOGRAFIA

ALTO_ITEM = 60
LADO_INSIGNIA = 14


def configurar_boton_riel(boton: QToolButton) -> None:
    boton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    boton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    boton.setFixedHeight(ALTO_ITEM)
    boton.setFont(
        QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_chip, TIPOGRAFIA.peso_medio)
    )


class ItemRiel(QToolButton):
    def __init__(
        self, nombre_icono: str, etiqueta: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._nombre_icono = nombre_icono
        self.setObjectName("item_riel")
        configurar_boton_riel(self)
        self.setText(etiqueta)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._contador = 0
        self._insignia = QLabel(self)
        self._insignia.setObjectName("riel_insignia")
        self._insignia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._insignia.setFixedSize(LADO_INSIGNIA, LADO_INSIGNIA)
        self._insignia.hide()
        self._actualizar_icono()
        self.toggled.connect(self._actualizar_icono)

    def establecer_contador(self, cantidad: int) -> None:
        self._contador = max(cantidad, 0)
        if self._contador <= 0:
            self._insignia.hide()
            return
        self._insignia.setText(str(self._contador) if self._contador < 100 else "99+")
        self._insignia.show()
        self._posicionar_insignia()

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self._posicionar_insignia()

    def _posicionar_insignia(self) -> None:
        if self._contador <= 0:
            return
        self._insignia.move(self.width() // 2 + 8, 6)

    def _actualizar_icono(self) -> None:
        color = COLORES.indigo if self.isChecked() else COLORES.tinta_sec
        self.setIcon(icono(self._nombre_icono, color, 20))


class Rail(QFrame):
    destino_elegido = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("riel")
        self.setFixedWidth(GEOMETRIA.riel_ancho)

        self.boton_lote = ItemRiel("dataset", "Lote")
        self.boton_errores = ItemRiel("warning", "Errores")
        self.boton_ajustes = ItemRiel("settings", "Ajustes")

        self.boton_historial = QToolButton()
        self.boton_historial.setObjectName("item_riel_historial")
        configurar_boton_riel(self.boton_historial)
        self.boton_historial.setText("Historial")
        self.boton_historial.setIcon(icono("history", COLORES.tinta_ter, 20))
        self.boton_historial.setEnabled(False)
        self.boton_historial.setCursor(Qt.CursorShape.ForbiddenCursor)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._grupo.addButton(self.boton_lote)
        self._grupo.addButton(self.boton_errores)
        self._grupo.addButton(self.boton_ajustes)

        self.boton_lote.setChecked(True)
        self.boton_lote.toggled.connect(self._al_marcar_lote)
        self.boton_errores.toggled.connect(self._al_marcar_errores)
        self.boton_ajustes.toggled.connect(self._al_marcar_ajustes)

        version = QLabel("v2.4")
        version.setObjectName("riel_version")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(self.boton_lote)
        disposicion.addWidget(self.boton_errores)
        disposicion.addWidget(self.boton_historial)
        disposicion.addWidget(self.boton_ajustes)
        disposicion.addStretch(1)
        disposicion.addWidget(version)

    def _al_marcar_lote(self, marcado: bool) -> None:
        if marcado:
            self.destino_elegido.emit("lote")

    def _al_marcar_errores(self, marcado: bool) -> None:
        if marcado:
            self.destino_elegido.emit("errores")

    def _al_marcar_ajustes(self, marcado: bool) -> None:
        if marcado:
            self.destino_elegido.emit("ajustes")
