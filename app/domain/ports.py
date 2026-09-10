from __future__ import annotations
from abc import ABC, abstractmethod
from app.domain.entities import Paciente

class IPacienteRepository(ABC):
    @abstractmethod
    def guardar_lote(self, pacientes: list[Paciente]) -> None:
        pass

    @abstractmethod
    def obtener_pendientes(self) -> list[Paciente]:
        pass

    @abstractmethod
    def actualizar_estado(self, paciente: Paciente) -> None:
        pass


class IExcelHandler(ABC):
    @abstractmethod
    def leer_pacientes(self, ruta_archivo: str) -> list[Paciente]:
        pass

    @abstractmethod
    def exportar_excel_limpio(self, ruta_destino: str, pacientes: list[Paciente]) -> None:
        pass

    @abstractmethod
    def exportar_excel_auditoria(self, ruta_origen: str, ruta_destino: str, pacientes: list[Paciente]) -> None:
        pass


class IScraperService(ABC):
    @abstractmethod
    def procesar_portal_1(self, paciente: Paciente) -> tuple[str, bytes | None]:
        pass