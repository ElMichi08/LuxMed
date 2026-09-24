from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QDialog

from app.infrastructure.ui.dialogs.close_confirmation_dialog import (
    CloseConfirmationDialog,
)


def test_close_confirmation_dialog_cancelar_rechaza() -> None:
    dialogo = CloseConfirmationDialog()

    dialogo.boton_cancelar.click()

    assert dialogo.result() == QDialog.DialogCode.Rejected


def test_close_confirmation_dialog_confirmar_acepta() -> None:
    dialogo = CloseConfirmationDialog()

    dialogo.boton_confirmar.click()

    assert dialogo.result() == QDialog.DialogCode.Accepted


def test_captura_close_confirmation_dialog(capturar: Callable[..., Path]) -> None:
    dialogo = CloseConfirmationDialog()
    tamano = dialogo.sizeHint()
    ruta = capturar(
        dialogo, "dialogo_confirmar_cierre", tamano.width(), tamano.height()
    )
    assert ruta.exists()
