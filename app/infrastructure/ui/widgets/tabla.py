from __future__ import annotations

from PyQt6.QtCore import QAbstractItemModel, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyledItemDelegate,
    QTableView,
)

from app.infrastructure.ui.models.columnas import Columna
from app.infrastructure.ui.theme.tokens import GEOMETRIA


def crear_tabla(
    modelo: QAbstractItemModel,
    columnas: tuple[Columna, ...],
    delegados: dict[int, QStyledItemDelegate] | None = None,
    con_borde: bool = False,
) -> QTableView:
    tabla = QTableView()
    if con_borde:
        tabla.setObjectName("tabla_con_borde")
    tabla.setModel(modelo)
    tabla.setShowGrid(False)
    tabla.setWordWrap(False)
    tabla.setAlternatingRowColors(False)
    tabla.setMouseTracking(True)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tabla.setTextElideMode(Qt.TextElideMode.ElideRight)
    vertical = tabla.verticalHeader()
    if vertical is not None:
        vertical.hide()
        vertical.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical.setDefaultSectionSize(GEOMETRIA.fila)
    horizontal = tabla.horizontalHeader()
    if horizontal is not None:
        horizontal.setFixedHeight(GEOMETRIA.cabecera_tabla)
        horizontal.setHighlightSections(False)
        horizontal.setStretchLastSection(False)
        for posicion, columna in enumerate(columnas):
            if columna.ancho is None:
                horizontal.setSectionResizeMode(posicion, QHeaderView.ResizeMode.Stretch)
            else:
                horizontal.setSectionResizeMode(posicion, QHeaderView.ResizeMode.Interactive)
                tabla.setColumnWidth(posicion, columna.ancho)
    for posicion, delegado in (delegados or {}).items():
        delegado.setParent(tabla)
        tabla.setItemDelegateForColumn(posicion, delegado)
    return tabla
