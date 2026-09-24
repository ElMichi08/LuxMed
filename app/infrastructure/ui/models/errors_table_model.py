from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt, pyqtSignal

from app.application.dto import FilaError

COLUMNAS = (
    "",
    "PACIENTE",
    "CÉDULA",
    "PORTAL QUE FALLÓ",
    "MOTIVO",
    "INTENTOS",
    "ÚLTIMO INTENTO",
    "ESTADO",
)
COLUMNA_SELECCION = 0
COLUMNA_ESTADO = 7
COLUMNAS_CENTRADAS = (0, 5, 6, 7)


class ErrorsTableModel(QAbstractTableModel):
    seleccion_cambiada = pyqtSignal()

    def __init__(
        self, filas: Iterable[FilaError] = (), parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._filas: list[FilaError] = list(filas)
        self._seleccionados: set[str] = {fila.paciente_id for fila in self._filas}

    def establecer_filas(self, filas: Iterable[FilaError]) -> None:
        self.beginResetModel()
        self._filas = list(filas)
        self._seleccionados = {fila.paciente_id for fila in self._filas}
        self.endResetModel()

    def fila_en(self, indice: int) -> FilaError:
        return self._filas[indice]

    def ids_seleccionados(self) -> tuple[str, ...]:
        return tuple(
            fila.paciente_id
            for fila in self._filas
            if fila.paciente_id in self._seleccionados
        )

    def total_seleccionados(self) -> int:
        return len(self._seleccionados)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        indice_padre = parent if parent is not None else QModelIndex()
        return 0 if indice_padre.isValid() else len(self._filas)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        indice_padre = parent if parent is not None else QModelIndex()
        return 0 if indice_padre.isValid() else len(COLUMNAS)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        if index.column() == COLUMNA_SELECCION:
            return base | Qt.ItemFlag.ItemIsUserCheckable
        return base

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return COLUMNAS[section]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            alineacion = (
                Qt.AlignmentFlag.AlignCenter
                if section in COLUMNAS_CENTRADAS
                else Qt.AlignmentFlag.AlignLeft
            )
            return alineacion | Qt.AlignmentFlag.AlignVCenter
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        fila = self._filas[index.row()]
        columna = index.column()
        if role == Qt.ItemDataRole.UserRole:
            return fila
        if role == Qt.ItemDataRole.CheckStateRole and columna == COLUMNA_SELECCION:
            marcado = fila.paciente_id in self._seleccionados
            return Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked
        if (
            role == Qt.ItemDataRole.DisplayRole
            and columna != COLUMNA_ESTADO
            and columna != COLUMNA_SELECCION
        ):
            return self._texto(fila, columna)
        if role == Qt.ItemDataRole.TextAlignmentRole and columna in COLUMNAS_CENTRADAS:
            return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if (
            role != Qt.ItemDataRole.CheckStateRole
            or index.column() != COLUMNA_SELECCION
        ):
            return False
        fila = self._filas[index.row()]
        if value == Qt.CheckState.Checked.value:
            self._seleccionados.add(fila.paciente_id)
        else:
            self._seleccionados.discard(fila.paciente_id)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        self.seleccion_cambiada.emit()
        return True

    def _texto(self, fila: FilaError, columna: int) -> str:
        valores = (
            "",
            fila.nombre,
            fila.cedula,
            f"Portal {int(fila.portal_fallido)}",
            fila.motivo,
            f"{fila.intentos} de {fila.intentos_maximos}",
            fila.ultimo_intento.strftime("%H:%M:%S"),
            "",
        )
        return valores[columna]
