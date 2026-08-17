from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class FasesPaciente:
    """Fases completadas por paciente — no presencia de archivos en disco: la
    consolidación (docs/BDD/11_consolidacion_pdf_paciente.feature) borra los PDFs
    individuales tras combinarlos, así que su ausencia ya no significa "falta
    descargarlo"."""

    portal1_ok: bool = False
    portal2_ok: bool = False
    portal3_ok: bool = False
    combinado_ok: bool = False


@dataclass(frozen=True)
class IntervaloPausa:
    inicio: datetime
    fin: datetime | None = None  # None mientras el lote sigue en pausa


@runtime_checkable
class CheckpointRepository(Protocol):
    """docs/arquitectura.md, sección "Contrato de checkpoint_repository.py".

    Al reanudar, process_patient.py consulta obtener_fases() (no el filesystem) para
    saber qué le falta a cada paciente. Los intervalos de pausa del lote se guardan por
    separado, para calcular "tiempo activo" en docs/BDD/13_resumen_numerico_lote.feature
    sin contar el tiempo pausado.
    """

    def obtener_fases(self, cedula: str, fecha_atencion: date) -> FasesPaciente: ...

    def guardar_fases(
        self, cedula: str, fecha_atencion: date, fases: FasesPaciente
    ) -> None: ...

    def registrar_inicio_pausa(self, momento: datetime) -> None: ...

    def registrar_fin_pausa(self, momento: datetime) -> None: ...

    def obtener_intervalos_pausa(self) -> list[IntervaloPausa]: ...
