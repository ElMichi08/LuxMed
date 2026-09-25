from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

NOMBRES_MES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)


@dataclass(frozen=True, slots=True, order=True)
class MesAtencion:
    anio: int
    mes: int

    @classmethod
    def de_fecha(cls, fecha: date) -> MesAtencion:
        return cls(fecha.year, fecha.month)

    @property
    def nombre(self) -> str:
        return f"{NOMBRES_MES[self.mes - 1]} {self.anio}"

    @property
    def nombre_carpeta(self) -> str:
        return f"{self.anio:04d}-{self.mes:02d} {NOMBRES_MES[self.mes - 1]}"

    def anterior(self) -> MesAtencion:
        return MesAtencion(self.anio - 1, 12) if self.mes == 1 else MesAtencion(self.anio, self.mes - 1)


@dataclass(frozen=True, slots=True)
class ConteoMes:
    mes: MesAtencion
    filas: int


def detectar_meses(fechas: Iterable[date]) -> tuple[ConteoMes, ...]:
    conteo = Counter(MesAtencion.de_fecha(fecha) for fecha in fechas)
    return tuple(
        ConteoMes(mes, filas)
        for mes, filas in sorted(conteo.items(), key=lambda par: (-par[1], par[0]))
    )


def meses_recientes(desde: MesAtencion, cantidad: int) -> tuple[MesAtencion, ...]:
    meses = [desde]
    while len(meses) < cantidad:
        meses.append(meses[-1].anterior())
    return tuple(meses)
