from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from app.infrastructure.ui.bootstrap import preparar

CAPTURAS_DIR = Path(__file__).resolve().parent / "_capturas"

Capturador = Callable[..., Path]


@pytest.fixture(scope="session", autouse=True)
def _tema_aplicado(qapp: QApplication) -> None:
    preparar(qapp)


@pytest.fixture
def capturar(qtbot: QtBot) -> Capturador:
    def _capturar(
        widget: QWidget, nombre: str, ancho: int = 1280, alto: int = 800
    ) -> Path:
        qtbot.addWidget(widget)
        widget.resize(ancho, alto)
        widget.show()
        qtbot.waitExposed(widget)
        CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)
        ruta = CAPTURAS_DIR / f"{nombre}.png"
        widget.grab().save(str(ruta))
        return ruta

    return _capturar
