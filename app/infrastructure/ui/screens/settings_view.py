from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, GEOMETRIA, TIPOGRAFIA

ANCHO_MAXIMO_PANEL = 760
ALTO_CAMPO = 36


class SettingsView(QWidget):
    carpeta_elegida = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._carpeta = Path()

        titulo = QLabel("Ajustes")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_semibold,
            )
        )

        subtitulo_seccion = QLabel("Carpeta de salida")
        subtitulo_seccion.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )

        texto_ayuda = QLabel(
            "Aquí se guardan el Excel limpio, el Excel auditado y los PDF consolidados de cada lote."
        )
        texto_ayuda.setWordWrap(True)
        texto_ayuda.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        texto_ayuda.setStyleSheet(f"color: {COLORES.tinta_sec};")

        self._campo_carpeta = QLineEdit()
        self._campo_carpeta.setReadOnly(True)
        self._campo_carpeta.setFixedHeight(ALTO_CAMPO)
        self._campo_carpeta.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_medio,
            )
        )
        self._campo_carpeta.setStyleSheet(
            f"background-color: {COLORES.lienzo}; color: {COLORES.tinta}; "
            f"border: 1px solid {COLORES.filete}; border-radius: {GEOMETRIA.radio}px; "
            f"padding: 0 {ESPACIADO.md}px;"
        )

        boton_cambiar = QPushButton("Cambiar…")
        boton_cambiar.setProperty("variante", "secundario")
        boton_cambiar.setFixedHeight(ALTO_CAMPO)
        boton_cambiar.setIcon(icono("folder_open", COLORES.tinta_sec, 16))
        boton_cambiar.clicked.connect(self._al_cambiar_carpeta)

        fila_campo = QHBoxLayout()
        fila_campo.setSpacing(ESPACIADO.md)
        fila_campo.addWidget(self._campo_carpeta, 1)
        fila_campo.addWidget(boton_cambiar)

        disposicion_seccion = QVBoxLayout()
        disposicion_seccion.setSpacing(0)
        disposicion_seccion.addWidget(subtitulo_seccion)
        disposicion_seccion.addSpacing(ESPACIADO.xs)
        disposicion_seccion.addWidget(texto_ayuda)
        disposicion_seccion.addSpacing(ESPACIADO.lg)
        disposicion_seccion.addLayout(fila_campo)

        panel = QFrame()
        panel.setObjectName("tarjeta")
        panel.setMaximumWidth(ANCHO_MAXIMO_PANEL)
        disposicion_panel = QVBoxLayout(panel)
        disposicion_panel.setContentsMargins(
            ESPACIADO.xxl, ESPACIADO.xxl, ESPACIADO.xxl, ESPACIADO.xxl
        )
        disposicion_panel.addLayout(disposicion_seccion)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(
            ESPACIADO.xxl, ESPACIADO.xl, ESPACIADO.xxl, ESPACIADO.xxl
        )
        disposicion.setSpacing(ESPACIADO.xl)
        disposicion.addWidget(titulo)
        disposicion.addWidget(panel)
        disposicion.addStretch(1)

    def mostrar_carpeta(self, carpeta: Path) -> None:
        self._carpeta = carpeta
        self._campo_carpeta.setText(str(carpeta))

    def _al_cambiar_carpeta(self) -> None:
        nueva = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta de salida", str(self._carpeta)
        )
        if nueva:
            self.carpeta_elegida.emit(Path(nueva))
