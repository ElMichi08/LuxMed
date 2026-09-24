from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ALTO = 48
LADO_MONOGRAMA = 24
LADO_AVATAR = 28


class TopBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("barra_superior")
        self.setFixedHeight(ALTO)

        self._monograma = QLabel("L")
        self._monograma.setObjectName("monograma")
        self._monograma.setFixedSize(LADO_MONOGRAMA, LADO_MONOGRAMA)
        self._monograma.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._marca = QLabel("LuxMed")
        self._marca.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )

        self._separador = QFrame()
        self._separador.setFixedSize(1, 16)
        self._separador.setStyleSheet(f"background-color: {COLORES.filete};")

        self._estado = QLabel("Sin lote activo")
        self._estado.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        self._estado.setStyleSheet(f"color: {COLORES.tinta_sec};")

        self._chip = QLabel("")
        self._chip.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self._chip.hide()

        self._usuario = QLabel("")
        self._usuario.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        self._usuario.setStyleSheet(f"color: {COLORES.tinta_sec};")

        self._avatar = QLabel("")
        self._avatar.setObjectName("avatar")
        self._avatar.setFixedSize(LADO_AVATAR, LADO_AVATAR)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_chip, TIPOGRAFIA.peso_bold)
        )

        izquierda = QHBoxLayout()
        izquierda.setSpacing(ESPACIADO.md)
        izquierda.addWidget(self._monograma)
        izquierda.addWidget(self._marca)
        izquierda.addWidget(self._separador)
        izquierda.addWidget(self._estado)
        izquierda.addWidget(self._chip)

        derecha = QHBoxLayout()
        derecha.setSpacing(ESPACIADO.sm)
        derecha.addWidget(self._usuario)
        derecha.addWidget(self._avatar)

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion.addLayout(izquierda)
        disposicion.addStretch(1)
        disposicion.addLayout(derecha)

    def establecer_sesion(self, usuario: str, iniciales: str) -> None:
        self._usuario.setText(usuario)
        self._avatar.setText(iniciales)

    def establecer_sin_lote(self) -> None:
        self._estado.setText("Sin lote activo")
        self._chip.hide()

    def establecer_lote(
        self, texto: str, texto_chip: str | None = None, tono_chip: str = "proceso"
    ) -> None:
        self._estado.setText(texto)
        if not texto_chip:
            self._chip.hide()
            return
        self._chip.setText(texto_chip)
        self._chip.setProperty("tono", tono_chip)
        repolish(self._chip)
        self._chip.show()
