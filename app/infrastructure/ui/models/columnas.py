from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from PyQt6.QtGui import QColor, QFont

from app.infrastructure.ui.theme.fuentes import fuente, fuente_mono
from app.infrastructure.ui.theme.tokens import TIPOGRAFIA

FILA_ROLE = Qt.ItemDataRole.UserRole + 1
IZQUIERDA = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
CENTRO = Qt.AlignmentFlag.AlignCenter
DERECHA = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

Texto = Callable[[object], str]
Color = Callable[[object], str | None]
Negrita = Callable[[object], bool]


def sin_color(_fila: object) -> str | None:
    return None


def sin_negrita(_fila: object) -> bool:
    return False


@dataclass(frozen=True)
class Columna:
    titulo: str
    texto: Texto
    ancho: int | None = None
    alineacion: Qt.AlignmentFlag = IZQUIERDA
    mono: bool = False
    color: Color = sin_color
    negrita: Negrita = sin_negrita


class ModeloColumnas(QAbstractTableModel):
    def __init__(
        self,
        columnas: Sequence[Columna],
        fondo: Color = sin_color,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._columnas = tuple(columnas)
        self._fondo = fondo
        self._filas: list[object] = []
        self._fuentes: dict[tuple[bool, bool], QFont] = {}

    @property
    def columnas(self) -> tuple[Columna, ...]:
        return self._columnas

    @property
    def filas(self) -> tuple[object, ...]:
        return tuple(self._filas)

    def fila(self, posicion: int) -> object:
        return self._filas[posicion]

    def establecer_filas(self, filas: Sequence[object]) -> None:
        self.beginResetModel()
        self._filas = list(filas)
        self.endResetModel()

    def reemplazar_filas(self, cambios: Mapping[int, object]) -> None:
        if not cambios:
            return
        for posicion, fila in cambios.items():
            self._filas[posicion] = fila
        self.dataChanged.emit(
            self.index(min(cambios), 0), self.index(max(cambios), len(self._columnas) - 1)
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._filas)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columnas)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if orientation is not Qt.Orientation.Horizontal:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._columnas[section].titulo
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._columnas[section].alineacion
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid():
            return None
        fila = self._filas[index.row()]
        columna = self._columnas[index.column()]
        if role == FILA_ROLE:
            return fila
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return columna.texto(fila)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return columna.alineacion
        if role == Qt.ItemDataRole.ForegroundRole:
            return _color(columna.color(fila))
        if role == Qt.ItemDataRole.BackgroundRole:
            return _color(self._fondo(fila))
        if role == Qt.ItemDataRole.FontRole:
            return self._fuente(columna.mono, columna.negrita(fila))
        return None

    def _fuente(self, mono: bool, negrita: bool) -> QFont:
        clave = (mono, negrita)
        if clave not in self._fuentes:
            peso = QFont.Weight.DemiBold if negrita else QFont.Weight.Normal
            self._fuentes[clave] = (
                fuente_mono(TIPOGRAFIA.base, peso)
                if mono
                else fuente(tamano=TIPOGRAFIA.base, peso=peso)
            )
        return self._fuentes[clave]


def _color(valor: str | None) -> QColor | None:
    return QColor(valor) if valor else None
