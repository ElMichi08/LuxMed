from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QWidget

from app.infrastructure.ui.widgets.base import columna, etiqueta, fila


class Panel(QFrame):
    def __init__(self, margenes: tuple[int, int, int, int] = (24, 24, 24, 24), espacio: int = 12) -> None:
        super().__init__()
        self.setObjectName("panel")
        self.contenido = columna(margenes, espacio)
        self.setLayout(self.contenido)


class NoticeBanner(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("banner")
        self._texto = etiqueta("")
        self._texto.setWordWrap(True)
        layout = fila((12, 6, 12, 6))
        layout.addWidget(self._texto)
        self.setLayout(layout)

    def mostrar(self, texto: str) -> None:
        self._texto.setText(texto)
        self.setVisible(bool(texto))


class ScreenHeader(QWidget):
    def __init__(self, titulo: str, acciones: Sequence[QWidget] = ()) -> None:
        super().__init__()
        self._titulo = etiqueta(titulo, "titulo")
        self._subtitulo = etiqueta("", "subtitulo")
        self._subtitulo.setWordWrap(True)
        textos = columna(espacio=2)
        textos.addWidget(self._titulo)
        textos.addWidget(self._subtitulo)
        layout = fila(espacio=12)
        layout.addLayout(textos, 1)
        for accion in acciones:
            layout.addWidget(accion, 0, Qt.AlignmentFlag.AlignVCenter)
        self.setLayout(layout)

    @property
    def subtitulo(self) -> QLabel:
        return self._subtitulo

    def establecer_subtitulo(self, texto: str) -> None:
        self._subtitulo.setText(texto)


def lista_de_vinetas(lineas: Sequence[str], rol: str = "ayuda") -> QWidget:
    contenedor = QWidget()
    layout = columna(espacio=6)
    for linea in lineas:
        texto = etiqueta(f"•  {linea}", rol)
        texto.setWordWrap(True)
        texto.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(texto)
    contenedor.setLayout(layout)
    return contenedor
