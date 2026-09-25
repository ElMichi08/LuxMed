from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PyQt6.QtWidgets import QFileDialog, QFrame, QPushButton

from app.infrastructure.ui.theme.icons import pixmap_svg
from app.infrastructure.ui.theme.tokens import COLORES
from app.infrastructure.ui.widgets.base import (
    boton,
    columna,
    establecer_propiedad,
    etiqueta,
)

EXTENSION_PERMITIDA = ".xlsx"


def ruta_excel(evento: QDragEnterEvent | QDropEvent) -> str | None:
    mime = evento.mimeData()
    if mime is None or not mime.hasUrls():
        return None
    rutas = [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]
    if len(rutas) != 1 or Path(rutas[0]).suffix.lower() != EXTENSION_PERMITIDA:
        return None
    return rutas[0]


class Dropzone(QFrame):
    archivo_elegido = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        imagen = etiqueta()
        imagen.setPixmap(pixmap_svg("table_view", COLORES.tinta_sec, 48))
        imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo = etiqueta("Arrastra aquí el listado de pacientes", "titulo")
        tipo = etiqueta("Archivos .xlsx", "mono")
        self._boton = boton("Elegir archivo", nombre_icono="upload_file")
        self._boton.clicked.connect(self._elegir)
        self._error = etiqueta("", "error")
        self._error.setWordWrap(True)
        self._error.hide()
        layout = columna((32, 48, 32, 48), 4)
        for widget in (imagen, titulo, tipo):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(widget)
        layout.addSpacing(20)
        layout.addWidget(self._boton, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(8)
        layout.addWidget(self._error, 0, Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)

    @property
    def boton(self) -> QPushButton:
        return self._boton

    def mostrar_error(self, mensaje: str) -> None:
        self._error.setText(mensaje)
        self._error.setVisible(bool(mensaje))

    def _elegir(self) -> None:
        ruta, _filtro = QFileDialog.getOpenFileName(
            self, "Elegir listado de pacientes", "", "Libros de Excel (*.xlsx)"
        )
        if ruta:
            self._emitir(ruta)

    def _emitir(self, ruta: str) -> None:
        self.mostrar_error("")
        self.archivo_elegido.emit(ruta)

    def dragEnterEvent(self, evento: QDragEnterEvent | None) -> None:
        if evento is not None and self.isEnabled() and ruta_excel(evento) is not None:
            evento.acceptProposedAction()
            establecer_propiedad(self, "arrastrando", True)

    def dragLeaveEvent(self, evento: QDragLeaveEvent | None) -> None:
        establecer_propiedad(self, "arrastrando", False)

    def dropEvent(self, evento: QDropEvent | None) -> None:
        establecer_propiedad(self, "arrastrando", False)
        if evento is None:
            return
        ruta = ruta_excel(evento)
        if ruta is not None and self.isEnabled():
            evento.acceptProposedAction()
            self._emitir(ruta)
