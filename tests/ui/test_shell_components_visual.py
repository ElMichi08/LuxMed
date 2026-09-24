from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.infrastructure.ui.shell.log_panel import LogPanel
from app.infrastructure.ui.shell.status_bar import StatusBar
from app.infrastructure.ui.shell.top_bar import TopBar


def test_captura_top_bar_con_lote(capturar: Callable[..., Path]) -> None:
    barra = TopBar()
    barra.establecer_sesion("admision.01", "A0")
    barra.establecer_lote(
        "cartera_septiembre.xlsx · Lote 2026-09-08-01 · 428 filas",
        "En curso",
        "proceso",
    )
    ruta = capturar(barra, "top_bar_con_lote", 1280, 48)
    assert ruta.exists()


def test_captura_top_bar_sin_lote(capturar: Callable[..., Path]) -> None:
    barra = TopBar()
    barra.establecer_sesion("admision.01", "A0")
    barra.establecer_sin_lote()
    ruta = capturar(barra, "top_bar_sin_lote", 1280, 48)
    assert ruta.exists()


def test_captura_status_bar(capturar: Callable[..., Path]) -> None:
    barra = StatusBar()
    barra.establecer_actividad("Consultando: Portal 2")
    barra.establecer_progreso(296, 428)
    ruta = capturar(barra, "status_bar", 1280, 28)
    assert ruta.exists()


def test_captura_log_panel_expandido(capturar: Callable[..., Path]) -> None:
    panel = LogPanel()
    panel.agregar_linea("14:18:22 Portal 1 · consulta completada")
    panel.agregar_linea("14:19:04 Portal 2 · consulta completada")
    panel.agregar_linea("14:22:07 Portal 1 · consulta completada")
    panel.alternar()
    contenedor = QWidget()
    disposicion = QVBoxLayout(contenedor)
    disposicion.setContentsMargins(0, 0, 0, 0)
    disposicion.addWidget(panel)
    ruta = capturar(contenedor, "log_panel_expandido", 1280, 220)
    assert ruta.exists()
