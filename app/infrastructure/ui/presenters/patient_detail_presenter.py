from __future__ import annotations

from app.application.ui_ports import IPatientDetailQuery
from app.infrastructure.ui.presenters.contracts import IPatientDetailView


class PatientDetailPresenter:
    def __init__(
        self, vista: IPatientDetailView, consulta: IPatientDetailQuery
    ) -> None:
        self._vista = vista
        self._consulta = consulta

    def mostrar(self, paciente_id: str) -> None:
        detalle = self._consulta.detalle(paciente_id)
        self._vista.mostrar_detalle(detalle)
