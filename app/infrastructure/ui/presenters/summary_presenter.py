from __future__ import annotations

from app.application.ui_ports import IBatchSummaryQuery
from app.infrastructure.ui.presenters.contracts import ISummaryView


class SummaryPresenter:
    def __init__(self, vista: ISummaryView, consulta: IBatchSummaryQuery) -> None:
        self._vista = vista
        self._consulta = consulta

    def cargar(self) -> None:
        self._vista.mostrar_resumen(self._consulta.resumen_actual())
