from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from app.application.dto import EstadoPaciente
from app.infrastructure.ui.theme.tokens import COLORES, TIPOGRAFIA
from app.infrastructure.ui.widgets.status_chip import TONO_POR_ESTADO

_COLORES_POR_TONO = {
    "exito": (COLORES.verde_fondo, COLORES.verde, COLORES.verde_borde),
    "proceso": (COLORES.indigo_suave, COLORES.indigo, COLORES.indigo_borde),
    "neutro": (COLORES.filete_suave, COLORES.tinta_sec, COLORES.filete),
    "alerta": (COLORES.rojo_fondo, COLORES.rojo, COLORES.rojo_borde),
}
ALTO_CHIP = 18
PADDING_HORIZONTAL = 8


class StatusChipDelegate(QStyledItemDelegate):
    def paint(
        self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        if painter is None:
            return
        fila = index.data(Qt.ItemDataRole.UserRole)
        estado = getattr(fila, "estado", None)
        if not isinstance(estado, EstadoPaciente):
            super().paint(painter, option, index)
            return
        tono = TONO_POR_ESTADO[estado]
        fondo, texto_color, borde = _COLORES_POR_TONO[tono]

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fuente = QFont(
            TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_chip, TIPOGRAFIA.peso_semibold
        )
        painter.setFont(fuente)
        metrica = painter.fontMetrics()
        ancho_texto = metrica.horizontalAdvance(estado.value)

        rect_celda = QRectF(option.rect)
        ancho_chip = ancho_texto + PADDING_HORIZONTAL * 2
        rect_chip = QRectF(
            rect_celda.left(),
            rect_celda.center().y() - ALTO_CHIP / 2,
            min(ancho_chip, rect_celda.width() - 4),
            ALTO_CHIP,
        )

        painter.setPen(QColor(borde))
        painter.setBrush(QColor(fondo))
        painter.drawRect(rect_chip)

        painter.setPen(QColor(texto_color))
        painter.drawText(rect_chip, Qt.AlignmentFlag.AlignCenter, estado.value)

        painter.restore()

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QWidget | None:
        return None
