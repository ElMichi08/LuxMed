from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RegistroExcelOriginal:
    """Una fila del Excel de entrada, sin filtrar todavía — la validación de cédula
    (docs/BDD/01_normalizacion_excel.feature) es una regla de dominio, no de este
    puerto. fila_excel identifica la fila para poder reconstruir el Excel de
    resultados 1:1 (docs/BDD/12_exportacion_excel_resultado.feature)."""

    fila_excel: int
    cedula: str
    fecha_atencion: date
    datos_originales: dict[str, object]


@runtime_checkable
class ExcelSource(Protocol):
    """docs/BDD/01_normalizacion_excel.feature — lectura del Excel original.

    Solo lee y parsea; no decide qué registro entra al lote ni cuál se descarta como
    "CEDULA_INVALIDA" — eso es responsabilidad de domain.
    """

    def leer(self, ruta: Path) -> list[RegistroExcelOriginal]: ...
