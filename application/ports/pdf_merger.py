from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class PdfMerger(Protocol):
    """docs/BDD/11_consolidacion_pdf_paciente.feature.

    Combina los PDFs individuales ya verificados en un único archivo, en el orden en
    que aparecen en pdf_paths (Portal 1→2→3 en Rama A, Portal 1→3 en Rama B — el orden
    lo decide quien llama, este puerto no conoce ramas), y borra los individuales tras
    combinar con éxito. Nombre del combinado: "{cedula}_{fecha_atencion:%Y%m%d}.pdf" —
    cédula + fecha de atención es el mismo par que identifica de forma única cada fila
    del Excel de entrada.
    """

    def combinar(
        self,
        cedula: str,
        fecha_atencion: date,
        pdf_paths: list[Path],
        destino_dir: Path,
    ) -> Path: ...
