from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from PyQt6.QtGui import QColor

from app.application.dto import FilaRevision
from app.infrastructure.ui.theme.tokens import COLORES

COLUMNAS = (
    "FILA EXCEL",
    "PACIENTE",
    "CÉDULA",
    "F. NACIMIENTO",
    "EDAD",
    "SEGURO",
    "ESTABLECIMIENTO",
    "MOTIVO",
)
COLUMNAS_CENTRADAS = (0, 4)


class ReviewTableModel(QAbstractTableModel):
    def __init__(
        self, filas: tuple[FilaRevision, ...] = (), parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._filas = filas

    def establecer_filas(self, filas: tuple[FilaRevision, ...]) -> None:
        self.beginResetModel()
        self._filas = filas
        self.endResetModel()

    def fila_en(self, indice: int) -> FilaRevision:
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
            if section in COLUMNAS_CENTRADAS:
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        fila = self._filas[index.row()]
        columna = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return self._texto(fila, columna)
        if role == Qt.ItemDataRole.TextAlignmentRole and columna in COLUMNAS_CENTRADAS:
            return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        if (
            role == Qt.ItemDataRole.ForegroundRole
            and columna in (2, 7)
            and fila.motivo_descarte
        ):
            return QColor(COLORES.rojo)
        return None

    def _texto(self, fila: FilaRevision, columna: int) -> str:
        valores = (
            f"{fila.fila_excel:04d}",
            fila.nombre,
            fila.cedula,
            fila.fecha_nacimiento.isoformat(),
            f"{fila.edad} a",
            fila.seguro,
            fila.establecimiento,
            fila.motivo_descarte or "",
        )
        return valores[columna]
