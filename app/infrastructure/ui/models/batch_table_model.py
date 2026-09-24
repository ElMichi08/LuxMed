from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from app.application.dto import FilaPaciente

COLUMNAS = (
    "PACIENTE",
    "CÉDULA",
    "EDAD",
    "RAMA",
    "SEGURO DERIVADO",
    "RUTA",
    "ESTADO",
    "HORA",
)
COLUMNA_RUTA = 5
COLUMNA_ESTADO = 6
COLUMNAS_CENTRADAS = (2, 3, 4)


class BatchTableModel(QAbstractTableModel):
    def __init__(
        self, filas: Iterable[FilaPaciente] = (), parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._filas: list[FilaPaciente] = list(filas)
        self._indice_por_id: dict[str, int] = {
            fila.paciente_id: i for i, fila in enumerate(self._filas)
        }

    def reset_rows(self, filas: Iterable[FilaPaciente]) -> None:
        self.beginResetModel()
        self._filas = list(filas)
        self._indice_por_id = {
            fila.paciente_id: i for i, fila in enumerate(self._filas)
        }
        self.endResetModel()

    def apply_updates(self, filas: Iterable[FilaPaciente]) -> None:
        for fila in filas:
            indice = self._indice_por_id.get(fila.paciente_id)
            if indice is None:
                posicion = len(self._filas)
                self.beginInsertRows(QModelIndex(), posicion, posicion)
                self._filas.append(fila)
                self._indice_por_id[fila.paciente_id] = posicion
                self.endInsertRows()
            else:
                self._filas[indice] = fila
                izquierda = self.index(indice, 0)
                derecha = self.index(indice, len(COLUMNAS) - 1)
                self.dataChanged.emit(izquierda, derecha)

    def fila_en(self, indice: int) -> FilaPaciente:
        return self._filas[indice]

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        indice_padre = parent if parent is not None else QModelIndex()
        return 0 if indice_padre.isValid() else len(self._filas)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        indice_padre = parent if parent is not None else QModelIndex()
        return 0 if indice_padre.isValid() else len(COLUMNAS)

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
        if role == Qt.ItemDataRole.DisplayRole and columna not in (
            COLUMNA_RUTA,
            COLUMNA_ESTADO,
        ):
            return self._texto(fila, columna)
        if role == Qt.ItemDataRole.TextAlignmentRole and columna in COLUMNAS_CENTRADAS:
            return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        return None

    def _texto(self, fila: FilaPaciente, columna: int) -> str:
        valores = (
            fila.nombre,
            fila.cedula,
            str(fila.edad),
            fila.rama.value if fila.rama is not None else "—",
            self._texto_seguro_derivado(fila),
            "",
            "",
            fila.hora.strftime("%H:%M:%S") if fila.hora is not None else "—",
        )
        return valores[columna]

    def _texto_seguro_derivado(self, fila: FilaPaciente) -> str:
        if fila.seguro_derivado is None:
            return "—"
        return "Sí" if fila.seguro_derivado else "No"
