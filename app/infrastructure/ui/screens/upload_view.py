from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from app.infrastructure.ui.widgets.base import columna, etiqueta
from app.infrastructure.ui.widgets.dropzone import Dropzone
from app.infrastructure.ui.widgets.paneles import Panel, lista_de_vinetas

ANCHO_CONTENIDO = 720

REGLAS_LECTURA = (
    "Columnas leídas: nombre, cédula, fecha de nacimiento, tipo de seguro, fecha de atención y establecimiento.",
    "Cédula válida: exactamente 10 dígitos numéricos. Las demás se descartan y no se consultan.",
    "La edad se calcula con la fecha de nacimiento al cargar el archivo.",
)


class UploadView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lienzo")
        self.dropzone = Dropzone()
        reglas = Panel(espacio=10)
        reglas.contenido.addWidget(etiqueta("QUÉ SE LEE DEL ARCHIVO", "etiqueta"))
        reglas.contenido.addWidget(lista_de_vinetas(REGLAS_LECTURA, rol="ayuda"))
        contenido = QWidget()
        contenido.setFixedWidth(ANCHO_CONTENIDO)
        interno = columna(espacio=24)
        interno.addWidget(self.dropzone)
        interno.addWidget(reglas)
        contenido.setLayout(interno)
        layout = columna((32, 32, 32, 32))
        layout.addStretch(1)
        layout.addWidget(contenido, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        self.setLayout(layout)
