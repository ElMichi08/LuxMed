from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Rama(Enum):
    RAMA_A = "Rama A"
    RAMA_B = "Rama B"


@dataclass(frozen=True)
class PdfArtifact:
    portal: int
    verificado: bool


@dataclass
class Patient:
    cedula: str
    es_menor_edad: bool
    tipo_seguro: str
    rama: Rama | None = None
    pdfs: list[PdfArtifact] = field(default_factory=list)

    @property
    def portales_verificados(self) -> frozenset[int]:
        return frozenset(pdf.portal for pdf in self.pdfs if pdf.verificado)


@dataclass
class Batch:
    id: str
    patients: list[Patient] = field(default_factory=list)
