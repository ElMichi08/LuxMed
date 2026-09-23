from __future__ import annotations
import io
import pytest
from pypdf import PdfWriter
from app.domain.entities import Paciente, EstadoValidacion
from app.infrastructure.pdf.pdf_merger import PdfConsolidatorAdapter


def _fake_pdf_pages_count(n: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(n):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_paciente(**overrides) -> Paciente:
    from datetime import date
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


class TestPdfConsolidatorAdapter:
    def test_no_pdfs_returns_none(self):
        adapter = PdfConsolidatorAdapter()
        p = _make_paciente()
        result = adapter.consolidar(p)
        assert result is None

    def test_single_pdf_passthrough(self):
        adapter = PdfConsolidatorAdapter()
        pdf_bytes = _fake_pdf_pages_count(1)
        p = _make_paciente(pdf_p1_propio_bytes=pdf_bytes)
        result = adapter.consolidar(p)
        assert result is not None
        assert result.startswith(b"%PDF")

    def test_two_pdfs_merged(self):
        adapter = PdfConsolidatorAdapter()
        pdf1 = _fake_pdf_pages_count(1)
        pdf2 = _fake_pdf_pages_count(1)
        p = _make_paciente(pdf_p1_propio_bytes=pdf1, pdf_p1_acreditador_bytes=pdf2)
        result = adapter.consolidar(p)
        assert result is not None
        reader = io.BytesIO(result)
        from pypdf import PdfReader
        merged = PdfReader(reader)
        assert len(merged.pages) == 2

    def test_three_pdfs_merged(self):
        adapter = PdfConsolidatorAdapter()
        pdf1 = _fake_pdf_pages_count(1)
        pdf2 = _fake_pdf_pages_count(1)
        pdf3 = _fake_pdf_pages_count(2)
        p = _make_paciente(
            pdf_p1_propio_bytes=pdf1,
            pdf_p1_acreditador_bytes=pdf2,
            pdf_p3_bytes=pdf3,
        )
        result = adapter.consolidar(p)
        assert result is not None
        from pypdf import PdfReader
        merged = PdfReader(io.BytesIO(result))
        assert len(merged.pages) == 4

    def test_corrupt_pdf_skipped(self):
        adapter = PdfConsolidatorAdapter()
        good = _fake_pdf_pages_count(1)
        bad = b"not a pdf at all"
        p = _make_paciente(pdf_p1_propio_bytes=good, pdf_p1_acreditador_bytes=bad)
        result = adapter.consolidar(p)
        assert result is not None
        from pypdf import PdfReader
        merged = PdfReader(io.BytesIO(result))
        assert len(merged.pages) == 1

    def test_all_corrupt_returns_none(self):
        adapter = PdfConsolidatorAdapter()
        bad1 = b"corrupt"
        bad2 = b"also corrupt"
        p = _make_paciente(pdf_p1_propio_bytes=bad1, pdf_p1_acreditador_bytes=bad2)
        result = adapter.consolidar(p)
        assert result is None

    def test_guardar_creates_file(self, tmp_path):
        adapter = PdfConsolidatorAdapter(output_dir=str(tmp_path))
        pdf_bytes = _fake_pdf_pages_count(1)
        p = _make_paciente(pdf_consolidado=pdf_bytes)
        ruta = adapter.guardar(p)
        assert ruta is not None
        assert ruta.exists()
        assert ruta.name == "1401349020_Juan Perez_REPORT.pdf"

    def test_guardar_none_returns_none(self, tmp_path):
        adapter = PdfConsolidatorAdapter(output_dir=str(tmp_path))
        p = _make_paciente()
        ruta = adapter.guardar(p)
        assert ruta is None

    def test_filename_sanitization(self, tmp_path):
        adapter = PdfConsolidatorAdapter(output_dir=str(tmp_path))
        pdf_bytes = _fake_pdf_pages_count(1)
        p = _make_paciente(
            nombre_y_apellidos="Maria José/López",
            pdf_consolidado=pdf_bytes,
        )
        ruta = adapter.guardar(p)
        assert ruta is not None
        assert "Maria_Jos_L pez" not in ruta.name
        assert "/" not in ruta.name
