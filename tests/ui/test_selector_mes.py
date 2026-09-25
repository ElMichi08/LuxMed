from __future__ import annotations

from pytestqt.qtbot import QtBot

from app.application.mes_atencion import ConteoMes, MesAtencion
from app.infrastructure.ui.widgets.selector_mes import SelectorMes


def test_ofrece_meses_del_excel_y_seis_anteriores_sin_el_mes_en_curso(qtbot: QtBot) -> None:
    selector = SelectorMes()
    qtbot.addWidget(selector)
    selector.establecer_opciones((ConteoMes(MesAtencion(2026, 4), 6),), MesAtencion(2026, 9))
    opciones = [selector.itemData(posicion) for posicion in range(selector.count())]
    assert opciones == [
        MesAtencion(2026, 4),
        MesAtencion(2026, 8),
        MesAtencion(2026, 7),
        MesAtencion(2026, 6),
        MesAtencion(2026, 5),
        MesAtencion(2026, 3),
    ]
    assert selector.mes == MesAtencion(2026, 4)


def test_cruza_el_cambio_de_anio(qtbot: QtBot) -> None:
    selector = SelectorMes()
    qtbot.addWidget(selector)
    selector.establecer_opciones((), MesAtencion(2027, 2))
    assert selector.itemData(0) == MesAtencion(2027, 1)
    assert selector.itemData(selector.count() - 1) == MesAtencion(2026, 8)
