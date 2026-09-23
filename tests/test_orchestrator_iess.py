from unittest.mock import MagicMock, PropertyMock
import pytest
from datetime import date
from app.application.orchestrator import OrchestratorService
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro


def _make_paciente(cedula="0105556567", entidad="iess"):
    return Paciente(
        nombre_y_apellidos="TEST PACIENTE",
        cedula=cedula,
        fecha_nacimiento=date(2000, 1, 1),
        aporta="IESS",
        fecha_atencion=date.today(),
        nom_establecimiento="HOSPITAL TEST",
        entidad_detectada=EntidadSeguro(entidad.upper()) if entidad != "iess" else EntidadSeguro.IESS,
    )


class TestIESSFlujoBasico:
    def test_paciente_iess_sin_acreditador(self):
        repo = MagicMock()
        scraper = MagicMock()
        scraper.procesar_portal_1.return_value = ("IESS", "Enfermedad", "COBERTURA IESS", None)
        scraper.existe_autenticacion_portal_3.return_value = False
        scraper.extraer_acreditador_portal_2.return_value = None

        orch = OrchestratorService(repository=repo, scraper=scraper)
        pac = _make_paciente()
        orch._procesar_paciente_individual(pac)

        assert pac.estado == EstadoValidacion.VALIDO
        assert pac.entidad_detectada == EntidadSeguro.IESS
        assert pac.cedula_acreditador is None
        assert pac.seguro_derivado is False
        scraper.extraer_acreditador_portal_2.assert_called_once()

    def test_paciente_iess_con_acreditador(self):
        repo = MagicMock()
        scraper = MagicMock()
        scraper.procesar_portal_1.return_value = ("IESS", "Enfermedad", "COBERTURA IESS", b"pdf_own")
        scraper.extraer_acreditador_portal_2.return_value = "0998887776"
        scraper.existe_autenticacion_portal_3.return_value = False

        orch = OrchestratorService(repository=repo, scraper=scraper)
        pac = _make_paciente()
        orch._procesar_paciente_individual(pac)

        assert pac.cedula_acreditador == "0998887776"
        assert pac.seguro_derivado is True
        assert scraper.procesar_portal_1.call_count == 2

    def test_paciente_iess_acreditador_invalido(self):
        repo = MagicMock()
        scraper = MagicMock()
        scraper.procesar_portal_1.return_value = ("IESS", "Enfermedad", "COBERTURA IESS", None)
        scraper.extraer_acreditador_portal_2.side_effect = Exception("ALTCHA fail")

        orch = OrchestratorService(repository=repo, scraper=scraper)
        pac = _make_paciente()
        orch._procesar_paciente_individual(pac)

        assert pac.estado == EstadoValidacion.PENDIENTE


class TestRutasPortal3:
    def test_issfa_ruta_directa(self):
        repo = MagicMock()
        scraper = MagicMock()
        scraper.procesar_portal_1.return_value = ("ISSFA", "Policial", "COBERTURA", None)
        portal3 = MagicMock()
        portal3.existe_autenticacion_portal_3.return_value = False

        orch = OrchestratorService(repository=repo, scraper=scraper, portal3_adapter=portal3)
        pac = _make_paciente(entidad="issfa")
        orch._procesar_paciente_individual(pac)

        assert pac.entidad_detectada == EntidadSeguro.ISSFA
        portal3.existe_autenticacion_portal_3.assert_called()

    def test_isspol_ruta_directa(self):
        repo = MagicMock()
        scraper = MagicMock()
        scraper.procesar_portal_1.return_value = ("ISSPOL", "Policial", "COBERTURA", None)
        portal3 = MagicMock()
        portal3.existe_autenticacion_portal_3.return_value = False

        orch = OrchestratorService(repository=repo, scraper=scraper, portal3_adapter=portal3)
        pac = _make_paciente(entidad="isspol")
        orch._procesar_paciente_individual(pac)

        assert pac.entidad_detectada == EntidadSeguro.ISSPOL
