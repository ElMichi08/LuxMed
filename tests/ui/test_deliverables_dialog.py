from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QLabel

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


ANCHO_CAPTURA = 560


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


CARPETA = Path("D:/LuxMed/salidas/2026-09")


def _textos_estado(dialogo: DeliverablesDialog) -> str:
    assert dialogo._pagina_estado is not None
    return " ".join(
        etiqueta.text() for etiqueta in dialogo._pagina_estado.findChildren(QLabel)
    )


def _textos(dialogo: DeliverablesDialog) -> str:
    return " ".join(etiqueta.text() for etiqueta in dialogo.findChildren(QLabel))


def test_dialogo_entregables_generar_no_cierra_y_muestra_generando() -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)

    dialogo._boton_generar.click()

    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert dialogo._boton_generar.text() == "Generando…"
    assert not dialogo._boton_generar.isEnabled()
    assert not dialogo._boton_cancelar.isEnabled()
    assert not dialogo._casilla_limpio.isEnabled()


def test_dialogo_entregables_mostrar_resultado_reemplaza_la_seleccion() -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)
    exportador = FakeDeliverablesExporter()
    dialogo.generar_solicitado.connect(
        lambda seleccion: dialogo.mostrar_resultado(exportador.exportar(seleccion))
    )
    dialogo.show()

    dialogo._boton_generar.click()

    textos = _textos_estado(dialogo)
    assert not dialogo._pagina_seleccion.isVisible()
    assert "Entregables generados" in textos
    assert "Excel limpio · 428 filas" in textos
    assert "Excel auditado · 428 filas · 117 en rojo" in textos
    assert "Expedientes consolidados · 311 archivos" in textos
    assert str(CARPETA) in textos
    assert dialogo._boton_abrir_carpeta.isVisible()


def test_dialogo_entregables_resultado_omite_lo_no_seleccionado() -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)
    dialogo._casilla_expedientes.setChecked(False)
    exportador = FakeDeliverablesExporter()
    dialogo.generar_solicitado.connect(
        lambda seleccion: dialogo.mostrar_resultado(exportador.exportar(seleccion))
    )

    dialogo._boton_generar.click()

    assert "Expedientes consolidados" not in _textos_estado(dialogo)


def test_dialogo_entregables_mostrar_error_sin_abrir_carpeta() -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)
    dialogo.show()
    dialogo._boton_generar.click()

    dialogo.mostrar_error("TimeoutError")

    textos = _textos_estado(dialogo)
    assert "No se pudieron generar los entregables" in textos
    assert "TimeoutError" in textos
    assert not hasattr(dialogo, "_boton_abrir_carpeta")


def test_dialogo_entregables_lote_detenido_indica_incompleto() -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(incompleto=True), CARPETA)

    textos = _textos(dialogo)

    assert "308 de 428 · incompleto" in textos
    assert "428 filas · 229 en rojo" in textos
    assert "199 archivos" in textos


def test_captura_dialogo_entregables_lote_detenido(
    capturar: Callable[..., Path],
) -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(incompleto=True), CARPETA)
    tamano = dialogo.sizeHint()
    ruta = capturar(
        dialogo, "dialogo_entregables_detenido", tamano.width(), tamano.height()
    )
    assert ruta.exists()


def test_captura_dialogo_entregables_resultado(capturar: Callable[..., Path]) -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)
    exportador = FakeDeliverablesExporter()
    dialogo.generar_solicitado.connect(
        lambda seleccion: dialogo.mostrar_resultado(exportador.exportar(seleccion))
    )
    dialogo._boton_generar.click()
    ruta = capturar(dialogo, "dialogo_entregables_resultado", ANCHO_CAPTURA, 420)
    assert ruta.exists()


def test_captura_dialogo_entregables_error(capturar: Callable[..., Path]) -> None:
    dialogo = DeliverablesDialog(resumen_lote_simulado(), CARPETA)
    dialogo._boton_generar.click()
    dialogo.mostrar_error("TimeoutError")
    ruta = capturar(dialogo, "dialogo_entregables_error", ANCHO_CAPTURA, 300)
    assert ruta.exists()
