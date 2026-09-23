from __future__ import annotations
import io
import pytest
from datetime import date
from pypdf import PdfWriter
from unittest.mock import MagicMock, patch
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro
from app.domain.ports import IPacienteRepository, IScraperService, IPdfConsolidator
from app.application.orchestrator import OrchestratorService
from app.infrastructure.pdf.pdf_merger import PdfConsolidatorAdapter


def _fake_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_paciente(**overrides) -> Paciente:
    defaults = dict(
        nombre_y_apellidos="Juan Perez",
        cedula="1401349020",
        fecha_nacimiento=date(1990, 1, 1),
        aporta="IESS",
        fecha_atencion=date(2026, 4, 7),
        nom_establecimiento="Hospital",
    )
    defaults.update(overrides)
    return Paciente(**defaults)


class TestOrchestratorPdfConsolidation:
    def test_consolidator_called_when_valido(self):
        repo = MagicMock(spec=IPacienteRepository)
        scraper = MagicMock(spec=IScraperService)
        consolidator = MagicMock(spec=IPdfConsolidator)
        consolidator.consolidar.return_value = b"merged pdf bytes"

        scraper.procesar_portal_1.return_value = (
            "IESS", "Seguro Regular", "registra cobertura", _fake_pdf()
        )

        orch = OrchestratorService(repo, scraper, pdf_consolidator=consolidator)
        p = _make_paciente()
        orch._procesar_paciente_individual(p)

        consolidator.consolidar.assert_called_once_with(p)
        assert p.pdf_consolidado == b"merged pdf bytes"

    def test_consolidator_not_called_when_invalido(self):
        repo = MagicMock(spec=IPacienteRepository)
        scraper = MagicMock(spec=IScraperService)
        consolidator = MagicMock(spec=IPdfConsolidator)

        scraper.procesar_portal_1.return_value = (
            "", "", "No registra cobertura", None
        )

        orch = OrchestratorService(repo, scraper, pdf_consolidator=consolidator)
        p = _make_paciente()
        orch._procesar_paciente_individual(p)

        consolidator.consolidar.assert_not_called()

    def test_no_consolidator_no_crash(self):
        repo = MagicMock(spec=IPacienteRepository)
        scraper = MagicMock(spec=IScraperService)

        scraper.procesar_portal_1.return_value = (
            "IESS", "Seguro Regular", "registra cobertura", _fake_pdf()
        )

        orch = OrchestratorService(repo, scraper, pdf_consolidator=None)
        p = _make_paciente()
        orch._procesar_paciente_individual(p)

        assert p.pdf_consolidado is None

    def test_consolidation_none_result(self):
        repo = MagicMock(spec=IPacienteRepository)
        scraper = MagicMock(spec=IScraperService)
        consolidator = MagicMock(spec=IPdfConsolidator)
        consolidator.consolidar.return_value = None

        scraper.procesar_portal_1.return_value = (
            "IESS", "Seguro Regular", "registra cobertura", None
        )

        orch = OrchestratorService(repo, scraper, pdf_consolidator=consolidator)
        p = _make_paciente()
        orch._procesar_paciente_individual(p)

        assert p.pdf_consolidado is None

    def test_end_to_end_with_adapter(self):
        repo = MagicMock(spec=IPacienteRepository)
        scraper = MagicMock(spec=IScraperService)
        adapter = PdfConsolidatorAdapter()

        pdf = _fake_pdf()
        scraper.procesar_portal_1.return_value = (
            "ISSFA", "Seguro ISSFA", "registra cobertura", pdf
        )

        orch = OrchestratorService(repo, scraper, pdf_consolidator=adapter)
        p = _make_paciente()
        orch._procesar_paciente_individual(p)

        assert p.pdf_consolidado is not None
        assert p.pdf_consolidado.startswith(b"%PDF")
