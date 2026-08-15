# Test de humo: confirma que cada puerto de application/ports/ es un contrato
# satisfacible con un *fake* mínimo (isinstance vía @runtime_checkable), no que la
# lógica de negocio funcione — eso se prueba cuando exista process_patient.py y use
# estos puertos con fakes reales (docs/arquitectura.md, "Estrategia de pruebas").
from datetime import date, datetime
from pathlib import Path

from application.ports.checkpoint_repository import CheckpointRepository, FasesPaciente
from application.ports.excel_report_writer import ExcelReportWriter
from application.ports.excel_source import ExcelSource, RegistroExcelOriginal
from application.ports.human_intervention import (
    HumanInterventionPort,
    ResolucionIntervencion,
)
from application.ports.pdf_merger import PdfMerger
from application.ports.pdf_verifier import PdfVerifier
from application.ports.portal_gateway import (
    Portal1Gateway,
    Portal2Gateway,
    Portal3Gateway,
    ResultadoConsultaPortal1,
    ResultadoConsultaPortal2,
    ResultadoConsultaPortal3,
)


class FakePortal1Gateway:
    def consultar(self, cedula: str, fecha_atencion: date) -> ResultadoConsultaPortal1:
        return ResultadoConsultaPortal1(encontrado=True)


class FakePortal2Gateway:
    def consultar_titular(
        self, cedula: str, fecha_atencion: date
    ) -> ResultadoConsultaPortal2:
        return ResultadoConsultaPortal2(tiene_cobertura=True)


class FakePortal3Gateway:
    def iniciar_sesion(self) -> None:
        pass

    def consultar_atencion(
        self, cedula: str, fecha_atencion: date
    ) -> ResultadoConsultaPortal3:
        return ResultadoConsultaPortal3(pdf_path=Path("fake.pdf"))


class FakePdfVerifier:
    def es_integro(self, pdf_path: Path) -> bool:
        return True

    def extraer_cedula_titular(self, pdf_path: Path) -> str:
        return "0102030405"


class FakePdfMerger:
    def combinar(self, cedula, fecha_atencion, pdf_paths, destino_dir) -> Path:
        return destino_dir / f"{cedula}_{fecha_atencion:%Y%m%d}.pdf"


class FakeCheckpointRepository:
    def obtener_fases(self, cedula: str, fecha_atencion: date) -> FasesPaciente:
        return FasesPaciente()

    def guardar_fases(self, cedula, fecha_atencion, fases) -> None:
        pass

    def registrar_inicio_pausa(self, momento: datetime) -> None:
        pass

    def registrar_fin_pausa(self, momento: datetime) -> None:
        pass

    def obtener_intervalos_pausa(self) -> list:
        return []


class FakeExcelSource:
    def leer(self, ruta: Path) -> list[RegistroExcelOriginal]:
        return []


class FakeExcelReportWriter:
    def escribir(self, ruta_original, resultados, destino) -> None:
        pass


class FakeHumanIntervention:
    def solicitar(self, solicitud) -> ResolucionIntervencion:
        return ResolucionIntervencion(opcion_elegida="reintentar")


def test_fakes_satisfacen_cada_protocol():
    assert isinstance(FakePortal1Gateway(), Portal1Gateway)
    assert isinstance(FakePortal2Gateway(), Portal2Gateway)
    assert isinstance(FakePortal3Gateway(), Portal3Gateway)
    assert isinstance(FakePdfVerifier(), PdfVerifier)
    assert isinstance(FakePdfMerger(), PdfMerger)
    assert isinstance(FakeCheckpointRepository(), CheckpointRepository)
    assert isinstance(FakeExcelSource(), ExcelSource)
    assert isinstance(FakeExcelReportWriter(), ExcelReportWriter)
    assert isinstance(FakeHumanIntervention(), HumanInterventionPort)


def test_resultado_portal2_sin_cobertura_no_exige_pdf_path():
    resultado = ResultadoConsultaPortal2(tiene_cobertura=False)
    assert resultado.pdf_path is None
