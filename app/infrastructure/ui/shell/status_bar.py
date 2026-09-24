from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ALTO = 28
LADO_PUNTO = 8


class StatusBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("barra_estado")
        self.setFixedHeight(ALTO)

        self._punto = QFrame()
        self._punto.setFixedSize(LADO_PUNTO, LADO_PUNTO)
        self._punto.setStyleSheet(
            f"background-color: {COLORES.verde}; border-radius: {LADO_PUNTO // 2}px;"
        )

        self._actividad = QLabel("")
        self._actividad.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )

        self._progreso = QLabel("")
        self._progreso.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        self._progreso.setStyleSheet(f"color: {COLORES.tinta_sec};")

        izquierda = QHBoxLayout()
        izquierda.setSpacing(ESPACIADO.xs)
        izquierda.addWidget(self._punto)
        izquierda.addWidget(self._actividad)

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion.addLayout(izquierda)
        disposicion.addStretch(1)
        disposicion.addWidget(self._progreso)

    def establecer_actividad(self, texto: str) -> None:
        self._actividad.setText(texto)

    def establecer_progreso(self, procesados: int, total: int) -> None:
        self._progreso.setText(f"Procesados {procesados} de {total}")
