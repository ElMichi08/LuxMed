from __future__ import annotations

from datetime import date

from app.application.mes_atencion import (
    ConteoMes,
    MesAtencion,
    detectar_meses,
    meses_recientes,
)


def test_nombre_de_carpeta_ordenable() -> None:
    assert MesAtencion(2026, 4).nombre_carpeta == "2026-04 Abril"
    assert MesAtencion(2026, 12).nombre == "Diciembre 2026"


def test_detecta_el_mes_predominante_primero() -> None:
    fechas = [date(2026, 4, 1), date(2026, 3, 30), date(2026, 4, 20), date(2026, 4, 9)]
    assert detectar_meses(fechas) == (
        ConteoMes(MesAtencion(2026, 4), 3),
        ConteoMes(MesAtencion(2026, 3), 1),
    )


def test_empate_prefiere_el_mes_mas_antiguo() -> None:
    assert detectar_meses([date(2026, 5, 1), date(2026, 4, 1)])[0].mes == MesAtencion(2026, 4)


def test_meses_recientes_cruza_el_anio() -> None:
    assert meses_recientes(MesAtencion(2026, 2), 3) == (
        MesAtencion(2026, 2),
        MesAtencion(2026, 1),
        MesAtencion(2025, 12),
    )
