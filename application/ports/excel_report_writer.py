from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class FilaResultado:
    fila_excel: int
    texto_estado: str


@runtime_checkable
class ExcelReportWriter(Protocol):
    """docs/BDD/12_exportacion_excel_resultado.feature — puerto simétrico a
    excel_source.py, en sentido inverso.

    Escribe un nuevo Excel con todas las columnas y filas del original sin modificar,
    más una columna "ESTADO" al final. FilaResultado.texto_estado ya viene resuelto por
    domain.reporte.estado_a_texto_excel antes de llegar acá — este puerto (y su adapter)
    no conocen EstadoPaciente ni deciden el mapeo, solo vuelcan el texto ya calculado
    (docs/arquitectura.md, decisión "El mapeo estado interno → texto de reporte vive en
    domain/reporte.py, no en el adapter de Excel").
    """

    def escribir(
        self,
        ruta_original: Path,
        resultados: list[FilaResultado],
        destino: Path,
    ) -> None: ...
