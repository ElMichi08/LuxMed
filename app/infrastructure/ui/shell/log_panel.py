from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ALTO_CABECERA = 28
LADO_ICONO_ALTERNAR = 14


class LogPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel_bitacora")
        self._expandido = False

        self._boton_alternar = QToolButton()
        self._boton_alternar.setAutoRaise(True)
        self._boton_alternar.setIcon(
            icono("expand_less", COLORES.tinta, LADO_ICONO_ALTERNAR)
        )
        self._boton_alternar.clicked.connect(self.alternar)

        self._titulo = QLabel("BITÁCORA")
        self._titulo.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_bold)
        )

        self._separador = QLabel("|")
        self._separador.setStyleSheet(f"color: {COLORES.tinta_ter};")

        self._ultima_linea = QLabel("")
        self._ultima_linea.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base)
        )
        self._ultima_linea.setStyleSheet(f"color: {COLORES.tinta_sec};")

        cabecera = QWidget()
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion_cabecera = QHBoxLayout(cabecera)
        disposicion_cabecera.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion_cabecera.setSpacing(ESPACIADO.xs)
        disposicion_cabecera.addWidget(self._boton_alternar)
        disposicion_cabecera.addWidget(self._titulo)
        disposicion_cabecera.addWidget(self._separador)
        disposicion_cabecera.addWidget(self._ultima_linea, 1)

        self._lista = QListWidget()
        self._lista.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        self._lista.setFixedHeight(160)
        self._lista.hide()

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addWidget(self._lista)

    def alternar(self) -> None:
        self._expandido = not self._expandido
        self._lista.setVisible(self._expandido)
        nombre_icono = "expand_more" if self._expandido else "expand_less"
        self._boton_alternar.setIcon(
            icono(nombre_icono, COLORES.tinta, LADO_ICONO_ALTERNAR)
        )

    def agregar_linea(self, texto: str) -> None:
        self._ultima_linea.setText(texto)
        self._lista.addItem(texto)
        self._lista.scrollToBottom()
