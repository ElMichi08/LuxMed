from __future__ import annotations

import logging
from collections.abc import Callable

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from app.application.lote_service import ErrorLote
from app.application.progreso import AvancePaciente, IObservadorLote, ResumenLote

logger = logging.getLogger(__name__)

EjecucionLote = Callable[[IObservadorLote], ResumenLote]


def mensaje_de_error(error: Exception) -> str:
    if isinstance(error, ErrorLote):
        return str(error)
    return f"Ocurrió un error inesperado ({type(error).__name__}). Revisa la vista Logs."


class TaskThread(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, tarea: Callable[[], object], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tarea = tarea
        self.finished.connect(self.deleteLater)

    def run(self) -> None:
        try:
            resultado = self._tarea()
        except Exception as error:
            logger.exception("Tarea en segundo plano fallida")
            self.failed.emit(mensaje_de_error(error))
        else:
            self.succeeded.emit(resultado)


class _ObservadorHilo(IObservadorLote):
    def __init__(self, hilo: BatchRunnerThread) -> None:
        self._hilo = hilo

    def paciente_actualizado(self, avance: AvancePaciente) -> None:
        self._hilo.patient_updated.emit(avance)

    def detencion_solicitada(self) -> bool:
        return self._hilo.isInterruptionRequested()


class BatchRunnerThread(QThread):
    patient_updated = pyqtSignal(object)
    batch_ended = pyqtSignal(object)
    batch_failed = pyqtSignal(str)

    def __init__(self, ejecucion: EjecucionLote, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._ejecucion = ejecucion
        self.finished.connect(self.deleteLater)

    def run(self) -> None:
        try:
            resumen = self._ejecucion(_ObservadorHilo(self))
        except Exception as error:
            logger.exception("El lote terminó con un error")
            self.batch_failed.emit(mensaje_de_error(error))
        else:
            self.batch_ended.emit(resumen)
