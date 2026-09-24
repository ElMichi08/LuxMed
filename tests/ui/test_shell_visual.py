from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.infrastructure.ui.shell.main_window import MainWindow
from app.infrastructure.ui.shell.navigation import Destino


def test_captura_shell_lote(capturar: Callable[..., Path]) -> None:
    ventana = MainWindow()
    ruta = capturar(ventana, "shell_lote")
    assert ruta.exists()


def test_captura_shell_errores(capturar: Callable[..., Path]) -> None:
    ventana = MainWindow()
    ventana.riel.boton_errores.setChecked(True)
    ventana.riel.boton_errores.establecer_contador(4)
    ruta = capturar(ventana, "shell_errores")
    assert ruta.exists()


def test_captura_shell_ajustes(capturar: Callable[..., Path]) -> None:
    ventana = MainWindow()
    ventana.riel.boton_ajustes.setChecked(True)
    ruta = capturar(ventana, "shell_ajustes")
    assert ruta.exists()


def test_navegacion_cambia_pagina_actual(capturar: Callable[..., Path]) -> None:
    ventana = MainWindow()
    capturar(ventana, "shell_navegacion_inicial")
    assert ventana.navegacion.pagina_actual() == Destino.LOTE
    ventana.riel.boton_ajustes.setChecked(True)
    assert ventana.navegacion.pagina_actual() == Destino.AJUSTES


def test_historial_deshabilitado(capturar: Callable[..., Path]) -> None:
    ventana = MainWindow()
    capturar(ventana, "shell_riel_historial")
    assert not ventana.riel.boton_historial.isEnabled()
