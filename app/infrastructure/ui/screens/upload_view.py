from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA
from app.infrastructure.ui.widgets.card import Card
from app.infrastructure.ui.widgets.dropzone import DropZone

ANCHO_CONTENIDO = 720

TEXTOS_INFORMATIVOS = (
    "Columnas leídas: nombre, cédula, fecha de nacimiento, tipo de seguro, código de clínica y establecimiento.",
    "Cédula válida: exactamente 10 dígitos numéricos. Las demás se descartan y no se consultan.",
    "La edad se calcula con la fecha de nacimiento al cargar el archivo.",
)


class UploadView(QWidget):
    archivo_elegido = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dropzone = DropZone()
        self._dropzone.archivo_elegido.connect(self.archivo_elegido.emit)

        self._etiqueta_error = QLabel("")
        self._etiqueta_error.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        self._etiqueta_error.setStyleSheet(f"color: {COLORES.rojo};")
        self._etiqueta_error.hide()

        tarjeta = Card("Qué se lee del archivo")
        for texto in TEXTOS_INFORMATIVOS:
            fila = QLabel(f"·  {texto}")
            fila.setWordWrap(True)
            fila.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo))
            tarjeta.agregar(fila)

        contenedor = QWidget()
        contenedor.setFixedWidth(ANCHO_CONTENIDO)
        disposicion_contenedor = QVBoxLayout(contenedor)
        disposicion_contenedor.setSpacing(ESPACIADO.xl)
        disposicion_contenedor.addWidget(self._dropzone)
        disposicion_contenedor.addWidget(self._etiqueta_error)
        disposicion_contenedor.addWidget(tarjeta)

        disposicion = QVBoxLayout(self)
        disposicion.addStretch(1)
        fila_central = QHBoxLayout()
        fila_central.addStretch(1)
        fila_central.addWidget(contenedor)
        fila_central.addStretch(1)
        disposicion.addLayout(fila_central)
        disposicion.addStretch(1)

    def establecer_cargando(self, mensaje: str | None) -> None:
        self._dropzone.establecer_cargando(mensaje)

    def mostrar_error(self, mensaje: str) -> None:
        self._etiqueta_error.setText(mensaje)
        self._etiqueta_error.show()

    def limpiar_error(self) -> None:
        self._etiqueta_error.hide()
