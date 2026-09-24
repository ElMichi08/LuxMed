from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import PreviewLote
from app.application.ui_ports import IBatchIntake
from app.infrastructure.ui.presenters.upload_presenter import (
    MENSAJE_ERROR_LECTURA,
    UploadPresenter,
)
from app.infrastructure.ui.screens.upload_view import UploadView
from tests.ui.fakes.dataset import preview_lote_simulado
from tests.ui.fakes.ports import FakeBatchIntake


class VistaUploadFalsa:
    def __init__(self) -> None:
        self.cargando_historial: list[str | None] = []
        self.errores: list[str] = []
        self.error_limpiado = False

    def establecer_cargando(self, mensaje: str | None) -> None:
        self.cargando_historial.append(mensaje)

    def mostrar_error(self, mensaje: str) -> None:
        self.errores.append(mensaje)

    def limpiar_error(self) -> None:
        self.error_limpiado = True


class IntakeQueFalla(IBatchIntake):
    def leer_listado(self, ruta: Path) -> PreviewLote:
        raise RuntimeError("archivo corrupto")


def test_upload_presenter_lee_archivo_correctamente() -> None:
    vista = VistaUploadFalsa()
    previews: list[PreviewLote] = []
    presenter = UploadPresenter(vista, FakeBatchIntake(), previews.append)

    presenter.archivo_elegido("cartera_septiembre.xlsx")

    assert len(previews) == 1
    assert previews[0] == preview_lote_simulado()
    assert vista.cargando_historial == ["Leyendo archivo…", None]
    assert vista.errores == []


def test_upload_presenter_maneja_error_de_lectura() -> None:
    vista = VistaUploadFalsa()
    previews: list[PreviewLote] = []
    presenter = UploadPresenter(vista, IntakeQueFalla(), previews.append)

    presenter.archivo_elegido("roto.xlsx")

    assert previews == []
    assert vista.errores == [MENSAJE_ERROR_LECTURA]


def test_captura_upload_vacio(capturar: Callable[..., Path]) -> None:
    vista = UploadView()
    ruta = capturar(vista, "upload_vacio")
    assert ruta.exists()


def test_captura_upload_cargando(capturar: Callable[..., Path]) -> None:
    vista = UploadView()
    vista.establecer_cargando("Leyendo archivo…")
    ruta = capturar(vista, "upload_cargando")
    assert ruta.exists()


def test_captura_upload_con_error(capturar: Callable[..., Path]) -> None:
    vista = UploadView()
    vista.mostrar_error(MENSAJE_ERROR_LECTURA)
    ruta = capturar(vista, "upload_con_error")
    assert ruta.exists()
