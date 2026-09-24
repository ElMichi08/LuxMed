from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import ResultadoEntregables, SeleccionEntregables
from app.infrastructure.ui.dialogs.deliverables_dialog import DeliverablesDialog
from app.infrastructure.ui.presenters.deliverables_presenter import (
    DeliverablesPresenter,
)
from tests.ui.fakes.dataset import resumen_lote_simulado
from tests.ui.fakes.ports import FakeDeliverablesExporter, FakeOutputFolderSettings


def test_deliverables_presenter_exporta_y_notifica() -> None:
    exportador = FakeDeliverablesExporter()
    resultados: list[ResultadoEntregables] = []
    presenter = DeliverablesPresenter(exportador, resultados.append)
    seleccion = SeleccionEntregables(
        excel_limpio=True,
        excel_auditado=True,
        expedientes=True,
        carpeta_destino=Path("D:/LuxMed/salidas/2026-09"),
    )

    presenter.exportar(seleccion)

    assert len(resultados) == 1
    assert exportador.exportaciones == [seleccion]
    assert (
        resultados[0].expedientes_generados
        == resumen_lote_simulado().expedientes_consolidados
    )


def test_fake_output_folder_settings_guarda_y_obtiene() -> None:
    ajustes = FakeOutputFolderSettings()
    nueva_carpeta = Path("D:/otra/carpeta")

    ajustes.guardar(nueva_carpeta)

    assert ajustes.obtener() == nueva_carpeta


def test_dialogo_entregables_todas_marcadas_por_defecto() -> None:
    dialogo = DeliverablesDialog(
        resumen_lote_simulado(), Path("D:/LuxMed/salidas/2026-09")
    )

    assert dialogo._casilla_limpio.isChecked()
    assert dialogo._casilla_auditado.isChecked()
    assert dialogo._casilla_expedientes.isChecked()
    assert dialogo._boton_generar.text() == "Generar 3 entregables"


def test_dialogo_entregables_desmarcar_actualiza_boton() -> None:
    dialogo = DeliverablesDialog(
        resumen_lote_simulado(), Path("D:/LuxMed/salidas/2026-09")
    )

    dialogo._casilla_expedientes.setChecked(False)

    assert dialogo._boton_generar.text() == "Generar 2 entregables"


def test_dialogo_entregables_ninguna_marcada_deshabilita_boton() -> None:
    dialogo = DeliverablesDialog(
        resumen_lote_simulado(), Path("D:/LuxMed/salidas/2026-09")
    )

    for casilla in (
        dialogo._casilla_limpio,
        dialogo._casilla_auditado,
        dialogo._casilla_expedientes,
    ):
        casilla.setChecked(False)

    assert not dialogo._boton_generar.isEnabled()


def test_dialogo_entregables_generar_emite_seleccion() -> None:
    dialogo = DeliverablesDialog(
        resumen_lote_simulado(), Path("D:/LuxMed/salidas/2026-09")
    )
    dialogo._casilla_expedientes.setChecked(False)

    emitidas: list[SeleccionEntregables] = []
    dialogo.generar_solicitado.connect(emitidas.append)
    dialogo._boton_generar.click()

    assert len(emitidas) == 1
    assert emitidas[0].excel_limpio is True
    assert emitidas[0].expedientes is False
    assert emitidas[0].carpeta_destino == Path("D:/LuxMed/salidas/2026-09")


def test_captura_dialogo_entregables(capturar: Callable[..., Path]) -> None:
    dialogo = DeliverablesDialog(
        resumen_lote_simulado(), Path("D:/LuxMed/salidas/2026-09")
    )
    tamano = dialogo.sizeHint()
    ruta = capturar(dialogo, "dialogo_entregables", tamano.width(), tamano.height())
    assert ruta.exists()
