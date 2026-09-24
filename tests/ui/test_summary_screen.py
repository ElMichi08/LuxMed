from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import ResumenLote
from app.infrastructure.ui.presenters.summary_presenter import SummaryPresenter
from app.infrastructure.ui.screens.summary_view import SummaryView
from tests.ui.fakes.dataset import resumen_lote_simulado
from tests.ui.fakes.ports import FakeBatchSummaryQuery


class VistaSummaryFalsa:
    def __init__(self) -> None:
        self.resumen_mostrado: ResumenLote | None = None

    def mostrar_resumen(self, resumen: ResumenLote) -> None:
        self.resumen_mostrado = resumen


def test_summary_presenter_carga_y_muestra() -> None:
    vista = VistaSummaryFalsa()
    presenter = SummaryPresenter(vista, FakeBatchSummaryQuery())

    presenter.cargar()

    assert vista.resumen_mostrado == resumen_lote_simulado()


def test_summary_view_filas_en_rojo_coincide_con_el_negocio() -> None:
    resumen = resumen_lote_simulado()
    assert resumen.filas_en_rojo == 117


def test_captura_summary_finalizado(capturar: Callable[..., Path]) -> None:
    vista = SummaryView()
    vista.mostrar_resumen(resumen_lote_simulado())
    ruta = capturar(vista, "summary_finalizado")
    assert ruta.exists()


def test_captura_summary_incompleto(capturar: Callable[..., Path]) -> None:
    vista = SummaryView()
    vista.mostrar_resumen(resumen_lote_simulado(incompleto=True))
    ruta = capturar(vista, "summary_incompleto")
    assert ruta.exists()


def test_resumen_lote_detenido_conserva_308_de_428_con_120_pendientes() -> None:
    resumen = resumen_lote_simulado(incompleto=True)

    assert resumen.incompleto
    assert resumen.procesados == 308
    assert resumen.pendientes == 120
    assert resumen.filas_en_rojo == 229
    assert resumen.expedientes_consolidados == 199
    assert resumen.hora_fin is None
    assert resumen.duracion is None
    assert sum(conteo.total for conteo in resumen.conteos) == resumen.procesados


def test_summary_view_lote_incompleto_indica_procesados_sobre_total() -> None:
    vista = SummaryView()

    vista.mostrar_resumen(resumen_lote_simulado(incompleto=True))

    assert "se procesaron 308 de 428" in vista._subtitulo.text()
    assert "229 filas quedarán en rojo" in vista._notas.text()
