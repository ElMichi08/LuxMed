from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel, QStackedWidget, QWidget

DURACION_FUNDIDO_MS = 180


def animar_opacidad(
    widget: QWidget,
    destino: float,
    al_terminar: Callable[[], None] | None = None,
    duracion_ms: int = DURACION_FUNDIDO_MS,
) -> QPropertyAnimation:
    efecto = widget.graphicsEffect()
    if not isinstance(efecto, QGraphicsOpacityEffect):
        efecto = QGraphicsOpacityEffect(widget)
        efecto.setOpacity(1.0 - destino)
        widget.setGraphicsEffect(efecto)
    animacion = QPropertyAnimation(efecto, b"opacity", widget)
    animacion.setDuration(duracion_ms)
    animacion.setStartValue(efecto.opacity())
    animacion.setEndValue(destino)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    if al_terminar is not None:
        animacion.finished.connect(al_terminar)
    animacion.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animacion


def cambiar_con_fundido(pila: QStackedWidget, destino: QWidget) -> None:
    if pila.currentWidget() is destino:
        return
    if not pila.isVisible():
        pila.setCurrentWidget(destino)
        return
    instantanea = QLabel(pila)
    instantanea.setPixmap(pila.grab())
    instantanea.resize(pila.size())
    pila.setCurrentWidget(destino)
    instantanea.show()
    instantanea.raise_()
    animar_opacidad(instantanea, 0.0, instantanea.deleteLater)
