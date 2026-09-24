from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from app.application.dto import (
    AccionOperador,
    CabeceraLote,
    DecisionOperador,
    DetallePaciente,
    FilaError,
    FilaPaciente,
    LineaBitacora,
    PreviewLote,
    ProgresoLote,
    ResultadoEjecucion,
    ResultadoEntregables,
    ResumenLote,
    SeleccionEntregables,
    SesionUsuario,
    SolicitudOperador,
)


class ILocalAuthenticator(ABC):
    @abstractmethod
    def autenticar(self, usuario: str, contrasena: str) -> SesionUsuario | None: pass


class IBatchIntake(ABC):
    @abstractmethod
    def leer_listado(self, ruta: Path) -> PreviewLote: pass


class IProgressReporter(ABC):
    @abstractmethod
    def paciente_actualizado(self, fila: FilaPaciente) -> None: pass
    @abstractmethod
    def linea_bitacora(self, linea: LineaBitacora) -> None: pass
    @abstractmethod
    def progreso_lote(self, progreso: ProgresoLote) -> None: pass


class IOperatorGate(ABC):
    @abstractmethod
    def solicitar(self, solicitud: SolicitudOperador) -> None: pass

    @abstractmethod
    def esperar(
        self,
        accion: AccionOperador,
        resuelto: Callable[[], bool],
    ) -> DecisionOperador | None: pass

    @abstractmethod
    def cerrar(self, accion: AccionOperador) -> None: pass


class IBatchExecution(ABC):
    @abstractmethod
    def ejecutar(
        self,
        progreso: IProgressReporter,
        compuerta: IOperatorGate,
    ) -> ResultadoEjecucion: pass


class IBatchExecutionFactory(ABC):
    @abstractmethod
    def ejecucion_de_lote(self, lote_id: str) -> IBatchExecution: pass


class IReprocessExecutionFactory(ABC):
    @abstractmethod
    def ejecucion_de_reproceso(
        self,
        paciente_ids: tuple[str, ...],
    ) -> IBatchExecution: pass


class ICurrentBatchQuery(ABC):
    @abstractmethod
    def cabecera_actual(self) -> CabeceraLote | None: pass


class IBatchSummaryQuery(ABC):
    @abstractmethod
    def resumen_actual(self) -> ResumenLote: pass


class IPatientDetailQuery(ABC):
    @abstractmethod
    def detalle(self, paciente_id: str) -> DetallePaciente: pass


class IErrorListQuery(ABC):
    @abstractmethod
    def errores_pendientes(self) -> tuple[FilaError, ...]: pass


class IDeliverablesExporter(ABC):
    @abstractmethod
    def exportar(self, seleccion: SeleccionEntregables) -> ResultadoEntregables: pass


class IOutputFolderSettings(ABC):
    @abstractmethod
    def obtener(self) -> Path: pass
    @abstractmethod
    def guardar(self, carpeta: Path) -> None: pass
