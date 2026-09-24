from __future__ import annotations

from app.application.dto import CabeceraLote, FilaPaciente, ProgresoLote
from app.infrastructure.ui.presenters.contracts import IProcessingView


class ProcessingPresenter:
    def __init__(
        self,
        vista: IProcessingView,
        cabecera: CabeceraLote,
        filas: tuple[FilaPaciente, ...],
        progreso: ProgresoLote,
    ) -> None:
        self._vista = vista
        vista.establecer_cabecera(cabecera)
        vista.establecer_filas(filas)
        vista.actualizar_progreso(progreso)
