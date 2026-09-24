from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

TITULO_INICIAL = "Arrastra aquí el listado de pacientes"
SUBTITULO_INICIAL = "Archivos .xlsx"


class DropZone(QFrame):
    archivo_elegido = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropzone")
        self.setProperty("arrastrando", False)
        self.setAcceptDrops(True)

        self._icono = QLabel()
        self._icono.setPixmap(icono("table_view", COLORES.tinta_sec, 48).pixmap(48, 48))
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._titulo = QLabel(TITULO_INICIAL)
        self._titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitulo = QLabel(SUBTITULO_INICIAL)
        self._subtitulo.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_subtitulo)
        )
        self._subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        self._subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._boton_elegir = QPushButton("Elegir archivo")
        self._boton_elegir.setProperty("variante", "secundario")
        self._boton_elegir.setIcon(icono("upload_file", COLORES.tinta_sec, 16))
        self._boton_elegir.clicked.connect(self._elegir_archivo)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(
            ESPACIADO.xxxl, ESPACIADO.xxl, ESPACIADO.xxxl, ESPACIADO.xxl
        )
        disposicion.setSpacing(ESPACIADO.sm)
        disposicion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disposicion.addWidget(self._icono)
        disposicion.addWidget(self._titulo)
        disposicion.addWidget(self._subtitulo)
        disposicion.addSpacing(ESPACIADO.md)
        disposicion.addWidget(self._boton_elegir, 0, Qt.AlignmentFlag.AlignCenter)

    def establecer_cargando(self, mensaje: str | None) -> None:
        cargando = mensaje is not None
        self._boton_elegir.setEnabled(not cargando)
        self.setEnabled(not cargando)
        self._titulo.setText(mensaje if mensaje else TITULO_INICIAL)
        self._subtitulo.setVisible(not cargando)

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        if event is not None and self.isEnabled() and self._tiene_xlsx(event):
            event.acceptProposedAction()
            self.setProperty("arrastrando", True)
            repolish(self)
        elif event is not None:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent | None) -> None:
        self.setProperty("arrastrando", False)
        repolish(self)

    def dropEvent(self, event: QDropEvent | None) -> None:
        self.setProperty("arrastrando", False)
        repolish(self)
        if event is None or not self.isEnabled():
            return
        ruta = self._primera_ruta_xlsx(event)
        if ruta is not None:
            event.acceptProposedAction()
            self.archivo_elegido.emit(ruta)

    def _elegir_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir listado de pacientes", "", "Excel (*.xlsx)"
        )
        if ruta:
            self.archivo_elegido.emit(ruta)

    def _tiene_xlsx(self, event: QDragEnterEvent) -> bool:
        return self._primera_ruta_xlsx(event) is not None

    def _primera_ruta_xlsx(self, event: QDragEnterEvent | QDropEvent) -> str | None:
        datos_mime = event.mimeData()
        if datos_mime is None or not datos_mime.hasUrls():
            return None
        for url in datos_mime.urls():
            ruta_local = url.toLocalFile()
            if ruta_local and Path(ruta_local).suffix.lower() == ".xlsx":
                return ruta_local
        return None
