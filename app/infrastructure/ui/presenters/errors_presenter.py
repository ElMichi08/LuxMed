from __future__ import annotations

from app.application.ui_ports import IErrorListQuery
from app.infrastructure.ui.presenters.contracts import IErrorsView


class ErrorsPresenter:
    def __init__(self, vista: IErrorsView, consulta: IErrorListQuery) -> None:
        self._vista = vista
        self._consulta = consulta

    def cargar(self) -> None:
        self._vista.mostrar_errores(self._consulta.errores_pendientes())
