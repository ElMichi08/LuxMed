from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QLabel

from app.infrastructure.ui.dialogs.batch_stopped_dialog import BatchStoppedDialog
from app.infrastructure.ui.screens.processing_view import ProcessingView
from tests.ui.fakes.dataset import resultado_detenido_simulado


def test_captura_dialogo_lote_detenido(capturar: Callable[..., Path]) -> None:
    dialogo = BatchStoppedDialog(resultado_detenido_simulado())
    tamano = dialogo.sizeHint()
    ruta = capturar(dialogo, "dialogo_lote_detenido", tamano.width(), tamano.height())
    assert ruta.exists()


def test_processing_view_muestra_y_oculta_dialogo_detenido() -> None:
    vista = ProcessingView()
    resultado = resultado_detenido_simulado()

    vista.mostrar_lote_detenido(resultado)
    assert vista._dialogo_detenido is not None

    vista.ocultar_lote_detenido()
    assert vista._dialogo_detenido is None


def test_dialogo_lote_detenido_muestra_procesados_y_pendientes_reales() -> None:
    dialogo = BatchStoppedDialog(resultado_detenido_simulado())

    textos = " ".join(etiqueta.text() for etiqueta in dialogo.findChildren(QLabel))

    assert "Los 308 pacientes ya procesados" in textos
    assert "los 120 pendientes" in textos
