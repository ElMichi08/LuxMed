from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA


class Card(QFrame):
    def __init__(self, titulo: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tarjeta")

        self._disposicion = QVBoxLayout(self)
        self._disposicion.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg
        )
        self._disposicion.setSpacing(ESPACIADO.md)

        if titulo:
            etiqueta = QLabel(titulo.upper())
            etiqueta.setFont(
                QFont(
                    TIPOGRAFIA.familia_narrow,
                    TIPOGRAFIA.tamano_etiqueta,
                    TIPOGRAFIA.peso_semibold,
                )
            )
            etiqueta.setStyleSheet(f"color: {COLORES.tinta_sec}; letter-spacing: 1px;")
            self._disposicion.addWidget(etiqueta)

    def agregar(self, widget: QWidget) -> None:
        self._disposicion.addWidget(widget)

    def disposicion_contenido(self) -> QVBoxLayout:
        return self._disposicion
