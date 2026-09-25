from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QModelIndex, QObject, QSortFilterProxyModel

from app.infrastructure.ui.models.columnas import ModeloColumnas

Predicado = Callable[[object], bool]


class FiltroProxy(QSortFilterProxyModel):
    def __init__(self, texto_busqueda: Callable[[object], str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._texto_busqueda = texto_busqueda
        self._predicado: Predicado | None = None
        self._texto = ""

    def establecer_predicado(self, predicado: Predicado | None) -> None:
        self._predicado = predicado
        self.invalidateFilter()

    def establecer_texto(self, texto: str) -> None:
        self._texto = texto.strip().casefold()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        modelo = self.sourceModel()
        if not isinstance(modelo, ModeloColumnas):
            return True
        fila = modelo.fila(source_row)
        if self._predicado is not None and not self._predicado(fila):
            return False
        return not self._texto or self._texto in self._texto_busqueda(fila).casefold()
