from __future__ import annotations
from datetime import date
from abc import ABC, abstractmethod
from app.domain.entities import Paciente

class IPacienteRepository(ABC):
    @abstractmethod
    def guardar_lote(self, pacientes: list[Paciente]) -> None: pass
    @abstractmethod
    def obtener_pendientes(self) -> list[Paciente]: pass
    @abstractmethod
    def actualizar_estado(self, paciente: Paciente) -> None: pass

class IExcelHandler(ABC):
    @abstractmethod
    def leer_pacientes(self, ruta_archivo: str) -> list[Paciente]: pass
    @abstractmethod
    def exportar_excel_limpio(self, ruta_destino: str, pacientes: list[Paciente]) -> None: pass
    @abstractmethod
    def exportar_excel_auditoria(self, ruta_origen: str, ruta_destino: str, pacientes: list[Paciente]) -> None: pass

class IPdfConsolidator(ABC):
    @abstractmethod
    def consolidar(self, paciente: Paciente) -> bytes | None:
        pass

    @abstractmethod
    def guardar(self, paciente: Paciente) -> object:
        pass

class IScraperService(ABC):
    @abstractmethod
    def existe_autenticacion_portal_3(self) -> bool:
        pass

    @abstractmethod
    def vincular_sesion_portal_3(self) -> bool:
        pass

    @abstractmethod
    def procesar_portal_1(self, cedula: str, fecha_atencion: date) -> tuple[str, str, str, bytes | None]:
        pass

    @abstractmethod
    def extraer_acreditador_portal_2(self, paciente: Paciente) -> str | None:
        pass
