from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from PyQt6.QtWidgets import QFrame, QLabel

from app.infrastructure.ui.theme.tokens import COLORES
from app.infrastructure.ui.widgets.base import (
    columna,
    establecer_propiedad,
    etiqueta,
    fila,
)


@dataclass(frozen=True, slots=True)
class DefinicionKpi:
    clave: str
    titulo: str
    color: str = COLORES.tinta
    nota: str = ""


class KpiTile(QFrame):
    def __init__(self, definicion: DefinicionKpi, ultimo: bool) -> None:
        super().__init__()
        self.setProperty("rol", "kpi")
        self.setProperty("ultimo", ultimo)
        layout = columna((20, 10, 20, 10), 2)
        self._titulo = etiqueta(definicion.titulo.upper(), "etiqueta")
        self._cifra = etiqueta("0", "kpi_cifra")
        self._cifra.setStyleSheet(f"color: {definicion.color};")
        layout.addWidget(self._titulo)
        layout.addWidget(self._cifra)
        if definicion.nota:
            nota = etiqueta(definicion.nota, "kpi_nota")
            nota.setStyleSheet(f"color: {definicion.color};")
            layout.addWidget(nota)
        self.setLayout(layout)

    @property
    def cifra(self) -> QLabel:
        return self._cifra

    def establecer_valor(self, valor: int | str) -> None:
        self._cifra.setText(str(valor))

    def establecer_activo(self, activo: bool) -> None:
        establecer_propiedad(self, "activo", activo)


class KpiStrip(QFrame):
    def __init__(self, definiciones: Sequence[DefinicionKpi], objeto: str = "tira_kpi") -> None:
        super().__init__()
        self.setObjectName(objeto)
        layout = fila()
        self._tiles: dict[str, KpiTile] = {}
        for posicion, definicion in enumerate(definiciones):
            tile = KpiTile(definicion, ultimo=posicion == len(definiciones) - 1)
            self._tiles[definicion.clave] = tile
            layout.addWidget(tile, 1)
        self.setLayout(layout)

    def tile(self, clave: str) -> KpiTile:
        return self._tiles[clave]

    def establecer_valores(self, valores: Mapping[str, int | str]) -> None:
        for clave, valor in valores.items():
            self._tiles[clave].establecer_valor(valor)


def panel_kpi(definiciones: Sequence[DefinicionKpi]) -> KpiStrip:
    return KpiStrip(definiciones, objeto="cinta_kpi")
