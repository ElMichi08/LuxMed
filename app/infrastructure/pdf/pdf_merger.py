from __future__ import annotations
import io
import re
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from app.domain.entities import Paciente
from app.domain.ports import IPdfConsolidator


class PdfConsolidatorAdapter(IPdfConsolidator):
    def __init__(self, output_dir: str = "data/pdf_exports") -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def consolidar(self, paciente: Paciente) -> bytes | None:
        pdfs = [
            paciente.pdf_p1_propio_bytes,
            paciente.pdf_p1_acreditador_bytes,
            paciente.pdf_p3_bytes,
        ]
        validos = [pdf for pdf in pdfs if pdf is not None]
        if not validos:
            return None

        writer = PdfWriter()
        for pdf_bytes in validos:
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception:
                continue

        if len(writer.pages) == 0:
            return None

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def guardar(self, paciente: Paciente) -> Path | None:
        if paciente.pdf_consolidado is None:
            return None
        nombre_seguro = re.sub(r'[\\/:*?"<>|]', '_', paciente.nombre_y_apellidos)
        filename = f"{paciente.cedula}_{nombre_seguro}_REPORT.pdf"
        ruta = self._output_dir / filename
        ruta.write_bytes(paciente.pdf_consolidado)
        return ruta
