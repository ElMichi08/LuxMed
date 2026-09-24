from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import PreviewLote
from app.application.ui_ports import IBatchIntake
from app.infrastructure.ui.presenters.contracts import IUploadView

MENSAJE_ERROR_LECTURA = "No se pudo leer el archivo."
MENSAJE_CARGANDO = "Leyendo archivo…"


class UploadPresenter:
    def __init__(
        self,
        vista: IUploadView,
        intake: IBatchIntake,
        al_leer_lote: Callable[[PreviewLote], None],
    ) -> None:
        self._vista = vista
        self._intake = intake
        self._al_leer_lote = al_leer_lote

    def archivo_elegido(self, ruta: str) -> None:
        self._vista.limpiar_error()
        self._vista.establecer_cargando(MENSAJE_CARGANDO)
        try:
            preview = self._intake.leer_listado(Path(ruta))
        except Exception:
            self._vista.establecer_cargando(None)
            self._vista.mostrar_error(MENSAJE_ERROR_LECTURA)
            return
        self._vista.establecer_cargando(None)
        self._al_leer_lote(preview)
