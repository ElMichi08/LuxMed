from __future__ import annotations

from enum import StrEnum

from PyQt6.QtCore import QModelIndex, QObject, QSortFilterProxyModel

from app.application.dto import EstadoPaciente
from app.infrastructure.ui.models.batch_table_model import BatchTableModel


class FiltroEstado(StrEnum):
    TODOS = "todos"
    EN_PROCESO = "en_proceso"
    COMPLETADOS = "completados"
    INVALIDOS = "invalidos"
    CON_ERROR = "con_error"


_ESTADOS_POR_FILTRO: dict[FiltroEstado, tuple[EstadoPaciente, ...]] = {
    FiltroEstado.EN_PROCESO: (EstadoPaciente.EN_PROCESO,),
    FiltroEstado.COMPLETADOS: (EstadoPaciente.COMPLETADO,),
    FiltroEstado.INVALIDOS: (
        EstadoPaciente.CEDULA_INVALIDA,
        EstadoPaciente.NO_ENCONTRADO,
    ),
    FiltroEstado.CON_ERROR: (
        EstadoPaciente.ERROR_PORTAL_1,
        EstadoPaciente.ERROR_PORTAL_2,
        EstadoPaciente.ERROR_PORTAL_3,
    ),
}


class BatchFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._texto_busqueda = ""
        self._filtro_estado = FiltroEstado.TODOS

    def establecer_busqueda(self, texto: str) -> None:
        self._texto_busqueda = texto.strip().lower()
        self.invalidateFilter()

    def establecer_filtro_estado(self, filtro: FiltroEstado) -> None:
        self._filtro_estado = filtro
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        modelo = self.sourceModel()
        if not isinstance(modelo, BatchTableModel):
            return True
        fila = modelo.fila_en(source_row)
        coincide_texto = (
            self._texto_busqueda in fila.nombre.lower()
            or self._texto_busqueda in fila.cedula.lower()
        )
        if self._texto_busqueda and not coincide_texto:
            return False
        if self._filtro_estado is FiltroEstado.TODOS:
            return True
        return fila.estado in _ESTADOS_POR_FILTRO[self._filtro_estado]
