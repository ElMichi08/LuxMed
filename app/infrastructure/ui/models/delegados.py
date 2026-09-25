from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QModelIndex, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from app.application.progreso import PasosRuta
from app.domain.entities import EstadoPaso
from app.infrastructure.ui.models.columnas import FILA_ROLE
from app.infrastructure.ui.theme.fuentes import fuente_mono
from app.infrastructure.ui.theme.tokens import COLORES, TIPOGRAFIA

ALTO_CHIP = 18
RELLENO_CHIP = 8
DIAMETRO_PUNTO = 10
LARGO_CONECTOR = 12
SEPARACION = 6
OPACIDAD_ATENUADA = 0.4


@dataclass(frozen=True, slots=True)
class ColoresTono:
    fondo: str
    texto: str
    borde: str


COLORES_TONO = {
    "exito": ColoresTono(COLORES.verde_fondo, COLORES.verde, COLORES.verde_borde),
    "proceso": ColoresTono(COLORES.indigo_borde, COLORES.indigo, COLORES.indigo_borde),
    "neutro": ColoresTono(COLORES.boton, COLORES.tinta_sec, COLORES.filete_suave),
    "alerta": ColoresTono(COLORES.rojo_fondo, COLORES.rojo, COLORES.rojo_borde),
}

ETIQUETA_PASO = {
    EstadoPaso.PENDIENTE: "Pendiente",
    EstadoPaso.EN_CURSO: "En curso",
    EstadoPaso.HECHO: "Hecho",
    EstadoPaso.OMITIDO: "Omitido",
    EstadoPaso.FALLIDO: "Fallido",
}

Chip = tuple[str, str]
ChipDe = Callable[[object], Chip | None]
RutaDe = Callable[[object], tuple[PasosRuta, bool] | None]


def pintar_chip(painter: QPainter, area: QRectF, texto: str, tono: str) -> None:
    colores = COLORES_TONO[tono]
    painter.save()
    painter.setFont(fuente_mono(TIPOGRAFIA.chip, QFont.Weight.DemiBold))
    ancho = painter.fontMetrics().horizontalAdvance(texto) + RELLENO_CHIP * 2
    chip = QRectF(area.left(), area.center().y() - ALTO_CHIP / 2, ancho, ALTO_CHIP)
    painter.setPen(QPen(QColor(colores.borde), 1))
    painter.setBrush(QColor(colores.fondo))
    painter.drawRect(chip.adjusted(0.5, 0.5, -0.5, -0.5))
    painter.setPen(QColor(colores.texto))
    painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, texto)
    painter.restore()


def texto_tooltip_ruta(pasos: PasosRuta) -> str:
    return " · ".join(
        f"P{posicion}: {ETIQUETA_PASO[paso]}" for posicion, paso in enumerate(pasos.como_tupla(), 1)
    )


def ancho_ruta() -> int:
    return DIAMETRO_PUNTO * 3 + (LARGO_CONECTOR + SEPARACION * 2) * 2


def pintar_ruta(painter: QPainter, area: QRectF, pasos: PasosRuta, atenuada: bool) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if atenuada:
        painter.setOpacity(OPACIDAD_ATENUADA)
    estados = pasos.como_tupla()
    inicio = area.center().x() - ancho_ruta() / 2
    centro_y = area.center().y()
    paso_x = DIAMETRO_PUNTO + LARGO_CONECTOR + SEPARACION * 2
    centros = [inicio + DIAMETRO_PUNTO / 2 + posicion * paso_x for posicion in range(3)]
    for posicion in range(2):
        _pintar_conector(painter, centros[posicion], centros[posicion + 1], centro_y, estados[posicion], estados[posicion + 1])
    for centro_x, estado in zip(centros, estados):
        _pintar_punto(painter, QPointF(centro_x, centro_y), estado)
    painter.restore()


def _color_conector(anterior: EstadoPaso, siguiente: EstadoPaso) -> str:
    if siguiente is EstadoPaso.FALLIDO:
        return COLORES.rojo
    if siguiente is EstadoPaso.EN_CURSO:
        return COLORES.indigo
    if anterior is EstadoPaso.HECHO and siguiente is EstadoPaso.HECHO:
        return COLORES.verde
    return COLORES.filete


def _pintar_conector(
    painter: QPainter, desde: float, hasta: float, y: float, anterior: EstadoPaso, siguiente: EstadoPaso
) -> None:
    omitido = EstadoPaso.OMITIDO in (anterior, siguiente)
    pluma = QPen(QColor(COLORES.tinta_ter if omitido else _color_conector(anterior, siguiente)), 1)
    if omitido:
        pluma.setDashPattern([2.0, 2.0])
    painter.setPen(pluma)
    radio = DIAMETRO_PUNTO / 2
    painter.drawLine(QPointF(desde + radio + SEPARACION, y), QPointF(hasta - radio - SEPARACION, y))


def _pintar_punto(painter: QPainter, centro: QPointF, estado: EstadoPaso) -> None:
    radio = DIAMETRO_PUNTO / 2
    rellenos = {
        EstadoPaso.HECHO: COLORES.verde,
        EstadoPaso.EN_CURSO: COLORES.indigo,
        EstadoPaso.FALLIDO: COLORES.rojo,
    }
    if estado in rellenos:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(rellenos[estado]))
        painter.drawEllipse(centro, radio, radio)
        if estado is EstadoPaso.FALLIDO:
            _pintar_aspa(painter, centro, radio * 0.45)
        return
    pluma = QPen(QColor(COLORES.tinta_ter if estado is EstadoPaso.OMITIDO else COLORES.filete), 1)
    if estado is EstadoPaso.OMITIDO:
        pluma.setDashPattern([2.0, 2.0])
        painter.setBrush(Qt.BrushStyle.NoBrush)
    else:
        painter.setBrush(QColor(COLORES.blanco))
    painter.setPen(pluma)
    painter.drawEllipse(centro, radio - 0.5, radio - 0.5)


def _pintar_aspa(painter: QPainter, centro: QPointF, margen: float) -> None:
    painter.setPen(QPen(QColor(COLORES.blanco), 1.2))
    painter.drawLine(centro + QPointF(-margen, -margen), centro + QPointF(margen, margen))
    painter.drawLine(centro + QPointF(-margen, margen), centro + QPointF(margen, -margen))


class _DelegadoBase(QStyledItemDelegate):
    def _fondo(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> QStyleOptionViewItem:
        opcion = QStyleOptionViewItem(option)
        self.initStyleOption(opcion, index)
        opcion.text = ""
        widget = opcion.widget
        estilo = widget.style() if isinstance(widget, QWidget) else None
        if estilo is not None:
            estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opcion, painter, widget)
        return opcion


class ChipDelegate(_DelegadoBase):
    def __init__(self, chip_de: ChipDe, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._chip_de = chip_de

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if painter is None:
            return
        chip = self._chip_de(index.data(FILA_ROLE))
        if chip is None:
            super().paint(painter, option, index)
            return
        opcion = self._fondo(painter, option, index)
        pintar_chip(painter, QRectF(opcion.rect).adjusted(10, 0, -10, 0), *chip)


class RutaDelegate(_DelegadoBase):
    def __init__(self, ruta_de: RutaDe, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ruta_de = ruta_de

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if painter is None:
            return
        opcion = self._fondo(painter, option, index)
        ruta = self._ruta_de(index.data(FILA_ROLE))
        if ruta is not None:
            pintar_ruta(painter, QRectF(opcion.rect), *ruta)
