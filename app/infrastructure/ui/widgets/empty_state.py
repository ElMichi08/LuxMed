from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

LADO_ICONO = 48


class EmptyState(QWidget):
    def __init__(
        self,
        nombre_icono: str,
        titulo: str,
        subtitulo: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._icono = QLabel()
        self._icono.setPixmap(
            icono(nombre_icono, COLORES.tinta_ter, LADO_ICONO).pixmap(
                LADO_ICONO, LADO_ICONO
            )
        )
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._titulo = QLabel(titulo)
        self._titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitulo = QLabel(subtitulo)
        self._subtitulo.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo)
        )
        self._subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        self._subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitulo.setVisible(bool(subtitulo))

        disposicion = QVBoxLayout(self)
        disposicion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disposicion.setSpacing(ESPACIADO.sm)
        disposicion.addWidget(self._icono)
        disposicion.addWidget(self._titulo)
        disposicion.addWidget(self._subtitulo)

    def establecer_texto(self, titulo: str, subtitulo: str = "") -> None:
        self._titulo.setText(titulo)
        self._subtitulo.setText(subtitulo)
        self._subtitulo.setVisible(bool(subtitulo))
