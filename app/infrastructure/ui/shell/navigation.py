from __future__ import annotations

from enum import StrEnum

from PyQt6.QtWidgets import QStackedWidget, QWidget


class Destino(StrEnum):
    LOTE = "lote"
    ERRORES = "errores"
    AJUSTES = "ajustes"


class Navigation(QStackedWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._paginas: dict[Destino, QWidget] = {}

    def registrar(self, destino: Destino, pagina: QWidget) -> None:
        self._paginas[destino] = pagina
        self.addWidget(pagina)

    def mostrar(self, destino: Destino) -> None:
        pagina = self._paginas.get(destino)
        if pagina is not None:
            self.setCurrentWidget(pagina)

    def pagina_actual(self) -> Destino | None:
        for destino, pagina in self._paginas.items():
            if pagina is self.currentWidget():
                return destino
        return None
