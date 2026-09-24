from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QToolButton

from app.infrastructure.ui.shell.rail import Rail
from app.infrastructure.ui.theme.tokens import GEOMETRIA

BORDE_IZQUIERDO = 3


def _riel_mostrado() -> Rail:
    riel = Rail()
    riel.show()
    for _ in range(3):
        QApplication.processEvents()
    return riel


def _botones(riel: Rail) -> tuple[QToolButton, ...]:
    return (
        riel.boton_lote,
        riel.boton_errores,
        riel.boton_historial,
        riel.boton_ajustes,
    )


def test_todos_los_botones_del_riel_ocupan_el_ancho_completo() -> None:
    riel = _riel_mostrado()

    anchos = {boton.text(): boton.geometry().width() for boton in _botones(riel)}

    assert set(anchos.values()) == {GEOMETRIA.riel_ancho}


def test_todos_los_botones_del_riel_empiezan_en_el_borde_izquierdo() -> None:
    riel = _riel_mostrado()

    posiciones = {boton.geometry().x() for boton in _botones(riel)}

    assert posiciones == {0}


def test_las_etiquetas_del_riel_caben_sin_desbordar() -> None:
    riel = _riel_mostrado()

    for boton in _botones(riel):
        texto = boton.fontMetrics().horizontalAdvance(boton.text())
        assert texto + BORDE_IZQUIERDO <= GEOMETRIA.riel_ancho, boton.text()


def test_marcar_otro_destino_no_cambia_el_ancho_de_lote() -> None:
    riel = _riel_mostrado()

    riel.boton_errores.setChecked(True)
    QApplication.processEvents()

    assert riel.boton_lote.geometry().width() == GEOMETRIA.riel_ancho
