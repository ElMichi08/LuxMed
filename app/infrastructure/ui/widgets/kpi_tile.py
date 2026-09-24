from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA


class KpiTile(QFrame):
    def __init__(self, etiqueta: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("kpi_tile")
        self.setProperty("activo", False)

        self._etiqueta = QLabel(etiqueta.upper())
        self._etiqueta.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self._etiqueta.setStyleSheet(
            f"color: {COLORES.tinta_sec}; letter-spacing: 1px;"
        )

        self._valor = QLabel("0")
        self._valor.setFont(
            QFont(
                TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_cifra, TIPOGRAFIA.peso_bold
            )
        )
        self._valor.setStyleSheet(f"color: {COLORES.tinta};")

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.sm, ESPACIADO.lg, ESPACIADO.sm
        )
        disposicion.setSpacing(0)
        disposicion.addWidget(self._etiqueta)
        disposicion.addWidget(self._valor)

    def establecer_valor(self, valor: int) -> None:
        self._valor.setText(str(valor))

    def establecer_color_valor(self, color: str) -> None:
        self._valor.setStyleSheet(f"color: {color};")

    def establecer_activo(self, activo: bool) -> None:
        self.setProperty("activo", activo)
        repolish(self)
        color_etiqueta = COLORES.indigo if activo else COLORES.tinta_sec
        self._etiqueta.setStyleSheet(f"color: {color_etiqueta}; letter-spacing: 1px;")
