from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QRectF, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from app.application.dto import FilaPaciente
from app.infrastructure.ui.widgets.route_dots import ANCHO, pintar_ruta


class RouteDotsDelegate(QStyledItemDelegate):
    def paint(
        self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        if painter is None:
            return
        fila = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(fila, FilaPaciente):
            super().paint(painter, option, index)
            return

        painter.save()
        rect_celda = QRectF(option.rect)
        rect_dibujo = QRectF(
            rect_celda.center().x() - ANCHO / 2,
            rect_celda.top(),
            ANCHO,
            rect_celda.height(),
        )
        pintar_ruta(painter, rect_dibujo, fila.ruta)
        painter.restore()

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QWidget | None:
        return None
