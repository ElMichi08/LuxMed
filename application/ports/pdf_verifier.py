from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class PdfVerifier(Protocol):
    """Verificación de integridad y extracción determinista (sin LLM — invariante #4).

    Usado en los 3 portales para verificar integridad de PDF #1/#2/#3
    (docs/BDD/03_consulta_portal1.feature, 05_consulta_portal2.feature,
    06_consulta_portal3.feature) y en la idempotencia al reanudar
    (docs/BDD/09_idempotencia_pdfs.feature). extraer_cedula_titular() es específico del
    PDF #2 (docs/BDD/05_..., escenario "Extracción exitosa de la cédula del titular") —
    solo se llama sobre un PDF ya confirmado íntegro con es_integro(); el propio feature
    aclara que en ese caso no debería fallar por datos ausentes.
    """

    def es_integro(self, pdf_path: Path) -> bool: ...

    def extraer_cedula_titular(self, pdf_path: Path) -> str: ...
