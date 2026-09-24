from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from app.infrastructure.ui.shell.navigation import Destino, Navigation
from app.infrastructure.ui.shell.rail import Rail
from app.infrastructure.ui.shell.top_bar import TopBar


def _pagina_vacia(texto: str) -> QWidget:
    pagina = QWidget()
    disposicion = QVBoxLayout(pagina)
    etiqueta = QLabel(texto)
    disposicion.addWidget(etiqueta)
    disposicion.addStretch(1)
    return pagina


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LuxMed")

        self.barra_superior = TopBar()
        self.riel = Rail()
        self.navegacion = Navigation()

        self.navegacion.registrar(Destino.LOTE, _pagina_vacia("Lote"))
        self.navegacion.registrar(Destino.ERRORES, _pagina_vacia("Errores"))
        self.navegacion.registrar(Destino.AJUSTES, _pagina_vacia("Ajustes"))

        self.riel.destino_elegido.connect(self._navegar)

        cuerpo = QWidget()
        disposicion_cuerpo = QHBoxLayout(cuerpo)
        disposicion_cuerpo.setContentsMargins(0, 0, 0, 0)
        disposicion_cuerpo.setSpacing(0)
        disposicion_cuerpo.addWidget(self.riel)
        disposicion_cuerpo.addWidget(self.navegacion, 1)

        contenedor = QWidget()
        disposicion_principal = QVBoxLayout(contenedor)
        disposicion_principal.setContentsMargins(0, 0, 0, 0)
        disposicion_principal.setSpacing(0)
        disposicion_principal.addWidget(self.barra_superior)
        disposicion_principal.addWidget(cuerpo, 1)

        self.setCentralWidget(contenedor)

    def _navegar(self, destino: str) -> None:
        self.navegacion.mostrar(Destino(destino))
