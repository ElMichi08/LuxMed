from __future__ import annotations

from collections.abc import Callable

from app.application.dto import ResultadoEntregables, SeleccionEntregables
from app.application.ui_ports import IDeliverablesExporter


class DeliverablesPresenter:
    def __init__(
        self,
        exportador: IDeliverablesExporter,
        al_exportar: Callable[[ResultadoEntregables], None],
    ) -> None:
        self._exportador = exportador
        self._al_exportar = al_exportar

    def exportar(self, seleccion: SeleccionEntregables) -> None:
        resultado = self._exportador.exportar(seleccion)
        self._al_exportar(resultado)
